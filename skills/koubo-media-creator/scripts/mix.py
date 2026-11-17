#!/usr/bin/env python3
"""Mix the cut voice with one continuous music bed and point the timeline at the result (BGM goes last).

usage: mix.py --public work/remotion/public [--bgm music/bed.mp3] [--bgm-offset 0] [--bgm-lufs -32]
              [--target -16] [--peak -1.5] [--duck 6] [--sting work/sting/sting.wav] [--sting-gain 0.40]

- voice: high-pass 70 Hz, gentle compression, then a STATIC gain to --target LUFS-I (measured, not dynamic loudnorm);
- music: one file, looped with a 2 s crossfade only if shorter than the film, faded in/out, set to --bgm-lufs
  and side-chain ducked by about --duck dB while the author speaks; it keeps playing under the legacy follow card;
- outro: with --sting (lov-logo-sting media end, build.py --outro) the music fades out in the 1.2 s before
  timeline.end.from, nothing plays under the outro, and the sting is summed sample-exact at end.from at --sting-gain
  before the limiter; the limiter defaults to -3.0 dBTP (0.95 gain pushed AAC-encoded films past 0 dBFS);
- master: sum, true-peak limiter at --peak dBTP, AAC 256 kbps → public/audio/mix.m4a, length = timeline frames;
- writes timeline.audio = "audio/mix.m4a" and prints the measured loudness of the master.
Without --bgm the voice alone is mastered (allowed for a first review; the delivery needs a music bed).
"""
import argparse
import json
import re
import subprocess
from pathlib import Path


def loudness(path, filt=""):
    chain = (filt + "," if filt else "") + "ebur128=peak=true"
    out = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path), "-af", chain, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summary = out[out.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary)
    return i, float(tp.group(1)) if tp else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--public", required=True)
    ap.add_argument("--bgm")
    ap.add_argument("--bgm-offset", type=float, default=0.0, help="seconds to skip into the music file")
    ap.add_argument("--bgm-lufs", type=float, default=-32.0)
    ap.add_argument("--target", type=float, default=-16.0)
    ap.add_argument("--peak", type=float, default=None, help="true-peak limiter dBFS (default -1.5; -3.0 with --sting)")
    ap.add_argument("--duck", type=float, default=6.0)
    ap.add_argument("--sting", help="lov-logo-sting sting.wav: summed at timeline.end.from; the music fades out before it")
    ap.add_argument("--sting-gain", type=float, default=0.40, help="sting gain in the pre-master mix (shared outro: 0.40)")
    a = ap.parse_args()
    if a.peak is None:
        a.peak = -3.0 if a.sting else -1.5
    pub = Path(a.public)
    tlp = pub / "data" / "timeline.json"
    tl = json.loads(tlp.read_text())
    dur = tl["durationInFrames"] / tl["fps"]
    speech = tl["speechFrames"] / tl["fps"]
    voice = pub / "audio" / "voice.wav"
    chain = "highpass=f=70,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=1"
    vi, _ = loudness(voice, chain)
    vgain = a.target - vi
    work = pub / "audio"
    vproc = work / "voice.proc.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(voice), "-af", f"{chain},volume={vgain:.2f}dB,apad",
                    "-t", f"{dur:.4f}", "-ar", "48000", "-ac", "2", str(vproc)], check=True)
    out = work / "mix.m4a"
    sting_at = tl["end"]["from"] / tl["fps"]
    sting_in, sting_graph = [], ""
    if a.sting:
        ms = int(round(sting_at * 1000))
        sting_in = ["-i", a.sting]
        sting_graph = f"aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume={a.sting_gain},apad"
    lim = 10 ** (a.peak / 20)
    if a.bgm:
        bed = work / "bed.wav"
        src_len = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                                 "csv=p=0", a.bgm]).decode()) - a.bgm_offset
        if src_len >= dur:
            graph = f"[0:a]atrim={a.bgm_offset}:{a.bgm_offset + dur:.4f},asetpts=PTS-STARTPTS[m]"
            ins = ["-i", a.bgm]
        else:  # loop with a 2 s crossfade, never a hard restart
            n = int(dur // max(1.0, src_len - 2)) + 2
            ins = []
            for _ in range(n):
                ins += ["-ss", str(a.bgm_offset), "-i", a.bgm]
            graph, prev = "", "[0:a]"
            for k in range(1, n):
                graph += f"{prev}[{k}:a]acrossfade=d=2:c1=tri:c2=tri[x{k}];"
                prev = f"[x{k}]"
            graph += f"{prev}atrim=0:{dur:.4f},asetpts=PTS-STARTPTS[m]"
        if a.sting:
            graph += f";[m]afade=t=in:d=0.8,afade=t=out:st={max(0, sting_at - 1.2):.3f}:d=1.2[mo]"
        else:
            graph += f";[m]afade=t=in:d=0.8,afade=t=out:st={max(0, dur - 1.6):.3f}:d=1.6[mo]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", graph, "-map", "[mo]", "-ar", "48000",
                        "-ac", "2", str(bed)], check=True)
        bi, _ = loudness(bed)
        bgain = a.bgm_lufs - bi
        thr = 10 ** ((a.target - 18) / 20)
        ratio = max(1.5, 1 + a.duck / 4)
        graph = (f"[1:a]volume={bgain:.2f}dB[b];[0:a]asplit[v][sc];"
                 f"[b][sc]sidechaincompress=threshold={thr:.4f}:ratio={ratio:.2f}:attack=20:release=350[bd];"
                 + (f"[2:a]{sting_graph}[st];[v][bd][st]amix=inputs=3" if a.sting else "[v][bd]amix=inputs=2")
                 + f":normalize=0:duration=first,alimiter=limit={lim:.4f}:level=disabled[o]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(vproc), "-i", str(bed), *sting_in, "-filter_complex", graph,
                        "-map", "[o]", "-t", f"{dur:.4f}", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", str(out)], check=True)
    else:
        if a.sting:
            graph = (f"[1:a]{sting_graph}[st];[0:a][st]amix=inputs=2:normalize=0:duration=first,"
                     f"alimiter=limit={lim:.4f}:level=disabled[o]")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(vproc), *sting_in, "-filter_complex", graph, "-map", "[o]",
                            "-t", f"{dur:.4f}", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", str(out)], check=True)
        else:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(vproc), "-af", f"alimiter=limit={lim:.4f}:level=disabled",
                            "-t", f"{dur:.4f}", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", str(out)], check=True)
    mi, mtp = loudness(out)
    tl["audio"] = "audio/mix.m4a"
    tlp.write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    print(json.dumps({"mix": str(out), "seconds": round(dur, 2), "speech_seconds": round(speech, 2),
                      "voice_gain_db": round(vgain, 2), "master_lufs_i": mi, "master_true_peak_dbfs": mtp,
                      "bgm": a.bgm or None, "sting": a.sting or None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
