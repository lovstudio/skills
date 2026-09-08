#!/usr/bin/env python3
"""Inspect, transcribe, plan and render a source-faithful prepared video library."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import wave


def speech_clips(wav, model):
    """Conservative ASR windows; these are never editorial deletion ranges."""
    import numpy as np
    import torch
    from silero_vad import get_speech_timestamps
    with wave.open(str(wav)) as f:
        samples=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype('float32')/32768
    spans=get_speech_timestamps(torch.from_numpy(samples),model,sampling_rate=16000,
        threshold=.3,min_speech_duration_ms=150,min_silence_duration_ms=800,speech_pad_ms=1000,
        return_seconds=False)
    merged=[]
    for span in spans:
        a,b=span['start']/16000,span['end']/16000
        if merged and a-merged[-1][1]<6: merged[-1][1]=b
        else: merged.append([a,b])
    return merged


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, data):
    path = Path(path)
    temp = path.with_name(path.name + ".writing")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def plan_digest(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def finite(value, low=0, high=math.inf):
    value = float(value)
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"value outside [{low}, {high}]: {value}")
    return value


def run(cmd, log=None):
    if log:
        with Path(log).open("w") as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
        if result.returncode:
            raise ValueError(f"command failed ({result.returncode}); see {log}")
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stderr[-3000:])
        return result.stdout


def probe(path):
    path = Path(path).expanduser().resolve(strict=True)
    p = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]))
    videos = [s for s in p["streams"] if s["codec_type"] == "video"]
    v = videos[0] if videos else {}
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read(1 << 20))
        f.seek(max(0, path.stat().st_size - (1 << 20)))
        h.update(f.read(1 << 20))
    return {"path": str(path), "name": path.name, "bytes": path.stat().st_size,
            "edge_sha256": h.hexdigest(), "duration": finite(p["format"]["duration"], .001),
            "width": v.get("width"), "height": v.get("height"),
            "fps": v.get("avg_frame_rate", "0/1"),
            "color_transfer": v.get("color_transfer", "unknown"),
            "has_audio": any(s["codec_type"] == "audio" for s in p["streams"]),
            "streams": [{k: s.get(k) for k in ["codec_type", "codec_name", "duration", "start_time", "sample_rate", "channels"]} for s in p["streams"]]}


def same_source(a, b):
    return all(a[k] == b[k] for k in ("bytes", "edge_sha256")) and abs(a["duration"] - b["duration"]) < .05


def setup(out, contract, resume=False):
    out = Path(out).expanduser().resolve()
    if out.exists():
        if not resume or not (out / "run.json").is_file() or read(out / "run.json") != contract:
            raise ValueError("occupied output or resume contract mismatch")
    else:
        out.mkdir(parents=True)
        write(out / "run.json", contract)
    return out


def timecode(t):
    ms = round(t * 1000)
    return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}.{ms%1000:03d}"


def join_cues(previous, incoming):
    """Merge only matching utterances overlapping across an ASR chunk boundary."""
    for cue in incoming:
        if previous and previous[-1]['chunk']!=cue['chunk']:
            old=previous[-1]
            a,b=re.sub(r'\W','',old['text']),re.sub(r'\W','',cue['text'])
            overlap=min(old['end'],cue['end'])-max(old['start'],cue['start'])
            if min(len(a),len(b))>=4 and (a in b or b in a) and min(len(a),len(b))/max(len(a),len(b))>=.8 and overlap>min(old['end']-old['start'],cue['end']-cue['start'])*.5:
                old['end']=max(old['end'],cue['end'])
                if len(b)>len(a):old['text']=cue['text']
                old['overlap_merged_from_chunk']=cue['chunk']
                continue
        previous.append(dict(cue))


def transcribe(args):
    audio = Path(args.audio).expanduser().resolve(strict=True)
    model = Path(args.model).expanduser().resolve(strict=True)
    info = probe(audio)
    chunk = finite(args.chunk_seconds, 30, 1800)
    vad_model=None;vad_contract=None
    if args.vad:
        if args.backend!='mlx': raise ValueError('--vad currently requires the mlx backend')
        import torch
        import silero_vad
        torch.set_num_threads(1)
        vad_model=silero_vad.load_silero_vad()
        vad_file=Path(silero_vad.__file__).parent/'data/silero_vad.jit'
        vad_contract={'sha256':sha(vad_file),'threshold':.3,'speech_pad_ms':1000,'merge_gap_seconds':6}
    if args.backend == 'mlx':
        import mlx_whisper
        weights=model/'weights.safetensors'
        if not weights.is_file(): weights=model/'weights.npz'
        model_sha=hashlib.sha256((sha(model/'config.json')+sha(weights)).encode()).hexdigest()
    else:
        model_sha=sha(model)
    audio_filter='loudnorm=I=-20:TP=-1.5:LRA=11'
    contract = {"stage": "asr", "audio_sha256": sha(audio), "model_sha256": model_sha,
                "language": args.language, "chunk_seconds": chunk, "overlap_seconds": 2,
                "backend":args.backend,"audio_filter":audio_filter,"condition_on_previous_text":False,'vad':vad_contract,
                'window_execution':'independent'}
    reuse=None
    if args.reuse_asr:
        reuse=Path(args.reuse_asr).resolve(strict=True)
        old=read(reuse/'run.json')
        if any(old.get(k)!=contract[k] for k in ['audio_sha256','model_sha256','language','chunk_seconds','overlap_seconds','backend','audio_filter']):
            raise ValueError('ASR reuse requires identical audio, model and chunk coordinates')
        contract['reused_run']={'path':str(reuse),'contract_sha256':sha(reuse/'run.json')}
    out = setup(args.output, contract, args.resume)
    cues = []
    total = math.ceil(info["duration"] / chunk)
    for i in range(total):
        owner_start, owner_end = i*chunk, min((i+1)*chunk, info["duration"])
        start, end = max(0, owner_start-2), min(info["duration"], owner_end+2)
        stem = out / f"chunk-{i+1:04d}"
        done = stem.with_suffix(".done.json")
        if not done.exists() and reuse is not None and (reuse/done.name).is_file():
            imported=read(reuse/done.name)
            raw_path=reuse/stem.with_suffix('.json').name
            if sha(raw_path)!=imported['raw_sha256']: raise ValueError('imported ASR chunk hash mismatch')
            shutil.copyfile(raw_path,stem.with_suffix('.json'))
            imported['provenance']={'reused_run':str(reuse),'contract_sha256':contract['reused_run']['contract_sha256']}
            write(done,imported)
        if done.is_file():
            result = read(done)
            if sha(stem.with_suffix(".json")) != result["raw_sha256"]:
                raise ValueError("ASR chunk hash mismatch")
            chunk_cues = result["cues"]
        else:
            wav = stem.with_suffix(".wav")
            if wav.exists():
                wav.unlink()  # This stage owns this incomplete temporary audio.
            run(["ffmpeg", "-v", "error", "-n", "-ss", str(start), "-i", str(audio), "-t", str(end-start),
                 "-ac", "1", "-af", audio_filter, "-ar", "16000", "-c:a", "pcm_s16le", str(wav)])
            if args.backend=='mlx':
                clips=speech_clips(wav,vad_model) if vad_model is not None else [[0,end-start]]
                print(f'ASR window {i+1}/{total}: {sum(b-a for a,b in clips):.1f}s candidate speech',flush=True)
                # mlx-whisper 0.4.3 does not reset seek at later clip starts.
                # Run each absolute window separately so VAD gaps really stay unprocessed.
                results=[mlx_whisper.transcribe(str(wav),path_or_hf_repo=str(model),language=args.language,
                    condition_on_previous_text=False,word_timestamps=True,hallucination_silence_threshold=2,
                    clip_timestamps=[a,b],verbose=None) for a,b in clips]
                raw={'segments':[s for part in results for s in part['segments']],
                     'text':' '.join(part['text'] for part in results),'window_results':results}
                raw['analysis_windows']=clips
                raw['vad_used']=vad_model is not None
                write(stem.with_suffix('.json'),raw)
                raw_cues=[{'text':c['text'],'a':c['start'],'b':c['end'],
                           'quality':{'avg_logprob':c.get('avg_logprob'),'no_speech_prob':c.get('no_speech_prob')}} for c in raw['segments']]
            else:
                run([args.whisper, "-m", str(model), "-f", str(wav), "-l", args.language,
                     "-t", str(args.threads), "-mc", "0", "-ojf", "-osrt", "-of", str(stem), "-sns"], stem.with_suffix(".log"))
                raw = read(stem.with_suffix(".json"))
                raw_cues=[{'text':c['text'],'a':c['offsets']['from']/1000,'b':c['offsets']['to']/1000} for c in raw['transcription']]
            chunk_cues = []
            for cue in raw_cues:
                text = cue["text"].strip()
                a = start + cue['a']
                b = start + cue['b']
                if text and owner_start <= (a+b)/2 < owner_end and a < b:
                    chunk_cues.append({"start": max(0,a), "end": min(info["duration"],b), "text": text,
                                       "chunk": i+1, "alignment": "asr-estimate",'quality':cue.get('quality',{})})
            write(done, {"cues": chunk_cues, "raw_sha256": sha(stem.with_suffix(".json"))})
            wav.unlink()
        join_cues(cues,chunk_cues)
        write(out / "progress.json", {"completed_chunks": i+1, "total_chunks": total, "covered_until": owner_end})
        write(out / "transcript.json", {"schema": "media-transcript/v1", "audio": info,
              "audio_sha256": contract["audio_sha256"], "model_sha256": contract["model_sha256"],
              "status": "complete" if i+1 == total else "running", "covered_until": owner_end, "cues": cues})
        (out / "transcript.txt").write_text("\n".join(f"{timecode(c['start'])} --> {timecode(c['end'])} {c['text']}" for c in cues), encoding="utf-8")
        print(f"ASR {i+1}/{total}: {timecode(owner_end)}", flush=True)


def analyze(args):
    import cv2
    import numpy as np
    source = probe(args.video)
    interval = finite(args.interval, 1, 300)
    if not source["width"]:
        raise ValueError("video stream required")
    contract = {"stage": "analysis", "source": source, "interval": interval, "width": 640}
    out = setup(args.output, contract, args.resume)
    (out / "frames").mkdir(exist_ok=True)
    times = [round(i*interval, 6) for i in range(math.ceil(source["duration"] / interval))]
    if len(times) > 3000:
        raise ValueError("more than 3000 samples; increase interval")
    def one(t):
        file = out / "frames" / f"{round(t*1000):012d}.jpg"
        if not file.is_file():
            temp = file.with_name(file.stem + ".partial.jpg")
            if temp.exists(): temp.unlink()
            run(["ffmpeg", "-v", "error", "-n", "-ss", str(t), "-i", source["path"],
                 "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "3", str(temp)])
            temp.replace(file)
        im = cv2.imread(str(file))
        if im is None:
            raise ValueError(f"cannot decode sample {t}")
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        subject = gray[int(gray.shape[0]*.60):]
        small = cv2.resize(gray, (17,16))
        bits = (small[:,1:] > small[:,:-1]).ravel()
        return {"time":t, "file":str(file.relative_to(out)), "sha256":sha(file),
                "luma": round(float(gray.mean()),3), "subject_luma":round(float(subject.mean()),3),
                "sharpness":round(float(cv2.Laplacian(gray,cv2.CV_64F).var()),3),
                "black_fraction":round(float(np.mean(gray<12)),4),
                "clipped_fraction":round(float(np.mean(gray>248)),4),
                "dhash":hex(int(''.join(map(lambda x:'1' if x else '0',bits)),2))[2:]}
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(one, times):
            rows.append(row)
            if len(rows)%20 == 0:
                write(out / "progress.json", {"completed":len(rows),"total":len(times)})
    audio = out / "audio-16k.wav"
    if source["has_audio"] and not audio.is_file():
        run(["ffmpeg", "-v", "error", "-n", "-i", source["path"], "-map", "0:a:0", "-vn",
             "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio)])
    quiet, windows = [], []
    if source["has_audio"]:
        with wave.open(str(audio)) as wav:
            assert wav.getsampwidth()==2 and wav.getnchannels()==1
            rate=wav.getframerate(); pos=0; quiet_start=None
            while True:
                raw=wav.readframes(round(rate*.25))
                if not raw: break
                vals=np.frombuffer(raw,dtype='<i2').astype(float)/32768
                db=float(20*np.log10(max(1e-9,np.sqrt(np.mean(vals*vals)))))
                a,b=pos/rate,(pos+len(vals))/rate
                windows.append({"start":a,"end":b,"rms_db":round(db,3)})
                if db < -42 and quiet_start is None: quiet_start=a
                if db >= -42 and quiet_start is not None:
                    if a-quiet_start>=2: quiet.append({"start":quiet_start,"end":a})
                    quiet_start=None
                pos+=len(vals)
            if quiet_start is not None and pos/rate-quiet_start>=2: quiet.append({"start":quiet_start,"end":pos/rate})
    write(out / "audio-windows.json", windows)
    result={"schema":"media-analysis/v1", "source":source,"status":"complete", "sample_interval":interval,
            "coverage":"full-span-sparse-visual-and-continuous-audio", "semantic_review":False,
            "frames":rows,"quiet_intervals":quiet,"audio":str(audio) if source["has_audio"] else None,
            "audio_sha256":sha(audio) if source["has_audio"] else None}
    sheets=[]
    for offset in range(0,len(rows),24):
        page=np.full((6*250,4*400,3),235,dtype=np.uint8)
        for j,row in enumerate(rows[offset:offset+24]):
            im=cv2.imread(str(out/row['file']))
            im=cv2.resize(im,(392,220))
            x,y=(j%4)*400+4,(j//4)*250+4
            page[y:y+220,x:x+392]=im
            cv2.putText(page,timecode(row['time']),(x,y+238),cv2.FONT_HERSHEY_SIMPLEX,.45,(30,30,30),1,cv2.LINE_AA)
        name=f'contact-{offset//24+1:02d}.jpg'
        if not cv2.imwrite(str(out/name),page): raise ValueError('cannot save contact sheet')
        sheets.append(name)
    result['contact_sheets']=sheets
    write(out / "analysis.json", result)
    print(json.dumps({"frames":len(rows),"quiet_intervals":len(quiet),"output":str(out)}))


def grade_filter(grade):
    if grade.get("mode") == "neutral":
        return "null"
    if grade.get('mode') != 'bright-documentary':
        raise ValueError('unknown grade mode')
    points=grade.get("curve", [[0,0],[.05,.02],[.1,.15],[.2,.4],[.3,.58],[.5,.75],[.7,.86],[.9,.95],[1,1]])
    if len(points)<2 or len(points)>16:
        raise ValueError("curve needs 2–16 points")
    pairs=[(finite(a,0,1),finite(b,0,1)) for a,b in points]
    if pairs[0]!=(0,0) or pairs[-1]!=(1,1) or any(b[0]<=a[0] or b[1]<a[1] for a,b in zip(pairs,pairs[1:])):
        raise ValueError("curve must be monotonic from 0/0 to 1/1")
    balance=grade.get("balance", {"rs":.015,"bs":-.02,"rm":.015,"bm":-.02,"rh":.01,"bh":-.03})
    if set(balance)-set(['rs','gs','bs','rm','gm','bm','rh','gh','bh']):
        raise ValueError("unknown color balance channel")
    cb=":".join(f"{k}={finite(v,-.15,.15)}" for k,v in balance.items())
    curve=' '.join(f'{a}/{b}' for a,b in pairs)
    return f"curves=master='{curve}'"+(f",colorbalance={cb}:pl=1" if cb else "")


def validate_plan(plan, source=None):
    if plan.get("schema")!="media-preprocess-plan/v1":
        raise ValueError("wrong plan schema")
    if plan.get('basis') not in ('technical-proposal-only','enhancement-only','semantic-reviewed'):
        raise ValueError('unknown plan basis')
    if source and not same_source(source,plan["source"]):
        raise ValueError("source mismatch")
    duration=finite(plan["source"]["duration"],.001)
    grade_filter(plan["grade"])
    if plan["source"].get("color_transfer") not in ("bt709","unknown","unspecified",None):
        raise ValueError("HDR/Log needs an explicit managed transform before this SDR pipeline")
    segments=plan["segments"]; end=0; ids=set()
    if not segments: raise ValueError("empty timeline")
    for seg in segments:
        a,b=finite(seg["start"],0,duration),finite(seg["end"],0,duration)
        if abs(a-end)>.025 or b<=a: raise ValueError("timeline gap, overlap or invalid range")
        sid=seg["id"]
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',sid) or sid in ids: raise ValueError("invalid/duplicate segment id")
        ids.add(sid)
        if seg.get("decision") not in ("keep","drop","review"): raise ValueError("invalid decision")
        if plan['basis'] != 'semantic-reviewed' and seg['decision'] != 'review':
            raise ValueError('content decisions require semantic-reviewed basis')
        if not seg.get("title") or not seg.get("reason") or not isinstance(seg.get("evidence"),list) or not seg["evidence"]:
            raise ValueError("title, reason and evidence required")
        if seg["decision"]=="drop":
            r=seg.get("review",{})
            if not all(r.get(k) is True for k in ["content_checked","visual_checked","boundary_checked"]):
                raise ValueError("drop requires actual content, visual and boundary review")
            if seg.get("contains_unique_content",True): raise ValueError("unique content cannot be dropped")
        if "grade" in seg: grade_filter(seg["grade"])
        end=b
    if abs(end-duration)>.025: raise ValueError("timeline must cover entire source")
    if not any(s['decision']!='drop' for s in segments): raise ValueError("cannot discard entire video")
    return plan


def plan_command(args):
    analysis=read(args.analysis)
    if args.decisions:
        plan=read(args.decisions)
        validate_plan(plan,analysis["source"])
    else:
        plan={"schema":"media-preprocess-plan/v1","source":analysis["source"],
              "basis":"technical-proposal-only","grade":{"mode":"bright-documentary"},
              "segments":[{"id":"segment-001","start":0,"end":analysis["source"]["duration"],
                           "title":"待语义审阅的完整素材","decision":"review","reason":"技术信号不能代替内容取舍",
                           "evidence":["analysis.json"],"contains_unique_content":True}]}
        validate_plan(plan)
        if args.enhancement_only:
            plan['basis']='enhancement-only'
            plan['segments'][0]['title']='全片明亮增强（未删减）'
            plan['segments'][0]['reason']='只完成画面增强；内容取舍与语义分段另行审阅'
    out=Path(args.output)
    if out.exists(): raise ValueError("output exists")
    write(out,plan)
    print(json.dumps({"segments":len(plan['segments']),"basis":plan['basis']}))


def media_check(path, duration, has_audio, decode=False):
    p=probe(path)
    if abs(p['duration']-duration)>max(.25,duration*.0001): raise ValueError("output duration mismatch")
    if p['has_audio']!=has_audio: raise ValueError("audio track mismatch")
    starts=[float(s['start_time']) for s in p['streams'] if s['start_time'] is not None and s['codec_type'] in ('audio','video')]
    if starts and max(starts)-min(starts)>.15: raise ValueError("audio/video start mismatch")
    if decode:
        run(["ffmpeg","-v","error","-xerror","-i",str(path),"-f","null","-"])
    return p


def compile_cube(grade, output):
    """Sample the numerical SDR transform at 65^3 points for Core Image."""
    import numpy as np
    n=65;v=np.linspace(0,65535,n).round().astype('<u2')
    b,g,r=np.meshgrid(v,v,v,indexing='ij');pixels=np.stack([r,g,b],axis=-1)
    result=subprocess.run(['ffmpeg','-v','error','-f','rawvideo','-pixel_format','rgb48le',
        '-video_size',f'{n*n}x{n}','-i','pipe:0','-frames:v','1','-vf',grade_filter(grade),
        '-f','rawvideo','-pix_fmt','rgb48le','pipe:1'],input=pixels.tobytes(),capture_output=True)
    if result.returncode: raise ValueError(result.stderr.decode()[-2000:])
    values=np.frombuffer(result.stdout,dtype='<u2').reshape(-1,3).astype('<f4')/65535
    np.concatenate([values,np.ones((len(values),1),dtype='<f4')],axis=1).astype('<f4').tofile(output)


def write_gallery(out, plan, manifest):
    """One local player, searchable segment list, and explicit review retention."""
    segments={s['id']:s for s in plan['segments']}
    files=[dict(f,reason=segments[f['id']]['reason']) for f in manifest['files']]
    payload=json.dumps(files,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    keep=sum(f['duration'] for f in files if f['decision']=='keep')
    review=sum(f['duration'] for f in files if f['decision']=='review')
    links=''.join(f"<li><a href='{html.escape(f['file'],quote=True)}'>{html.escape(f['title'])}</a></li>" for f in files)
    page="""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>媒体素材库</title><style>
:root{color-scheme:light;--ink:#282b29;--muted:#74786f;--line:#deded5;--paper:#f6f5f0;--green:#3a5547}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.65 system-ui,-apple-system,sans-serif}header,main,footer{max-width:1440px;margin:auto;padding:28px 36px}header{border-bottom:1px solid var(--line)}.eyebrow{font-size:12px;letter-spacing:2px;color:var(--muted)}h1{font-size:34px;letter-spacing:-1px;margin:8px 0}header p{margin:6px 0;color:var(--muted)}.stats{display:flex;gap:28px;flex-wrap:wrap;margin-top:20px}.stats b{font-size:22px;margin-right:6px;font-weight:550}main{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(330px,1fr);gap:32px}.player{position:sticky;top:24px;align-self:start}video{width:100%;aspect-ratio:16/9;background:#1e211e;border-radius:6px}h2{font-size:23px;line-height:1.5;margin:18px 0 7px}#source{font:13px/1.6 ui-monospace,monospace;color:var(--muted)}#reason{color:#62685f}a{color:var(--green);text-underline-offset:4px}button,input{font:inherit}input{width:100%;padding:11px 14px;border:1px solid var(--line);background:white;border-radius:5px;margin-bottom:12px}nav{display:flex;gap:6px;margin-bottom:14px}button{cursor:pointer;border:1px solid var(--line);background:transparent;color:inherit;border-radius:5px;padding:7px 12px}button.active{background:var(--green);color:white;border-color:var(--green)}.row{display:block;width:100%;text-align:left;border:0;border-bottom:1px solid var(--line);border-radius:0;padding:16px 13px}.row.selected{background:#e7ece4}.row small{display:block;color:var(--muted);font:12px/1.6 ui-monospace,monospace;margin-top:5px}.tag{font-size:11px;margin-right:9px;color:var(--muted)}#list{max-height:73vh;overflow:auto}.controls{display:flex;gap:9px;align-items:center;margin-top:20px}.controls a{margin-left:auto}footer{font-size:13px;color:var(--muted);border-top:1px solid var(--line)}#empty{color:var(--muted);padding:30px 0}@media(max-width:850px){header,main,footer{padding:22px 18px}main{display:block}.player{position:static;margin-bottom:30px}#list{max-height:none}h1{font-size:29px}.stats{gap:15px}}
</style></head><body><header><div class="eyebrow">LOCAL MEDIA LIBRARY</div><h1>媒体素材库</h1><p>按内容组织的明亮素材。保持原始顺序、画幅与原声。</p><div class="stats">__STATS__</div></header>
<main><section class="player"><video id="player" controls preload="metadata" playsinline></video><h2 id="title"></h2><div id="source"></div><p id="reason"></p><div class="controls"><button id="prev">上一段</button><button id="next">下一段</button><a id="download" download>下载此段</a></div></section><section><input id="search" type="search" placeholder="搜索主题或说明" aria-label="搜索片段"><nav aria-label="片段筛选"><button data-filter="keep">可用内容</button><button data-filter="review">待复核</button><button data-filter="all">全部保留</button></nav><div id="count"></div><div id="list"></div><p id="empty" hidden>没有匹配的片段。</p></section></main>
<footer>待复核片段已保留在素材库中。删减理由与源时间码见 <a href="plan.json">取舍清单</a>；文件与时间线映射见 <a href="manifest.json">素材清单</a>。原片不受影响。<noscript><ul>__LINKS__</ul></noscript></footer>
<script id="data" type="application/json">__DATA__</script><script>
const files=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id);let filter=files.some(f=>f.decision==='keep')?'keep':'all',selected=null,visible=[];
const clock=s=>{s=Math.floor(s);return [Math.floor(s/3600),Math.floor(s/60)%60,s%60].map(v=>String(v).padStart(2,'0')).join(':')};
function select(f){if(!f)return;selected=f;$('player').src=f.file;$('title').textContent=f.title;$('source').textContent=`原片 ${clock(f.source_start)} — ${clock(f.source_end)} · ${clock(f.duration)} · ${f.decision==='review'?'待复核':'可用内容'}`;$('reason').textContent=f.reason;$('download').href=f.file;renderList()}
function renderList(){const query=$('search').value.trim().toLowerCase();visible=files.filter(f=>(filter==='all'||f.decision===filter)&&(f.title+' '+f.reason).toLowerCase().includes(query));$('list').replaceChildren();for(const f of visible){const b=document.createElement('button');b.className='row'+(selected?.id===f.id?' selected':'');b.textContent=f.title;const s=document.createElement('small');s.textContent=`${String(files.indexOf(f)+1).padStart(2,'0')} / ${clock(f.source_start)} / ${clock(f.duration)}${f.decision==='review'?' / 待复核':''}`;b.append(s);b.onclick=()=>select(f);$('list').append(b)}$('count').textContent=`${visible.length} 段 · ${clock(visible.reduce((n,f)=>n+f.duration,0))}`;$('empty').hidden=visible.length>0;document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('active',b.dataset.filter===filter))}
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;renderList();if(!visible.some(f=>f.id===selected?.id)&&visible.length)select(visible[0])});$('search').oninput=renderList;$('prev').onclick=()=>select(visible[Math.max(0,visible.indexOf(selected)-1)]);$('next').onclick=()=>select(visible[Math.min(visible.length-1,visible.indexOf(selected)+1)]);renderList();select(visible[0]);
</script></body></html>"""
    stats=f'<span><b>{len(files)}</b> 个片段</span><span><b>{keep/60:.1f}</b> 分钟可用</span><span><b>{review/60:.1f}</b> 分钟待复核</span><span><b>{manifest.get("dropped_duration",0)/60:.1f}</b> 分钟已剔除</span>'
    page=page.replace('__STATS__',stats).replace('__LINKS__',links).replace('__DATA__',payload)
    (Path(out)/'gallery.html').write_text(page,encoding='utf-8')


def render(args):
    plan=read(args.plan); source=probe(args.video)
    validate_plan(plan,source)
    if not args.preview and plan.get("basis")=="technical-proposal-only":
        raise ValueError("semantic review required before full render; use --preview to inspect grading")
    input_path=source['path'];prepared_contract=None
    if args.prepared_run:
        if args.engine!='ffmpeg':raise ValueError('prepared master reuse uses the ffmpeg engine')
        prep=Path(args.prepared_run).resolve(strict=True);pm=read(prep/'manifest.json');pp=read(prep/'plan.json')
        if pm.get('status')!='rendered' or pp.get('basis')!='enhancement-only' or len(pm['files'])!=1 or not same_source(pm['source'],source) or plan_digest(pp)!=pm['plan_sha256']:
            raise ValueError('prepared master must be a complete, unchanged enhancement of this source')
        f=pm['files'][0];master=(prep/f['file']).resolve()
        if prep not in master.parents or abs(f['source_start'])>.025 or abs(f['source_end']-source['duration'])>.025 or sha(master)!=f['sha256']:
            raise ValueError('prepared master coverage or hash mismatch')
        if any(grade_filter(s.get('grade',plan['grade']))!=grade_filter(f['grade']) for s in plan['segments'] if s['decision']!='drop'):
            raise ValueError('prepared master grade does not match requested segment grades')
        media_check(master,source['duration'],source['has_audio'])
        input_path=str(master);prepared_contract={'manifest_sha256':sha(prep/'manifest.json'),'master_sha256':f['sha256'],'path':input_path,'video_encoding_generation':2,'audio_input':'original-source'}
    contract={"stage":"render","source":source,"plan_sha256":plan_digest(plan),"codec":args.codec,
              "bitrate_mbps":args.bitrate_mbps,"preview":args.preview,"concatenate":args.concatenate,
              'engine':args.engine,'resolved_grades':[grade_filter(s.get('grade',plan['grade'])) for s in plan['segments']],
              'prepared_master':prepared_contract}
    if args.engine=='metal':
        if sys.platform!='darwin' or args.codec!='h264_videotoolbox':
            raise ValueError('Metal requires macOS and h264_videotoolbox')
        contract['renderer_sha256']=sha(Path(__file__).with_name('render_metal.swift'))
    out=setup(args.output,contract,args.resume)
    (out/'segments').mkdir(exist_ok=True)
    write(out/'plan.json',plan)
    if args.engine=='metal':
        binary=out/'render-metal'
        if not binary.exists():
            run(['xcrun','swiftc','-O',str(Path(__file__).with_name('render_metal.swift')),'-o',str(binary)],out/'compile-metal.log')
    files=[]; timeline=0
    selected=[s for s in plan['segments'] if s['decision']!='drop']
    if args.preview: selected=selected[:1]
    for i,seg in enumerate(selected):
        duration=min(seg['end']-seg['start'],args.preview) if args.preview else seg['end']-seg['start']
        name=f"{i+1:03d}-{seg['id']}.mp4"; dst=out/'segments'/name; done=dst.with_suffix('.done.json')
        grade=seg.get('grade',plan['grade'])
        if dst.exists() and done.is_file():
            entry=read(done)
            if sha(dst)!=entry['sha256']: raise ValueError("rendered file changed")
            media_check(dst,duration,source['has_audio'])
        else:
            if dst.exists(): raise ValueError("unverified existing final; inspect it before resuming")
            temp=dst.with_name(dst.stem+'.partial.mp4')
            if temp.exists(): temp.unlink()
            needed=duration*(args.bitrate_mbps*1e6+256000)/8*1.4+512*1024*1024
            if shutil.disk_usage(out).free<needed: raise ValueError("insufficient output space")
            cmd=['ffmpeg','-hide_banner','-nostdin','-v','warning','-n','-ss',str(seg['start']),'-i',input_path]
            if prepared_contract and source['has_audio']:
                cmd+=['-ss',str(seg['start']),'-i',source['path']]
            cmd+=['-t',str(duration),'-map','0:v:0','-map','1:a:0?' if prepared_contract and source['has_audio'] else '0:a:0?',
                  '-vf','null' if prepared_contract else grade_filter(grade),'-c:v',args.codec]
            if args.codec=='libx264': cmd+=['-preset','slow','-crf','18']
            else: cmd+=['-b:v',str(round(args.bitrate_mbps*1e6))]
            cmd+=['-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-ar','48000','-map_metadata','-1',
                  '-movflags','+faststart','-progress',str(dst.with_suffix('.progress.txt')),str(temp)]
            if args.engine=='metal':
                cube=dst.with_suffix('.cube-rgba')
                compile_cube(grade,cube)
                run([str(binary),source['path'],str(temp),str(seg['start']),str(duration),str(cube),'65',str(args.bitrate_mbps)],dst.with_suffix('.log'))
            else:
                run(cmd,dst.with_suffix('.log'))
            p=media_check(temp,duration,source['has_audio'])
            if [p['width'],p['height']]!=[source['width'],source['height']]: raise ValueError("size changed")
            temp.replace(dst)
            entry={"id":seg['id'],"title":seg['title'],"decision":seg['decision'],"file":str(dst.relative_to(out)),
                   "source_start":seg['start'],"source_end":seg['start']+duration,"duration":duration,
                   "timeline_start":timeline,"timeline_end":timeline+duration,"sha256":sha(dst),
                   "size":[p['width'],p['height']],"audio":p['has_audio'],"grade":grade}
            write(done,entry)
        files.append(entry);timeline+=duration
        write(out/'progress.json',{"completed":i+1,"total":len(selected),"processed_source_until":seg['end']})
        write(out/'manifest.json',{"schema":"media-preprocess-output/v1","status":"rendering","source":source,
                                  "plan_sha256":contract['plan_sha256'],"files":files})
        print(f"render {i+1}/{len(selected)}: {name}",flush=True)
    manifest={"schema":"media-preprocess-output/v1","status":"preview" if args.preview else "rendered",
              "source":source,"plan_sha256":contract['plan_sha256'],"files":files,"kept_duration":timeline,
              "dropped_duration":sum(s['end']-s['start'] for s in plan['segments'] if s['decision']=='drop'),
              "review_duration":sum(f['duration'] for f in files if f['decision']=='review'),"publication":"not-published",
              'prepared_master':prepared_contract}
    if args.concatenate and not args.preview:
        listing=out/'concat.txt'
        listing.write_text(''.join(f"file '{f['file']}'\n" for f in files),encoding='utf-8')
        dst=out/'prepared.mp4'
        stamp=out/'prepared.done.json'
        if dst.exists():
            if not stamp.is_file() or read(stamp)['sha256']!=sha(dst): raise ValueError("unverified assembled output")
        else:
            temp=out/'prepared.partial.mp4'
            if temp.exists(): temp.unlink()
            if shutil.disk_usage(out).free<sum((out/f['file']).stat().st_size for f in files)*1.1:
                raise ValueError("insufficient space for assembled copy")
            run(['ffmpeg','-v','error','-n','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(temp)],out/'concat.log')
            media_check(temp,timeline,source['has_audio'])
            temp.replace(dst)
            write(stamp,{'sha256':sha(dst)})
        media_check(dst,timeline,source['has_audio'])
        manifest['assembled']={"file":"prepared.mp4","sha256":sha(dst),"duration":timeline}
    write(out/'manifest.json',manifest)
    write_gallery(out,plan,manifest)
    print(json.dumps({"output":str(out),"files":len(files),"duration":timeline}))


def verify(args):
    out=Path(args.output).resolve();m=read(out/'manifest.json')
    if m.get('status') not in ('preview','rendered'): raise ValueError('render is not complete')
    plan=read(out/'plan.json')
    if plan_digest(plan)!=m['plan_sha256']: raise ValueError("plan modified")
    validate_plan(plan,m['source'])
    selected=[s for s in plan['segments'] if s['decision']!='drop']
    if m['status']=='preview':selected=selected[:1]
    if [s['id'] for s in selected]!=[f['id'] for f in m['files']]:raise ValueError('incomplete or reordered segment files')
    timeline=0
    for seg,f in zip(selected,m['files']):
        if abs(f['source_start']-seg['start'])>.025 or abs(f['timeline_start']-timeline)>.025:
            raise ValueError('source or output timeline mismatch')
        expected=seg['end']-seg['start'] if m['status']=='rendered' else min(seg['end']-seg['start'],read(out/'run.json')['preview'])
        if abs(f['duration']-expected)>.025 or abs(f['source_end']-seg['start']-expected)>.025:
            raise ValueError('segment coverage mismatch')
        timeline+=expected
        if abs(f['timeline_end']-timeline)>.025:raise ValueError('output timeline mismatch')
    if abs(m['kept_duration']-timeline)>.025:raise ValueError('kept duration mismatch')
    for f in m['files']+([m['assembled']] if 'assembled' in m else []):
        p=(out/f['file']).resolve()
        if out not in p.parents: raise ValueError("path escapes output")
        if sha(p)!=f['sha256']: raise ValueError("output hash mismatch")
        info=media_check(p,f['duration'],m['source']['has_audio'],args.decode)
        if [info['width'],info['height']]!=[m['source']['width'],m['source']['height']] or Fraction(info['fps'])!=Fraction(m['source']['fps']):
            raise ValueError('output dimensions or frame rate changed')
    report={"status":"passed","count":len(m['files']),"full_decode":args.decode,"semantic_review":"separate"}
    write(out/'verification.json',report);print(json.dumps(report))


def main():
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='command',required=True)
    p=subs.add_parser('probe');p.add_argument('video')
    p=subs.add_parser('analyze');p.add_argument('video');p.add_argument('--output',required=True);p.add_argument('--interval',type=float,default=30);p.add_argument('--workers',type=int,choices=range(1,5),default=2);p.add_argument('--resume',action='store_true')
    p=subs.add_parser('transcribe');p.add_argument('audio');p.add_argument('--model',required=True);p.add_argument('--backend',choices=['whisper-cpp','mlx'],default='whisper-cpp');p.add_argument('--vad',action='store_true');p.add_argument('--reuse-asr');p.add_argument('--output',required=True);p.add_argument('--language',default='zh');p.add_argument('--chunk-seconds',type=float,default=600);p.add_argument('--whisper',default='whisper-cli');p.add_argument('--threads',type=int,choices=range(1,17),default=6);p.add_argument('--resume',action='store_true')
    p=subs.add_parser('plan');p.add_argument('analysis');g=p.add_mutually_exclusive_group();g.add_argument('--decisions');g.add_argument('--enhancement-only',action='store_true');p.add_argument('--output',required=True)
    p=subs.add_parser('render');p.add_argument('video');p.add_argument('--plan',required=True);p.add_argument('--output',required=True);p.add_argument('--prepared-run');p.add_argument('--engine',choices=['ffmpeg','metal'],default='ffmpeg');p.add_argument('--codec',choices=['libx264','h264_videotoolbox'],default='libx264');p.add_argument('--bitrate-mbps',type=float,default=14);p.add_argument('--preview',type=float,default=0);p.add_argument('--resume',action='store_true');p.add_argument('--concatenate',action='store_true')
    p=subs.add_parser('verify');p.add_argument('output');p.add_argument('--decode',action='store_true')
    args=parser.parse_args()
    try:
        if args.command=='probe': print(json.dumps(probe(args.video),ensure_ascii=False,indent=2))
        elif args.command=='render':
            finite(args.bitrate_mbps,1,200);finite(args.preview,0,120);render(args)
        else: {'analyze':analyze,'transcribe':transcribe,'plan':plan_command,'verify':verify}[args.command](args)
    except (ValueError,KeyError,OSError,AssertionError) as e:
        parser.exit(2,f"error: {e}\n")


if __name__=='__main__':
    main()
