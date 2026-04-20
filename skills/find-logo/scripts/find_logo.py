#!/usr/bin/env python3
"""find-logo — fetch a brand/product logo from public sources, score candidates,
keep the best (prefer wide-aspect + transparent), archive to a per-brand dir.

Sources tried (in order):
  1. Clearbit Logo API            https://logo.clearbit.com/<domain>
  2. Favicon (Google s2, 256px)   https://www.google.com/s2/favicons?domain=<domain>&sz=256
  3. og:image / twitter:image     scraped from https://<domain>/
  4. <link rel="icon"> variants   scraped from https://<domain>/

The caller (Claude) is expected to run WebSearch as a fallback when this
script exits with status 2 (no candidates). This script itself makes no
search-engine calls — we keep the deterministic pipeline here.

Usage:
  find_logo.py --name "Anthropic"
  find_logo.py --name "Anthropic" --url https://anthropic.com
  find_logo.py --url https://anthropic.com
  find_logo.py --name "OpenAI" --out ~/.lovstudio/logo-collection
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
DEFAULT_OUT = Path.home() / ".lovstudio" / "logo-collection"
TIMEOUT = 10


# ---------- helpers ----------

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", s)
    return s.strip("-") or "logo"


def domain_from_url(url: str) -> str:
    p = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    return p.netloc or p.path


def guess_domain(name: str) -> Optional[str]:
    """Very light guess: lowercase, strip spaces, try .com. Caller may override."""
    guess = re.sub(r"\s+", "", name.lower())
    guess = re.sub(r"[^a-z0-9-]", "", guess)
    return f"{guess}.com" if guess else None


def http_get(url: str, *, binary: bool = False) -> tuple[int, bytes, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = r.read()
            return r.status, data, dict(r.headers)
    except Exception as e:
        return 0, b"", {"error": str(e)}


# ---------- image probing ----------

def sniff_format(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:3] == b"GIF":
        return "gif"
    if data[:2] == b"\xff\xd8":
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:6] in (b"<?xml ", b"<svg x") or b"<svg" in data[:256].lower():
        return "svg"
    if data[:4] == b"\x00\x00\x01\x00":
        return "ico"
    return None


def png_size(data: bytes) -> Optional[tuple[int, int]]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w = int.from_bytes(data[16:20], "big")
    h = int.from_bytes(data[20:24], "big")
    return w, h


def png_has_alpha(data: bytes) -> bool:
    # color type byte at offset 25; 4 = GA, 6 = RGBA, and tRNS chunk → has alpha
    if len(data) < 26 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    ct = data[25]
    if ct in (4, 6):
        return True
    return b"tRNS" in data[:4096]


def jpg_size(data: bytes) -> Optional[tuple[int, int]]:
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            return None
        while data[i] == 0xFF:
            i += 1
        marker = data[i]; i += 1
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return int.from_bytes(data[i+3:i+5], "big"), int.from_bytes(data[i+1:i+3], "big")
        seg_len = int.from_bytes(data[i:i+2], "big")
        i += seg_len
    return None


def svg_size(data: bytes) -> Optional[tuple[int, int]]:
    head = data[:2048].decode("utf-8", errors="ignore")
    vb = re.search(r'viewBox=["\']\s*[\-0-9.]+\s+[\-0-9.]+\s+([0-9.]+)\s+([0-9.]+)', head)
    if vb:
        return int(float(vb.group(1))), int(float(vb.group(2)))
    w = re.search(r'\bwidth=["\']([0-9.]+)', head)
    h = re.search(r'\bheight=["\']([0-9.]+)', head)
    if w and h:
        return int(float(w.group(1))), int(float(h.group(1)))
    return None


def probe(data: bytes) -> dict:
    fmt = sniff_format(data)
    size = None
    alpha = False
    if fmt == "png":
        size = png_size(data)
        alpha = png_has_alpha(data)
    elif fmt == "jpg":
        size = jpg_size(data)
    elif fmt == "svg":
        size = svg_size(data)
        alpha = True  # svg = vector, effectively transparent
    elif fmt == "webp":
        # cheap: assume alpha if VP8L or VP8X with alpha flag
        alpha = b"VP8L" in data[:64] or (b"VP8X" in data[:64] and (data[20] & 0x10) != 0)
    return {
        "format": fmt,
        "width": size[0] if size else None,
        "height": size[1] if size else None,
        "has_alpha": alpha,
        "bytes": len(data),
    }


# ---------- og:image scraper ----------

class MetaIconParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.og_image: Optional[str] = None
        self.tw_image: Optional[str] = None
        self.icons: list[tuple[str, Optional[str]]] = []  # (href, sizes)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            prop = (a.get("property") or a.get("name") or "").lower()
            if prop == "og:image" and a.get("content"):
                self.og_image = a["content"]
            elif prop == "twitter:image" and a.get("content"):
                self.tw_image = a["content"]
        elif tag == "link":
            rel = (a.get("rel") or "").lower()
            if "icon" in rel and a.get("href"):
                self.icons.append((a["href"], a.get("sizes")))


def scrape_page_images(page_url: str) -> list[str]:
    status, body, _ = http_get(page_url)
    if status != 200 or not body:
        return []
    parser = MetaIconParser()
    try:
        parser.feed(body.decode("utf-8", errors="ignore"))
    except Exception:
        return []
    urls: list[str] = []
    for u in (parser.og_image, parser.tw_image):
        if u:
            urls.append(urllib.parse.urljoin(page_url, u))
    # icons: prefer the largest declared sizes first
    def icon_rank(it):
        sz = it[1] or ""
        m = re.search(r"(\d+)x(\d+)", sz)
        return -(int(m.group(1)) if m else 0)
    for href, _ in sorted(parser.icons, key=icon_rank):
        urls.append(urllib.parse.urljoin(page_url, href))
    # de-dup, preserve order
    seen = set(); out = []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out


# ---------- scoring ----------

def score(info: dict) -> float:
    """Higher is better. Rewards wide aspect, alpha, reasonable size, vector."""
    if not info.get("format"):
        return -1e9
    s = 0.0
    fmt = info["format"]
    if fmt == "svg":
        s += 40
    elif fmt == "png":
        s += 20
    elif fmt == "webp":
        s += 10
    elif fmt == "ico":
        s -= 20
    elif fmt == "jpg":
        s -= 10

    if info.get("has_alpha"):
        s += 30

    w, h = info.get("width"), info.get("height")
    if w and h and h > 0:
        ratio = w / h
        if ratio >= 2:
            s += 25  # long / banner
        elif ratio >= 1.3:
            s += 10
        elif 0.9 <= ratio <= 1.1:
            s -= 5   # square — OK but not preferred
        else:
            s -= 15  # tall

        short = min(w, h)
        if short >= 128:
            s += 15
        elif short >= 64:
            s += 5
        elif short < 32:
            s -= 20

    b = info.get("bytes") or 0
    if b < 400:
        s -= 30  # probably a stub
    return s


# ---------- pipeline ----------

@dataclass
class Candidate:
    source: str       # clearbit / favicon / og / icon-link / manual
    url: str
    data: bytes
    info: dict
    score: float

    def ext(self) -> str:
        return self.info.get("format") or "bin"


def try_candidates(domain: str) -> list[Candidate]:
    cands: list[Candidate] = []

    def add(source: str, url: str) -> None:
        status, data, _ = http_get(url)
        if status != 200 or not data:
            return
        info = probe(data)
        if not info["format"]:
            return
        cands.append(Candidate(source, url, data, info, score(info)))

    # 1. Clearbit
    add("clearbit", f"https://logo.clearbit.com/{domain}")

    # 2. og:image + link[rel=icon] on https://<domain>/
    for src_url in scrape_page_images(f"https://{domain}/"):
        add("page", src_url)
        if len(cands) >= 8:
            break

    # 3. Google s2 favicon (always resolves, ranked low)
    add("google-s2", f"https://www.google.com/s2/favicons?domain={domain}&sz=256")

    return cands


def archive(best: Candidate, alts: list[Candidate], slug: str, brand_name: str,
            source_domain: str, out_root: Path, keep_alts: int) -> Path:
    brand_dir = out_root / slug
    brand_dir.mkdir(parents=True, exist_ok=True)
    primary = brand_dir / f"logo.{best.ext()}"
    primary.write_bytes(best.data)

    meta = {
        "brand": brand_name,
        "slug": slug,
        "source_domain": source_domain,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "primary": {
            "file": primary.name,
            "source": best.source,
            "url": best.url,
            "score": round(best.score, 2),
            **best.info,
        },
        "alternates": [],
    }

    for i, c in enumerate(alts[:keep_alts]):
        alt_name = f"alt-{i+1}.{c.ext()}"
        (brand_dir / alt_name).write_bytes(c.data)
        meta["alternates"].append({
            "file": alt_name,
            "source": c.source,
            "url": c.url,
            "score": round(c.score, 2),
            **c.info,
        })

    (brand_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return brand_dir


def main() -> int:
    ap = argparse.ArgumentParser(description="Find & archive a brand logo.")
    ap.add_argument("--name", help="Brand / product name")
    ap.add_argument("--url", help="Official URL or domain (overrides name guess)")
    ap.add_argument("--slug", help="Override archive slug (default: slugified name/domain)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help=f"Archive root (default: {DEFAULT_OUT})")
    ap.add_argument("--keep-alts", type=int, default=2, help="How many runner-up candidates to keep")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON to stdout")
    args = ap.parse_args()

    if not args.name and not args.url:
        ap.error("need --name or --url")

    domain = domain_from_url(args.url) if args.url else guess_domain(args.name)
    if not domain:
        print("ERROR: could not derive domain; pass --url", file=sys.stderr)
        return 2

    brand_name = args.name or domain
    slug = args.slug or slugify(args.name or domain.split(".")[0])
    out_root = Path(os.path.expanduser(args.out))

    cands = try_candidates(domain)
    if not cands:
        msg = {"status": "no-candidates", "domain": domain, "brand": brand_name,
               "hint": "fall back to WebSearch + manual --url"}
        print(json.dumps(msg) if args.json else f"no candidates for {domain} — try WebSearch")
        return 2

    cands.sort(key=lambda c: c.score, reverse=True)
    best, *rest = cands
    brand_dir = archive(best, rest, slug, brand_name, domain, out_root, args.keep_alts)

    result = {
        "status": "ok",
        "brand": brand_name,
        "slug": slug,
        "dir": str(brand_dir),
        "primary": {
            "file": f"logo.{best.ext()}",
            "source": best.source,
            "score": round(best.score, 2),
            **best.info,
        },
        "alternates_kept": min(len(rest), args.keep_alts),
    }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        p = result["primary"]
        print(f"✓ {brand_name} → {brand_dir}")
        print(f"  primary: {p['file']}  ({p.get('width')}x{p.get('height')}, "
              f"alpha={p['has_alpha']}, src={p['source']}, score={p['score']})")
        if result["alternates_kept"]:
            print(f"  +{result['alternates_kept']} alternates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
