#!/usr/bin/env python3
"""集成 modern-screenshot 到任意 HTML，实现一键导出主体内容为 PNG。

无第三方依赖。子命令：
  integrate <html>   给 HTML 注入「导出图片」按钮与截图逻辑
  verify <html>      用 headless Chrome 端到端验证截图尺寸一致
  self-test          用内置最小示例跑完整 integrate + verify
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

LIB_NAME = "modern-screenshot.js"
LIB_VERSION = "4.5.1"
DEFAULT_WIDTH = 760
DEFAULT_SCALE = 2

# --------------------------------------------------------------------------
# 注入片段
# --------------------------------------------------------------------------

# 颜色用 var(--x, fallback)：目标页定义了设计令牌则自动适配主题，否则回退中性色。
SHOT_CSS = """
  /* auto-injected: modern-screenshot export */
  #capture { {width_decl}margin: 0 auto; }
  .shot-bar { position: fixed; right: 20px; bottom: 20px; z-index: 9999; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
  #shot { display: inline-flex; align-items: center; gap: 7px; padding: 10px 16px; border: 1px solid var(--line, rgba(0,0,0,.14)); border-radius: 999px; background: var(--surface, #fff); color: var(--ink, #1c1a18); font-size: 13px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 16px rgba(0,0,0,.10); transition: border-color .15s, transform .05s; font-family: inherit; line-height: 1; }
  #shot:hover { border-color: var(--accent, #CC785C); }
  #shot:active { transform: scale(.97); }
  #shot.busy { opacity: .55; pointer-events: none; }
  #shot .ico { width: 15px; height: 15px; flex: 0 0 auto; }
  .shot-err { display: none; max-width: 340px; align-items: flex-start; gap: 8px; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--line, rgba(0,0,0,.14)); background: var(--surface, #fff); font-size: 12px; color: var(--ink-soft, #6e6660); line-height: 1.5; box-shadow: 0 4px 16px rgba(0,0,0,.10); }
  .shot-err.show { display: flex; }
  .shot-err code { display: block; margin-top: 4px; font-size: 11px; color: var(--ink-faint, #9a918a); word-break: break-all; user-select: all; }
  .shot-err button { flex: 0 0 auto; padding: 2px 9px; font-size: 11px; border: 1px solid var(--line, rgba(0,0,0,.14)); border-radius: 6px; background: var(--surface-2, #f0ece5); color: var(--ink, #1c1a18); cursor: pointer; font-family: inherit; }
"""

SHOT_BAR = """<div class="shot-bar">
  <button id="shot" type="button" title="导出 PNG 图片">
    <svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
    <span>导出图片</span>
  </button>
  <div class="shot-err" id="shot-err"><span id="shot-err-msg"></span><button id="shot-err-copy" type="button">复制</button></div>
</div>
"""

SHOT_JS = """
(function () {
  var btn = document.getElementById('shot');
  var label = btn.querySelector('span');
  var errBox = document.getElementById('shot-err');
  var errMsg = document.getElementById('shot-err-msg');
  var errCopy = document.getElementById('shot-err-copy');
  var lastErr = '';
  function showErr(msg, detail) { lastErr = detail || msg; errMsg.textContent = msg; errBox.classList.add('show'); }
  function hideErr() { errBox.classList.remove('show'); }
  errCopy.addEventListener('click', function () {
    if (navigator.clipboard) { navigator.clipboard.writeText(lastErr).catch(function () {}); }
    else { window.prompt('复制以下错误信息：', lastErr); }
  });
  btn.addEventListener('click', function () {
    if (typeof modernScreenshot === 'undefined') { showErr('截图库未加载（modern-screenshot 内联失败）', 'modernScreenshot is undefined'); return; }
    hideErr();
    var node = document.getElementById('capture');
    var width = node.scrollWidth, height = node.scrollHeight, scale = {scale};
    var bg = getComputedStyle(document.body).backgroundColor;
    btn.classList.add('busy');
    var old = label.textContent;
    label.textContent = '生成中…';
    modernScreenshot.domToPng(node, { width: width, height: height, scale: scale, backgroundColor: bg })
      .then(function (dataUrl) {
        var a = document.createElement('a');
        a.download = {title_json};
        a.href = dataUrl;
        a.click();
        label.textContent = '已保存';
        window.setTimeout(function () { label.textContent = old; }, 1400);
      })
      .catch(function (e) {
        var m = e && e.message ? e.message : String(e);
        showErr('截图失败：' + m, JSON.stringify(e && e.stack ? e.stack : m));
      })
      .finally(function () { btn.classList.remove('busy'); });
  });
})();
"""


# --------------------------------------------------------------------------
# HTML 结构工具（仅用 stdlib，支持简单 CSS 选择器与嵌套闭合）
# --------------------------------------------------------------------------

def _open_pat(tag: str, ident: Optional[str], is_id: bool) -> str:
    if is_id:
        return r'<[a-zA-Z][^>]*\bid="' + re.escape(ident) + r'"[^>]*>'
    if ident is not None:
        return r'<[a-zA-Z][^>]*\bclass="[^"]*?\b' + re.escape(ident) + r'\b[^"]*"[^>]*>'
    return r'<' + tag + r'\b[^>]*>'


def _tag_of(open_html: str) -> str:
    m = re.match(r'<([a-zA-Z][a-zA-Z0-9]*)', open_html)
    return m.group(1) if m else "div"


def find_element_range(html: str, open_pat: str) -> Tuple[Optional[int], Optional[int]]:
    """返回匹配 open_pat 的元素 [start, end)，支持同名标签嵌套。"""
    mo = re.search(open_pat, html, re.I)
    if not mo:
        return None, None
    tag = _tag_of(mo.group(0))
    open_re = re.compile(r'<' + tag + r'\b[^>]*>', re.I)
    close_re = re.compile(r'</' + tag + r'\s*>', re.I)
    depth = 0
    i = mo.start()
    while i < len(html):
        no = open_re.search(html, i)
        nc = close_re.search(html, i)
        if nc is None:
            return None, None
        if no is not None and no.start() < nc.start():
            depth += 1
            i = no.end()
        else:
            depth -= 1
            i = nc.end()
            if depth == 0:
                return mo.start(), i
    return None, None


def parse_selector(sel: str) -> Tuple[Optional[str], Optional[str], bool]:
    """返回 (tag, ident, is_id)。tag 为 None 表示按 id/class 定位。"""
    sel = sel.strip()
    if sel.startswith("#"):
        return None, sel[1:], True
    if sel.startswith("."):
        return None, sel[1:], False
    if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9]*", sel):
        return sel, None, False
    raise ValueError(f"暂不支持该选择器（仅支持 tag / #id / .class）：{sel}")


def resolve_target(html: str, selector: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """确定要截图的主体内容范围。"""
    if selector:
        tag, ident, is_id = parse_selector(selector)
        return find_element_range(html, _open_pat(tag or "div", ident, is_id))
    # 自动：<main>（及其前置顶层 <header>）→ <article> → <body> 内容
    m = find_element_range(html, r'<main\b[^>]*>')
    if m[0] is not None:
        h = find_element_range(html, r'<header\b[^>]*>')
        if h[0] is not None and h[1] is not None and h[1] <= m[0]:
            if not html[h[1]:m[0]].strip():
                return h[0], m[1]
        return m
    a = find_element_range(html, r'<article\b[^>]*>')
    if a[0] is not None:
        return a
    bo = re.search(r'<body\b[^>]*>', html, re.I)
    bc = re.search(r'</body\s*>', html, re.I)
    if bo and bc:
        return bo.end(), bc.start()
    return None, None


def infer_title(html: str, src_name: str) -> str:
    m = re.search(r'<title[^>]*>([^<]*)</title>', html, re.I)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return Path(src_name).stem or "screenshot"


def inject_css(html: str, css: str) -> str:
    if '</style>' in html:
        return html.replace('</style>', css + '</style>', 1)
    if '</head>' in html:
        return html.replace('</head>', '<style>' + css + '</style></head>', 1)
    return '<style>' + css + '</style>' + html


def inject_script(html: str, script: str) -> str:
    if '</body>' in html:
        return html.replace('</body>', script + '</body>', 1)
    return html + script


# --------------------------------------------------------------------------
# 注入主逻辑
# --------------------------------------------------------------------------

def build_injected(html: str, *, selector: Optional[str], width: int,
                   scale: int, title: str) -> str:
    lib = load_lib()

    start, end = resolve_target(html, selector)
    if start is None or end is None:
        raise ValueError(f"未找到可截图的目标元素（selector={selector or 'auto'}，可尝试 --selector main 或 --selector body）")

    target = html[start:end]
    width_decl = f"width: {width}px; " if width > 0 else ""
    css = SHOT_CSS.replace('{width_decl}', width_decl)
    js = SHOT_JS.replace('{scale}', str(scale)).replace(
        '{title_json}', json.dumps(title, ensure_ascii=False))

    # 1) 用 shot-bar + #capture 包裹目标
    html = (
        html[:start]
        + SHOT_BAR
        + '\n<div id="capture">\n'
        + target
        + '\n</div>\n'
        + html[end:]
    )
    # 2) 注入 CSS
    html = inject_css(html, css)
    # 3) 注入库 + 截图逻辑（在 </body> 前）
    script = (
        '<script>/*! modern-screenshot v%s | MIT | inline */\n%s\n</script>\n'
        % (LIB_VERSION, lib)
    ) + '<script>\n' + js + '\n</script>\n'
    html = inject_script(html, script)
    return html


# --------------------------------------------------------------------------
# 验证（headless Chrome 端到端）
# --------------------------------------------------------------------------

def _find_chrome(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    for cand in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "google-chrome", "chromium", "chromium-browser", "chrome",
    ):
        if Path(cand).exists() or not cand.startswith("/"):
            return cand
    raise SystemExit("未找到 Chrome/Chromium，请用 --chrome 指定可执行文件路径")


def build_test_page(html: str, scale: int) -> str:
    lib = load_lib()
    style = ""
    s0 = html.find('<style')
    if s0 != -1:
        s1 = html.find('</style>', s0)
        if s1 != -1:
            style = html[s0:s1 + len('</style>')]
    c0, c1 = find_element_range(html, r'<div\b[^>]*\bid="capture"[^>]*>')
    if c0 is None or c1 is None:
        raise SystemExit("未找到 #capture，请先运行 integrate")
    capture = html[c0:c1]
    return (
        '<title>verify</title>\n' + style + '\n' + capture +
        '\n<pre id="result">pending</pre>\n' +
        '<script>/*! modern-screenshot */\n' + lib + '\n</script>\n' +
        '<script>\nwindow.addEventListener("load", function () {\n'
        '  var node = document.getElementById("capture");\n'
        '  var width = node.scrollWidth, height = node.scrollHeight, scale = %d;\n'
        '  modernScreenshot.domToPng(node, { width: width, height: height, scale: scale, '
        'backgroundColor: getComputedStyle(document.body).backgroundColor })\n'
        '    .then(function (u) {\n'
        '      var b = atob(u.split(",")[1]);\n'
        '      var w = ((b.charCodeAt(16)<<24)|(b.charCodeAt(17)<<16)|(b.charCodeAt(18)<<8)|b.charCodeAt(19))>>>0;\n'
        '      var h = ((b.charCodeAt(20)<<24)|(b.charCodeAt(21)<<16)|(b.charCodeAt(22)<<8)|b.charCodeAt(23))>>>0;\n'
        '      document.getElementById("result").textContent = "OK out=" + w + "x" + h '
        '+ " node=" + width + "x" + height + " expect=" + (width*scale) + "x" + (height*scale);\n'
        '    })\n'
        '    .catch(function (e) { document.getElementById("result").textContent = '
        '"FAIL " + (e && e.message ? e.message : e); });\n'
        '});\n</script>\n' % scale
    )


def verify(html_path: str, scale: int, chrome: Optional[str]) -> dict:
    html = Path(html_path).read_text(encoding="utf-8")
    test = build_test_page(html, scale)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    try:
        tmp.write(test)
        tmp.close()
        cmd = [_find_chrome(chrome), "--headless=new", "--disable-gpu", "--no-sandbox",
               "--window-size=1280,900", "--virtual-time-budget=8000", "--dump-dom",
               "file://" + tmp.name]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=25).stdout
        except subprocess.TimeoutExpired as e:
            # headless Chrome 可能因 pending 请求不退出，但 --dump-dom 已把结果写入 stdout
            out = (e.stdout or "") + (e.stderr or "")
    finally:
        Path(tmp.name).unlink(missing_ok=True)
    m = re.search(r'<pre id="result">([^<]*)</pre>', out)
    text = m.group(1) if m else f"未解析到结果（Chrome 输出 {len(out)} 字节）"
    ok = text.startswith("OK")
    return {"ok": ok, "result": text}


# --------------------------------------------------------------------------
# 自测
# --------------------------------------------------------------------------

SELF_TEST_HTML = """<!doctype html>
<title>截图自测</title>
<style>
  body { margin: 0; background: #F7F5F1; color: #1C1A18; font-family: -apple-system, "PingFang SC", sans-serif; }
  .wrap { max-width: 760px; margin: 0 auto; padding: 24px 20px; }
  h1 { font-size: 24px; }
  .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  .cell { background: #fff; border: 1px solid #E6E0D7; border-radius: 12px; padding: 12px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: right; padding: 8px 12px; border-bottom: 1px solid #E6E0D7; white-space: nowrap; }
  th:first-child, td:first-child { text-align: left; }
</style>
<header class="wrap">
  <h1>截图自测页</h1>
  <div class="grid">
    <div class="cell">A</div><div class="cell">B</div><div class="cell">C</div><div class="cell">D</div>
  </div>
</header>
<main class="wrap">
  <table>
    <thead><tr><th>名称</th><th>数量</th><th>单价</th></tr></thead>
    <tbody>
      <tr><td>甲</td><td>3</td><td>¥12.00</td></tr>
      <tr><td>乙</td><td>17</td><td>¥2.06</td></tr>
    </tbody>
  </table>
</main>
"""


def self_test(scale: int, chrome: Optional[str]) -> dict:
    injected = build_injected(SELF_TEST_HTML, selector=None, width=DEFAULT_WIDTH,
                              scale=scale, title="screenshot-self-test.png")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    try:
        tmp.write(injected)
        tmp.close()
        return verify(tmp.name, scale, chrome)
    finally:
        Path(tmp.name).unlink(missing_ok=True)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def load_lib() -> str:
    p = skill_dir() / "assets" / LIB_NAME
    if not p.exists():
        raise SystemExit(f"缺少 {LIB_NAME}，请确认 assets/ 目录完整")
    return p.read_text(encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("integrate", help="注入截图能力")
    i.add_argument("html", help="目标 HTML 文件路径")
    i.add_argument("--selector", help="主体内容选择器（tag / #id / .class；默认自动探测 main+header）")
    i.add_argument("--width", type=int, default=DEFAULT_WIDTH,
                   help=f"截图容器固定宽度 px（默认 {DEFAULT_WIDTH}；0 表示跟随内容宽度）")
    i.add_argument("--scale", type=int, default=DEFAULT_SCALE,
                   help=f"输出缩放倍数（默认 {DEFAULT_SCALE}，适合网络传播）")
    i.add_argument("--title", help="下载文件名（默认取 <title> 或源文件名）")
    i.add_argument("--out", help="输出文件路径（默认覆盖源文件）")
    i.add_argument("--in-place", action="store_true", help="就地覆盖源文件（等价于默认行为）")

    v = sub.add_parser("verify", help="端到端验证")
    v.add_argument("html", help="已注入截图能力的 HTML 文件")
    v.add_argument("--scale", type=int, default=DEFAULT_SCALE, help="与 integrate 时一致的缩放倍数")
    v.add_argument("--chrome", help="Chrome/Chromium 可执行文件路径")

    s = sub.add_parser("self-test", help="内置示例跑完整 integrate + verify")
    s.add_argument("--scale", type=int, default=DEFAULT_SCALE)
    s.add_argument("--chrome", help="Chrome/Chromium 可执行文件路径")

    args = p.parse_args()

    if args.cmd == "integrate":
        src = Path(args.html)
        html = src.read_text(encoding="utf-8")
        title = args.title or infer_title(html, src.name)
        try:
            out = build_injected(html, selector=args.selector, width=args.width,
                                 scale=args.scale, title=title)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        dst = Path(args.out) if args.out else src
        dst.write_text(out, encoding="utf-8")
        print(f"integrated={dst.resolve()}")
        print(f"selector={args.selector or 'auto'}")
        print(f"width={args.width} scale={args.scale}")
        print(f"title={title}")
        print("next=python3 %s verify %s --scale %d" % (__file__, dst, args.scale))
        return 0

    if args.cmd == "verify":
        r = verify(args.html, args.scale, args.chrome)
        print(r["result"])
        return 0 if r["ok"] else 1

    if args.cmd == "self-test":
        r = self_test(args.scale, args.chrome)
        print(r["result"])
        return 0 if r["ok"] else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
