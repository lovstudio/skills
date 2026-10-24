#!/usr/bin/env python3
"""Normalize Tingwu word timestamps without rewriting the source transcript."""
import argparse
import collections
import json
import re
from pathlib import Path


def normalize(path, output):
    data=json.loads(path.read_text())
    paragraphs=data['Transcription']['Paragraphs']
    sentences=[]
    for paragraph in paragraphs:
        buckets=collections.OrderedDict()
        for word in paragraph.get('Words',[]):
            buckets.setdefault(word.get('SentenceId',0),[]).append(word)
        for words in buckets.values():
            if not words: continue
            sentences.append({'start':words[0]['Start']/1000,'end':words[-1]['End']/1000,
                              'speaker':str(paragraph.get('SpeakerId','unknown')),
                              'text':''.join(w['Text'] for w in words)})
    sentences.sort(key=lambda s:(s['start'],s['end']))
    text='\n'.join(s['text'] for s in sentences)
    units=lambda s:len(re.findall(r'[\u3400-\u9fff]|[A-Za-z]+(?:\x27[A-Za-z]+)?|\d+(?:\.\d+)?',s))
    duration=data['Transcription']['AudioInfo']['Duration']/1000
    counts=collections.Counter()
    times=collections.Counter()
    for s in sentences:
        counts[s['speaker']]+=units(s['text']);times[s['speaker']]+=s['end']-s['start']
    dominant=counts.most_common(1)[0][0] if counts else 'unknown'
    gaps=[b['start']-a['end'] for a,b in zip(sentences,sentences[1:]) if b['start']>a['end']]
    lexical={word:len(re.findall(re.escape(word),text)) for word in ['本质','底层','其实','所以','但是','比如','你看','我们','你','不是','而是','为什么','认知','信念','感受']}
    output.mkdir(parents=True,exist_ok=True)
    result={'sample_id':path.stem,'provider':'tingwu','timing_precision':'ASR estimate, not manually aligned',
            'duration_seconds':duration,'unit_definition':'one Han character or one Latin word or numeric group',
            'spoken_units':units(text),'overall_units_per_min':round(units(text)/duration*60,3),
            'speaker_unit_counts':dict(counts),'speaker_sentence_seconds':dict(times),
            'dominant_speaker_id':dominant,'dominant_speaker_units_per_min':round(counts[dominant]/max(times[dominant],.001)*60,3),
            'sentence_count':len(sentences),'sentence_lengths_units':[units(s['text']) for s in sentences],
            'inter_sentence_gaps_seconds':gaps,'lexical_counts':lexical,'sentences':sentences}
    (output/(path.stem+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (output/(path.stem+'.txt')).write_text('\n'.join(f"[{s['start']:.3f}-{s['end']:.3f}][{s['speaker']}] {s['text']}" for s in sentences)+'\n')
    def stamp(t):
        ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
    (output/(path.stem+'.srt')).write_text('\n\n'.join(f"{i+1}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{s['text']}" for i,s in enumerate(sentences))+'\n')
    return {k:v for k,v in result.items() if k not in ('sentences','sentence_lengths_units','inter_sentence_gaps_seconds')}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    rows=[normalize(f,Path(a.output)) for f in sorted(Path(a.input).glob('*.json')) if not f.name.endswith('.job.json')]
    (Path(a.output)/'speech-metrics.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'normalized','samples':len(rows)},ensure_ascii=False))


if __name__=='__main__': main()
