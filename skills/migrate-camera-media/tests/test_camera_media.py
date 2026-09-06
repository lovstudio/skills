import contextlib
import importlib.util
import io
import json
import plistlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('camera_media', Path(__file__).parents[1]/'scripts/camera_media.py')
media = importlib.util.module_from_spec(spec); spec.loader.exec_module(media)


class OffloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.src, self.dst, self.report = (self.root/p for p in ('source', 'card', 'report'))
        self.src.mkdir()
        (self.src/'empty').mkdir(); (self.src/'.hidden').mkdir()
        (self.src/'.hidden/zero.ind').write_bytes(b'')
        (self.src/'clip.mp4').write_bytes(bytes(range(256))*257)
        self.small_chunks = patch.object(media, 'CHUNK', 4096); self.small_chunks.start()

    def tearDown(self):
        self.small_chunks.stop(); self.temp.cleanup()

    def identity(self, path):
        source = path == self.src
        return {'uuid': 'SRC' if source else 'DST', 'mount': str(self.src if source else self.root),
                'external_root': True, 'internal': False}

    def session(self):
        return media.Session(self.src, self.dst, self.report, 'SRC', 'DST', identity=self.identity)

    def transfer(self):
        with contextlib.redirect_stdout(io.StringIO()): return self.session().transfer()

    def test_full_copy_and_readback(self):
        m = self.transfer()
        self.assertEqual(m['status'], 'verified')
        self.assertEqual((self.dst/'clip.mp4').read_bytes(), (self.src/'clip.mp4').read_bytes())
        self.assertTrue((self.dst/'empty').is_dir())
        self.assertTrue((self.dst/'.hidden/zero.ind').is_file())
        self.assertTrue(all(e['verified'] for e in m['files'].values()))

    def test_resume_odd_length_prefix(self):
        self.report.mkdir(); self.dst.mkdir()
        (self.dst/'clip.mp4.partial').write_bytes((self.src/'clip.mp4').read_bytes()[:8209])
        media.save(self.report/'manifest.json', {'source': str(self.src), 'destination': str(self.dst),
                   'source_uuid': 'SRC', 'destination_uuid': 'DST', 'status': 'copying',
                   'snapshot': media.snapshot(self.src), 'files': {}})
        self.transfer()
        self.assertEqual((self.dst/'clip.mp4').read_bytes(), (self.src/'clip.mp4').read_bytes())
        self.assertFalse((self.dst/'clip.mp4.partial').exists())

    def test_changed_source_rejected_before_resuming(self):
        self.transfer(); (self.src/'new.mp4').write_bytes(b'new')
        with self.assertRaisesRegex(RuntimeError, 'Source changed'): self.transfer()
        self.assertFalse((self.dst/'new.mp4').exists())

    def test_damaged_backup_blocks_cleanup(self):
        self.transfer(); (self.dst/'clip.mp4').write_bytes(b'corrupt')
        with self.assertRaisesRegex(RuntimeError, 'Backup changed'): self.session().cleanup(True)
        self.assertTrue((self.src/'clip.mp4').exists())

    def test_same_size_corruption_fails_hash_verification(self):
        self.transfer()
        with (self.dst/'clip.mp4').open('r+b') as f: f.write(b'X')
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'): self.session().verify()
        with self.assertRaisesRegex(RuntimeError, 'completed verification'): self.session().cleanup(True)

    def test_sidecars_must_be_known_appledouble(self):
        m = self.transfer()
        p = self.dst/'._clip.mp4'; p.write_bytes(struct.pack('>II', 0x51607, 0x20000))
        self.assertIn('._clip.mp4', self.session().paths(m)[1])
        p.write_bytes(b'not apple double')
        with self.assertRaisesRegex(RuntimeError, 'Unrecognized sidecar'): self.session().paths(m)

    def test_unexpected_destination_file_rejected(self):
        m = self.transfer(); (self.dst/'unexpected.mp4').write_bytes(b'x')
        with self.assertRaisesRegex(RuntimeError, 'Unexpected destination'): self.session().paths(m)

    def test_cleanup_defaults_to_plan(self):
        self.transfer(); p = self.session().cleanup()
        self.assertEqual(p['status'], 'plan_only')
        self.assertTrue((self.src/'clip.mp4').exists())

    def test_cleanup_retains_protected_marker(self):
        (self.src/'protected.ind').write_bytes(b'')
        real_snapshot = media.snapshot
        def flagged(root):
            result = real_snapshot(root)
            if root == self.src and 'protected.ind' in result['files']:
                result['files']['protected.ind']['flags'] = 2
            return result
        with patch.object(media, 'snapshot', flagged):
            self.transfer(); result = self.session().cleanup(True)
        self.assertEqual(result['status'], 'cleared_with_retained_files')
        self.assertTrue((self.src/'protected.ind').exists())
        self.assertFalse((self.src/'clip.mp4').exists())
        self.assertTrue((self.dst/'clip.mp4').exists())

    def test_wrong_volume_rejected(self):
        s = self.session(); s.source_uuid = 'WRONG'
        with self.assertRaisesRegex(RuntimeError, 'UUID mismatch'): s.transfer()
        self.assertFalse(self.dst.exists())

    def test_usb_registry_accepts_dictionary_and_array_roots(self):
        tree = {'IORegistryEntryChildren': [{'USB Product Name': 'Fixture camera',
                'UsbLinkSpeed': 5000000000, 'USB Serial Number': 'do-not-emit'}]}
        for raw in (tree, [tree]):
            with patch.object(media.subprocess, 'check_output', return_value=plistlib.dumps(raw)):
                result = media.usb_links()
            self.assertEqual(result[0]['link_bits_per_second'], 5000000000)
            self.assertNotIn('do-not-emit', str(result))

    def test_source_symlink_rejected(self):
        (self.src/'link.mp4').symlink_to(self.src/'clip.mp4')
        with self.assertRaisesRegex(RuntimeError, 'Symlink'): self.transfer()

    def test_resumed_destination_symlink_rejected(self):
        self.transfer()
        (self.dst/'link').symlink_to(self.root)
        with self.assertRaisesRegex(RuntimeError, 'Symlink'): self.transfer()

    def test_traversal_manifest_rejected(self):
        self.transfer(); m = media.read(self.report/'manifest.json')
        m['snapshot']['files']['../escape'] = {'size': 0, 'mtime_ns': 0}
        media.save(self.report/'manifest.json', m)
        with self.assertRaisesRegex(RuntimeError, 'Unsafe manifest'): self.session().cleanup(True)


if __name__ == '__main__':
    unittest.main()
