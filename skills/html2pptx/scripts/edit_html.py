#!/usr/bin/env python3
"""
edit_html — local live-preview HTML editor with one-click PPTX export.

Boots a tiny HTTP server (default http://127.0.0.1:5757). The browser shows:
  • left pane:  editor (textarea, monospace) bound to the source HTML file
  • right pane: live preview <iframe> that re-renders on every keystroke
  • toolbar:    [Save HTML] [Export PPTX]

Saving writes back to the source file. Export runs html2pptx.py against the
current (unsaved) buffer and offers the .pptx as a download.

Examples:
  python3 edit_html.py --input deck.html
  python3 edit_html.py --input deck.html --port 8080
  python3 edit_html.py --input deck.html --size 1280x720 --selector ".slide"
"""

from __future__ import annotations

import argparse
import http.server
import json
import socketserver
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import webbrowser
from pathlib import Path

EDITOR_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>html2pptx · editor</title>
<style>
  :root {
    --bg: #F9F9F7;
    --fg: #181818;
    --primary: #CC785C;
    --border: #e2e2dd;
    --muted: #8a8a82;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    background: var(--bg);
    color: var(--fg);
    display: grid;
    grid-template-rows: 48px 1fr;
  }
  header {
    display: flex; align-items: center; gap: 12px;
    padding: 0 16px;
    border-bottom: 1px solid var(--border);
    background: #fff;
  }
  header h1 {
    font-size: 14px; font-weight: 600; margin: 0;
    color: var(--primary); letter-spacing: 0.04em;
  }
  header .file { font-size: 12px; color: var(--muted); margin-left: 4px; }
  header .spacer { flex: 1; }
  header button {
    appearance: none; border: 1px solid var(--border);
    background: #fff; color: var(--fg);
    padding: 6px 12px; border-radius: 6px;
    font: inherit; font-size: 13px; cursor: pointer;
  }
  header button.primary {
    background: var(--primary); border-color: var(--primary); color: #fff;
  }
  header button:disabled { opacity: 0.5; cursor: not-allowed; }
  header .status { font-size: 12px; color: var(--muted); min-width: 140px; text-align: right; }
  main { display: grid; grid-template-columns: 1fr 1fr; min-height: 0; }
  .pane { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
  .pane + .pane { border-left: 1px solid var(--border); }
  .pane > .label {
    padding: 6px 12px; font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--muted);
    border-bottom: 1px solid var(--border); background: #fff;
  }
  textarea {
    flex: 1; width: 100%; resize: none; border: 0; outline: none;
    padding: 14px; font-family: ui-monospace, Menlo, Consolas, monospace;
    font-size: 13px; line-height: 1.5; tab-size: 2;
    background: #fff; color: var(--fg);
  }
  iframe { flex: 1; width: 100%; border: 0; background: #fff; }
</style>
</head>
<body>
<header>
  <h1>html2pptx</h1>
  <span class="file" id="filename"></span>
  <span class="spacer"></span>
  <span class="status" id="status">ready</span>
  <button id="save">Save HTML</button>
  <button id="export" class="primary">Export PPTX</button>
</header>
<main>
  <section class="pane">
    <div class="label">source · HTML</div>
    <textarea id="editor" spellcheck="false"></textarea>
  </section>
  <section class="pane">
    <div class="label">live preview</div>
    <iframe id="preview" sandbox="allow-same-origin allow-scripts"></iframe>
  </section>
</main>
<script>
const ed = document.getElementById('editor');
const pv = document.getElementById('preview');
const status = document.getElementById('status');
const filenameEl = document.getElementById('filename');
const saveBtn = document.getElementById('save');
const exportBtn = document.getElementById('export');

let dirty = false;
let timer = null;

function setStatus(msg, color) {
  status.textContent = msg;
  status.style.color = color || 'var(--muted)';
}

function refreshPreview() {
  const html = ed.value;
  const blob = new Blob([html], { type: 'text/html' });
  pv.src = URL.createObjectURL(blob);
}

async function loadFile() {
  const r = await fetch('/file');
  const data = await r.json();
  filenameEl.textContent = data.path;
  ed.value = data.content;
  refreshPreview();
}

ed.addEventListener('input', () => {
  dirty = true;
  setStatus('● unsaved', 'var(--primary)');
  clearTimeout(timer);
  timer = setTimeout(refreshPreview, 220);
});

saveBtn.addEventListener('click', async () => {
  setStatus('saving...');
  const r = await fetch('/file', {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    body: ed.value,
  });
  if (r.ok) { dirty = false; setStatus('saved ✓', '#4a9'); }
  else setStatus('save failed', '#c44');
});

exportBtn.addEventListener('click', async () => {
  exportBtn.disabled = true;
  setStatus('exporting PPTX...', 'var(--primary)');
  try {
    const r = await fetch('/export', {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      body: ed.value,
    });
    if (!r.ok) {
      const err = await r.text();
      setStatus('export failed', '#c44');
      alert('Export failed:\n\n' + err);
      return;
    }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'deck.pptx';
    a.click();
    URL.revokeObjectURL(url);
    setStatus('exported ✓', '#4a9');
  } finally {
    exportBtn.disabled = false;
  }
});

window.addEventListener('beforeunload', e => {
  if (dirty) { e.preventDefault(); e.returnValue = ''; }
});

loadFile();
</script>
</body>
</html>
"""


def make_handler(state):
    class Handler(http.server.BaseHTTPRequestHandler):
        # Keep stdout clean
        def log_message(self, fmt, *args):
            pass

        def _send(self, status, body, ctype="text/plain; charset=utf-8", extra=None):
            data = body if isinstance(body, (bytes, bytearray)) else body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            if extra:
                for k, v in extra.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            if path in ("/", "/index.html"):
                self._send(200, EDITOR_HTML, "text/html; charset=utf-8")
                return
            if path == "/file":
                payload = {
                    "path": str(state["input"]),
                    "content": state["input"].read_text(encoding="utf-8"),
                }
                self._send(200, json.dumps(payload), "application/json")
                return
            self._send(404, "not found")

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            path = urllib.parse.urlparse(self.path).path

            if path == "/file":
                state["input"].write_text(body, encoding="utf-8")
                self._send(200, "ok")
                return

            if path == "/export":
                try:
                    pptx_bytes = run_export(body, state)
                except subprocess.CalledProcessError as e:
                    self._send(500, e.stderr or str(e))
                    return
                except Exception as e:
                    self._send(500, str(e))
                    return
                self._send(
                    200,
                    pptx_bytes,
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    {"Content-Disposition": 'attachment; filename="deck.pptx"'},
                )
                return

            self._send(404, "not found")

    return Handler


def run_export(html_body: str, state) -> bytes:
    """Write buffer to a temp .html, run html2pptx.py, return .pptx bytes."""
    skill_dir = Path(__file__).resolve().parent
    converter = skill_dir / "html2pptx.py"

    with tempfile.TemporaryDirectory(prefix="html2pptx-edit-") as tmp:
        tmp_path = Path(tmp)
        # Copy referenced assets by writing the HTML next to the original so
        # relative paths still resolve.
        src_dir = state["input"].parent
        tmp_html = src_dir / f".html2pptx.preview.{state['input'].stem}.html"
        tmp_html.write_text(html_body, encoding="utf-8")
        tmp_pptx = tmp_path / "deck.pptx"
        try:
            cmd = [
                sys.executable, str(converter),
                "--input", str(tmp_html),
                "--output", str(tmp_pptx),
                "--size", f"{state['width']}x{state['height']}",
                "--scale", str(state["scale"]),
                "--split", state["split"],
                "--selector", state["selector"],
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return tmp_pptx.read_bytes()
        finally:
            try:
                tmp_html.unlink()
            except FileNotFoundError:
                pass


def parse_size(s: str):
    w, h = s.lower().replace("×", "x").split("x")
    return int(w), int(h)


def main() -> int:
    ap = argparse.ArgumentParser(description="Live HTML editor with PPTX export.")
    ap.add_argument("--input", "-i", required=True, help="Path to .html file to edit")
    ap.add_argument("--port", type=int, default=5757)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--size", type=parse_size, default=(1920, 1080))
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--split", choices=["auto", "selector", "single"], default="auto")
    ap.add_argument("--selector", default=".slide, section.slide, [data-slide]")
    ap.add_argument("--no-open", action="store_true", help="Don't auto-open browser")
    args = ap.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        # Bootstrap an empty deck so users can start from zero.
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(_starter_html(), encoding="utf-8")
        print(f"  • created starter template at {input_path}")

    width, height = args.size
    state = {
        "input": input_path,
        "width": width,
        "height": height,
        "scale": args.scale,
        "split": args.split,
        "selector": args.selector,
    }

    handler = make_handler(state)
    with socketserver.ThreadingTCPServer((args.host, args.port), handler) as srv:
        url = f"http://{args.host}:{args.port}/"
        print(f"  ▸ editing {input_path}")
        print(f"  ▸ open {url}")
        if not args.no_open:
            threading.Timer(0.2, lambda: webbrowser.open(url)).start()
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n  ✓ stopped")
    return 0


def _starter_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>my deck</title>
<style>
  body { margin: 0; font-family: -apple-system, "Helvetica Neue", sans-serif; }
  .slide {
    width: 1920px; height: 1080px;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    box-sizing: border-box; padding: 80px;
    page-break-after: always;
  }
  .slide.title { background: #181818; color: #F9F9F7; }
  .slide.title h1 { font-size: 120px; font-weight: 700; margin: 0; }
  .slide.title p { font-size: 36px; color: #CC785C; margin: 24px 0 0; }
  .slide.body { background: #F9F9F7; color: #181818; }
  .slide.body h2 { font-size: 80px; margin: 0 0 40px; color: #CC785C; }
  .slide.body p  { font-size: 36px; line-height: 1.5; max-width: 1400px; }
</style>
</head>
<body>
  <section class="slide title">
    <h1>Hello, deck</h1>
    <p>edit me, hit Export PPTX</p>
  </section>
  <section class="slide body">
    <h2>Slide two</h2>
    <p>Each <code>.slide</code> element becomes one page in the PPTX.
       Style them however you like — Playwright renders the real browser.</p>
  </section>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
