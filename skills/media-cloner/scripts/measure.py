#!/usr/bin/env python3
"""Read-only measurement of reference videos for lov-media-cloner.

Subcommands:
  media       whole-file probe, scene cuts, silence, loudness/true peak, timed frames, contact sheet
  layout      frames every N s + macOS Vision OCR, summarised per screen zone (optionally colours)
  tones       test-tone / beep events in a frequency band (separators, splices)
  transcribe  local ASR with mlx-whisper or openai-whisper, raw JSON kept, normalised transcript written
  import      normalise existing Whisper JSON, Tingwu JSON or SRT into media-cloner-transcript/v1
  speakers    acoustic two-cluster speaker hint per ASR segment (hint only)

Every subcommand reads a media-cloner-sources/v1 manifest whose split is frozen. The default
partition is train. Holdout samples stay sealed until the style profile is frozen: pass
--partition holdout --frozen PACK_DIR, and the pack's FROZEN.json must match.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import statistics as st
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
DEFAULT_ZONES = SKILL / 'assets' / 'layout-zones.vertical.json'
TRANSCRIPT_SCHEMA = 'media-cloner-transcript/v1'
PUNCT = re.compile(r'[，。？！、,?!；;：:…]')


class Fail(Exception):
    pass


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value, indent=1):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=indent, default=float) + '\n', encoding='utf-8')
    tmp.replace(path)


def say(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def split_digest(samples):
    payload = sorted([s['sample_id'], s.get('partition'), s.get('sha256')] for s in samples)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def run(cmd, log=None):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if log:
        Path(log).write_text(p.stderr)
    if p.returncode:
        raise Fail(f'{cmd[0]} exit={p.returncode}: {p.stderr[-600:]}')
    return p


def select(manifest, partition, frozen, only=None):
    """Return manifest rows for a partition, enforcing the frozen split and the holdout seal."""
    mpath = Path(manifest).expanduser().resolve()
    data = read(mpath)
    if data.get('schema') != 'media-cloner-sources/v1':
        raise Fail(f'{mpath.name}: expected a media-cloner-sources/v1 manifest')
    split = data.get('split')
    if not split:
        raise Fail('freeze the train/holdout split first: cloner.py freeze-split')
    if split_digest(data['samples']) != split['sha256']:
        raise Fail('sources changed after the split was frozen')
    if partition in ('holdout', 'all'):
        if not frozen:
            raise Fail('holdout is sealed until the style profile is frozen; rerun with --frozen PACK_DIR after cloner.py freeze')
        pack = Path(frozen).expanduser().resolve()
        fz = pack / 'FROZEN.json'
        if not fz.is_file():
            raise Fail('--frozen pack has no FROZEN.json')
        record = read(fz)
        if record['profile_sha256'] != sha_file(pack / 'style-profile.json'):
            raise Fail('--frozen pack changed after freeze')
        if record.get('split_sha256') and record['split_sha256'] != split['sha256']:
            raise Fail('--frozen pack was frozen against a different split')
    rows = [dict(s) for s in data['samples'] if partition == 'all' or s['partition'] == partition]
    if only:
        rows = [s for s in rows if s['sample_id'] in only]
        if len(rows) != len(set(only)):
            raise Fail('a requested sample is not in this partition (holdout stays sealed before freeze)')
    for s in rows:
        p = Path(s.get('path', '')).expanduser()
        s['_path'] = str(p if p.is_absolute() else (mpath.parent / p).resolve()) if s.get('path') else None
    return mpath, data, sorted(rows, key=lambda s: (s.get('rank') if isinstance(s.get('rank'), int) else 10 ** 9, s['sample_id']))


def need_media(s):
    if not s['_path'] or not Path(s['_path']).is_file():
        raise Fail(f"media missing for {s['sample_id']}; download and register it first")
    return s['_path']


# ---------- media ----------

def measure_one(s, out, threshold, silence_db, silence_min):
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
    source, sid = need_media(s), s['sample_id']
    folder = out / sid
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / 'metrics.json'
    if dest.exists():
        say({'sample': sid, 'status': 'reused'})
        return read(dest)
    probe = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', source]).stdout)
    duration = float(probe['format']['duration'])
    video = next(x for x in probe['streams'] if x['codec_type'] == 'video')
    scene = run(['ffmpeg', '-nostdin', '-hide_banner', '-i', source, '-an', '-sn', '-vf',
                 f"scale=320:-2,select='gt(scene,{threshold})',showinfo", '-fps_mode', 'vfr', '-f', 'null', '-'], folder / 'scene.log')
    cuts = sorted(set(float(t) for t in re.findall(r'pts_time:([\d.]+)', scene.stderr)))
    bounds = [0] + cuts + [duration]
    lengths = [b - a for a, b in zip(bounds, bounds[1:]) if b > a]
    audio = run(['ffmpeg', '-nostdin', '-hide_banner', '-i', source, '-vn', '-sn', '-af',
                 f'silencedetect=noise={silence_db}dB:d={silence_min},loudnorm=I=-16:TP=-1:LRA=11:print_format=json',
                 '-f', 'null', '-'], folder / 'audio.log')
    found = re.findall(r'\{\s*"input_i".*?\}', audio.stderr, re.S)
    loud = json.loads(found[-1]) if found else {}
    starts = [float(t) for t in re.findall(r'silence_start: ([\d.]+)', audio.stderr)]
    ends = [float(t) for t in re.findall(r'silence_end: ([\d.]+)', audio.stderr)]
    if len(starts) > len(ends):
        ends.append(duration)
    silences = [{'start': a, 'end': b, 'duration': round(b - a, 4)} for a, b in zip(starts, ends) if b >= a]
    times = sorted(set(round(min(duration - 0.1, t), 3) for t in
                       [0.5, 3, 10, 20] + [duration * p for p in (.1, .25, .4, .55, .7, .85, .95)] + [duration - 1] if t >= 0))
    cap = cv2.VideoCapture(source)
    frames, thumbs = [], []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        path = folder / f'frame-{t:08.3f}.jpg'
        cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        frames.append({'time_seconds': t, 'image': path.name})
        thumbs.append((t, Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))))
    cap.release()
    if thumbs:
        cw = 240
        ch = int(cw * thumbs[0][1].height / thumbs[0][1].width) + 22
        sheet = Image.new('RGB', (cw * 3, ch * ((len(thumbs) + 2) // 3)), '#eeeeee')
        draw = ImageDraw.Draw(sheet)
        for k, (t, im) in enumerate(thumbs):
            im = im.copy()
            im.thumbnail((cw - 4, ch - 22))
            x, y = (k % 3) * cw, (k // 3) * ch
            sheet.paste(im, (x + (cw - im.width) // 2, y + 20))
            draw.text((x + 6, y + 4), f'{sid[:8]}  {t:.2f}s', fill='black')
        sheet.save(folder / 'contact.jpg', quality=92)
    chunks = [{'source_start': round(x, 3), 'duration': 15.0, 'sample_start': k * 15.0}
              for k, x in enumerate([0.0, duration * .4, duration * .8]) if x + 1 < duration]
    if chunks and any(x['codec_type'] == 'audio' for x in probe['streams']):
        graph = ';'.join(f"[0:a]atrim=start={c['source_start']}:duration=15,asetpts=PTS-STARTPTS[a{k}]" for k, c in enumerate(chunks))
        graph += ';' + ''.join(f'[a{k}]' for k in range(len(chunks))) + f'concat=n={len(chunks)}:v=0:a=1[out]'
        run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-i', source, '-filter_complex', graph, '-map', '[out]',
             '-ar', '16000', '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '48k', str(folder / 'audio-sample.mp3')])
    result = {
        'sample_id': sid, 'rank': s.get('rank'), 'partition': s['partition'], 'title': s.get('title', ''),
        'duration_seconds': duration, 'width': video['width'], 'height': video['height'],
        'video_codec': video['codec_name'], 'frame_rate': video['avg_frame_rate'],
        'scene_detection': {'method': f'FFmpeg full decode, downscale 320 px, scene threshold {threshold}',
                            'limitation': 'hard visual transitions only; misses subtle jump cuts and is not semantic',
                            'cut_times_seconds': cuts, 'cut_count': len(cuts),
                            'detected_segment_duration_percentiles': {str(p): round(float(np.percentile(lengths, p)), 4) for p in (10, 50, 90)}},
        'audio': {'integrated_lufs': loud.get('input_i'), 'true_peak_dbtp': loud.get('input_tp'),
                  'loudness_range_lu': loud.get('input_lra'), 'silence_threshold_db': silence_db, 'silence_min_seconds': silence_min,
                  'silences': silences, 'silence_seconds': round(sum(x['duration'] for x in silences), 4),
                  'limitation': 'mixed-track silence is not a VAD or a music-separated speech pause metric'},
        'frames': frames, 'audio_sample_segments': chunks}
    write(dest, result)
    say({'sample': sid, 'status': 'measured', 'cuts': len(cuts), 'frames': len(frames), 'lufs': loud.get('input_i')})
    return result


def cmd_media(a):
    _, _, rows = select(a.manifest, a.partition, a.frozen, a.sample)
    out = Path(a.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(a.workers, 4))) as pool:
        results = list(pool.map(lambda s: measure_one(s, out, a.scene_threshold, a.silence_db, a.silence_min), rows))
    write(out / f'index.{a.partition}.json', [{'sample_id': r['sample_id'], 'rank': r['rank'], 'duration_seconds': r['duration_seconds'],
                                                'cuts': r['scene_detection']['cut_count'], 'integrated_lufs': r['audio']['integrated_lufs'],
                                                'true_peak_dbtp': r['audio']['true_peak_dbtp']} for r in results])
    say({'status': 'measured', 'partition': a.partition, 'count': len(results), 'output': str(out)})
    return 0


# ---------- layout ----------

def ocr_binary(out):
    binary = out / '.bin' / 'ocr_frames'
    if not binary.exists():
        binary.parent.mkdir(parents=True, exist_ok=True)
        run(['swiftc', '-O', str(SKILL / 'scripts' / 'ocr_frames.swift'), '-o', str(binary)])
    return binary


def in_zone(box, z):
    b = box['bbox']
    cx = b['x'] + b['width'] / 2
    y0, y1 = z.get('y', [0, 1])
    x0, x1 = z.get('x', [0, 1])
    return (y0 <= b['y'] < y1 and x0 <= b['x'] < x1
            and ('center_x_max_offset' not in z or abs(cx - 0.5) < z['center_x_max_offset'])
            and ('center_x_max' not in z or cx < z['center_x_max'])
            and ('min_height' not in z or b['height'] > z['min_height'])
            and ('max_height' not in z or b['height'] < z['max_height']))


def kmeans_hex(px, k=4, iters=12):
    import numpy as np
    px = px.reshape(-1, 3).astype(np.float32)
    if len(px) < k:
        return []
    lum = px @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    centers = px[np.argsort(lum)[np.linspace(0, len(px) - 1, k).astype(int)]]
    for _ in range(iters):
        lab = ((px[:, None, :] - centers[None]) ** 2).sum(-1).argmin(1)
        centers = np.array([px[lab == i].mean(0) if (lab == i).any() else centers[i] for i in range(k)])
    shares = np.bincount(lab, minlength=k) / len(px)
    rows = [['#%02X%02X%02X' % tuple(int(v) for v in c.clip(0, 255)), round(float(sh), 3)] for c, sh in zip(centers, shares)]
    return sorted(rows, key=lambda r: -r[1])


def zone_colors(frames_dir, boxes, limit=30):
    import numpy as np
    from PIL import Image
    samples = []
    for t, box in boxes[:limit]:
        f = frames_dir / f't-{t:08.3f}.jpg'
        if not f.is_file():
            continue
        im = Image.open(f).convert('RGB')
        b = box['bbox']
        crop = im.crop((int(b['x'] * im.width), int(b['y'] * im.height),
                        int((b['x'] + b['width']) * im.width), int((b['y'] + b['height']) * im.height)))
        arr = np.asarray(crop).reshape(-1, 3)
        if len(arr):
            samples.append(arr[np.linspace(0, len(arr) - 1, min(len(arr), 600)).astype(int)])
    return kmeans_hex(np.concatenate(samples)) if samples else []


def summarise(frames, duration, zones, wall=None, frames_dir=None, colors=False):
    wall = re.compile(wall) if wall else None
    rows = []
    for fr in frames:
        texts = [x for x in fr['texts'] if x['confidence'] > 0.3 and not (wall and wall.match(x['text']))]
        hit = {}
        for z in zones:
            boxes = [x for x in texts if in_zone(x, z)]
            hit[z['name']] = boxes if len(boxes) >= z.get('min_boxes', 1) else []
        rows.append({'t': fr['time_seconds'], 'zones': hit})
    result = {}
    for z in zones:
        name = z['name']
        present = [r for r in rows if r['zones'][name]]
        boxes = [(r['t'], x) for r in rows for x in r['zones'][name]]
        chars = [len(re.sub(r'\s', '', x['text'])) for _, x in boxes]
        summary = {
            'kind': z.get('kind', 'other'),
            'frame_ratio': round(len(present) / max(1, len(rows)), 3), 'boxes': len(boxes),
            'chars_median': st.median(chars) if chars else None,
            'box_height_median': round(st.median([x['bbox']['height'] for _, x in boxes]), 4) if boxes else None,
            'box_top_median': round(st.median([x['bbox']['y'] for _, x in boxes]), 4) if boxes else None,
            'max_boxes_per_frame': max((len(r['zones'][name]) for r in rows), default=0),
            'boxes_with_punctuation': sum(1 for _, x in boxes if PUNCT.search(x['text']) and not re.search(r'\d,\d', x['text'])),
            'first_seen_s': present[0]['t'] if present else None, 'last_seen_s': present[-1]['t'] if present else None,
            'examples': [x['text'] for _, x in boxes[:6]]}
        if z.get('kind') == 'title':
            first = [r for r in rows if r['t'] <= 6 and r['zones'][name]]
            lines = [x['text'] for x in first[0]['zones'][name]] if first else []

            def shows(r):
                joined = ''.join(x['text'] for x in r['zones'][name])
                return bool(lines) and any(len(set(l) & set(joined)) >= max(3, int(len(set(l)) * 0.5)) for l in lines)
            until = 0
            for r in rows:
                if shows(r):
                    until = r['t']
                elif r['t'] - until > 4:
                    break
            summary.update(lines=lines, visible_until_s=until if lines else None,
                           height_median_while_visible=round(st.median([x['bbox']['height'] for r in rows if shows(r) for x in r['zones'][name]]), 4) if lines and until else None)
        if z.get('kind') == 'card':
            summary['times'] = [r['t'] for r in present]
        if colors and frames_dir is not None and boxes:
            summary['colors'] = zone_colors(frames_dir, boxes)
        result[name] = summary
    return {'duration_seconds': duration, 'frames': len(rows), 'zones': result}


def discover(frames):
    bins = {}
    for fr in frames:
        for x in fr['texts']:
            if x['confidence'] <= 0.3:
                continue
            b = x['bbox']
            key = round(int(b['y'] / 0.05) * 0.05, 2)
            d = bins.setdefault(key, {'boxes': 0, 'heights': [], 'centers': [], 'chars': [], 'frames': set()})
            d['boxes'] += 1
            d['heights'].append(b['height'])
            d['centers'].append(b['x'] + b['width'] / 2)
            d['chars'].append(len(re.sub(r'\s', '', x['text'])))
            d['frames'].add(fr['time_seconds'])
    total = max(1, len(frames))
    return [{'top_bin': k, 'boxes': d['boxes'], 'frame_ratio': round(len(d['frames']) / total, 3),
             'height_median': round(st.median(d['heights']), 4), 'center_x_median': round(st.median(d['centers']), 3),
             'chars_median': st.median(d['chars'])} for k, d in sorted(bins.items())]


def cmd_layout(a):
    _, _, rows = select(a.manifest, a.partition, a.frozen, a.sample)
    out = Path(a.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    zones = read(a.zones or DEFAULT_ZONES)['zones']
    binary = ocr_binary(out)
    summary = {}
    for s in rows:
        sid = s['sample_id']
        d = out / sid
        frames_dir, ocr = d / 'frames', d / 'ocr.json'
        if not ocr.exists():
            frames_dir.mkdir(parents=True, exist_ok=True)
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', need_media(s), '-vf', f'fps={1 / a.every},scale=720:-2',
                 '-q:v', '3', '-start_number', '0', str(frames_dir / 'f-%05d.jpg')])
            for f in sorted(frames_dir.glob('f-*.jpg')):
                f.rename(frames_dir / f"t-{int(f.stem[2:]) * a.every:08.3f}.jpg")
            run([str(binary), str(frames_dir), str(ocr)])
        frames = read(ocr)
        item = {'rank': s.get('rank'), 'partition': s['partition'],
                **summarise(frames, s.get('duration_seconds'), zones, a.wall_regex, frames_dir, a.colors)}
        if a.discover:
            item['text_bins'] = discover(frames)
        summary[sid] = item
        say({'sample': sid, 'zones': {k: v['frame_ratio'] for k, v in item['zones'].items()}})
    target = out / f'layout.{a.partition}.json'
    write(target, {'method': f'Vision OCR every {a.every} s, 720 px frames; zone boxes in top-left normalised coordinates',
                   'zones': zones, 'samples': summary})
    say({'status': 'written', 'output': str(target), 'samples': len(summary)})
    return 0


# ---------- tones ----------

def cmd_tones(a):
    import numpy as np
    _, _, rows = select(a.manifest, a.partition, a.frozen, a.sample)
    out = {}
    low, high = a.frequency - a.band, a.frequency + a.band
    for s in rows:
        raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', need_media(s), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                             capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.float32)
        win, hits = 4000, []
        f = np.fft.rfftfreq(win, 1 / 16000)
        band = (f > low) & (f < high)
        for i in range(0, len(x) - win, win):
            seg = x[i:i + win]
            spec = np.abs(np.fft.rfft(seg * np.hanning(win)))
            if spec[band].max() / (np.median(spec) + 1e-9) > a.ratio and 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9) > a.min_dbfs:
                hits.append(i / 16000)
        events = []
        for t in hits:
            if events and t - events[-1][1] <= 0.26:
                events[-1][1] = t + 0.25
            else:
                events.append([t, t + 0.25])
        out[s['sample_id']] = {'rank': s.get('rank'), 'events': [[round(b, 2), round(e, 2)] for b, e in events]}
        say({'sample': s['sample_id'], 'events': out[s['sample_id']]['events']})
    target = Path(a.out).expanduser().resolve()
    write(target, {'method': f'0.25 s windows, {low:g}-{high:g} Hz peak/median > {a.ratio:g}, RMS > {a.min_dbfs:g} dBFS; audio only, confirm with frames',
                   'partition': a.partition, 'results': out})
    say({'status': 'written', 'output': str(target), 'samples': len(out)})
    return 0


# ---------- transcripts ----------

def segment(start, end, text, speaker=None, words=None):
    seg = {'start': round(float(start), 3), 'end': round(float(end), 3), 'text': text}
    if speaker is not None:
        seg['speaker'] = str(speaker)
    if words:
        seg['words'] = words
    return seg


def from_whisper(data):
    segs = []
    for s in data['segments']:
        words = [{'word': w['word'], 'start': round(float(w['start']), 3), 'end': round(float(w['end']), 3)}
                 for w in s.get('words') or [] if 'start' in w and 'end' in w]
        segs.append(segment(s['start'], s['end'], s['text'], s.get('speaker'), words))
    return segs, data.get('language')


def from_tingwu(data):
    segs = []
    for p in data['Transcription']['Paragraphs']:
        buckets = {}
        for w in p.get('Words', []):
            buckets.setdefault(w.get('SentenceId', 0), []).append(w)
        for words in buckets.values():
            if words:
                segs.append(segment(words[0]['Start'] / 1000, words[-1]['End'] / 1000, ''.join(w['Text'] for w in words),
                                    p.get('SpeakerId', 'unknown'),
                                    [{'word': w['Text'], 'start': round(w['Start'] / 1000, 3), 'end': round(w['End'] / 1000, 3)} for w in words]))
    return sorted(segs, key=lambda s: (s['start'], s['end'])), None


def from_srt(text):
    stamp = re.compile(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)')
    segs = []
    for block in re.split(r'\n\s*\n', text.strip()):
        lines = [l for l in block.splitlines() if l.strip()]
        for k, line in enumerate(lines):
            m = stamp.search(line)
            if m:
                g = [int(v) for v in m.groups()]
                start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
                end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
                segs.append(segment(start, end, ''.join(lines[k + 1:])))
                break
    return segs, None


def normalise(path, fmt):
    path = Path(path)
    if fmt == 'auto':
        if path.suffix.lower() == '.srt':
            fmt = 'srt'
        else:
            data = read(path)
            fmt = 'tingwu' if isinstance(data, dict) and 'Transcription' in data else 'whisper'
    if fmt == 'srt':
        segs, lang = from_srt(path.read_text(encoding='utf-8-sig'))
    elif fmt == 'tingwu':
        segs, lang = from_tingwu(read(path))
    else:
        segs, lang = from_whisper(read(path))
    return fmt, segs, lang


def transcript_doc(s, provider, fmt, source_name, segs, lang):
    return {'schema': TRANSCRIPT_SCHEMA, 'sample_id': s['sample_id'], 'provider': provider, 'source_format': fmt,
            'source_file': source_name, 'media_sha256': s.get('sha256'), 'language': lang,
            'word_timestamps': any('words' in x for x in segs),
            'note': 'ASR output kept verbatim; misheard words are not corrected', 'segments': segs}


def cmd_import(a):
    _, _, rows = select(a.manifest, a.partition, a.frozen, a.sample)
    src, out = Path(a.input).expanduser().resolve(), Path(a.out).expanduser().resolve()
    done, missing = [], []
    for s in rows:
        sid = s['sample_id']
        files = sorted(p for p in src.iterdir() if sid in p.name and p.suffix.lower() in ('.json', '.srt') and not p.name.endswith('.job.json'))
        if not files:
            missing.append(sid)
            continue
        if len(files) > 1:
            raise Fail(f'several transcript files match {sid}: {[p.name for p in files]}')
        fmt, segs, lang = normalise(files[0], a.format)
        write(out / f'{sid}.json', transcript_doc(s, a.provider or fmt, fmt, files[0].name, segs, lang or a.language))
        done.append(sid)
    say({'status': 'imported' if not missing else 'partial', 'partition': a.partition, 'imported': len(done), 'missing': missing})
    return 0 if not missing else 1


def cmd_transcribe(a):
    _, _, rows = select(a.manifest, a.partition, a.frozen, a.sample)
    raw_dir, out = Path(a.raw).expanduser().resolve(), Path(a.out).expanduser().resolve()
    backend = a.backend
    if backend == 'auto':
        import importlib.util
        backend = 'mlx-whisper' if importlib.util.find_spec('mlx_whisper') else 'whisper' if importlib.util.find_spec('whisper') else None
        if backend is None:
            raise Fail('no local ASR: install mlx-whisper (Apple Silicon) or openai-whisper, or use `measure.py import` with existing transcripts')
    model_name = a.model or ('mlx-community/whisper-large-v3-mlx' if backend == 'mlx-whisper' else 'large-v3')
    loaded = None
    for s in rows:
        sid = s['sample_id']
        target = out / f'{sid}.json'
        if target.exists() and not a.force:
            say({'sample': sid, 'status': 'reused'})
            continue
        media = need_media(s)
        if backend == 'mlx-whisper':
            import mlx_whisper
            result = mlx_whisper.transcribe(media, path_or_hf_repo=model_name, language=a.language, word_timestamps=True)
        else:
            import whisper
            loaded = loaded or whisper.load_model(model_name)
            result = loaded.transcribe(media, language=a.language, word_timestamps=True)
        raw = raw_dir / f'{sid}.{backend}.json'
        result['_meta'] = {'backend': backend, 'model': model_name, 'media_sha256': s.get('sha256')}
        write(raw, result)
        segs, lang = from_whisper(result)
        write(target, transcript_doc(s, f'{backend} {model_name}', 'whisper', raw.name, segs, lang or a.language))
        say({'sample': sid, 'status': 'transcribed', 'segments': len(segs)})
    say({'status': 'transcribed', 'partition': a.partition, 'samples': len(rows), 'output': str(out)})
    return 0


# ---------- speakers ----------

def cmd_speakers(a):
    import numpy as np
    import librosa
    _, _, rows = select(a.manifest, a.partition, a.frozen, [a.sample])
    s = rows[0]
    sr = 32000
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', need_media(s), '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    segs = read(a.transcript)['segments']
    feats = []
    for seg in segs:
        part = x[int(seg['start'] * sr):int(seg['end'] * sr)]
        if len(part) < sr * 0.25:
            feats.append(None)
            continue
        spec = np.abs(librosa.stft(part, n_fft=1024, hop_length=320)) ** 2
        f = librosa.fft_frequencies(sr=sr, n_fft=1024)
        e = spec.sum(0)
        v = e > np.percentile(e, 50)
        feats.append(float(10 * np.log10((spec[(f > 4000) & (f < 7500)][:, v].sum() + 1e-12) / (spec[(f > 300) & (f < 4000)][:, v].sum() + 1e-12))))
    vals = np.array([v for v in feats if v is not None])
    if len(vals) < 4:
        raise Fail('too few voiced segments for a speaker hint')
    c = np.array([np.percentile(vals, 15), np.percentile(vals, 85)])
    for _ in range(20):
        lab = np.abs(vals[:, None] - c[None]).argmin(1)
        c = np.array([vals[lab == i].mean() if (lab == i).any() else c[i] for i in range(2)])
    lo, hi = sorted(c)
    thr, gap = (lo + hi) / 2, hi - lo
    lines = []
    for seg, v in zip(segs, feats):
        tag = '?' if v is None or gap < a.min_gap else ('A' if v < thr - 1.5 else 'B' if v > thr + 1.5 else '?')
        m, sec = divmod(seg['start'], 60)
        lines.append(f"[{int(m):02d}:{sec:04.1f}] {tag} {seg['text'].strip()}")
    head = f'# centroids {lo:.1f}/{hi:.1f} dB, gap {gap:.1f} dB; A = darker path, B = brighter path; hint only, confirm by reading\n'
    Path(a.out).write_text(head + '\n'.join(lines) + '\n', encoding='utf-8')
    say({'status': 'written', 'output': a.out, 'gap_db': round(float(gap), 1), 'segments': len(segs)})
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='command', required=True)

    def base(name, help_text):
        p = sp.add_parser(name, help=help_text)
        p.add_argument('--manifest', required=True, help='research/sources.json (media-cloner-sources/v1, split frozen)')
        p.add_argument('--partition', choices=['train', 'holdout', 'all'], default='train')
        p.add_argument('--frozen', help='frozen style-pack directory; required to unseal holdout')
        return p
    m = base('media', 'whole-file measurements')
    m.add_argument('--out', required=True); m.add_argument('--sample', action='append')
    m.add_argument('--workers', type=int, default=2); m.add_argument('--scene-threshold', type=float, default=0.23)
    m.add_argument('--silence-db', type=float, default=-35); m.add_argument('--silence-min', type=float, default=0.2)
    l = base('layout', 'OCR layout scan')
    l.add_argument('--out', required=True); l.add_argument('--sample', action='append')
    l.add_argument('--every', type=float, default=2.0); l.add_argument('--zones', help='zones JSON; default assets/layout-zones.vertical.json')
    l.add_argument('--wall-regex', help='regex for background signage to ignore'); l.add_argument('--colors', action='store_true')
    l.add_argument('--discover', action='store_true', help='add a histogram of text-box positions to help define zones')
    t = base('tones', 'test-tone scan')
    t.add_argument('--out', required=True); t.add_argument('--sample', action='append')
    t.add_argument('--frequency', type=float, default=1000); t.add_argument('--band', type=float, default=20)
    t.add_argument('--ratio', type=float, default=2000); t.add_argument('--min-dbfs', type=float, default=-15)
    r = base('transcribe', 'local ASR')
    r.add_argument('--raw', required=True); r.add_argument('--out', required=True); r.add_argument('--sample', action='append')
    r.add_argument('--backend', choices=['auto', 'mlx-whisper', 'whisper'], default='auto'); r.add_argument('--model')
    r.add_argument('--language', default='zh'); r.add_argument('--force', action='store_true')
    i = base('import', 'normalise existing transcripts')
    i.add_argument('--input', required=True); i.add_argument('--out', required=True); i.add_argument('--sample', action='append')
    i.add_argument('--format', choices=['auto', 'whisper', 'tingwu', 'srt'], default='auto')
    i.add_argument('--provider'); i.add_argument('--language', default=None)
    k = base('speakers', 'speaker hint')
    k.add_argument('--sample', required=True); k.add_argument('--transcript', required=True); k.add_argument('--out', required=True)
    k.add_argument('--min-gap', type=float, default=6.0)
    a = ap.parse_args()
    try:
        return globals()['cmd_' + a.command](a)
    except Fail as exc:
        say({'status': 'failed', 'command': a.command, 'message': str(exc)})
        return 1


if __name__ == '__main__':
    sys.exit(main())
