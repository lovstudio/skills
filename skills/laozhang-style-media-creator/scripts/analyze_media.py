#!/usr/bin/env python3
"""Read-only whole-file measurements and timestamped visual/audio samples."""
import argparse
import concurrent.futures
import json
import re
import subprocess
from pathlib import Path


def run(cmd, log=None):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if log:
        Path(log).write_text(p.stderr)
    if p.returncode:
        raise RuntimeError(f'{cmd[0]} exit={p.returncode}: {p.stderr[-800:]}')
    return p


def analyze(row, out):
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
    source = Path(row.get('output_path') or row['path']).expanduser().resolve()
    nid = row.get('note_id') or source.stem
    if not re.fullmatch(r'[A-Za-z0-9-]+', nid):
        raise ValueError('sample id must be ASCII letters, digits or hyphens')
    folder = out / nid
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / 'metrics.json'
    if dest.exists():
        print(json.dumps({'sample': nid, 'status': 'reused'}), flush=True)
        return json.loads(dest.read_text())
    probe = json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(source)]).stdout)
    duration = float(probe['format']['duration'])
    video = next(s for s in probe['streams'] if s['codec_type']=='video')
    scene = run(['ffmpeg','-hide_banner','-i',str(source),'-an','-sn','-vf',
                 "scale=320:-2,select='gt(scene,0.23)',showinfo",'-fps_mode','vfr','-f','null','-'],folder/'scene.log')
    cuts = sorted(set(float(t) for t in re.findall(r'pts_time:([\d.]+)',scene.stderr)))
    bounds = [0]+cuts+[duration]
    lengths = [b-a for a,b in zip(bounds,bounds[1:]) if b>a]
    audio = run(['ffmpeg','-hide_banner','-i',str(source),'-vn','-sn','-af',
                 'silencedetect=noise=-35dB:d=0.2,loudnorm=I=-16:TP=-1:LRA=11:print_format=json',
                 '-f','null','-'],folder/'audio.log')
    loudness_match = re.findall(r'\{\s*"input_i".*?\}',audio.stderr,re.S)
    loudness = json.loads(loudness_match[-1]) if loudness_match else {}
    starts = [float(t) for t in re.findall(r'silence_start: ([\d.]+)',audio.stderr)]
    ends = [float(t) for t in re.findall(r'silence_end: ([\d.]+)',audio.stderr)]
    if len(starts)>len(ends):
        ends.append(duration)
    silences = [{'start':s,'end':e,'duration':round(e-s,4)} for s,e in zip(starts,ends) if e>=s]
    times = sorted(set(round(min(duration-.1,t),3) for t in [0.5,3,10,20]+[duration*p for p in [.1,.25,.4,.55,.7,.85,.95]]+[duration-1]))
    cap = cv2.VideoCapture(str(source))
    frames=[]
    sheet=Image.new('RGB',(720,1840),'#eeeeee')
    draw=ImageDraw.Draw(sheet)
    for idx,t in enumerate(times):
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000)
        ok,frame=cap.read()
        if not ok:
            raise RuntimeError(f'frame unavailable at {t}')
        frame_path=folder/f'frame-{t:08.3f}.jpg'
        cv2.imwrite(str(frame_path),frame,[cv2.IMWRITE_JPEG_QUALITY,92])
        image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
        thumb=image.copy();thumb.thumbnail((236,426))
        x=(idx%3)*240+(240-thumb.width)//2;y=(idx//3)*460+20
        sheet.paste(thumb,(x,y))
        draw.text(((idx%3)*240+6,(idx//3)*460+3),f'{nid[:6]}  {t:.2f}s',fill='black')
        frames.append({'time_seconds':t,'image':frame_path.name})
    cap.release()
    sheet.save(folder/'contact.jpg',quality=94)
    chunks=[{'source_start':s,'duration':15.0,'sample_start':i*15.0} for i,s in enumerate([0.0,duration*.4,duration*.8])]
    audio_filter=';'.join(f"[0:a]atrim=start={c['source_start']}:duration=15,asetpts=PTS-STARTPTS[a{i}]" for i,c in enumerate(chunks))
    audio_filter+=';[a0][a1][a2]concat=n=3:v=0:a=1[out]'
    run(['ffmpeg','-y','-v','error','-i',str(source),'-filter_complex',audio_filter,'-map','[out]',
         '-ar','16000','-ac','1','-c:a','libmp3lame','-b:a','48k',str(folder/'audio-sample.mp3')])
    result={'sample_id':nid,'rank':row.get('rank'),'title':row.get('title',source.stem),
            'duration_seconds':duration,'width':video['width'],'height':video['height'],
            'video_codec':video['codec_name'],'frame_rate':video['avg_frame_rate'],
            'scene_detection':{'method':'FFmpeg full decode, downscale 320px, scene threshold 0.23',
                               'limitation':'hard visual transitions, not exhaustive semantic or subtle jump cuts',
                               'cut_times_seconds':cuts,'cut_count':len(cuts),
                               'detected_segment_duration_percentiles':{str(p):round(float(np.percentile(lengths,p)),4) for p in [10,50,90]}},
            'audio':{'integrated_lufs':loudness.get('input_i'),'true_peak_dbtp':loudness.get('input_tp'),
                     'loudness_range_lu':loudness.get('input_lra'),'silence_threshold_db':-35,
                     'silences':silences,'silence_seconds':round(sum(s['duration'] for s in silences),4),
                     'limitation':'mixed-track silence is not a VAD or a music-separated speech pause metric'},
            'frames':frames,'audio_sample_segments':chunks}
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'sample':nid,'rank':row.get('rank'),'status':'measured','cuts':len(cuts),'frames':len(frames)},ensure_ascii=False),flush=True)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--workers',type=int,default=2)
    args=p.parse_args()
    data=json.loads(Path(args.manifest).read_text())
    rows=data['results'] if isinstance(data,dict) else data
    out=Path(args.output).expanduser().resolve();out.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(args.workers,2))) as pool:
        results=list(pool.map(lambda row:analyze(row,out),rows))
    (out/'measurements.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'measured','count':len(results),'output':str(out)}),flush=True)


if __name__=='__main__':
    main()
