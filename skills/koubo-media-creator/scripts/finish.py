#!/usr/bin/env python3
"""Render the short and its covers, then run the delivery checks and write qc/report.json.

usage: finish.py EPISODE_DIR [--name 作者-主题-YYYY-MM-DD] [--version v0.1] [--skip-render] [--concurrency 6]
                 [--model turbo] [--no-cer]

1. `remotion render Short` → deliverables/<version>/<name>-<version>.mp4 (H.264 CRF 18, AAC from the mounted mix),
   then a stream copy that writes bt709 colour tags; `remotion still Cover34 / Cover169` →
   <name>-<version>-cover-34.png / -cover-169.png.
2. Checks: 1080×1920, 30 fps, frame count = timeline, duration, bitrate ≤ 10 Mbps for Channels, integrated
   loudness and true peak of the encoded file, a re-transcription against the script (needs mlx-whisper;
   --no-cer to skip): the gate is the DROPPED ratio (script chars with no counterpart, i.e. swallowed words
   from a bad cut) ≤ 3 %; CER is reported for reference only because homophones and numerals are ASR noise.
   No initial prompt is used: Whisper echoes prompt text into the transcript. Then a 1 fps contact sheet
   (qc/sheet-<version>-NN.jpg) and cover
   thumbnails at platform size (270×360, 480×270) for the read-at-a-glance check.
The agent must still LOOK at the sheets and thumbnails; numbers alone are not acceptance.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

PUNCT = re.compile(r"[\s，。！？、：；“”‘’（）《》【】,.!?:;\"'()\[\]<>…—\-~·]")


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


DIGIT = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn_numbers(s):
    """七 → 7, 三十 → 30, 二十五 → 25, 一百二十 → 120 (enough for spoken counts); 他/她/它 → 他."""
    def conv(m):
        txt, total, cur = m.group(0), 0, 0
        for ch in txt:
            if ch in DIGIT:
                cur = DIGIT[ch]
            elif ch == "十":
                total += (cur or 1) * 10
                cur = 0
            elif ch == "百":
                total += (cur or 1) * 100
                cur = 0
        return str(total + cur)
    s = re.sub(r"[零一二两三四五六七八九十百]+", conv, s)
    return re.sub(r"[她它]", "他", s)


def compare(ref, hyp):
    """CER for reference, and the chars of the script that have no counterpart (swallowed by a cut)."""
    import difflib
    ref, hyp = cn_numbers(ref), cn_numbers(hyp)
    sm = difflib.SequenceMatcher(None, ref, hyp, autojunk=False)
    errors, dropped, spans = 0, 0, []
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == "equal":
            continue
        errors += max(a1 - a0, b1 - b0)
        lost = (a1 - a0) if tag == "delete" else max(0, (a1 - a0) - (b1 - b0)) if tag == "replace" else 0
        if lost:
            dropped += lost
            spans.append(ref[max(0, a0 - 4):a1 + 4])
    n = max(1, len(ref))
    return errors / n, dropped / n, spans


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("episode")
    ap.add_argument("--name", default="short", help="deliverable base name, e.g. the Profile's naming rule")
    ap.add_argument("--version", default="v0.1")
    ap.add_argument("--skip-render", action="store_true")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--model", default="turbo")
    ap.add_argument("--no-cer", action="store_true")
    a = ap.parse_args()
    ep = Path(a.episode).resolve()
    rem = ep / "work" / "remotion"
    tl = json.loads((rem / "public" / "data" / "timeline.json").read_text())
    out = ep / "deliverables" / a.version
    qc = ep / "qc"
    out.mkdir(parents=True, exist_ok=True)
    qc.mkdir(parents=True, exist_ok=True)
    base = f"{a.name}-{a.version}"
    raw = out / f"{base}.raw.mp4"
    final = out / f"{base}.mp4"
    covers = {"34": out / f"{base}-cover-34.png", "169": out / f"{base}-cover-169.png"}
    if not a.skip_render:
        run(["npx", "remotion", "render", "src/index.ts", "Short", str(raw), "--codec", "h264", "--crf", "18",
             "--audio-codec", "aac", "--audio-bitrate", "256k", f"--concurrency={a.concurrency}"], cwd=rem)
        run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-c", "copy", "-bsf:v",
             "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1",
             "-movflags", "+faststart", str(final)])
        raw.unlink()
        for comp, key in (("Cover34", "34"), ("Cover169", "169")):
            run(["npx", "remotion", "still", "src/index.ts", comp, str(covers[key])], cwd=rem)

    pr = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format",
                                             "-of", "json", str(final)]))
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    aud = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    frames = int(v.get("nb_read_frames", 0))
    dur = float(pr["format"]["duration"])
    mbps = int(pr["format"]["bit_rate"]) / 1e6
    loud = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(final), "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    summ = loud[loud.rfind("Summary:"):]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    checks = {
        "size_1080x1920": (v["width"], v["height"]) == (1080, 1920),
        "fps_30": v["r_frame_rate"] in ("30/1", "30000/1000"),
        "frames_match_timeline": frames == tl["durationInFrames"],
        "has_audio": aud is not None,
        "bitrate_le_10mbps": mbps <= 10,
        "loudness_-17_to_-15": -17 <= lufs <= -15,
        "true_peak_le_-1": tp <= -1.0,
        "bt709_tagged": v.get("color_primaries") == "bt709",
    }
    report = {"film": str(final), "frames": frames, "timeline_frames": tl["durationInFrames"], "seconds": round(dur, 2),
              "mbps": round(mbps, 2), "lufs_i": lufs, "true_peak_dbfs": tp, "animatic": bool(tl.get("animatic"))}

    if not a.no_cer:
        script = json.loads((ep / "work" / "script.json").read_text())
        ref = PUNCT.sub("", "".join(ln["text"] for ln in script["lines"])).lower()
        import mlx_whisper
        models = {"turbo": "mlx-community/whisper-large-v3-turbo", "large-v3": "mlx-community/whisper-large-v3-mlx"}
        r = mlx_whisper.transcribe(str(final), path_or_hf_repo=models.get(a.model, a.model), language="zh")
        hyp = r["text"]
        try:
            import opencc
            hyp = opencc.OpenCC("t2s").convert(hyp)
        except Exception:
            pass
        hyp = PUNCT.sub("", hyp).lower()
        c, d, spans = compare(ref, hyp)
        report["cer_reference"] = round(c, 3)
        report["dropped_ratio"] = round(d, 3)
        report["dropped_spans"] = spans[:30]
        report["heard"] = r["text"][:2000]
        checks["dropped_le_3pct"] = d <= 0.03

    # 1 fps contact sheets, 6×4 per page; cover thumbnails at platform size
    for old in qc.glob(f"sheet-{a.version}-*.jpg"):
        old.unlink()
    run(["ffmpeg", "-v", "error", "-y", "-i", str(final), "-vf",
         "fps=1,scale=180:320,drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=14:fontcolor=white:box=1:boxcolor=black@0.6,tile=6x4",
         str(qc / f"sheet-{a.version}-%02d.jpg")])
    for key, size in (("34", "270:360"), ("169", "480:270")):
        if covers[key].exists():
            run(["ffmpeg", "-v", "error", "-y", "-i", str(covers[key]), "-vf", f"scale={size}",
                 str(qc / f"thumb-{a.version}-cover-{key}.png")])
    report["checks"] = checks
    report["ok"] = all(checks.values())
    report["sheets"] = sorted(str(p) for p in qc.glob(f"sheet-{a.version}-*.jpg"))
    (qc / f"report-{a.version}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: report[k] for k in report if k not in ("heard", "sheets")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
