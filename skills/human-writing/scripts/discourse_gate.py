#!/usr/bin/env python3
"""Locate editorial scaffolding and validate explicit, text-bound editorial review.

This is a review-coverage gate, not an AI detector or a semantic quality classifier.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = 'lov-human-writing/discourse-gate/v1'
REVIEW_SCHEMA = 'lov-human-writing/discourse-review/v1'
PATTERNS = {
    'classification_preamble': r'(?:是|分成|分为).{0,6}(?:[三四五两二2345]件事|[三四五两二2345]个(?:层次|层面|问题))',
    'announced_clarification': r'(?:先(?:把|来|说|厘清|澄清|讲清)|有必要(?:先)?(?:厘清|澄清|讲清)|需要(?:先)?(?:说清|讲清|厘清)).{0,45}(?:准确|清楚|一点|概念|地方|部分)|先(?:厘清|澄清|讲清)',
    'task_announcement': r'(?:这次|本文|接下来)(?:我们|我)?(?:要做的|要讨论的|将要解释的)|(?:值得|需要|必须)(?:留意|注意|重视)|不容忽视',
    'placeholder_handoff': r'负责(?:的是)?(?:另|这|那)一(?:段|层|部分|环)|各管一段',
    'broad_impact_question': r'(?:网关|路由|账号).{0,25}(?:会受什么影响|会受到什么影响)',
    'editorial_risk_instruction': r'风险.{0,12}(?:不能|不可|不应).{0,6}(?:写成|说成|承诺|表述为).{0,5}(?:零|没有|不存在)',
    'abstract_recap': r'解决(?:的)?(?:是|了).{0,12}(?:很具体的问题|具体的问题|真实痛点|实际痛点)|(?:这|其)(?:正是|就是).{0,18}(?:意义所在|价值所在)',
}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def units_of(text):
    """Keep paragraph text and source lines; exclude fenced code, metadata, images.

    Quotations remain reviewable but are not scanned as the author's own prose.
    """
    units, buf = [], []
    fence, front = None, False
    def flush():
        if not buf:
            return
        line, raw = buf[0][0], '\n'.join(s for _, s in buf)
        clean = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', raw).strip()
        if clean:
            index = len(units) + 1
            units.append({'id': f'u{index:03d}-{digest(raw.encode())[:10]}',
                          'line': line, 'kind': 'quote' if clean.startswith('>') else 'heading' if re.match(r'^#{1,6}\s', clean) else 'paragraph',
                          'text': raw})
        buf.clear()
    for n, line in enumerate(text.splitlines(), 1):
        if n == 1 and line.strip() == '---':
            front = True
            continue
        if front:
            if line.strip() in {'---', '...'}:
                front = False
            continue
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            flush()
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        if not line.strip():
            flush()
        elif re.match(r'^#{1,6}\s', line):
            flush(); buf.append((n, line)); flush()
        else:
            buf.append((n, line))
    flush()
    return units

def scan(data):
    units = units_of(data.decode('utf-8'))
    findings = []
    for unit in units:
        if unit['kind'] == 'quote':
            continue
        visible = re.sub(r'`[^`]*`|https?://\S+', '', unit['text'])
        visible = re.sub(r'[*_]', '', visible)
        for family, pattern in PATTERNS.items():
            for m in re.finditer(pattern, visible):
                findings.append({'unit_id': unit['id'], 'family': family, 'evidence': m.group(0)})
    return {'schema': SCHEMA, 'input_sha256': digest(data), 'status': 'needs_review',
            'scope': 'review_coverage_and_text_integrity',
            'limitations': '词面扫描不穷尽语义；accepted 只证明审读记录完整且对应当前文本，不判定作者身份或保证文风质量。',
            'units': units, 'findings': findings}

def validate_review(report, review):
    errors = []
    if not isinstance(review, dict):
        return ['review must be an object']
    if review.get('schema') != REVIEW_SCHEMA:
        errors.append('review schema mismatch')
    if review.get('input_sha256') != report['input_sha256']:
        errors.append('review is stale: input_sha256 mismatch')
    if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip():
        errors.append('reviewer must identify the actual reviewer')
    decisions = review.get('units')
    if not isinstance(decisions, list):
        return errors + ['review units must be a list']
    expected = {u['id'] for u in report['units']}
    seen = set()
    for d in decisions:
        if not isinstance(d, dict):
            errors.append('review unit must be an object'); continue
        uid = d.get('id')
        if not isinstance(uid, str):
            errors.append('unit id must be a string'); continue
        if uid not in expected or uid in seen:
            errors.append(f'unknown or duplicate review unit: {uid}')
        seen.add(uid)
        if d.get('decision') not in {'accept', 'protected'}:
            errors.append(f'unresolved review unit: {uid}')
        if not isinstance(d.get('reason'), str) or not d['reason'].strip():
            errors.append(f'missing contextual reason: {uid}')
    if expected - seen:
        errors.append('unreviewed units: ' + ', '.join(sorted(expected - seen)))
    if not expected:
        errors.append('no prose units found')
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report = scan(args.input.read_bytes())
        if args.review:
            review = json.loads(args.review.read_text())
            report['errors'] = validate_review(report, review)
            report['review'] = review
            if not report['errors']:
                report['status'] = 'accepted'
        else:
            report['errors'] = ['semantic review required, including units without pattern matches']
    except (OSError, ValueError) as error:
        report = {'schema': SCHEMA, 'status': 'needs_review', 'errors': [str(error)]}
    output = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(output)
    else:
        print(output, end='')
    return 0 if report['status'] == 'accepted' else 1

if __name__ == '__main__':
    raise SystemExit(main())
