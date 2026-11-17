#!/usr/bin/env python3
"""Render the logo sting as a standalone clip (H.264 + AAC 48 kHz, bt709) with Remotion.

Copies assets/remotion-template/ and assets/remotion/LogoSting.tsx into a work dir (never into the skill dir), writes
the input props, links a Remotion 4.0.534 install, runs `npx remotion render` once per aspect and checks every output
with ffprobe.

  render_sting.py --spec spec.json --timing timing.json --audio sting.wav --aspect 9x16,16x9 --out out/

Dependencies: --node-modules DIR reuses an existing install (linked read-only: Remotion's caches stay in the work
dir); otherwise `npm install` runs once into ~/.cache/lov-logo-sting/remotion-4.0.534 and is linked from there.
Needs node/npx, ffprobe, and ffmpeg (only when the colour tags have to be added afterwards).
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "remotion-template"
COMPONENT = SKILL_DIR / "assets" / "remotion" / "LogoSting.tsx"
REMOTION_VERSION = "4.0.534"
ASPECTS = {"9x16": (1080, 1920), "16x9": (1920, 1080), "1x1": (1080, 1080), "4x3": (1440, 1080)}
CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "lov-logo-sting" / f"remotion-{REMOTION_VERSION}"
WORK_MARK = ".lov-logo-sting-work"
SHADOW_MARK = ".lov-logo-sting-shadow"


def log(msg):
    print(f"[render_sting] {msg}", flush=True)


def die(msg, code=2):
    print(f"render_sting: error: {msg}", file=sys.stderr)
    sys.exit(code)


def inside(path, root):
    try:
        Path(path).resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def load_json(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        die(f"cannot read {what} {path}: {exc}")


def check_inputs(spec, timing):
    if spec.get("schema", "logo-sting-spec/v1") != "logo-sting-spec/v1":
        die(f"spec schema is {spec.get('schema')!r}, expected logo-sting-spec/v1")
    if not isinstance(spec.get("mark"), list) or not spec["mark"] or not all(isinstance(m, dict) and m.get("d") for m in spec["mark"]):
        die("spec.mark must list at least one shape with path data 'd'")
    if not isinstance(spec.get("word", []), list):
        die("spec.word must be a list (may be empty)")
    for key in ("markBox", "logoBox"):
        if not (isinstance(spec.get(key), list) and len(spec[key]) == 4):
            die(f"spec.{key} must be [x0, y0, x1, y1]")
    colors = spec.get("colors") or {}
    for key in ("final", "accent", "hot"):
        if not isinstance(colors.get(key), str) or not colors[key].startswith("#"):
            die(f"spec.colors.{key} must be a #hex colour")
    if timing.get("schema", "logo-sting-timing/v1") != "logo-sting-timing/v1":
        die(f"timing schema is {timing.get('schema')!r}, expected logo-sting-timing/v1")
    for key in ("fps", "bar", "dur", "cut", "gate"):
        if not isinstance(timing.get(key), (int, float)) or timing[key] <= 0:
            die(f"timing.{key} must be a positive number")
    if not isinstance(timing.get("hits"), list) or not timing["hits"]:
        die("timing.hits must list the stroke frames")
    if len(timing["hits"]) != len(spec["mark"]):
        die(f"timing has {len(timing['hits'])} hits but the spec has {len(spec['mark'])} mark strokes; rebuild the timing with --spec")
    if not timing["gate"] < timing["bar"] < timing["cut"] < timing["dur"]:
        die("timing must satisfy gate < bar < cut < dur")


def parse_aspects(values):
    out = []
    for value in values:
        for a in value.split(","):
            a = a.strip()
            if not a:
                continue
            if a not in ASPECTS:
                die(f"unknown aspect {a!r}; choose from {', '.join(ASPECTS)}")
            if a not in out:
                out.append(a)
    if not out:
        die("give at least one --aspect")
    return out


def output_paths(out, aspects):
    p = Path(out).expanduser()
    if p.suffix.lower() in (".mp4", ".mov"):
        if len(aspects) == 1:
            return {aspects[0]: p}
        return {a: p.with_name(f"{p.stem}-{a}{p.suffix}") for a in aspects}
    if p.suffix:
        die(f"--out {out}: give a directory or an .mp4/.mov file")
    return {a: p / f"logo-sting-{a}.mp4" for a in aspects}


def prepare_work_dir(work):
    if work.exists():
        entries = [e for e in os.listdir(work) if e != ".DS_Store"]
        if entries and not (work / WORK_MARK).exists():
            die(f"--work-dir {work} is not empty and was not made by render_sting.py; give an empty or new directory")
    work.mkdir(parents=True, exist_ok=True)
    (work / WORK_MARK).write_text("scratch dir of lov-logo-sting/scripts/render_sting.py; safe to delete\n")
    for item in TEMPLATE.iterdir():
        if item.name in ("node_modules", ".DS_Store"):
            continue
        dst = work / item.name
        if item.is_dir():
            shutil.copytree(item, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dst)
    shutil.copy2(COMPONENT, work / "src" / "LogoSting.tsx")
    (work / "public").mkdir(exist_ok=True)


def remotion_version(nm):
    pkg = nm / "remotion" / "package.json"
    try:
        return json.loads(pkg.read_text())["version"]
    except (OSError, ValueError, KeyError):
        return None


def clear_node_modules(work):
    nm = work / "node_modules"
    if nm.is_symlink():
        nm.unlink()
    elif nm.is_dir():
        if not (nm / SHADOW_MARK).exists():
            die(f"{nm} is a real install, not one render_sting.py linked; use another --work-dir")
        shutil.rmtree(nm)
    return nm


def link_existing(work, src):
    """Shadow node_modules: a real dir of links into `src`, so Remotion's webpack cache and browser download (both kept
    under <project>/node_modules) land in the work dir and the other install is only read."""
    src = Path(src).expanduser().resolve()
    ver = remotion_version(src)
    if ver is None or not (src / "@remotion" / "cli").exists():
        die(f"--node-modules {src} has no remotion + @remotion/cli install")
    if ver != REMOTION_VERSION:
        log(f"warning: {src} has remotion {ver}; the template pins {REMOTION_VERSION}")
    nm = clear_node_modules(work)
    nm.mkdir()
    (nm / SHADOW_MARK).write_text(f"{src}\n")
    for entry in sorted(os.listdir(src)):
        if entry in (".cache", ".remotion"):
            continue
        os.symlink(src / entry, nm / entry)
    log(f"linked node_modules entries from {src} (read-only reuse)")
    shells = sorted(glob.glob(str(src / ".remotion" / "chrome-headless-shell" / "*" / "chrome-headless-shell-*" / "headless_shell")))
    shells += sorted(glob.glob(str(src / ".remotion" / "chrome-headless-shell" / "*" / "chrome-headless-shell-*" / "chrome-headless-shell")))
    if shells:
        log(f"reusing its headless browser: {shells[0]}")
        return shells[0]
    log("no headless browser in that install; Remotion will download one into the work dir")
    return None


def link_cache(work):
    want = (TEMPLATE / "package.json").read_text()
    pkg = CACHE / "package.json"
    ready = pkg.exists() and pkg.read_text() == want and remotion_version(CACHE / "node_modules") == REMOTION_VERSION
    if not ready:
        if shutil.which("npm") is None:
            die("npm not found; install Node.js or pass --node-modules DIR")
        CACHE.mkdir(parents=True, exist_ok=True)
        pkg.write_text(want)
        log(f"installing Remotion {REMOTION_VERSION} once into {CACHE} (npm install) ...")
        res = subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=CACHE)
        if res.returncode != 0 or remotion_version(CACHE / "node_modules") != REMOTION_VERSION:
            die(f"npm install in {CACHE} failed (exit {res.returncode})")
    else:
        log(f"using cached install {CACHE / 'node_modules'}")
    nm = clear_node_modules(work)
    os.symlink(CACHE / "node_modules", nm)


def ffprobe(path):
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=index,codec_type,codec_name,width,height,pix_fmt,color_space,color_primaries,color_transfer,"
         "sample_rate,channels,nb_frames,duration:format=duration,size", "-of", "json", str(path)],
        capture_output=True, text=True)
    if res.returncode != 0:
        die(f"ffprobe failed on {path}: {res.stderr.strip()}")
    return json.loads(res.stdout)


def tag_bt709(path):
    tagged = path.with_name(path.stem + "-bt709" + path.suffix)
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(path), "-map", "0", "-c", "copy",
           "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart", str(tagged)]
    log("tagging bt709 afterwards: " + " ".join(cmd))
    if subprocess.run(cmd).returncode != 0:
        die(f"ffmpeg could not tag {path}")
    tagged.replace(path)


def verify(path, aspect, timing, with_audio):
    info = ffprobe(path)
    w, h = ASPECTS[aspect]
    fps = timing["fps"]
    want = timing["dur"] / fps
    problems = []
    vs = [s for s in info["streams"] if s["codec_type"] == "video"]
    aus = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if len(vs) != 1:
        problems.append(f"{len(vs)} video streams")
        return info, problems
    v = vs[0]
    if v.get("codec_name") != "h264" or (v.get("width"), v.get("height")) != (w, h) or v.get("pix_fmt") != "yuv420p":
        problems.append(f"video is {v.get('codec_name')} {v.get('width')}x{v.get('height')} {v.get('pix_fmt')}, want h264 {w}x{h} yuv420p")
    nb = v.get("nb_frames")
    if nb is not None and nb.isdigit() and int(nb) != int(timing["dur"]):
        problems.append(f"{nb} video frames, want {timing['dur']}")
    vd = float(v.get("duration") or info["format"]["duration"])
    if abs(vd - want) > 0.5 / fps:
        problems.append(f"video lasts {vd:.4f} s, want {want:.4f} s")
    if with_audio:
        if len(aus) != 1:
            problems.append(f"{len(aus)} audio streams, want 1")
        else:
            a = aus[0]
            if a.get("codec_name") != "aac" or a.get("sample_rate") != "48000":
                problems.append(f"audio is {a.get('codec_name')} {a.get('sample_rate')} Hz, want aac 48000")
            ad = float(a.get("duration") or 0)
            if abs(ad - want) > 1.0 / fps + 0.03:
                problems.append(f"audio lasts {ad:.4f} s, want {want:.4f} s")
    return info, problems


def colour_tagged(info):
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    return all(v.get(k) == "bt709" for k in ("color_space", "color_primaries", "color_transfer"))


def main():
    ap = argparse.ArgumentParser(description="Render the logo sting as a standalone H.264/AAC clip from the Remotion template.")
    ap.add_argument("--spec", required=True, help="logo spec JSON from logo_spec.py")
    ap.add_argument("--timing", required=True, help="timing JSON from sting_timing.py")
    ap.add_argument("--audio", help="sting WAV from sting_audio.py (omit for a silent clip)")
    ap.add_argument("--aspect", action="append", required=True,
                    help=f"one of {', '.join(ASPECTS)}; repeat or give a comma list (9x16,16x9)")
    ap.add_argument("--out", required=True,
                    help="output .mp4 (one aspect; with several, -<aspect> is added to the name) or a directory")
    ap.add_argument("--work-dir", help="Remotion project dir to (re)use (default: a new dir under the system temp dir, removed on success)")
    ap.add_argument("--node-modules", help="reuse an existing node_modules with remotion 4.0.534 (read-only)")
    ap.add_argument("--crf", type=int, default=16, help="H.264 CRF (default 16)")
    ap.add_argument("--intro", choices=("point", "black"), default="point", help="start from a centred point of light (default) or from black")
    ap.add_argument("--gain", type=float, default=0.95, help="sting gain (default 0.95, as in the reference mix)")
    ap.add_argument("--keep-work-dir", action="store_true", help="keep the auto-created work dir after a successful render")
    args = ap.parse_args()

    aspects = parse_aspects(args.aspect)
    spec = load_json(args.spec, "spec")
    timing = load_json(args.timing, "timing")
    check_inputs(spec, timing)
    audio = Path(args.audio).expanduser().resolve() if args.audio else None
    if audio and not audio.is_file():
        die(f"--audio {audio} not found")
    if not (0 <= args.crf <= 51):
        die("--crf must be 0..51")
    for tool in ("npx", "ffprobe"):
        if shutil.which(tool) is None:
            die(f"{tool} not found on PATH")
    outs = output_paths(args.out, aspects)
    for p in outs.values():
        if inside(p, SKILL_DIR):
            die(f"refusing to write {p} inside the skill dir {SKILL_DIR}")

    auto = args.work_dir is None
    work = Path(tempfile.mkdtemp(prefix="lov-logo-sting-")) if auto else Path(args.work_dir).expanduser().resolve()
    if inside(work, SKILL_DIR):
        die(f"refusing to use a work dir inside the skill dir {SKILL_DIR}")
    log(f"work dir {work}")
    prepare_work_dir(work)

    props = {"spec": spec, "timing": timing, "gain": args.gain, "intro": args.intro}
    if audio:
        shutil.copy2(audio, work / "public" / "sting.wav")
        props["audioSrc"] = "sting.wav"
        if shutil.which("ffprobe"):
            ad = float(ffprobe(work / "public" / "sting.wav")["format"]["duration"])
            want = timing["dur"] / timing["fps"]
            if abs(ad - want) > 1.0 / timing["fps"]:
                log(f"warning: {audio.name} lasts {ad:.3f} s but the timing is {want:.3f} s; was it made from this timing?")
    (work / "props.json").write_text(json.dumps(props, ensure_ascii=False))

    browser = link_existing(work, args.node_modules) if args.node_modules else link_cache(work)

    results = []
    for aspect in aspects:
        comp = f"Sting-{aspect}"
        tmp = work / "out" / f"{comp}.mp4"
        tmp.parent.mkdir(exist_ok=True)
        cmd = ["npx", "--no-install", "remotion", "render", "src/index.ts", comp, str(tmp), "--props=props.json",
               "--codec=h264", f"--crf={args.crf}", "--pixel-format=yuv420p", "--color-space=bt709", "--log=warn"]
        if audio:
            cmd += ["--audio-codec=aac", "--audio-bitrate=320k", "--sample-rate=48000"]
        if browser:
            cmd.append(f"--browser-executable={browser}")
        log(f"rendering {comp} ({ASPECTS[aspect][0]}x{ASPECTS[aspect][1]}, {timing['dur']} frames at {timing['fps']} fps)")
        log("$ " + " ".join(cmd))
        res = subprocess.run(cmd, cwd=work)
        if res.returncode != 0 or not tmp.exists():
            die(f"remotion render failed for {comp} (exit {res.returncode}); work dir kept: {work}", 1)
        if not colour_tagged(ffprobe(tmp)):
            if shutil.which("ffmpeg") is None:
                die("output is not tagged bt709 and ffmpeg is not available to tag it")
            tag_bt709(tmp)
        info, problems = verify(tmp, aspect, timing, audio is not None)
        if problems:
            die(f"{comp} failed verification: {'; '.join(problems)}; work dir kept: {work}", 1)
        dst = outs[aspect]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp), str(dst))
        v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
        a = [s for s in info["streams"] if s["codec_type"] == "audio"]
        summary = {
            "aspect": aspect,
            "file": str(dst),
            "bytes": int(info["format"]["size"]),
            "duration": round(float(info["format"]["duration"]), 4),
            "video": f"h264 {v['width']}x{v['height']} {v.get('nb_frames')} frames bt709",
            "audio": f"aac {a[0]['sample_rate']} Hz {a[0]['channels']} ch" if a else None,
        }
        results.append(summary)
        log(f"ok {dst} ({summary['bytes'] / 1e6:.1f} MB, {summary['duration']} s)")

    if auto and not args.keep_work_dir:
        shutil.rmtree(work, ignore_errors=True)
    else:
        log(f"work dir kept: {work}")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
