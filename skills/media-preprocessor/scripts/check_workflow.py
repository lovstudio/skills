#!/usr/bin/env python3
"""Exercise editorial guards, rendering, resume and integrity on synthetic media."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

CLI=Path(__file__).with_name('media_preprocessor.py')


def call(*args,ok=True):
    p=subprocess.run([sys.executable,str(CLI),*map(str,args)],capture_output=True,text=True)
    assert (p.returncode==0)==ok,p.stdout+p.stderr
    return p.stdout


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metal',action='store_true',help='Also exercise the optional macOS backend')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='preprocessor-') as d:
        root=Path(d);video=root/'课堂 原片.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=25:duration=4',
                        '-f','lavfi','-i','sine=frequency=440:duration=4','-c:v','libx264','-c:a','aac',str(video)],check=True)
        call('analyze',video,'--interval',1,'--output',root/'analysis')
        call('analyze',video,'--interval',1,'--output',root/'analysis','--resume')
        call('analyze',video,'--interval',2,'--output',root/'analysis','--resume',ok=False)
        call('analyze',video,'--interval','nan','--output',root/'bad',ok=False)
        fake=root/'fake-whisper'
        fake.write_text('#!/usr/bin/env python3\nimport sys,json\nfrom pathlib import Path\na=sys.argv\np=Path(a[a.index("-of")+1]+".json")\np.write_text(json.dumps({"transcription":[{"text":"synthetic speech","offsets":{"from":0,"to":4000}}]}))\n')
        fake.chmod(0o755)
        model=root/'test-model.bin';model.write_bytes(b'synthetic model fixture')
        asr_args=('transcribe',root/'analysis/audio-16k.wav','--model',model,'--whisper',fake,'--output',root/'asr')
        call(*asr_args)
        before=(root/'asr/chunk-0001.json').stat().st_mtime_ns
        call(*asr_args,'--resume')
        assert before==(root/'asr/chunk-0001.json').stat().st_mtime_ns
        assert json.loads((root/'asr/transcript.json').read_text())['status']=='complete'
        call('transcribe',root/'analysis/audio-16k.wav','--model',model,'--whisper',fake,'--output',root/'asr-reuse','--reuse-asr',root/'asr')
        assert json.loads((root/'asr-reuse/chunk-0001.done.json').read_text())['provenance']['reused_run']==str((root/'asr').resolve())
        model.write_bytes(b'changed model fixture')
        call(*asr_args,'--resume',ok=False)
        call('plan',root/'analysis/analysis.json','--output',root/'draft.json')
        call('render',video,'--plan',root/'draft.json','--output',root/'blocked',ok=False)
        call('plan',root/'analysis/analysis.json','--enhancement-only','--output',root/'enhance.json')
        call('render',video,'--plan',root/'enhance.json','--output',root/'enhanced')
        call('verify',root/'enhanced','--decode')
        from creator_handoff import export_handoff
        enhanced_handoff=export_handoff(root/'enhanced',root/'enhanced-handoff.json',decode=True)
        assert enhanced_handoff['editorial_status']=='full-recording-content-review-required'
        p=json.loads((root/'draft.json').read_text());p['basis']='semantic-reviewed';p['grade']={'mode':'neutral'}
        base=p['segments'][0]
        p['segments']=[dict(base,id='keep-01',start=0,end=1,decision='keep',title='<script>fixture</script>'),
                       dict(base,id='drop-01',start=1,end=2,decision='drop',contains_unique_content=False,
                            review=dict.fromkeys(['content_checked','visual_checked','boundary_checked'],True)),
                       dict(base,id='review-01',start=2,end=4,decision='review')]
        def save(obj): (root/'plan.json').write_text(json.dumps(obj))
        save(p)
        call('plan',root/'analysis/analysis.json','--decisions',root/'plan.json','--output',root/'accepted.json')
        for change in ['gap','unreviewed','unique','source','nan','duplicate','path','basis','enhancement-drop']:
            bad=copy.deepcopy(p)
            if change=='gap':bad['segments'][1]['start']=1.2
            elif change=='unreviewed':bad['segments'][1]['review']['content_checked']=False
            elif change=='unique':bad['segments'][1]['contains_unique_content']=True
            elif change=='source':bad['source']['edge_sha256']='wrong'
            elif change=='nan':bad['segments'][0]['end']=float('nan')
            elif change=='duplicate':bad['segments'][1]['id']=bad['segments'][0]['id']
            elif change=='path':bad['segments'][0]['id']='../escape'
            elif change=='basis':bad['basis']='bypass'
            elif change=='enhancement-drop':bad['basis']='enhancement-only'
            save(bad);call('plan',root/'analysis/analysis.json','--decisions',root/'plan.json','--output',root/'rejected.json',ok=False)
        save(p)
        call('render',video,'--plan',root/'plan.json','--prepared-run',root/'enhanced','--output',root/'grade-mismatch',ok=False)
        prepared_plan=copy.deepcopy(p);prepared_plan['grade']={'mode':'bright-documentary'};save(prepared_plan)
        call('render',video,'--plan',root/'plan.json','--prepared-run',root/'enhanced','--output',root/'reused-master')
        call('verify',root/'reused-master','--decode')
        save(p)
        call('render',video,'--plan',root/'plan.json','--output',root/'render','--codec','libx264','--concatenate')
        call('verify',root/'render','--decode')
        manifest=json.loads((root/'render/manifest.json').read_text())
        handoff=export_handoff(root/'render',root/'creator-handoff.json',decode=True)
        assert [(f['source_start'],f['source_end'],f['local_start']) for f in handoff['files']]==[(0,1,0),(2,4,0)]
        assert handoff['verification']['full_decode'] is True
        assert manifest['kept_duration']==3 and manifest['dropped_duration']==1 and manifest['review_duration']==2
        for bad_manifest in [dict(manifest,status='rendering'),dict(manifest,files=manifest['files'][:1])]:
            (root/'render/manifest.json').write_text(json.dumps(bad_manifest))
            call('verify',root/'render',ok=False)
        (root/'render/manifest.json').write_text(json.dumps(manifest))
        assert '<script>fixture' not in (root/'render/gallery.html').read_text()
        call('render',video,'--plan',root/'plan.json','--output',root/'render','--codec','libx264','--concatenate','--resume')
        assert json.loads((root/'render/manifest.json').read_text())['assembled']==manifest['assembled']
        if args.metal:
            call('render',video,'--plan',root/'plan.json','--output',root/'metal','--engine','metal','--codec','h264_videotoolbox','--concatenate')
            call('verify',root/'metal','--decode')
        target=root/'render'/manifest['files'][0]['file'];target.write_bytes(b'corrupt')
        call('verify',root/'render',ok=False)
        assert video.is_file()
    print('PASSED: source binding, full coverage, drop guards, review retention, exact durations, A/V tracks, decode, resume, escaping and corruption detection')


if __name__=='__main__':main()
