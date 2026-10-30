#!/usr/bin/env python3
"""Cut the chosen takes into continuous mezzanine tracks and write the Remotion timeline.

usage: build.py work/script.json work/takes.json --recording recording/take.mov --public work/remotion/public
                [--root EPISODE_DIR] [--still brand/portrait.jpg] [--face-y 0.33] [--speed 1.0] [--fps 30]
                [--end-seconds 2.5] [--max-caption 14] [--animatic]

- presenter: the recording's video, trimmed to the takes' spans, scaled/cropped to 1080×1920 (bt709, 30 fps)
  as ONE continuous file public/media/presenter.mp4; with --still (audio-only stand-in take) the presenter is
  that image instead. Speed changes keep pitch (atempo) and frame counts are locked to the timeline.
- voice: the same spans as ONE continuous public/audio/voice.wav (8 ms fades at joins only).
- captions: text from the script (never from ASR), timed by mapping each script char onto the take's
  ASR char times; ≤ --max-caption chars per caption, emphasis words never split, no trailing punctuation.
- shots: one or more b-roll per line, split at a b-roll's `at` substring or evenly; images are copied to
  public/broll/ with their pixel size recorded so boxes and focus land on the right pixels.
- end card: --end-seconds after the last line, voice silent, music continues.
Writes public/data/timeline.json; mix.py later adds public/audio/mix.m4a and points the timeline at it.
"""
import argparse
import difflib
import json
import re
import shutil
import subprocess
from pathlib import Path

PUNCT = re.compile(r"[\s，。！？、：；“”‘’（）《》【】,.!?:;\"'()\[\]<>…—\-~·]")
BREAK = re.compile(r"[，。！？；：,.!?;:]")
STRIP = "，。！？、：；,.!?;: "
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm"}
try:
    import opencc
    _T2S = opencc.OpenCC("t2s")
except Exception:
    _T2S = None
try:
    import jieba
    jieba.setLogLevel(60)
except Exception:
    jieba = None


def norm_char(c):
    c = _T2S.convert(c) if _T2S else c
    if "０" <= c <= "ｚ":
        c = chr(ord(c) - 0xFEE0)
    return c.lower()


def probe(path):
    out = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))
    v = next((s for s in out["streams"] if s["codec_type"] == "video" and s.get("disposition", {}).get("attached_pic") != 1), None)
    return v, float(out["format"]["duration"])


def split_caption(text, emphasis, limit):
    """Phrases at punctuation, then balanced word-boundary splits; emphasis words stay whole."""
    pieces = [p for p in re.split(r"(?<=[，。！？；：,.!?;:])", text) if p.strip(STRIP)]
    out = []
    for p in pieces:
        disp = p.strip(STRIP + "　")
        if len(PUNCT.sub("", disp)) <= limit:
            out.append(disp)
            continue
        # prefer a list comma: the most balanced 、 cut that leaves both halves short enough
        cuts = [k + 1 for k, ch in enumerate(disp) if ch == "、"]
        ok = [k for k in cuts if len(PUNCT.sub("", disp[:k])) <= limit and len(PUNCT.sub("", disp[k:])) <= limit]
        if ok:
            k = min(ok, key=lambda k: abs(len(PUNCT.sub("", disp[:k])) - len(PUNCT.sub("", disp[k:]))))
            out += [disp[:k], disp[k:]]
            continue
        tokens = list(jieba.cut(disp)) if jieba else list(disp)
        merged = []  # keep emphasis words atomic
        i = 0
        while i < len(tokens):
            hit = None
            for w in sorted(emphasis or [], key=len, reverse=True):
                if "".join(tokens[i:]).startswith(w):
                    hit = w
                    break
            if hit:
                acc, j = "", i
                while len(acc) < len(hit):
                    acc += tokens[j]
                    j += 1
                merged.append(acc)
                i = j
            else:
                merged.append(tokens[i])
                i += 1
        n = len(PUNCT.sub("", disp))
        parts = -(-n // limit)
        target = n / parts
        cur, acc = "", 0
        for t in merged:
            tl = len(PUNCT.sub("", t))
            if cur and acc + tl > target * 1.15 and len(out) < 99:
                out.append(cur.strip())
                cur, acc = "", 0
            cur += t
            acc += tl
        if cur.strip():
            out.append(cur.strip())
    # the genre's captions carry no punctuation: inner commas become a space, ?/! and periods drop
    clean = [re.sub(r"\s*[，、；：,;:]\s*", " ", c.strip(STRIP)).strip() for c in out]
    return [re.sub(r"[。！？!?]", "", c).strip() for c in clean if c]


def char_clock(text, heard_chars):
    """Source time for every non-punctuation char of `text`, from the take's ASR chars."""
    idx = [i for i, c in enumerate(text) if not PUNCT.match(c)]
    s = "".join(norm_char(text[i]) for i in idx)
    h = "".join(c for c, _, _ in heard_chars)
    times = [None] * len(s)
    for tag, a0, a1, b0, b1 in difflib.SequenceMatcher(None, s, h, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and a1 - a0 == b1 - b0):
            for k in range(a1 - a0):
                times[a0 + k] = heard_chars[b0 + k][1]
        elif tag == "replace":
            for k in range(a1 - a0):
                times[a0 + k] = heard_chars[b0 + int(k * (b1 - b0) / (a1 - a0))][1]
    known = [k for k, t in enumerate(times) if t is not None]
    if not known:
        return {}
    for k in range(len(times)):
        if times[k] is None:
            lo = max((x for x in known if x < k), default=None)
            hi = min((x for x in known if x > k), default=None)
            if lo is None:
                times[k] = times[hi]
            elif hi is None:
                times[k] = times[lo]
            else:
                times[k] = times[lo] + (times[hi] - times[lo]) * (k - lo) / (hi - lo)
    return {idx[k]: times[k] for k in range(len(idx))}


def default_fit(layout, w, h):
    """Full-screen evidence is shown whole; on the split panel fill it unless that crops more than 25%."""
    if layout == "broll":
        return "contain"
    panel = 1080 / 910  # layout.ts SPLIT: brollTop 100 → brollBottom 1010
    aspect = w / h
    crop = 1 - min(aspect / panel, panel / aspect)
    return "cover" if crop <= 0.25 else "contain"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("script")
    ap.add_argument("takes")
    ap.add_argument("--recording", required=True)
    ap.add_argument("--public", required=True)
    ap.add_argument("--root")
    ap.add_argument("--still", help="presenter image when the recording is audio only (animatic)")
    ap.add_argument("--face-y", type=float, default=0.33, help="face centre as a fraction of presenter height")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--end-seconds", type=float, default=2.5)
    ap.add_argument("--max-caption", type=int, default=14)
    ap.add_argument("--animatic", action="store_true", help="mark the film as a stand-in preview")
    ap.add_argument("--placeholder", action="store_true",
                    help="show --still as a small native-size portrait in a stand-in frame (for small brand photos)")
    ap.add_argument("--logo", help="official brand logo, light version (watermark, end card, cover)")
    ap.add_argument("--allow-missing", action="store_true",
                    help="preview before all evidence exists: a missing b-roll becomes a labelled empty panel")
    a = ap.parse_args()

    sp = Path(a.script)
    s = json.loads(sp.read_text())
    tk = json.loads(Path(a.takes).read_text())
    root = Path(a.root) if a.root else sp.resolve().parent.parent
    pub = Path(a.public)
    for d in ("media", "audio", "broll", "data", "img"):
        (pub / d).mkdir(parents=True, exist_ok=True)
    rec = Path(a.recording)
    vstream, _ = probe(rec)
    if vstream is None and not a.still:
        raise SystemExit("recording has no video stream: pass --still <portrait> for an animatic")
    fps, speed = a.fps, a.speed
    takes = {t["id"]: t for t in tk["lines"]}

    # 1. spans → output frames
    spans, cursor = [], 0
    for ln in s["lines"]:
        t = takes.get(ln["id"])
        if not t or not t["spans"]:
            print(f"WARN {ln['id']}: no take, skipped")
            continue
        for src_in, src_out in t["spans"]:
            frames = max(1, round((src_out - src_in) / speed * fps))
            spans.append({"id": ln["id"], "in": src_in, "out": src_in + frames * speed / fps, "f0": cursor, "frames": frames})
            cursor += frames
    total_speech = cursor

    def out_frame(lid, t_src):
        """Map a source time inside a line's takes to an output frame (gaps snap forward)."""
        cand = [x for x in spans if x["id"] == lid]
        for x in cand:
            if t_src < x["in"]:
                return x["f0"]
            if t_src <= x["out"]:
                return x["f0"] + round((t_src - x["in"]) / speed * fps)
        return cand[-1]["f0"] + cand[-1]["frames"] if cand else 0

    # 2. voice + presenter mezzanines
    fades = []
    for k, x in enumerate(spans):
        d = x["out"] - x["in"]
        chain = f"[0:a]atrim={x['in']:.4f}:{x['out']:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={max(0, d - 0.008):.4f}:d=0.008"
        if abs(speed - 1) > 1e-3:
            chain += f",atempo={speed}"
        fades.append(chain + f"[a{k}]")
    seconds = total_speech / fps
    graph = ";".join(fades) + ";" + "".join(f"[a{k}]" for k in range(len(spans))) + \
        f"concat=n={len(spans)}:v=0:a=1,aresample=48000,apad,atrim=0:{seconds:.4f}[a]"
    voice = pub / "audio" / "voice.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(rec), "-filter_complex", graph, "-map", "[a]", "-ac", "2",
                    "-ar", "48000", "-c:a", "pcm_s16le", str(voice)], check=True)
    if vstream is not None and not a.still:
        vg = ";".join(f"[0:v]trim={x['in']:.4f}:{x['out']:.4f},setpts=(PTS-STARTPTS)/{speed},fps={fps},"
                      f"trim=end_frame={x['frames']}[v{k}]" for k, x in enumerate(spans))
        vg += ";" + "".join(f"[v{k}]" for k in range(len(spans))) + f"concat=n={len(spans)}:v=1:a=0," \
              "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p[v]"
        presenter = pub / "media" / "presenter.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(rec), "-filter_complex", vg, "-map", "[v]",
                        "-frames:v", str(total_speech), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(presenter)], check=True)
        got = int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                                           "stream=nb_read_frames", "-of", "csv=p=0", str(presenter)]).decode().strip())
        if got != total_speech:
            raise SystemExit(f"presenter has {got} frames, timeline needs {total_speech}")
        pres = {"kind": "video", "src": "media/presenter.mp4", "faceY": a.face_y}
    else:
        dst = pub / "img" / ("portrait" + Path(a.still).suffix.lower())
        shutil.copy2(a.still, dst)
        pres = {"kind": "image", "src": f"img/{dst.name}", "faceY": a.face_y, "placeholder": a.placeholder}

    # 3. captions and shots
    from PIL import Image
    captions, shots = [], []
    for ln in s["lines"]:
        t = takes.get(ln["id"])
        if not t or not t["spans"]:
            continue
        lspans = [x for x in spans if x["id"] == ln["id"]]
        L0, L1 = lspans[0]["f0"], lspans[-1]["f0"] + lspans[-1]["frames"]
        clock = char_clock(ln["text"], t["chars"])
        text = ln["text"]

        def frame_at(char_index):
            src = clock.get(char_index)
            return L0 if src is None else min(L1, max(L0, out_frame(ln["id"], src)))

        chunks = split_caption(text, ln.get("emphasis"), a.max_caption)
        pos, starts = 0, []
        for c in chunks:
            first = text.find(c[0], pos)
            starts.append(frame_at(first if first >= 0 else pos))
            pos = (first if first >= 0 else pos) + len(c)
        starts[0] = L0
        for k, c in enumerate(chunks):
            f0 = max(starts[k], captions[-1]["to"] if captions else 0)
            f1 = starts[k + 1] if k + 1 < len(chunks) else L1
            if f1 - f0 < 8 and captions and k > 0:  # too short to read: merge into previous
                captions[-1]["text"] += c
                captions[-1]["to"] = f1
                continue
            captions.append({"from": f0, "to": max(f1, f0 + 8), "text": c, "line": ln["id"],
                             "hl": [w for w in ln.get("emphasis") or [] if w in c]})

        layout = ln.get("layout", "split")
        brolls = (ln.get("broll") or []) if layout != "face" else []
        if not brolls:
            shots.append({"from": L0, "to": L1, "line": ln["id"], "layout": "face", "callout": ln.get("callout")})
            continue
        cuts = []
        for k, b in enumerate(brolls):
            if b.get("at") and b["at"] in text:
                cuts.append(frame_at(text.index(b["at"])))
            else:
                cuts.append(L0 + round((L1 - L0) * k / len(brolls)))
        cuts[0] = L0
        for k, b in enumerate(brolls):
            srcp = root / b["src"]
            if not srcp.exists():
                if not a.allow_missing:
                    raise SystemExit(f"{ln['id']}: b-roll missing: {b['src']} (run capture.py or check shotlist.md)")
                shots.append({"from": cuts[k], "to": cuts[k + 1] if k + 1 < len(brolls) else L1, "line": ln["id"],
                              "layout": layout, "missing": b["src"], "label": b.get("label"),
                              "callout": ln.get("callout") if k == 0 else None})
                continue
            dst = pub / "broll" / srcp.name
            if not dst.exists() or dst.stat().st_mtime < srcp.stat().st_mtime:
                shutil.copy2(srcp, dst)
            kind = "video" if srcp.suffix.lower() in VIDEO_EXT else "image"
            if kind == "image":
                with Image.open(srcp) as im:
                    w, h = im.size
            else:
                v, _ = probe(srcp)
                w, h = int(v["width"]), int(v["height"])
            shots.append({"from": cuts[k], "to": cuts[k + 1] if k + 1 < len(brolls) else L1, "line": ln["id"],
                          "layout": layout, "src": f"broll/{srcp.name}", "kind": kind, "w": w, "h": h,
                          "fit": b.get("fit") or default_fit(layout, w, h),
                          "boxes": b.get("boxes") or [], "focus": b.get("focus"), "label": b.get("label"),
                          "start": b.get("start", 0), "callout": ln.get("callout") if k == 0 else None})

    logo = None
    if a.logo:
        dst = pub / "img" / ("logo" + Path(a.logo).suffix.lower())
        shutil.copy2(a.logo, dst)
        logo = f"img/{dst.name}"

    # cover spec from script.cover (cut-out and evidence cards copied into public/img)
    cov = s.get("cover") or {}
    spec = {"headline": cov.get("headline") or [], "accent": cov.get("accent") or [], "tag": cov.get("tag"),
            "cutout": None, "cards": [], "bg": None, "logo": logo}
    for key in ("cutout", "bg"):
        if cov.get(key) and (root / cov[key]).exists():
            dst = pub / "img" / f"cover-{key}{Path(cov[key]).suffix.lower()}"
            shutil.copy2(root / cov[key], dst)
            spec[key] = f"img/{dst.name}"
            if key == "cutout":
                from PIL import Image
                with Image.open(dst) as im:
                    spec["cutoutPx"] = list(im.size)  # the cover never upscales the cut-out past 1.1×
    for k, c in enumerate(cov.get("cards") or []):
        if (root / c).exists():
            dst = pub / "img" / f"cover-card-{k}{Path(c).suffix.lower()}"
            shutil.copy2(root / c, dst)
            spec["cards"].append(f"img/{dst.name}")
    (pub / "data" / "cover.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1))

    end_frames = round(a.end_seconds * fps)
    author = s.get("author") or {}
    end = {"from": total_speech, "frames": end_frames, "name": author.get("name", ""), "handle": author.get("handle", ""),
           "line": (s.get("end") or {}).get("line", ""), "avatar": None, "covers": []}
    if author.get("avatar") and (root / author["avatar"]).exists():
        dst = pub / "img" / ("avatar" + Path(author["avatar"]).suffix.lower())
        shutil.copy2(root / author["avatar"], dst)
        end["avatar"] = f"img/{dst.name}"
    for k, c in enumerate((s.get("end") or {}).get("covers") or []):
        if (root / c).exists():
            dst = pub / "img" / f"endcover-{k}{Path(c).suffix.lower()}"
            shutil.copy2(root / c, dst)
            end["covers"].append(f"img/{dst.name}")
    timeline = {"schema": "talking-head-timeline/v1", "fps": fps, "width": 1080, "height": 1920,
                "durationInFrames": total_speech + end_frames, "speechFrames": total_speech, "animatic": a.animatic,
                "presenter": pres, "logo": logo, "audio": "audio/voice.wav", "watermark": author.get("handle") or author.get("name", ""),
                "captions": captions, "shots": shots, "end": end, "title": s.get("title", "")}
    (pub / "data" / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1))
    print(json.dumps({"frames": timeline["durationInFrames"], "seconds": round(timeline["durationInFrames"] / fps, 2),
                      "spans": len(spans), "captions": len(captions), "shots": len(shots), "presenter": pres["kind"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
