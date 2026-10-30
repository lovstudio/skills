#!/usr/bin/env python3
"""Gate a talking-head short script (script.json, schema talking-head-script/v1) before recording.

usage: check_script.py work/script.json [--root EPISODE_DIR] [--strict] [--rate 5.8] [--json qc/script-check.json]

Checks, all from references/style-grammar.md and references/script-format.md:
- structure: unique ids, known format/beat/layout, hook first, cta last, a setup beat within the first three lines;
- timing: estimated seconds per line at --rate chars/s (punctuation and spaces excluded, one Latin word = 1.5 chars),
  per-format total range, per-line ceiling (split long lines), per-shot ceiling for on-screen evidence;
- evidence: the hook carries b-roll, b-roll covers most of the film, every line with a number cites a fact id;
- voice: no AI-ish boilerplate and no borrowed signature catch phrases;
- packaging: emphasis words occur in the line, cover headline lines are short;
- --strict (before build): every b-roll src exists under --root.
Exit 1 on any ERROR; WARN lines are advisory.
"""
import argparse
import json
import re
import sys
from pathlib import Path

FORMATS = {"list": (25, 45), "tips": (35, 100), "review": (85, 135), "tier": (140, 240), "case": (85, 145)}
BEATS = {"hook", "setup", "point", "proof", "verdict", "cta"}
LAYOUTS = {"split", "face", "broll"}
MAX_LINE_SECONDS = 5.5
MAX_SHOT_SECONDS = 4.2
MIN_BROLL_SHARE = 0.6
# AI-ish boilerplate that reads as generated copy (style-grammar §3)
BANNED = ["在当今", "赋能", "让我们一起", "总而言之", "综上所述", "值得一提的是", "深度解析", "不仅如此",
          "毋庸置疑", "众所周知", "颠覆性", "史诗级", "家人们", "宝子们"]
# signature phrases of the reference creator; the film is the author's, not an impersonation (style-grammar §0)
BORROWED = ["我的天啊这里还有更多AI玩法", "这里还有更多AI玩法", "这个博主教会你更多AI技巧", "卡尔"]
PUNCT = re.compile(r"[\s，。！？、：；“”‘’（）《》【】,.!?:;\"'()\[\]<>…—\-~·]")
# digits (versions, prices, counts) and spelled-out measurements need a fact; structural counts such as 两个/三招 do not
NUM = re.compile(r"\d|%|[一二两三四五六七八九十百千万亿]+(秒|分钟|小时|天|周|倍|万|亿|块|元|美元|积分|token)")


def spoken_chars(text: str) -> float:
    """Chinese characters count 1, a Latin word or number run counts 1.5 (it takes longer to say)."""
    t = PUNCT.sub("", text)
    latin = re.findall(r"[A-Za-z0-9.+#]+", t)
    cjk = re.sub(r"[A-Za-z0-9.+#]+", "", t)
    return len(cjk) + 1.5 * len(latin)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("script")
    ap.add_argument("--root", help="episode directory that b-roll src paths are relative to (default: script's parent's parent)")
    ap.add_argument("--strict", action="store_true", help="also require every b-roll file to exist")
    ap.add_argument("--rate", type=float, default=5.8, help="planning speech rate, chars per second")
    ap.add_argument("--json", help="write the report as JSON")
    a = ap.parse_args()

    path = Path(a.script)
    s = json.loads(path.read_text())
    root = Path(a.root) if a.root else path.resolve().parent.parent
    errors, warns, rows = [], [], []
    E, W = errors.append, warns.append

    if s.get("schema") != "talking-head-script/v1":
        E("schema must be talking-head-script/v1")
    fmt = s.get("format")
    if fmt not in FORMATS:
        E(f"format must be one of {sorted(FORMATS)}")
    for k in ("topic", "title", "lines"):
        if not s.get(k):
            E(f"missing {k}")
    lines = s.get("lines") or []
    facts = {f.get("id") for f in s.get("facts") or []}
    for f in s.get("facts") or []:
        if not f.get("source"):
            E(f"fact {f.get('id')}: missing source")

    ids = [ln.get("id") for ln in lines]
    if len(ids) != len(set(ids)):
        E("line ids are not unique")

    total, broll_time, run_layout, run_len = 0.0, 0.0, None, 0
    for i, ln in enumerate(lines):
        lid, text = ln.get("id", f"#{i}"), ln.get("text", "")
        beat, layout = ln.get("beat"), ln.get("layout", "split")
        sec = spoken_chars(text) / a.rate
        total += sec
        brolls = ln.get("broll") or []
        if beat not in BEATS:
            E(f"{lid}: beat must be one of {sorted(BEATS)}")
        if layout not in LAYOUTS:
            E(f"{lid}: layout must be one of {sorted(LAYOUTS)}")
        if not text.strip():
            E(f"{lid}: empty text")
        if sec > MAX_LINE_SECONDS:
            E(f"{lid}: about {sec:.2f}s to say (> {MAX_LINE_SECONDS}s); split into two lines")
        if layout in ("split", "broll") and not brolls:
            E(f"{lid}: layout {layout} needs at least one b-roll")
        if layout == "face" and brolls:
            W(f"{lid}: layout face ignores its b-roll")
        if brolls and layout != "face":
            broll_time += sec
            per = sec / len(brolls)
            if per > MAX_SHOT_SECONDS:
                W(f"{lid}: one b-roll holds about {per:.1f}s; add a second image, a focus push or split the line")
        for b in brolls:
            if not b.get("src"):
                E(f"{lid}: b-roll without src")
            elif a.strict and not (root / b["src"]).exists():
                E(f"{lid}: b-roll missing on disk: {b['src']}")
            for box in (b.get("boxes") or []) + ([b["focus"]] if b.get("focus") else []):
                if len(box) != 4 or not all(0 <= v <= 1 for v in box) or box[0] + box[2] > 1.001 or box[1] + box[3] > 1.001:
                    E(f"{lid}: boxes/focus are normalized [x, y, w, h] inside 0..1, got {box}")
        for w in ln.get("emphasis") or []:
            if w not in text:
                E(f"{lid}: emphasis {w!r} is not in the line text")
        compact = PUNCT.sub("", text)
        for p in BANNED:
            if p in compact:
                E(f"{lid}: AI-ish boilerplate {p!r}")
        for p in BORROWED:
            if PUNCT.sub("", p) in compact:
                E(f"{lid}: borrowed signature phrase {p!r}; write the author's own line")
        if NUM.search(text) and not (set(ln.get("facts") or []) & facts):
            E(f"{lid}: has a number or count but cites no fact id from facts[]")
        for fid in ln.get("facts") or []:
            if fid not in facts:
                E(f"{lid}: cites unknown fact {fid}")
        run_len = run_len + 1 if layout == run_layout else 1
        run_layout = layout
        if run_len == 6:
            W(f"{lid}: six lines in a row with layout {layout}; switch layout every 2-4 lines")
        rows.append({"id": lid, "beat": beat, "layout": layout, "seconds": round(sec, 2), "brolls": len(brolls)})

    if lines:
        if lines[0].get("beat") != "hook":
            E("first line must be the hook")
        elif spoken_chars(lines[0].get("text", "")) > 20:
            W("hook is longer than 20 spoken chars (> ~3.5s); lead with the result")
        if not lines[0].get("broll"):
            E("the hook must show its evidence on screen (b-roll)")
        if lines[-1].get("beat") != "cta":
            E("last line must be the cta (a question or a call to action)")
        if not any(ln.get("beat") == "setup" for ln in lines[1:3]):
            W("no setup beat (question or pain point) in lines 2-3")
    if fmt in FORMATS:
        lo, hi = FORMATS[fmt]
        if total < lo * 0.85 or total > hi * 1.15:
            E(f"estimated {total:.0f}s is outside {fmt} range {lo}-{hi}s")
        elif total < lo or total > hi:
            W(f"estimated {total:.0f}s is at the edge of {fmt} range {lo}-{hi}s")
    share = broll_time / total if total else 0
    if share < MIN_BROLL_SHARE:
        W(f"b-roll covers {share:.0%} of the spoken time (< {MIN_BROLL_SHARE:.0%}); show more evidence")

    cover = s.get("cover") or {}
    head = cover.get("headline") or []
    if not 1 <= len(head) <= 3:
        E("cover.headline needs 1-3 lines")
    for h in head:
        n = spoken_chars(h)
        if n > 9:
            E(f"cover line {h!r} is {n:.0f} chars (> 9)")
        elif n > 7:
            W(f"cover line {h!r} is {n:.0f} chars (> 7)")
    if not cover.get("expression"):
        W("cover.expression is empty; the teleprompter asks the author for a cover pose")

    report = {"script": str(path), "format": fmt, "estimated_seconds": round(total, 1), "broll_share": round(share, 2),
              "lines": rows, "errors": errors, "warnings": warns, "ok": not errors}
    for r in rows:
        print(f"{r['id']:>5} {r['beat']:<8} {r['layout']:<6} {r['seconds']:>5.1f}s  broll={r['brolls']}")
    print(f"total ≈ {total:.1f}s  b-roll share {share:.0%}  format {fmt}")
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(report, ensure_ascii=False, indent=1))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
