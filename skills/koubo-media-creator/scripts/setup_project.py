#!/usr/bin/env python3
"""Install the Remotion starter into an episode (work/remotion) with fonts and public folders.

usage: setup_project.py EPISODE_DIR [--sans FONT.ttf] [--display FONT.ttf] [--no-install] [--force]

Copies assets/starter to EPISODE_DIR/work/remotion (refuses to overwrite src/ unless --force), creates
public/{media,audio,broll,img,data,fonts}, copies the caption/heading font (a variable CJK sans with weight
900, e.g. Noto Sans SC) to public/fonts/sans.ttf and a display face to public/fonts/display.ttf (falls back to
the sans), writes a one-second silence for the placeholder timeline, and runs `pnpm install`.
Font search order without flags: the Profile record `fonts`, then common user/system font folders.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CANDIDATES = {
    "sans": ["NotoSansSC-VariableFont_wght.ttf", "NotoSansSC-Black.ttf", "SourceHanSansSC-Heavy.otf", "AlibabaPuHuiTi-3-105-Heavy.ttf"],
    "display": ["SmileySans-Oblique.ttf", "SmileySans-Oblique.otf"],
}
FOLDERS = [Path.home() / "Library/Fonts", Path("/Library/Fonts"), Path.home() / ".local/share/fonts", Path("/usr/share/fonts")]


def find(kind):
    for name in CANDIDATES[kind]:
        for d in FOLDERS:
            hit = next(iter(d.rglob(name)), None) if d.exists() else None
            if hit:
                return hit
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("episode")
    ap.add_argument("--sans")
    ap.add_argument("--display")
    ap.add_argument("--no-install", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    ep = Path(a.episode)
    dst = ep / "work" / "remotion"
    if (dst / "src").exists() and not a.force:
        print(f"{dst}/src exists; keeping it (pass --force to reset the template)")
    else:
        # template code and config only; an episode's public/data (timeline, cover) is never reset
        keep = {"timeline.json", "cover.json"} if (dst / "public" / "data").exists() else set()
        shutil.copytree(SKILL / "assets" / "starter", dst, dirs_exist_ok=True,
                        ignore=lambda d, names: [n for n in names if n in keep and Path(d).name == "data"])
    pub = dst / "public"
    for d in ("media", "audio", "broll", "img", "data", "fonts"):
        (pub / d).mkdir(parents=True, exist_ok=True)
    sans = Path(a.sans) if a.sans else find("sans")
    disp = Path(a.display) if a.display else find("display") or sans
    if not sans or not sans.exists():
        raise SystemExit("no heavy CJK sans found: pass --sans <Noto Sans SC variable .ttf or similar>")
    shutil.copy2(sans, pub / "fonts" / "sans.ttf")
    shutil.copy2(disp, pub / "fonts" / "display.ttf")
    if not (pub / "audio" / "silence.wav").exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "1",
                        str(pub / "audio" / "silence.wav")], check=True)
    if not a.no_install:
        subprocess.run(["pnpm", "install", "--prefer-offline"], cwd=dst, check=True)
    print({"project": str(dst), "sans": sans.name, "display": disp.name})


if __name__ == "__main__":
    main()
