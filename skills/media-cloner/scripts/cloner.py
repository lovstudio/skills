#!/usr/bin/env python3
"""Workflow ledger for cloning a creator's video style into an evidence-backed style pack.

Subcommands: doctor, route, init, register, freeze-split, build, verify, freeze,
holdout-init, holdout-check, metrics, status. Every command prints one JSON object and
exits non-zero on failure. Rules are written by the host AI as a JSON draft; this script
resolves quotes against preserved transcripts, assigns evidence IDs, derives support from
evidence, refuses holdout evidence, and freezes the result.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil
import statistics
import subprocess
import sys
import unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCHEMAS = SKILL / 'assets' / 'schemas'
DIMENSIONS = ['thinking', 'narrative', 'language', 'delivery', 'visual', 'subtitles', 'editing_audio', 'coupling']
RESULTS = ('hit', 'partial', 'miss', 'not_applicable')
QUOTE_KINDS = ('quote', 'transcript')   # transcript: legacy kind in packs built before media-cloner
SOURCES_SCHEMA = 'media-cloner-sources/v1'
SPEC_KEYS = {'kind', 'sample_id', 't', 'q', 'start', 'end', 'file', 'field', 'description', 'local_reference', 'rights', 'key', 'use'}
UNITS_RE = re.compile(r'[㐀-鿿]|[A-Za-z]+(?:\'[A-Za-z]+)?|\d+(?:\.\d+)?')
HAN_RE = re.compile(r'[㐀-鿿]')


class Fail(Exception):
    def __init__(self, message, **details):
        super().__init__(message)
        self.details = details


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value, indent=1):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=indent) + '\n', encoding='utf-8')
    tmp.replace(path)


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def sha_json(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def today():
    return dt.date.today().isoformat()


def rank_key(s):
    return (s.get('rank') if isinstance(s.get('rank'), int) else 10 ** 9, s['sample_id'])


_VALIDATORS = {}


def schema_check(value, name):
    try:
        import jsonschema
    except ImportError:
        raise Fail('jsonschema is required; run with `uv run --with jsonschema --with pyyaml python ...`')
    if name not in _VALIDATORS:
        schema = read(SCHEMAS / name)
        jsonschema.Draft202012Validator.check_schema(schema)
        _VALIDATORS[name] = jsonschema.Draft202012Validator(schema)
    errors = sorted(_VALIDATORS[name].iter_errors(value), key=lambda e: [str(p) for p in e.path])
    if errors:
        raise Fail(f'{name}: {len(errors)} schema error(s)',
                   errors=[f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors[:20]])


# ---------- sources and split ----------

def load_sources(path):
    path = Path(path).expanduser().resolve()
    data = read(path)
    if data.get('schema') != SOURCES_SCHEMA:
        raise Fail(f'{path.name}: schema must be {SOURCES_SCHEMA}')
    schema_check(data, 'sources.schema.json')
    ids = [s['sample_id'] for s in data['samples']]
    if len(ids) != len(set(ids)):
        raise Fail('duplicate sample_id in sources')
    return path, data


def media_path(manifest, sample):
    p = Path(sample['path']).expanduser()
    return p if p.is_absolute() else (manifest.parent / p).resolve()


def split_digest(samples):
    return sha_json(sorted([s['sample_id'], s.get('partition'), s.get('sha256')] for s in samples))


def check_split(data, require=True):
    split = data.get('split')
    if not split:
        if require:
            raise Fail('the train/holdout split is not frozen yet; run cloner.py freeze-split first')
        return None
    if split_digest(data['samples']) != split['sha256']:
        raise Fail('sources changed after the split was frozen; start a new version instead of editing the split')
    return split


def ffprobe(path):
    p = subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)],
                       capture_output=True, text=True)
    if p.returncode:
        raise Fail(f'ffprobe failed for {Path(path).name}', stderr=p.stderr[-400:])
    return json.loads(p.stdout)


# ---------- transcripts and quote location ----------

def keep(ch):
    return unicodedata.category(ch)[0] not in 'PZC'


def norm(text):
    return ''.join(ch for ch in text if keep(ch))


def units(text):
    return len(UNITS_RE.findall(text))


def find_transcript(directory, sid):
    d = Path(directory)
    exact = d / f'{sid}.json'
    if exact.is_file():
        return exact
    hits = sorted(p for p in d.glob(f'*{sid}*.json') if not p.name.endswith('.tmp'))
    if len(hits) > 1:
        raise Fail(f'ambiguous transcripts for {sid}', files=[p.name for p in hits])
    return hits[0] if hits else None


def load_segments(directory, sid):
    path = find_transcript(directory, sid)
    if path is None:
        raise Fail(f'no transcript for sample {sid} in {Path(directory).name}')
    segs = read(path).get('segments')
    if not isinstance(segs, list):
        raise Fail(f'{path.name}: expected a segments list (media-cloner-transcript/v1 or Whisper JSON)')
    return path, [{'start': float(s['start']), 'end': float(s['end']), 'text': s['text']} for s in segs]


def search(segs, t, needle):
    raw, idx = '', []
    for s in segs:
        for ch in s['text']:
            if keep(ch):
                idx.append((len(raw), s))
            raw += ch
    flat = ''.join(raw[i] for i, _ in idx)
    n = norm(needle)
    if not n:
        return None
    hits = [m.start() for m in re.finditer(re.escape(n), flat)]
    if not hits:
        return None
    best = min(hits, key=lambda h: abs(idx[h][1]['start'] - t))
    a, b = idx[best], idx[best + len(n) - 1]
    s0, s1 = a[1], b[1]
    excerpt = ''.join(s['text'] for s in segs if s0['start'] <= s['start'] <= s1['start'])
    quote = raw[a[0]:b[0] + 1]
    if quote not in excerpt:
        return None
    return {'start': round(s0['start'], 2), 'end': round(s1['end'], 2), 'quote': quote, 'excerpt': excerpt}


def locate(segs, t, needle, before=12.0, after=35.0):
    hit = search([s for s in segs if t - before <= s['start'] <= t + after], t, needle)
    if hit is None:
        hit = search(segs, t, needle)
        if hit is not None:
            hit['outside_window'] = True
    return hit


def nearby(segs, t, span=20.0):
    return ''.join(s['text'] for s in segs if t - span <= s['start'] <= t + span)[:240]


def drop_holdout(value, holdout):
    if isinstance(value, dict):
        return {k: drop_holdout(v, holdout) for k, v in value.items() if k not in holdout}
    if isinstance(value, list):
        return [drop_holdout(v, holdout) for v in value
                if not (isinstance(v, dict) and v.get('sample_id') in holdout)]
    return value


# ---------- commands ----------

def cmd_doctor(a):
    tools = {t: bool(shutil.which(t)) for t in ['ffmpeg', 'ffprobe', 'swiftc', 'node', 'npx', 'uv']}
    mods = {m: bool(importlib.util.find_spec(m)) for m in
            ['jsonschema', 'yaml', 'numpy', 'cv2', 'PIL', 'librosa', 'mlx_whisper', 'whisper']}
    resources = ['assets/schemas/' + n for n in ['sources.schema.json', 'rules-draft.schema.json', 'style-profile.schema.json',
                                                  'evidence.schema.json', 'holdout-report.schema.json', 'transcript.schema.json']]
    resources += ['assets/layout-zones.vertical.json', 'scripts/measure.py', 'scripts/ocr_frames.swift', 'scripts/build_audio.py',
                  'references/analysis-protocol.md', 'references/rules-and-evidence.md', 'templates/remotion/package.json']
    missing = [r for r in resources if not (SKILL / r).is_file()]
    capabilities = {
        'ledger': mods['jsonschema'],
        'measure_media': tools['ffmpeg'] and tools['ffprobe'] and mods['numpy'] and mods['cv2'] and mods['PIL'],
        'layout_ocr': sys.platform == 'darwin' and tools['swiftc'] and tools['ffmpeg'],
        'tone_scan': tools['ffmpeg'] and mods['numpy'],
        'asr_local': mods['mlx_whisper'] or mods['whisper'],
        'transcript_import': True,
        'speaker_hint': tools['ffmpeg'] and mods['numpy'] and mods['librosa'],
        'template_render': tools['node'] and tools['npx'],
    }
    ready = not missing and capabilities['ledger']
    emit({'status': 'ready' if ready else 'missing_resources', 'skill_id': 'lov-media-cloner', 'missing': missing,
          'tools': tools, 'python_modules': mods, 'capabilities': capabilities,
          'hint': 'uv run --with jsonschema --with pyyaml --with numpy --with opencv-python-headless --with pillow python ...'})
    return 0 if ready else 1


POSITIVE = re.compile(
    r'(复刻|克隆|模仿|提炼|拆解|学习).{0,16}(视频|短视频|博主|up主|账号|频道|主播|vlog|剪辑|口播|切片|节目|作品).{0,16}(风格|画风|剪辑|包装|套路|模板|结构|调性)'
    r'|(复刻|克隆).{0,8}(博主|up主|账号|频道|主播)'
    r'|(视频|博主|账号|up主|频道).{0,12}风格.{0,10}(复刻|克隆|风格包|模板|画像|规则)'
    r'|clone.{0,40}(video|creator|channel|youtuber|vlogger).{0,30}style'
    r'|(video|creator|channel).{0,24}style.{0,24}(clone|pack|profile|replicat)', re.I)
NEGATIVE = re.compile(
    r'^\s*(只要|仅|只|just|only).{0,8}(下载|download)|冒充|假冒|换脸|deepfake|face.?swap|voice.?clon|声纹'
    r'|(克隆|复刻).{0,8}(声音|嗓音|人脸|脸)|(文章|文风|写作|公众号).{0,4}风格|writing style|这张图|单张图|这张海报', re.I)


def cmd_route(a):
    text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    ready = 'TODO' not in text and '# 视频风格复刻' in text
    positive, negative = bool(POSITIVE.search(a.request)), bool(NEGATIVE.search(a.request))
    emit({'status': 'ready' if ready else 'scaffold', 'activate': bool(ready and positive and not negative),
          'positive_match': positive, 'negative_match': negative, 'request': a.request})
    return 0 if ready else 1


README = """# {creator} · 视频风格复刻

工作区由 `lov-media-cloner` 初始化（{date}）。平台：{platform}；主页：{profile}。

- `research/`：仅本地。候选清单、`sources.json`（样本、哈希、冻结拆分）、原片、下载报告、测量、OCR、转写与证据截图。原片、截图和完整转写不进入任何作品或安装包。
- `research/rules-draft.json`：宿主撰写的规则草稿，由 `cloner.py build` 解析成风格包。
- `style-pack/{slug}-v0.1/`：风格包（style-profile.json、evidence.jsonl、FROZEN.json、holdout-report.json）。
- `deliverables/`：风格说明书、模板预览与演示成片。
- `work/`：模板工程与演示的构建文件。

进度：`python3 <SKILL_DIR>/scripts/cloner.py status --project .`
"""


def cmd_init(a):
    slug = a.slug.strip().lower()
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise Fail('slug must be lowercase ASCII kebab-case, e.g. xiaonuan')
    root = Path(a.root).expanduser().resolve() if a.root else Path.cwd().resolve()
    project = root / f'{slug}-style-clone'
    if project.exists() and any(project.iterdir()):
        raise Fail(f'{project.name} already exists and is not empty; use cloner.py status --project to resume')
    for d in ['research/sources', 'research/download-reports', 'research/measurements', 'research/layout', 'research/tones',
              'research/transcripts/raw', 'research/transcripts/normalized', 'research/evidence-images', 'style-pack', 'cases',
              'deliverables', 'work']:
        (project / d).mkdir(parents=True, exist_ok=True)
    write(project / 'research' / 'sources.json', {
        'schema': SOURCES_SCHEMA,
        'creator': {'display_name': a.creator, 'platform': a.platform, 'profile_url': a.profile_url or ''},
        'era_scope': '', 'selection': '', 'rights': '公开作品，仅用于本地风格分析；原片、人像、声音、台词不作为新作品素材',
        'samples': []})
    write(project / 'research' / 'candidates.json', {'creator': a.creator, 'collected_at': today(), 'items': []})
    (project / 'README.md').write_text(README.format(creator=a.creator, date=today(), platform=a.platform,
                                                     profile=a.profile_url or '未提供', slug=slug), encoding='utf-8')
    emit({'status': 'initialized', 'project': str(project), 'next': 'inventory candidates, then fill research/sources.json'})
    return 0


def cmd_register(a):
    path, data = load_sources(a.sources)
    frozen = data.get('split')
    done, missing = [], []
    for s in data['samples']:
        if not s.get('path'):
            missing.append(s['sample_id'])
            continue
        f = media_path(path, s)
        if not f.is_file():
            missing.append(s['sample_id'])
            continue
        digest = sha_file(f)
        if frozen and s.get('sha256') and s['sha256'] != digest:
            raise Fail(f"media for {s['sample_id']} changed after the split was frozen")
        probe = ffprobe(f)
        video = next((x for x in probe['streams'] if x['codec_type'] == 'video'), {})
        audio = next((x for x in probe['streams'] if x['codec_type'] == 'audio'), {})
        s.update(sha256=digest, bytes=f.stat().st_size, duration_seconds=round(float(probe['format']['duration']), 3),
                 width=video.get('width'), height=video.get('height'), video_codec=video.get('codec_name'),
                 fps=video.get('avg_frame_rate'), audio_codec=audio.get('codec_name'),
                 audio_sample_rate=audio.get('sample_rate'), audio_channels=audio.get('channels'))
        done.append(s['sample_id'])
    write(path, data)
    emit({'status': 'registered' if not missing else 'partial', 'registered': len(done), 'missing_media': missing})
    return 0 if not missing else 1


def cmd_freeze_split(a):
    path, data = load_sources(a.sources)
    for s in data['samples']:
        if s.get('partition') not in ('train', 'holdout'):
            raise Fail(f"{s['sample_id']}: partition must be train or holdout")
        if not s.get('sha256') or not s.get('duration_seconds'):
            raise Fail(f"{s['sample_id']}: run cloner.py register before freezing the split")
    train = [s for s in data['samples'] if s['partition'] == 'train']
    hold = [s for s in data['samples'] if s['partition'] == 'holdout']
    if len(train) < 3 or not hold:
        raise Fail('need at least 3 training samples and 1 holdout sample')
    if not data.get('era_scope') or not data.get('selection'):
        raise Fail('record era_scope and selection before freezing, so the sample frame is explicit')
    digest = split_digest(data['samples'])
    if data.get('split'):
        if data['split']['sha256'] == digest:
            emit({'status': 'already_frozen', **data['split']})
            return 0
        raise Fail('split already frozen with different content; start a new version instead of editing it')
    data['split'] = {'frozen_at': a.date or today(), 'train': len(train), 'holdout': len(hold), 'sha256': digest}
    write(path, data)
    emit({'status': 'split_frozen', **data['split'],
          'holdout_ids': [s['sample_id'] for s in sorted(hold, key=rank_key)]})
    return 0


def cmd_build(a):
    _, sources = load_sources(a.sources)
    split = check_split(sources)
    draft_path = Path(a.draft).expanduser().resolve()
    draft = read(draft_path)
    schema_check(draft, 'rules-draft.schema.json')
    samples = {s['sample_id']: s for s in sources['samples']}
    train = {k for k, s in samples.items() if s['partition'] == 'train'}
    hold = {k for k, s in samples.items() if s['partition'] == 'holdout'}
    out = Path(a.out).expanduser().resolve()
    if (out / 'FROZEN.json').exists():
        raise Fail('target pack is frozen; build the revision into a new version directory')
    errors, warnings = [], []
    dims = [d['id'] for d in draft['dimensions']]
    if sorted(dims) != sorted(DIMENSIONS):
        errors.append({'error': 'dimensions must be exactly the eight standard ids', 'found': dims})
    staged = {}
    for m in draft.get('measurement_files', []):
        src = (draft_path.parent / m['from']).resolve()
        dest = (out / m['to']).resolve()
        if not dest.is_relative_to(out / 'measurements'):
            errors.append({'error': 'measurement copies must land under measurements/', 'to': m['to']})
        elif not src.is_file():
            errors.append({'error': 'measurement source missing', 'from': m['from']})
        else:
            staged[m['to']] = drop_holdout(read(src), hold)
    segcache, evidence, by_id, keys = {}, [], {}, {}

    def resolve(spec, rule_id):
        if 'use' in spec:
            if spec['use'] not in keys:
                errors.append({'rule': rule_id, 'error': 'unknown evidence key', 'use': spec['use']})
                return None
            return keys[spec['use']]
        sid = spec.get('sample_id')
        if sid not in samples:
            errors.append({'rule': rule_id, 'error': 'unknown sample', 'sample_id': sid})
            return None
        if sid in hold:
            errors.append({'rule': rule_id, 'error': 'holdout sample used in rule selection', 'sample_id': sid})
            return None
        s, kind = samples[sid], spec['kind']
        dur = float(s['duration_seconds'])
        item = {'id': f'E{len(evidence) + 1:03d}', 'kind': kind, 'sample_id': sid, 'rank': s.get('rank')}
        if kind == 'quote':
            if sid not in segcache:
                segcache[sid] = load_segments(a.transcripts, sid)
            tpath, segs = segcache[sid]
            hit = locate(segs, float(spec['t']), spec['q'])
            if hit is None:
                errors.append({'rule': rule_id, 'error': 'quote not found in transcript', 'sample_id': sid,
                               't': spec['t'], 'q': spec['q'], 'nearby': nearby(segs, float(spec['t']))})
                return None
            if hit.get('outside_window'):
                warnings.append({'rule': rule_id, 'warning': 'quote found outside the -12/+35 s hint window', 'q': spec['q'],
                                 'found_at': hit['start']})
            item.update(start_seconds=hit['start'], end_seconds=round(min(hit['end'], dur), 2), quote=hit['quote'],
                        source_excerpt=hit['excerpt'],
                        transcript_source=draft.get('transcript_source', 'local transcript; ASR errors kept verbatim'))
        elif kind == 'measurement':
            target = (out / spec['file']).resolve()
            if spec['file'] not in staged and not (target.is_relative_to(out) and target.is_file()):
                errors.append({'rule': rule_id, 'error': 'measurement file is not in the pack', 'file': spec['file']})
                return None
            start, end = spec.get('start', 0.0), spec.get('end')
            item.update(start_seconds=round(start, 2), end_seconds=round(min(end if end is not None else dur, dur), 2),
                        file=spec['file'], field=spec['field'])
        else:
            item.update(start_seconds=round(spec['start'], 2), end_seconds=round(min(spec['end'], dur), 2),
                        description=spec['description'], local_reference=spec['local_reference'],
                        rights=spec.get('rights', 'source frame kept in the local research folder only; not packaged'))
            if a.project_root and not any(Path(a.project_root).expanduser().glob(spec['local_reference'])):
                warnings.append({'rule': rule_id, 'warning': 'visual reference not found locally', 'path': spec['local_reference']})
        if not 0 <= item['start_seconds'] <= item['end_seconds'] <= dur + 0.05:
            errors.append({'rule': rule_id, 'error': 'evidence time outside the source', 'sample_id': sid,
                           'start': item['start_seconds'], 'end': item['end_seconds'], 'duration': dur})
            return None
        for k, v in spec.items():
            if k not in SPEC_KEYS:
                item[k] = v
        evidence.append(item)
        by_id[item['id']] = item
        if spec.get('key'):
            if spec['key'] in keys:
                errors.append({'rule': rule_id, 'error': 'duplicate evidence key', 'key': spec['key']})
            keys[spec['key']] = item['id']
        return item['id']

    rules, seen = [], set()
    for r in draft['rules']:
        if r['id'] in seen:
            errors.append({'rule': r['id'], 'error': 'duplicate rule id'})
        seen.add(r['id'])
        eids = [e for e in (resolve(spec, r['id']) for spec in r['evidence']) if e]
        support = sorted({by_id[e]['sample_id'] for e in eids})
        if not eids:
            errors.append({'rule': r['id'], 'error': 'rule has no resolved evidence'})
        if not len(support) <= r['eligible_sample_count'] <= len(train):
            errors.append({'rule': r['id'], 'error': 'eligible_sample_count must lie between support and the training count',
                           'support': len(support), 'eligible': r['eligible_sample_count'], 'train': len(train)})
        rules.append({'id': r['id'], 'dimension': r['dimension'], 'observation': r['observation'],
                      'instruction': r['instruction'], 'strength': r['strength'], 'evidence_ids': eids,
                      'support_sample_ids': support, 'support_count': len(support),
                      'eligible_sample_count': r['eligible_sample_count'], 'confidence': r['confidence'],
                      'scope': r['scope'], 'exceptions': r['exceptions'], 'validation': r['validation']})
    for spec in draft.get('extra_evidence', []):
        resolve(spec, '<extra_evidence>')
    report_base = {'built_at': today(), 'draft_sha256': sha_file(draft_path), 'split_sha256': split['sha256']}
    if errors:
        report = {'status': 'failed', **report_base, 'errors': errors, 'warnings': warnings}
        write(draft_path.with_name(draft_path.stem + '.build-report.json'), report)
        raise Fail(f'build failed with {len(errors)} error(s); see {draft_path.stem}.build-report.json', errors=errors[:10])
    ordered = sorted(sources['samples'], key=rank_key)
    profile = {
        'schema_version': '0.1.0', 'style_id': draft['style_id'], 'display_name': draft['display_name'],
        'version': draft['version'], 'status': draft['status'],
        'training_sample_ids': [s['sample_id'] for s in ordered if s['partition'] == 'train'],
        'holdout_sample_ids': [s['sample_id'] for s in ordered if s['partition'] == 'holdout'],
        'samples': [{'sample_id': s['sample_id'], 'rank': s.get('rank', 0), 'title': s.get('title', ''),
                     'source_url': s.get('source_url', ''), 'sha256': s['sha256'],
                     'duration_seconds': round(float(s['duration_seconds']), 3), 'partition': s['partition']} for s in ordered],
        'dimensions': draft['dimensions'], 'rules': rules,
        'metrics': draft.get('metrics', {}), 'narrative_templates': draft.get('narrative_templates', []),
        'layout_templates': draft.get('layout_templates', []), 'audio_visual_triggers': draft.get('audio_visual_triggers', []),
        'guardrails': draft.get('guardrails', []), 'limits': draft.get('limits', []), 'provenance': draft.get('provenance', {}),
    }
    schema_check(profile, 'style-profile.schema.json')
    for to, value in staged.items():
        write(out / to, value)
    if a.per_video:
        write(out / 'per-video-analysis.json', drop_holdout(read(a.per_video), hold))
    write(out / 'style-profile.json', profile)
    (out / 'evidence.jsonl').write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in evidence), encoding='utf-8')
    kinds = {}
    for e in evidence:
        kinds[e['kind']] = kinds.get(e['kind'], 0) + 1
    write(out / 'build-report.json', {'status': 'built', **report_base, 'rules': len(rules), 'evidence': len(evidence),
                                      'evidence_by_kind': kinds, 'measurement_files': sorted(staged), 'warnings': warnings})
    emit({'status': 'built', 'pack': str(out), 'rules': len(rules), 'evidence': len(evidence), 'evidence_by_kind': kinds,
          'warnings': len(warnings)})
    return 0


def read_evidence(pack):
    rows = []
    for n, line in enumerate((pack / 'evidence.jsonl').read_text(encoding='utf-8').splitlines(), 1):
        if line.strip():
            rows.append(json.loads(line))
    return rows


def verify_pack(pack, sources_path=None, transcripts=None):
    pack = Path(pack).expanduser().resolve()
    p = read(pack / 'style-profile.json')
    schema_check(p, 'style-profile.schema.json')
    problems, warnings = [], []
    train, held = set(p['training_sample_ids']), set(p['holdout_sample_ids'])
    if train & held:
        problems.append('training/holdout leakage')
    sources = {s['sample_id']: s for s in p['samples']}
    if train | held != set(sources):
        problems.append('split does not cover the sample list')
    evidence = read_evidence(pack)
    for e in evidence:
        schema_check(e, 'evidence.schema.json')
    e_by_id = {x['id']: x for x in evidence}
    if len(e_by_id) != len(evidence):
        problems.append('duplicate evidence id')
    for x in evidence:
        s = sources.get(x['sample_id'])
        if s is None:
            problems.append(f"{x['id']}: unknown sample")
            continue
        if not 0 <= x['start_seconds'] <= x['end_seconds'] <= s['duration_seconds'] + 0.05:
            problems.append(f"{x['id']}: time outside the source")
        if x['kind'] in QUOTE_KINDS and x['quote'] not in x['source_excerpt']:
            problems.append(f"{x['id']}: quote is not an exact substring of its source excerpt")
        if x.get('file'):
            f = (pack / x['file']).resolve()
            if not f.is_relative_to(pack) or not f.is_file():
                problems.append(f"{x['id']}: {x['kind']} file missing from pack: {x['file']}")
    if sorted(d['id'] for d in p['dimensions']) != sorted(DIMENSIONS):
        problems.append('dimensions must be exactly the eight standard ids')
    used_dims = set()
    for rule in p['rules']:
        used_dims.add(rule['dimension'])
        missing = [i for i in rule['evidence_ids'] if i not in e_by_id]
        if missing:
            problems.append(f"{rule['id']}: unknown evidence {missing}")
            continue
        support = {e_by_id[i]['sample_id'] for i in rule['evidence_ids']}
        if not support <= train:
            problems.append(f"{rule['id']}: holdout or unknown sample used in rule selection")
        if support != set(rule['support_sample_ids']) or rule['support_count'] != len(support):
            problems.append(f"{rule['id']}: support is not backed by its evidence")
        if not rule['support_count'] <= rule['eligible_sample_count'] <= len(train):
            problems.append(f"{rule['id']}: invalid denominator")
        if rule['strength'] == 'required' and rule['eligible_sample_count'] and rule['support_count'] / rule['eligible_sample_count'] < 0.5:
            warnings.append(f"{rule['id']}: required with support below half of eligible samples")
    for d in DIMENSIONS:
        if d not in used_dims:
            warnings.append(f'dimension without rules: {d}')
    if len({r['id'] for r in p['rules']}) != len(p['rules']):
        problems.append('duplicate rule id')
    split_sha = None
    if sources_path:
        _, man = load_sources(sources_path)
        split_sha = check_split(man)['sha256']
        manifest = {s['sample_id']: s for s in man['samples']}
        for sid, s in sources.items():
            m = manifest.get(sid)
            if m is None:
                problems.append(f'{sid}: not in sources manifest')
            elif m.get('sha256') != s['sha256'] or m['partition'] != s['partition'] or abs(float(m['duration_seconds']) - s['duration_seconds']) > 0.05:
                problems.append(f'{sid}: pack and sources manifest disagree')
    if transcripts:
        cache = {}
        for x in evidence:
            if x['kind'] not in QUOTE_KINDS:
                continue
            if x['sample_id'] not in cache:
                cache[x['sample_id']] = load_segments(transcripts, x['sample_id'])[1]
            segs = cache[x['sample_id']]
            if norm(x['source_excerpt']) not in norm(''.join(s['text'] for s in segs)):
                problems.append(f"{x['id']}: source excerpt not found in the preserved transcript")
            elif not any(abs(round(s['start'], 2) - x['start_seconds']) < 0.011 for s in segs):
                problems.append(f"{x['id']}: start time does not match a transcript segment")
    frozen = None
    fz = pack / 'FROZEN.json'
    if fz.is_file():
        frozen = read(fz)
        if frozen['profile_sha256'] != sha_file(pack / 'style-profile.json'):
            problems.append('style-profile.json changed after freeze; revise into a new version')
        if frozen.get('evidence_sha256') and frozen['evidence_sha256'] != sha_file(pack / 'evidence.jsonl'):
            problems.append('evidence.jsonl changed after freeze; revise into a new version')
        if split_sha and frozen.get('split_sha256') and frozen['split_sha256'] != split_sha:
            problems.append('pack was frozen against a different split')
    kinds = {}
    for e in evidence:
        kinds[e['kind']] = kinds.get(e['kind'], 0) + 1
    return p, evidence, {
        'status': 'passed' if not problems else 'failed', 'style_id': p['style_id'], 'profile_version': p['version'],
        'rules': len(p['rules']), 'evidence_items': len(evidence), 'evidence_by_kind': kinds,
        'training_samples': len(train), 'holdout_samples': len(held), 'frozen': bool(frozen),
        'transcripts_checked': bool(transcripts), 'problems': problems, 'warnings': warnings}


def cmd_verify(a):
    _, _, report = verify_pack(a.pack, a.sources, a.transcripts)
    emit(report)
    return 0 if report['status'] == 'passed' else 1


def cmd_freeze(a):
    pack = Path(a.pack).expanduser().resolve()
    p, evidence, report = verify_pack(pack, a.sources, a.transcripts)
    if report['status'] != 'passed':
        raise Fail('verification failed; fix the pack before freezing', problems=report['problems'])
    _, man = load_sources(a.sources)
    record = {'profile_sha256': sha_file(pack / 'style-profile.json'), 'evidence_sha256': sha_file(pack / 'evidence.jsonl'),
              'split_sha256': man['split']['sha256'], 'frozen_at': a.date or today(),
              'rules': len(p['rules']), 'evidence': len(evidence)}
    fz = pack / 'FROZEN.json'
    if fz.exists():
        old = read(fz)
        if old.get('profile_sha256') == record['profile_sha256']:
            emit({'status': 'already_frozen', **old})
            return 0
        raise Fail('pack already frozen with different content; revise into a new version directory')
    write(fz, record)
    emit({'status': 'frozen', **record, 'next': 'holdout is unsealed: measure/transcribe it with --frozen, then holdout-init'})
    return 0


def frozen_profile(pack):
    pack = Path(pack).expanduser().resolve()
    fz = pack / 'FROZEN.json'
    if not fz.is_file():
        raise Fail('pack is not frozen; holdout checks start after cloner.py freeze')
    record = read(fz)
    if record['profile_sha256'] != sha_file(pack / 'style-profile.json'):
        raise Fail('style-profile.json changed after freeze')
    return pack, record, read(pack / 'style-profile.json')


def cmd_holdout_init(a):
    pack, record, p = frozen_profile(a.pack)
    out = Path(a.out).expanduser().resolve() if a.out else pack / 'holdout-report.json'
    if out.exists():
        raise Fail(f'{out.name} already exists; edit it instead of regenerating')
    titles = {s['sample_id']: s for s in p['samples']}
    report = {'profile_sha256': record['profile_sha256'], 'checked_at': None,
              'method': 'host read full holdout transcripts and inspected frames AFTER freezing the profile; rules applied as written',
              'samples': {sid: {'rank': titles[sid]['rank'], 'title': titles[sid]['title'], 'subtype_observed': '',
                                'results': {r['id']: {'result': None, 'note': ''} for r in p['rules']}}
                          for sid in p['holdout_sample_ids']},
              'summary': {}, 'suggested_revisions': [],
              'not_claimed': ['human blind test', 'listening review', 'style similarity score']}
    write(out, report)
    emit({'status': 'prepared', 'report': str(out), 'pairs': len(p['rules']) * len(p['holdout_sample_ids'])})
    return 0


def cmd_holdout_check(a):
    pack, record, p = frozen_profile(a.pack)
    path = Path(a.report).expanduser().resolve() if a.report else pack / 'holdout-report.json'
    report = read(path)
    schema_check(report, 'holdout-report.schema.json')
    problems = []
    if report['profile_sha256'] != record['profile_sha256']:
        problems.append('report was written against a different profile')
    held, rule_ids = p['holdout_sample_ids'], [r['id'] for r in p['rules']]
    if set(report['samples']) != set(held):
        problems.append('report samples differ from the holdout split')
    counts = {k: 0 for k in RESULTS}
    independent = {k: 0 for k in RESULTS}
    missing, contaminated = [], 0
    for sid in held:
        results = report['samples'].get(sid, {}).get('results', {})
        for rid in rule_ids:
            r = results.get(rid)
            if not r or r.get('result') not in RESULTS:
                missing.append(f'{sid}:{rid}')
                continue
            counts[r['result']] += 1
            if r.get('contaminated'):
                contaminated += 1
            else:
                independent[r['result']] += 1
            if r['result'] in ('partial', 'miss') and not r.get('note'):
                problems.append(f'{sid}:{rid}: partial or miss needs a note')
        extra = set(results) - set(rule_ids)
        if extra:
            problems.append(f'{sid}: results for unknown rules {sorted(extra)}')
    if not report.get('checked_at'):
        problems.append('checked_at is empty')
    summary = {**counts, 'recorded': sum(counts.values()), 'expected': len(held) * len(rule_ids),
               'contaminated': contaminated, 'independent': independent}
    if a.write_summary and not problems and not missing:
        report['summary'] = summary
        write(path, report)
    status = 'failed' if problems else ('incomplete' if missing else 'passed')
    emit({'status': status, 'summary': summary, 'missing_pairs': missing[:40], 'missing_count': len(missing),
          'problems': problems, 'not_claimed': report.get('not_claimed', [])})
    return 0 if status == 'passed' else 1


METRIC_NOTES = {
    'duration_seconds': ('seconds', 'FFprobe'),
    'spoken_units_per_min': ('text units per minute (Han char, Latin word or number)', 'ASR full text / full duration; includes pauses'),
    'han_per_min': ('Han characters per minute', 'ASR full text / full duration'),
    'integrated_lufs': ('LUFS', 'FFmpeg loudnorm, whole file'),
    'true_peak_dbtp': ('dBTP', 'FFmpeg loudnorm, whole file'),
    'silence_fraction': ('fraction of duration', 'FFmpeg silencedetect on the mixed track; not VAD'),
    'hard_cuts_per_minute': ('cuts per minute', 'FFmpeg scene detection; misses soft jump cuts'),
    'detected_segment_median_seconds': ('seconds', 'FFmpeg scene detection'),
    'first_tone_seconds': ('seconds', 'tone scan, first event onset'),
}


def pct(values, q):
    v = sorted(values)
    k = (len(v) - 1) * q / 100
    f = int(k)
    c = min(f + 1, len(v) - 1)
    return round(v[f] + (v[c] - v[f]) * (k - f), 3)


def cmd_metrics(a):
    path, sources = load_sources(a.sources)
    check_split(sources)
    train = sorted([s for s in sources['samples'] if s['partition'] == 'train'], key=rank_key)
    layout = read(a.layout)['samples'] if a.layout else {}
    tones = read(a.tones)['results'] if a.tones else {}
    lexicon = {k: re.compile(v) for k, v in read(a.lexicon).items()} if a.lexicon else {}
    rows, raws, lex_tot, lex_sup = [], [], {k: 0 for k in lexicon}, {k: 0 for k in lexicon}
    for s in train:
        sid, d = s['sample_id'], float(s['duration_seconds'])
        row = {'sample_id': sid, 'rank': s.get('rank'), 'title': s.get('title', ''), 'duration_seconds': round(d, 3)}
        raw = {'duration_seconds': d}
        if a.transcripts:
            text = ''.join(x['text'] for x in load_segments(a.transcripts, sid)[1])
            raw.update(spoken_units_per_min=units(text) / (d / 60), han_per_min=len(HAN_RE.findall(text)) / (d / 60))
            row.update(spoken_units=units(text), spoken_units_per_min=round(raw['spoken_units_per_min'], 1),
                       han_per_min=round(raw['han_per_min'], 1))
            if lexicon:
                lx = {k: len(rx.findall(text)) for k, rx in lexicon.items()}
                for k, n in lx.items():
                    lex_tot[k] += n
                    lex_sup[k] += 1 if n else 0
                row['lexicon'] = lx
        if a.measurements:
            mf = Path(a.measurements) / sid / 'metrics.json'
            if mf.is_file():
                m = read(mf)
                au, sc = m['audio'], m['scene_detection']
                raw.update(integrated_lufs=float(au['integrated_lufs']), true_peak_dbtp=float(au['true_peak_dbtp']),
                           silence_fraction=au['silence_seconds'] / d, hard_cuts_per_minute=sc['cut_count'] / (d / 60),
                           detected_segment_median_seconds=sc['detected_segment_duration_percentiles']['50'])
                row.update(integrated_lufs=raw['integrated_lufs'], true_peak_dbtp=raw['true_peak_dbtp'],
                           silence_fraction=round(raw['silence_fraction'], 3), hard_cuts=sc['cut_count'],
                           hard_cuts_per_minute=round(raw['hard_cuts_per_minute'], 3),
                           detected_segment_median_seconds=raw['detected_segment_median_seconds'])
        if sid in tones:
            ev = tones[sid]['events']
            row['tone_events'] = ev
            if ev:
                raw['first_tone_seconds'] = row['first_tone_seconds'] = ev[0][0]
        if sid in layout:
            for zone, z in layout[sid]['zones'].items():
                for k in ('frame_ratio', 'chars_median', 'box_height_median', 'box_top_median', 'visible_until_s'):
                    if isinstance(z.get(k), (int, float)) and not isinstance(z.get(k), bool):
                        raw[f'{zone}.{k}'] = row[f'{zone}.{k}'] = z[k]
        rows.append(row)
        raws.append(raw)
    metrics = {}
    for k in sorted({k for r in raws for k in r}):
        vals = [r[k] for r in raws if k in r]
        u, method = METRIC_NOTES.get(k, ('', 'layout scan' if '.' in k else ''))
        metrics[k] = {'units': u, 'sample_count': len(vals), 'p10': pct(vals, 10), 'median': pct(vals, 50), 'p90': pct(vals, 90),
                      'min': round(min(vals), 3), 'max': round(max(vals), 3), 'method': method}
    out = {'scope': f'training samples only ({len(train)}); holdout excluded', 'per_sample': rows, 'metrics': metrics}
    if lexicon:
        out.update(lexicon_totals=lex_tot, lexicon_sample_support=lex_sup)
    write(a.out, out)
    emit({'status': 'written', 'output': str(Path(a.out).resolve()), 'samples': len(rows), 'metrics': len(metrics)})
    return 0


def cmd_status(a):
    project = Path(a.project).expanduser().resolve()
    research = project / 'research'
    state = {'project': str(project)}
    stage, nxt = 'empty', 'cloner.py init'
    src = research / 'sources.json'
    if src.is_file():
        data = read(src)
        n = len(data.get('samples', []))
        reg = sum(1 for s in data.get('samples', []) if s.get('sha256'))
        state.update(samples=n, registered=reg, split=data.get('split'))
        stage, nxt = 'sampling', 'select samples and fill sources.json'
        if n and reg == n:
            stage, nxt = 'registered', 'choose the holdout and run freeze-split'
        if data.get('split'):
            train = [s['sample_id'] for s in data['samples'] if s['partition'] == 'train']
            norm_dir = research / 'transcripts' / 'normalized'
            have = sum(1 for sid in train if norm_dir.is_dir() and find_transcript(norm_dir, sid))
            measured = sum(1 for sid in train if (research / 'measurements' / sid / 'metrics.json').is_file())
            state.update(train_transcripts=have, train_measured=measured, train=len(train))
            stage, nxt = 'split_frozen', 'measure and transcribe the training set'
            if have == len(train) and measured == len(train):
                stage, nxt = 'measured', 'read transcripts in full and write research/rules-draft.json'
    if (research / 'rules-draft.json').is_file():
        stage, nxt = 'drafted', 'cloner.py build'
    packs = sorted((project / 'style-pack').glob('*-v*/style-profile.json')) if (project / 'style-pack').is_dir() else []
    if packs:
        pack = packs[-1].parent
        state['pack'] = pack.name
        stage, nxt = 'built', 'cloner.py verify, then freeze'
        if (pack / 'FROZEN.json').is_file():
            stage, nxt = 'frozen', 'unseal holdout with --frozen and run holdout-init'
            hr = pack / 'holdout-report.json'
            if hr.is_file():
                rep = read(hr)
                stage, nxt = 'holdout_in_progress', 'record every rule x holdout result, then holdout-check --write-summary'
                if rep.get('summary', {}).get('recorded') and rep['summary'].get('recorded') == rep['summary'].get('expected'):
                    stage, nxt = 'holdout_checked', 'write the style guide in deliverables/'
    guides = sorted((project / 'deliverables').glob('*.md')) if (project / 'deliverables').is_dir() else []
    if guides and stage == 'holdout_checked':
        stage, nxt = 'guide_written', 'optional: template preview, demo with own footage, packaging'
        state['guide'] = guides[-1].name
    if (project / 'work' / 'remotion' / 'package.json').is_file():
        state['template'] = 'work/remotion'
    renders = sorted((project / 'deliverables').glob('*.mp4')) if (project / 'deliverables').is_dir() else []
    if renders:
        state['renders'] = [r.name for r in renders]
    emit({'status': 'ok', 'stage': stage, 'next': nxt, **state})
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='command', required=True)
    sp.add_parser('doctor')
    r = sp.add_parser('route'); r.add_argument('--request', required=True)
    i = sp.add_parser('init')
    i.add_argument('--slug', required=True); i.add_argument('--creator', required=True)
    i.add_argument('--platform', default='unknown'); i.add_argument('--profile-url'); i.add_argument('--root')
    g = sp.add_parser('register'); g.add_argument('--sources', required=True)
    f = sp.add_parser('freeze-split'); f.add_argument('--sources', required=True); f.add_argument('--date')
    b = sp.add_parser('build')
    b.add_argument('--draft', required=True); b.add_argument('--sources', required=True)
    b.add_argument('--transcripts', required=True); b.add_argument('--out', required=True)
    b.add_argument('--per-video'); b.add_argument('--project-root')
    v = sp.add_parser('verify'); v.add_argument('--pack', required=True); v.add_argument('--sources'); v.add_argument('--transcripts')
    z = sp.add_parser('freeze')
    z.add_argument('--pack', required=True); z.add_argument('--sources', required=True)
    z.add_argument('--transcripts'); z.add_argument('--date')
    h = sp.add_parser('holdout-init'); h.add_argument('--pack', required=True); h.add_argument('--out')
    c = sp.add_parser('holdout-check')
    c.add_argument('--pack', required=True); c.add_argument('--report'); c.add_argument('--write-summary', action='store_true')
    m = sp.add_parser('metrics')
    m.add_argument('--sources', required=True); m.add_argument('--out', required=True)
    m.add_argument('--measurements'); m.add_argument('--transcripts'); m.add_argument('--layout')
    m.add_argument('--tones'); m.add_argument('--lexicon', help='JSON object: label -> regular expression')
    s = sp.add_parser('status'); s.add_argument('--project', required=True)
    a = ap.parse_args()
    handler = globals()['cmd_' + a.command.replace('-', '_')]
    try:
        return handler(a)
    except Fail as exc:
        emit({'status': 'failed', 'command': a.command, 'message': str(exc), **exc.details})
        return 1


if __name__ == '__main__':
    sys.exit(main())
