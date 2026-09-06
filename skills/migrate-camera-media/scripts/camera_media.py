#!/usr/bin/env python3
"""Camera-card offload, verification, and separately authorized cleanup (macOS)."""
import argparse
import concurrent.futures as cf
from collections import deque
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import shutil
import stat
import struct
import subprocess
import sys
import time

VERSION = '0.1.0'
CHUNK = 8 * 1024 * 1024


def fail(message):
    raise RuntimeError(message)


def now():
    return dt.datetime.now().astimezone().isoformat()


def save(path, value):
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def safe_rel(rel):
    p = PurePosixPath(rel)
    if not rel or p.is_absolute() or '..' in p.parts or any(c in rel for c in '\n\r\\'):
        fail('Unsafe manifest path: ' + repr(rel))
    return rel


def snapshot(root):
    files, dirs = {}, {}
    if root.is_symlink() or not root.is_dir():
        fail('Source must be an existing, non-symlink directory')
    def walk_error(exc):
        raise exc
    for base, subdirs, names in os.walk(root, onerror=walk_error, followlinks=False):
        subdirs.sort(); names.sort()
        rel = Path(base).relative_to(root).as_posix()
        st = os.lstat(base)
        dirs[rel] = {'mtime_ns': st.st_mtime_ns, 'atime_ns': st.st_atime_ns}
        for name in subdirs:
            if not stat.S_ISDIR(os.lstat(Path(base) / name).st_mode):
                fail('Symlink or special directory found')
        for name in names:
            path = Path(base) / name
            st = path.lstat()
            if not stat.S_ISREG(st.st_mode):
                fail('Symlink or special file found: ' + str(path))
            rel = safe_rel(path.relative_to(root).as_posix())
            files[rel] = {'size': st.st_size, 'mtime_ns': st.st_mtime_ns,
                          'atime_ns': st.st_atime_ns, 'flags': getattr(st, 'st_flags', 0)}
    return {'files': files, 'directories': dirs}


def signature(e):
    return e['size'], e['mtime_ns']


def difference(before, after):
    a, b = before['files'], after['files']
    return {'added': sorted(b.keys() - a.keys()), 'removed': sorted(a.keys() - b.keys()),
            'changed': sorted(p for p in a.keys() & b.keys() if signature(a[p]) != signature(b[p])),
            'directories_added': sorted(after['directories'].keys() - before['directories'].keys()),
            'directories_removed': sorted(before['directories'].keys() - after['directories'].keys())}


def unchanged(before, after):
    d = difference(before, after)
    if any(d.values()):
        fail('Source changed; preserve old session and reconcile before continuing: ' + json.dumps(d))


def volume_info(path):
    if sys.platform != 'darwin':
        fail('This CLI supports macOS only')
    p = path
    while not p.exists():
        p = p.parent
    p = p.resolve(strict=True)
    while not os.path.ismount(p):
        p = p.parent
    data = plistlib.loads(subprocess.check_output(['diskutil', 'info', '-plist', str(p)]))
    mount = data.get('MountPoint')
    if not mount or not os.path.ismount(mount) or not data.get('VolumeUUID'):
        fail('Missing mounted-volume identity')
    return {'uuid': data['VolumeUUID'].upper(), 'mount': mount,
            'filesystem': data.get('FilesystemType'), 'device': data.get('DeviceIdentifier'),
            'internal': data.get('Internal'), 'size': data.get('VolumeSize'),
            'external_root': mount.startswith('/Volumes/') and not data.get('Internal')}


def usb_links():
    roots = plistlib.loads(subprocess.check_output(['ioreg', '-a', '-p', 'IOUSB', '-l']))
    if isinstance(roots, dict): roots = [roots]
    found = []
    def walk(node):
        if 'UsbLinkSpeed' in node:
            found.append({'name': node.get('USB Product Name', node.get('IORegistryEntryName')),
                          'link_bits_per_second': node['UsbLinkSpeed'], 'location_id': node.get('locationID')})
        for child in node.get('IORegistryEntryChildren', []): walk(child)
    for root in roots: walk(root)
    return found


def nocache(f):
    if sys.platform == 'darwin':
        fcntl.fcntl(f.fileno(), 48, 1)


def hash_file(path):
    digest, size = hashlib.sha256(), 0
    with path.open('rb', buffering=0) as f:
        nocache(f)
        while True:
            chunk = f.read(CHUNK)
            if not chunk: break
            digest.update(chunk); size += len(chunk)
    return size, digest.hexdigest()


def metadata(src, dst, entry):
    # macOS system Python may lack os.listxattr; use the established xattr module.
    import xattr
    for name in xattr.listxattr(str(src)):
        xattr.setxattr(str(dst), name, xattr.getxattr(str(src), name))
    os.utime(dst, ns=(entry['atime_ns'], entry['mtime_ns']))


def write_all(f, chunk):
    view = memoryview(chunk)
    while view:
        n = f.write(view)
        if not n: fail('Zero-byte write')
        view = view[n:]
    return len(chunk)


def flush(path):
    with path.open('rb', buffering=0) as f:
        os.fsync(f.fileno())
        if sys.platform == 'darwin':
            try: fcntl.fcntl(f.fileno(), 51)
            except OSError as exc:
                if exc.errno not in (errno.EINVAL, errno.ENOTSUP, errno.ENOTTY): raise
                return {'fsync': True, 'fullfsync': False, 'reason': str(exc)}
    return {'fsync': True, 'fullfsync': sys.platform == 'darwin'}


class Session:
    def __init__(self, source, destination, report, source_uuid, destination_uuid, identity=volume_info):
        self.source, self.dest, self.report = map(lambda p: Path(p).absolute(), (source, destination, report))
        self.source_uuid, self.dest_uuid = source_uuid.upper(), destination_uuid.upper()
        self.identity = identity
        self.started, self.last_progress = time.monotonic(), 0
        self.state = {'version': VERSION, 'status': 'preflight', 'started_at': now(),
                      'source': str(self.source), 'destination': str(self.dest),
                      'copy_bytes': 0, 'verify_bytes': 0, 'copied_files': 0, 'verified_files': 0}

    def identities(self):
        if any(p.is_symlink() for p in (self.source, self.dest, self.report)):
            fail('Session roots must not be symlinks')
        paths = [p.resolve() for p in (self.source, self.dest, self.report)]
        for i, a in enumerate(paths):
            for b in paths[i+1:]:
                if a == b or a in b.parents or b in a.parents:
                    fail('Source, card destination, and report directory must not overlap')
        src, dst, rep = map(self.identity, (self.source, self.dest, self.report))
        if src['uuid'] != self.source_uuid or dst['uuid'] != self.dest_uuid or rep['uuid'] != self.dest_uuid:
            fail('Volume UUID mismatch; do not reuse device numbers after reconnection')
        if paths[0] != Path(src['mount']) or not src.get('external_root'):
            fail('Source must be the external card volume root')
        if src['uuid'] == dst['uuid']:
            fail('Destination is on the source volume')

    def progress(self, force=False):
        t = time.monotonic()
        if force or t-self.last_progress >= 15:
            self.state['elapsed_seconds'] = round(t-self.started, 2)
            save(self.report/'status.json', self.state)
            print(json.dumps(self.state, ensure_ascii=False), flush=True)
            self.last_progress = t

    def load(self):
        self.identities()
        manifest = read(self.report/'manifest.json')
        expected = {'source': str(self.source), 'destination': str(self.dest),
                    'source_uuid': self.source_uuid, 'destination_uuid': self.dest_uuid}
        if any(manifest.get(k) != v for k, v in expected.items()): fail('Session identity mismatch')
        for group in ('files', 'directories'):
            for rel in manifest['snapshot'][group]: safe_rel(rel)
        if not set(manifest['files']).issubset(manifest['snapshot']['files']): fail('Unexpected manifest files')
        return manifest

    def paths(self, manifest):
        actual = snapshot(self.dest)
        expected = manifest['snapshot']
        if not set(expected['files']).issubset(actual['files']) or set(actual['directories']) != set(expected['directories']):
            fail('Missing payload paths or unexpected directories in destination')
        extras = []
        for rel in sorted(actual['files'].keys()-expected['files'].keys()):
            p = Path(rel); counterpart = (p.parent/p.name[2:]).as_posix()
            if not p.name.startswith('._') or counterpart not in set(expected['files']) | set(expected['directories']):
                fail('Unexpected destination file: '+rel)
            with (self.dest/rel).open('rb') as f: head = f.read(8)
            if head != struct.pack('>II', 0x00051607, 0x00020000): fail('Unrecognized sidecar: '+rel)
            extras.append(rel)
        return actual, extras

    def verify(self, manifest=None):
        manifest = manifest or self.load()
        self.identities()
        expected = manifest['snapshot']
        if set(manifest['files']) != set(expected['files']): fail('Copy is incomplete')
        manifest['status'] = 'verifying'
        save(self.report/'manifest.json', manifest)
        self.state.update(status='verifying', verify_bytes=0, verified_files=0)
        self.progress(True)
        actual, extras = self.paths(manifest)
        for rel, entry in manifest['files'].items():
            if actual['files'][rel]['size'] != expected['files'][rel]['size']: fail('Size mismatch: '+rel)
            digest, count = hashlib.sha256(), 0
            self.state['current_file'] = rel
            with (self.dest/rel).open('rb', buffering=0) as f:
                nocache(f)
                while True:
                    chunk = f.read(CHUNK)
                    if not chunk: break
                    digest.update(chunk); count += len(chunk); self.state['verify_bytes'] += len(chunk)
                    self.progress()
            if count != expected['files'][rel]['size'] or digest.hexdigest() != entry['sha256']:
                fail('SHA-256 mismatch: '+rel)
            entry.update(verified=True, destination_sha256=digest.hexdigest(),
                         destination_mtime_ns=(self.dest/rel).stat().st_mtime_ns)
            self.state['verified_files'] += 1
        unchanged(expected, snapshot(self.source)); self.identities()
        self.paths(manifest)
        manifest.update(status='verified', verified_at=now(), generated_appledouble=extras)
        save(self.report/'manifest.json', manifest)
        with (self.report/'checksums.sha256').open('w', encoding='utf-8') as f:
            for rel, e in manifest['files'].items(): f.write(e['sha256']+'  '+rel+'\n')
            f.flush(); os.fsync(f.fileno())
        self.state.update(status='verified', completed_at=now(), generated_appledouble_count=len(extras))
        self.progress(True)
        return manifest

    def transfer(self):
        import xattr  # Fail before creating destinations if dependency is missing.
        self.identities(); current = snapshot(self.source)
        total = sum(e['size'] for e in current['files'].values())
        if self.report.exists() or self.dest.exists():
            manifest = self.load()
            unchanged(manifest['snapshot'], current)
            snapshot(self.dest)  # Reject existing symlinks before any resumed writes.
        else:
            manifest = {'version': VERSION, 'source': str(self.source), 'destination': str(self.dest),
                        'source_uuid': self.source_uuid, 'destination_uuid': self.dest_uuid,
                        'status': 'copying', 'algorithm': 'SHA-256', 'snapshot': current, 'files': {}}
            self.report.mkdir(parents=True); self.dest.mkdir(parents=True)
            save(self.report/'manifest.json', manifest)
        if manifest['status'] == 'verified':
            return self.verify(manifest)
        # Conservative admission avoids running out of space during a resumed transfer.
        if shutil.disk_usage(self.dest).free < total + 1024**3: fail('Insufficient free space')
        self.state.update(status='copying', total_files=len(current['files']), total_bytes=total)
        for rel in current['directories']:
            if rel != '.': (self.dest/rel).mkdir(exist_ok=True)
        self.progress(True)
        with cf.ThreadPoolExecutor(max_workers=1) as writer, cf.ThreadPoolExecutor(max_workers=1) as hasher:
            for rel, entry in current['files'].items():
                self.identities()
                self.state['current_file'] = rel
                src, dst = self.source/rel, self.dest/rel
                partial = dst.with_name(dst.name+'.partial')
                if dst.exists():
                    recorded = manifest['files'].get(rel)
                    if not recorded or hash_file(dst) != (entry['size'], recorded['sha256']):
                        fail('Existing destination is unverified; preserve it: '+rel)
                    self.state['copy_bytes'] += entry['size']; self.state['copied_files'] += 1
                    continue
                prefix = partial.stat().st_size if partial.exists() else 0
                if partial.is_symlink() or prefix > entry['size']: fail('Invalid partial file: '+rel)
                digest, count, pending = hashlib.sha256(), 0, deque()
                with src.open('rb', buffering=0) as sf:
                    nocache(sf)
                    st = os.fstat(sf.fileno())
                    if (st.st_size, st.st_mtime_ns) != signature(entry): fail('Source changed: '+rel)
                    if prefix:
                        self.state['status'] = 'checking_partial_prefix'; self.progress(True)
                        with partial.open('rb', buffering=0) as pf:
                            nocache(pf)
                            while count < prefix:
                                chunk = sf.read(min(CHUNK, prefix-count))
                                if not chunk or pf.read(len(chunk)) != chunk: fail('Partial prefix mismatch: '+rel)
                                digest.update(chunk); count += len(chunk); self.progress()
                        self.state['copy_bytes'] += prefix
                    self.state['status'] = 'copying'
                    with partial.open('ab' if partial.exists() else 'xb', buffering=0) as df:
                        nocache(df)
                        while True:
                            if len(pending) >= 4:
                                wf, hf = pending.popleft(); self.state['copy_bytes'] += wf.result(); hf.result()
                                self.progress()
                            chunk = sf.read(CHUNK)
                            if not chunk: break
                            count += len(chunk)
                            pending.append((writer.submit(write_all, df, chunk), hasher.submit(digest.update, chunk)))
                        for wf, hf in pending: self.state['copy_bytes'] += wf.result(); hf.result()
                        st = os.fstat(sf.fileno())
                        if count != entry['size'] or (st.st_size, st.st_mtime_ns) != signature(entry):
                            fail('Source changed or read length mismatch: '+rel)
                        os.fsync(df.fileno())
                metadata(src, partial, entry)
                # Save the hash before rename so a crash immediately after rename is resumable.
                manifest['files'][rel] = {'sha256': digest.hexdigest()}
                save(self.report/'manifest.json', manifest)
                if dst.exists(): fail('Destination appeared during copy: '+rel)
                os.rename(partial, dst)
                self.state['copied_files'] += 1; self.progress()
        for rel, entry in sorted(current['directories'].items(), key=lambda x: len(Path(x[0]).parts), reverse=True):
            metadata(self.source/rel, self.dest/rel, entry)
        if current['files']: self.state['flush'] = flush(self.dest/next(iter(current['files'])))
        self.state['copy_seconds'] = round(time.monotonic()-self.started, 2)
        return self.verify(manifest)

    def cleanup(self, apply=False):
        manifest = self.load()
        if manifest.get('status') != 'verified': fail('Cleanup requires completed verification')
        original, current = manifest['snapshot'], snapshot(self.source)
        unchanged(original, current)
        actual, extras = self.paths(manifest)
        if set(manifest['files']) != set(original['files']): fail('Incomplete manifest')
        protected, eligible = [], []
        for rel, src in current['files'].items():
            e = manifest['files'][rel]
            if not e.get('verified') or e.get('destination_sha256') != e['sha256']:
                fail('File verification missing: '+rel)
            if (actual['files'][rel]['size'], actual['files'][rel]['mtime_ns']) != (src['size'], e['destination_mtime_ns']):
                fail('Backup changed; run verify before cleanup: '+rel)
            flags = src.get('flags', 0)
            if flags & (getattr(stat, 'UF_IMMUTABLE', 2) | getattr(stat, 'SF_IMMUTABLE', 0x20000)):
                protected.append(rel)
            else: eligible.append(rel)
        plan = {'status': 'plan_only', 'created_at': now(), 'source': str(self.source),
                'source_uuid': self.source_uuid, 'eligible_files': eligible, 'protected_files': protected,
                'eligible_bytes': sum(current['files'][p]['size'] for p in eligible),
                'evidence': 'Previous full SHA-256 verification plus current source/backup path-size-mtime checks.'}
        if not apply: return plan
        # CLI confirmation is an execution latch, never a substitute for conversation authorization.
        self.identities(); unchanged(current, snapshot(self.source))
        plan.update(status='cleaning', deleted_files=[], permission_denied=[])
        save(self.report/'cleanup.json', plan)
        try:
            for rel in eligible:
                self.identities()
                st = (self.source/rel).lstat()
                if (st.st_size, st.st_mtime_ns) != signature(current['files'][rel]): fail('Source changed before deletion: '+rel)
                dst = (self.dest/rel).stat(); e = manifest['files'][rel]
                if (dst.st_size, dst.st_mtime_ns) != (current['files'][rel]['size'], e['destination_mtime_ns']):
                    fail('Backup changed before deletion: '+rel)
                try: (self.source/rel).unlink(); plan['deleted_files'].append(rel)
                except PermissionError as exc: plan['permission_denied'].append({'path': rel, 'error': str(exc)})
                save(self.report/'cleanup.json', plan)
            for rel in sorted((p for p in current['directories'] if p!='.'), key=lambda p:len(Path(p).parts), reverse=True):
                try: (self.source/rel).rmdir()
                except OSError as exc:
                    if exc.errno not in (errno.ENOTEMPTY, errno.EACCES, errno.EPERM): raise
            subprocess.run(['/bin/sync'], check=True)
            plan['remaining'] = snapshot(self.source)
            plan['free_bytes'] = shutil.disk_usage(self.source).free
            plan['status'] = 'cleared' if not plan['remaining']['files'] else 'cleared_with_retained_files'
            plan['completed_at'] = now()
        except BaseException as exc:
            plan.update(status='partial_cleanup', error=repr(exc)); raise
        finally: save(self.report/'cleanup.json', plan)
        return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    sub = parser.add_subparsers(dest='command', required=True)
    inspect = sub.add_parser('inspect', help='Read-only source inventory and volume identity')
    inspect.add_argument('--source', type=Path, required=True)
    inspect.add_argument('--compare', type=Path, help='Compare with a previous manifest')
    inspect.add_argument('--usb', action='store_true', help='Include negotiated USB speeds, without serial numbers')
    for name in ('transfer', 'verify', 'cleanup'):
        p = sub.add_parser(name)
        for option in ('source', 'destination', 'report'): p.add_argument('--'+option, type=Path, required=True)
        for option in ('source-uuid', 'destination-uuid'): p.add_argument('--'+option, required=True)
        if name == 'cleanup':
            p.add_argument('--apply', action='store_true', help='Destructive; requires prior user authorization')
            p.add_argument('--confirm-source-uuid', help='Must equal --source-uuid when applying')
    args = parser.parse_args()
    session = None
    try:
        if args.command == 'inspect':
            snap = snapshot(args.source)
            result = {'volume': volume_info(args.source), 'files': len(snap['files']),
                      'bytes': sum(e['size'] for e in snap['files'].values()), 'snapshot': snap}
            if args.compare: result['difference'] = difference(read(args.compare)['snapshot'], snap)
            if args.usb: result['usb_links'] = usb_links()
        else:
            session = Session(args.source, args.destination, args.report, args.source_uuid, args.destination_uuid)
            if args.command == 'cleanup':
                if args.apply and (args.confirm_source_uuid or '').upper() != args.source_uuid.upper():
                    fail('--apply requires matching --confirm-source-uuid')
                result = session.cleanup(args.apply)
            else:
                manifest = session.transfer() if args.command == 'transfer' else session.verify()
                result = {'status': manifest['status'], 'files': len(manifest['files']), 'report': str(args.report)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (Exception, KeyboardInterrupt) as exc:
        if session and session.report.is_dir():
            save(session.report/'last-error.json', {'error': repr(exc), 'at': now(), 'status': 'paused' if isinstance(exc, KeyboardInterrupt) else 'failed'})
        print(str(exc), file=sys.stderr); return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
