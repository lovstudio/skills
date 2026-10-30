#!/usr/bin/env python3
"""Export a checked script.json as a recording kit: teleprompter.html, script.md and shotlist.md.

usage: teleprompter.py work/script.json --out deliverables [--root EPISODE_DIR] [--rate 5.8]

teleprompter.html is self-contained (open it on the laptop above the phone, or on a second phone):
line-by-line auto advance at the planning rate, Space start/pause, ←/→ previous/next line, ↑/↓ speed,
M mirror for a teleprompter glass, F fullscreen. Its first card is the recording checklist and the
cover pose. script.md is the reviewable script with beats and shots; shotlist.md lists every on-screen
asset with its status on disk (exists / missing) and the capture note, so the evidence can be gathered
before or while the author records.
"""
import argparse
import html
import json
import re
from pathlib import Path

PUNCT = re.compile(r"[\s，。！？、：；“”‘’（）《》【】,.!?:;\"'()\[\]<>…—\-~·]")
BEAT_ZH = {"hook": "钩子", "setup": "悬念", "point": "要点", "proof": "证据", "verdict": "判断", "cta": "收尾"}
LAYOUT_ZH = {"split": "上素材·下出镜", "face": "全脸", "broll": "全素材"}


def spoken_chars(text):
    t = PUNCT.sub("", text)
    latin = re.findall(r"[A-Za-z0-9.+#]+", t)
    return len(re.sub(r"[A-Za-z0-9.+#]+", "", t)) + 1.5 * len(latin)


def mark(text, words):
    out = html.escape(text)
    for w in sorted(set(words or []), key=len, reverse=True):
        out = out.replace(html.escape(w), f"<b>{html.escape(w)}</b>")
    return out


PAGE = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>提词器 · %(title)s</title>
<style>
:root{--bg:#0b0b0b;--fg:#f5f5f5;--dim:#8a8a8a;--hi:#ffc21a}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--fg);font-family:"PingFang SC","Noto Sans SC",sans-serif}
#stage{height:100vh;overflow:hidden;position:relative}
#track{position:absolute;left:0;right:0;transition:transform .35s ease}
.card{padding:4vh 6vw;opacity:.28;transition:opacity .2s}
.card.on{opacity:1}
.meta{font-size:clamp(14px,1.6vw,20px);color:var(--dim);margin-bottom:.6em;letter-spacing:.04em}
.text{font-size:clamp(34px,5.4vw,76px);font-weight:800;line-height:1.35}
.text b{color:var(--hi)}
.check{font-size:clamp(18px,2.2vw,30px);line-height:1.7}
.check li{margin:.2em 0}
#bar{position:fixed;left:0;right:0;bottom:0;padding:10px 6vw;font-size:14px;color:var(--dim);background:#000c;display:flex;gap:2em}
#prog{position:fixed;left:0;top:0;height:4px;background:var(--hi);width:0}
body.mirror #stage{transform:scaleX(-1)}
</style></head><body>
<div id="prog"></div><div id="stage"><div id="track">%(cards)s</div></div>
<div id="bar"><span id="pos"></span><span id="spd"></span><span>空格 开始/暂停 · ←→ 上/下一句 · ↑↓ 语速 · M 镜像 · F 全屏</span></div>
<script>
const durs=%(durs)s;let i=0,speed=1,playing=false,timer=null,started=0;
const cards=[...document.querySelectorAll('.card')],track=document.getElementById('track');
function show(){cards.forEach((c,k)=>c.classList.toggle('on',k===i));
 const c=cards[i];track.style.transform=`translateY(${innerHeight*0.38-c.offsetTop}px)`;
 document.getElementById('pos').textContent=`${i}/${cards.length-1}`;
 document.getElementById('spd').textContent=`语速 ×${speed.toFixed(2)}`;}
function tick(){clearTimeout(timer);if(!playing||i>=cards.length-1){playing=false;return}
 const d=durs[i]*1000/speed;started=performance.now();
 timer=setTimeout(()=>{i++;show();tick()},d);}
setInterval(()=>{const p=document.getElementById('prog');if(!playing){return}
 const d=durs[i]*1000/speed;p.style.width=Math.min(100,(performance.now()-started)/d*100)+'%%'},50);
addEventListener('keydown',e=>{
 if(e.code==='Space'){e.preventDefault();playing=!playing;if(playing&&i===0){i=1;show()}tick()}
 if(e.code==='ArrowRight'){i=Math.min(cards.length-1,i+1);show();tick()}
 if(e.code==='ArrowLeft'){i=Math.max(0,i-1);show();tick()}
 if(e.code==='ArrowUp'){speed=Math.min(1.6,speed+0.05);show()}
 if(e.code==='ArrowDown'){speed=Math.max(0.6,speed-0.05);show()}
 if(e.key==='m'||e.key==='M')document.body.classList.toggle('mirror');
 if(e.key==='f'||e.key==='F')document.documentElement.requestFullscreen?.();});
addEventListener('resize',show);show();
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("script")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--root", help="episode directory for b-roll paths (default: script's parent's parent)")
    ap.add_argument("--rate", type=float, default=5.8)
    a = ap.parse_args()
    sp = Path(a.script)
    s = json.loads(sp.read_text())
    root = Path(a.root) if a.root else sp.resolve().parent.parent
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lines = s["lines"]
    cover = s.get("cover") or {}

    checklist = [
        "手机竖拍 9:16，1080p 或 4K，30 fps；镜头与眼睛平齐，胸口以上入画，头顶留一拳",
        "领夹麦或靠近嘴的麦克风；关空调和风扇；背景保留有生活感的实景",
        "光从脸的正前方或斜前方来，别背光",
        f"开机先拍 3 秒封面表情：{cover.get('expression') or '夸张一点的惊讶，手指向画面上方'}",
        "一条录完全部台词；念错就停半拍，从这一句开头整句重读，不用喊卡、不用重开机",
        "句与句之间停半拍；语气比平时聊天再快一点、再兴奋一点",
    ]
    cards = ['<div class="card on"><div class="meta">录制清单 · 按空格开始</div><ol class="check">'
             + "".join(f"<li>{html.escape(c)}</li>" for c in checklist) + "</ol></div>"]
    durs = [3.0]
    for ln in lines:
        sec = max(1.2, spoken_chars(ln["text"]) / a.rate + 0.45)
        meta = f"{ln['id']} · {BEAT_ZH.get(ln.get('beat'), ln.get('beat'))} · {LAYOUT_ZH.get(ln.get('layout', 'split'))}"
        cards.append(f'<div class="card"><div class="meta">{html.escape(meta)}</div>'
                     f'<div class="text">{mark(ln["text"], ln.get("emphasis"))}</div></div>')
        durs.append(round(sec, 2))
    cards.append('<div class="card"><div class="meta">结束</div><div class="text">停 2 秒再关机</div></div>')
    durs.append(2.0)
    (out / "teleprompter.html").write_text(PAGE % {"title": html.escape(s.get("title", "")), "cards": "\n".join(cards),
                                                   "durs": json.dumps(durs)})

    total = sum(spoken_chars(ln["text"]) / a.rate for ln in lines)  # speech only, same estimate as check_script
    md = [f"# {s.get('title', '')}", "", f"- 主题：{s.get('topic', '')}", f"- 片型：{s.get('format')}",
          f"- 预估时长：约 {total:.0f} 秒（{a.rate} 字/秒）",
          f"- 封面：{' / '.join(cover.get('headline') or [])}（标签：{cover.get('tag') or '无'}）",
          f"- 封面表情：{cover.get('expression') or '未定'}", "", "| # | 节拍 | 台词 | 画面 |", "| --- | --- | --- | --- |"]
    shots = ["# 上屏素材清单", "", "| 句 | 文件 | 状态 | 怎么拿 |", "| --- | --- | --- | --- |"]
    for ln in lines:
        brolls = ln.get("broll") or []
        view = LAYOUT_ZH.get(ln.get("layout", "split"), "")
        if ln.get("callout"):
            view += f"，大标注「{ln['callout']}」"
        if brolls:
            view += "：" + "、".join(Path(b["src"]).name + (f"（{b['label']}）" if b.get("label") else "") for b in brolls)
        md.append(f"| {ln['id']} | {BEAT_ZH.get(ln.get('beat'), '')} | {ln['text']} | {view} |")
        for b in brolls:
            cap = b.get("capture") or {}
            how = cap.get("url") or cap.get("note") or cap.get("prompt") or "—"
            ok = "已有" if (root / b["src"]).exists() else "缺"
            shots.append(f"| {ln['id']} | `{b['src']}` | {ok} | {how} |")
    md += ["", f"片尾：{(s.get('end') or {}).get('line', '')}"]
    facts = s.get("facts") or []
    if facts:
        md += ["", "## 事实与出处", ""] + [f"- {f['id']}：{f['claim']}（{f['source']}，核对 {f.get('checked', '?')}）" for f in facts]
    (out / "script.md").write_text("\n".join(md) + "\n")
    (out / "shotlist.md").write_text("\n".join(shots) + "\n")
    missing = sum(1 for row in shots[4:] if "| 缺 |" in row)
    print(json.dumps({"teleprompter": str(out / "teleprompter.html"), "script_md": str(out / "script.md"),
                      "shotlist": str(out / "shotlist.md"), "lines": len(lines), "estimated_seconds": round(total, 1),
                      "broll_missing": missing}, ensure_ascii=False))


if __name__ == "__main__":
    main()
