#!/usr/bin/env python3
"""Generate one content-specific BGM candidate with Google Lyria 3 through OpenRouter.

usage: gen_bgm.py --name a --prompt "Instrumental ... no vocals ..." --out music/gen/a [--ledger ledger/costs.jsonl] [--dry-run]

- Tell the author the unit price before the first paid call (observed 2026-10: about $0.08 per full
  track with google/lyria-3-pro-preview) and record every call in the cost ledger.
- The request asks for "audio": {"format": "wav"} and streams; audio arrives as delta.audio.data chunks
  (observed as MP3 bytes even when WAV is asked). A stream that ends with only structure text such as
  "[[A0]] [[B1]]" and no audio is a failed call: retry once, do not treat it as music.
- The key is read only from OPENROUTER_API_KEY and never printed.
- Adapted from lov-interview-media-creator (same author, MIT). After generation listen to the candidates or run
  a vocal-isolation check: Whisper "hears" lyrics in most instrumentals.
"""
import argparse
import base64
import datetime
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://openrouter.ai/api/v1/chat/completions"


def strip(node):
    if isinstance(node, dict):
        return {k: (f"<{len(v)} chars>" if isinstance(v, str) and len(v) > 400 else strip(v)) for k, v in node.items()}
    if isinstance(node, list):
        return [strip(v) for v in node]
    return node


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--name", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="google/lyria-3-pro-preview")
    ap.add_argument("--out", required=True, help="output path without extension")
    ap.add_argument("--ledger", help="append one JSON line per call (cost, status)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    body = {"model": a.model, "modalities": ["text", "audio"], "stream": True, "audio": {"format": "wav"},
            "messages": [{"role": "user", "content": a.prompt}]}
    if a.dry_run:
        print(json.dumps({"would_call": a.model, "prompt_chars": len(a.prompt)}, ensure_ascii=False))
        return
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is not set")
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.time()
    audio, text, usage, last, chunks, done = bytearray(), [], None, None, 0, False
    status = "ok"
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    done = True
                    break
                ev = json.loads(payload)
                last = ev
                usage = ev.get("usage") or usage
                for c in ev.get("choices") or []:
                    d = c.get("delta") or {}
                    if d.get("content"):
                        text.append(d["content"])
                    au = d.get("audio") or {}
                    if au.get("data"):
                        audio.extend(base64.b64decode(au["data"]))
                        chunks += 1
    except urllib.error.HTTPError as e:
        status = f"http {e.code}"
        print(status, e.read()[:300])
    head = bytes(audio[:12])
    ext = ("mp3" if head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") else
           "wav" if head[:4] == b"RIFF" else "ogg" if head[:4] == b"OggS" else "flac" if head[:4] == b"fLaC" else "bin")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not audio:
        status = status if status != "ok" else "no-audio"
    else:
        out.with_suffix("." + ext).write_bytes(bytes(audio))
    meta = {"name": a.name, "model": a.model, "prompt": a.prompt, "status": status, "done": done, "bytes": len(audio),
            "chunks": chunks, "format": ext, "usage": usage, "wall_seconds": round(time.time() - t0, 1),
            "text": "".join(text)[:500], "last_event": strip(last)}
    out.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    if a.ledger:
        Path(a.ledger).parent.mkdir(parents=True, exist_ok=True)
        with open(a.ledger, "a") as f:
            f.write(json.dumps({"time": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "service": "openrouter",
                                "model": a.model, "item": a.name, "status": status,
                                "cost_usd": (usage or {}).get("cost")}, ensure_ascii=False) + "\n")
    print(json.dumps({k: meta[k] for k in ("status", "bytes", "format", "wall_seconds")} | {"cost": (usage or {}).get("cost")}))
    if status != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
