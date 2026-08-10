#!/usr/bin/env python3
"""
Scaffold a Fumadocs documentation site for a product code repository.

Given a product source repo (local path or already-cloned dir), this creates a
sibling Fumadocs (Next.js) app configured to serve under the `/docs` base path,
ready to deploy to https://{product-id}.lovstudio.ai/docs.

It only scaffolds the shell + config. Actual page authoring is done by the agent
(reading the source repo and writing MDX into content/docs/).

Usage:
    python3 scaffold_docs.py --product-id myapp --out ./myapp-docs
    python3 scaffold_docs.py --product-id myapp --out ./myapp-docs --pm pnpm
    python3 scaffold_docs.py --product-id myapp --out ./myapp-docs --title "MyApp"

The CLI runs `create-fumadocs-app` non-interactively, then rewrites:
  - next.config.mjs  → basePath '/docs'
  - app config       → so internal links resolve under /docs
  - content/docs/    → cleared to a single placeholder index
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd=None, env=None):
    print(f"$ {' '.join(cmd)}", file=sys.stderr)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def proxy_env():
    """Inherit ClashX proxy if present — npm/git over the network need it in
    the Claude Code sandbox."""
    env = os.environ.copy()
    if "https_proxy" not in env and Path.home().exists():
        # Caller is expected to export these; we don't force-set, just pass through.
        pass
    return env


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def scaffold(product_id: str, out: Path, pm: str, title: str):
    if out.exists() and any(out.iterdir()):
        sys.exit(f"ERROR: {out} exists and is not empty")

    env = proxy_env()
    # create-fumadocs-app: Next.js + fuma-docs-mdx, no git (we manage git), install deps.
    run(
        [
            "npx", "-y", "create-fumadocs-app@latest", str(out),
            "--template", "+next+fuma-docs-mdx",
            "--pm", pm,
            "--src",
            "--install",
            "--no-git",
            "--search", "orama",
        ],
        env=env,
    )

    patch_basepath(out, title or product_id)
    reset_content(out, title or product_id)
    write_vercel_json(out)
    print(f"✓ Fumadocs site scaffolded at {out}", file=sys.stderr)
    print(f"  basePath: /docs", file=sys.stderr)
    print(f"  next: author MDX in {out}/content/docs/ from the product source", file=sys.stderr)


def patch_basepath(out: Path, title: str):
    """Set Next.js basePath to /docs so the site lives at domain/docs."""
    for name in ("next.config.mjs", "next.config.js", "next.config.ts"):
        cfg = out / name
        if cfg.exists():
            text = cfg.read_text()
            if "basePath" not in text:
                # Inject basePath into the exported config object.
                text = re.sub(
                    r"(const config\s*=\s*\{)",
                    r"\1\n  basePath: '/docs',",
                    text,
                    count=1,
                )
                if "basePath" not in text:
                    # Fallback: handle `export default { ... }` shape.
                    text = re.sub(
                        r"(export default\s*\{)",
                        r"\1\n  basePath: '/docs',",
                        text,
                        count=1,
                    )
            cfg.write_text(text)
            return
    print("WARN: no next.config.* found; set basePath '/docs' manually", file=sys.stderr)


def reset_content(out: Path, title: str):
    """Clear the demo content to a single index page placeholder."""
    docs = out / "content" / "docs"
    if docs.exists():
        for p in docs.iterdir():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
    docs.mkdir(parents=True, exist_ok=True)

    (docs / "index.mdx").write_text(
        f"""---
title: {title}
description: {title} documentation
---

Welcome to the **{title}** documentation.

> This is a placeholder. The agent will replace it with real pages generated
> from the product source code.
"""
    )
    (docs / "meta.json").write_text(
        json.dumps({"title": title, "pages": ["index"]}, ensure_ascii=False, indent=2)
    )


def write_vercel_json(out: Path):
    """Next.js handles routing natively; deploy skill reads this if present.
    Kept minimal — Next.js does not need SPA rewrites."""
    # Intentionally no rewrites for Next.js. Leave a marker file empty-safe.
    pass


def main():
    ap = argparse.ArgumentParser(description="Scaffold a Fumadocs docs site under /docs")
    ap.add_argument("--product-id", required=True, help="Product id → subdomain {id}.lovstudio.ai")
    ap.add_argument("--out", required=True, help="Output directory for the docs site")
    ap.add_argument("--pm", default="pnpm", choices=["pnpm", "npm", "yarn", "bun"])
    ap.add_argument("--title", default="", help="Human-facing product title (defaults to product-id)")
    args = ap.parse_args()

    product_id = slugify(args.product_id)
    if not product_id:
        sys.exit("ERROR: --product-id slugifies to empty")
    out = Path(os.path.expanduser(args.out)).resolve()

    scaffold(product_id, out, args.pm, args.title)


if __name__ == "__main__":
    main()
