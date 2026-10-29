#!/usr/bin/env python3
"""Mirror skills.yaml to the Aliyun OSS object that lovstudio.cn reads.

GitHub raw is slow or unreachable from mainland China, so the China site reads
the catalog from OSS instead. CI uploads after every catalog push and nightly;
each upload also refreshes the object's Last-Modified, which the site treats as
a heartbeat: a copy older than 48 hours means this job stopped, and the site
goes back to GitHub first.

The bucket, object key and source are fixed. Nothing here changes ACLs or the
bucket policy, and the only credentials used are the STS session CI assumes
through GitHub OIDC (ALIBABA_CLOUD_* variables).

Usage:
    python3 scripts/mirror-catalog-cn.py            # validate, compare with the live mirror
    python3 scripts/mirror-catalog-cn.py --apply    # upload, then verify the public copy
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BUCKET = "lovstudio-downloads"
REGION = "cn-hangzhou"
KEY = "catalogs/skills.yaml"
SOURCE = "https://raw.githubusercontent.com/lovstudio/skills/main/skills.yaml"
PUBLIC_URL = f"https://{BUCKET}.oss-{REGION}.aliyuncs.com/{KEY}"
# Same rule as lovstudio.ai's validateSkillsCatalog (JavaScript \w is ASCII-only).
REPO = re.compile(r"[\w.-]+/[\w.-]+", re.ASCII)


def validate(text: str) -> int:
    """Refuse anything the site would reject, so an upload can never blank the China catalog."""
    data = yaml.safe_load(text)
    skills = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(skills, list) or not skills:
        raise ValueError("skills.yaml must contain a non-empty skills list")
    for entry in skills:
        valid = (
            isinstance(entry, dict)
            and isinstance(entry.get("name"), str) and entry["name"].strip()
            and isinstance(entry.get("repo"), str) and REPO.fullmatch(entry["repo"])
            and isinstance(entry.get("description"), str) and entry["description"].strip()
        )
        if not valid:
            raise ValueError(f"invalid catalog entry: {entry.get('name') if isinstance(entry, dict) else entry!r}")
    if all(entry.get("test") is True for entry in skills):
        raise ValueError("skills.yaml has no public entries")
    return len(skills)


def object_request_fields(digest: str, commit: str) -> dict:
    return {
        "content_type": "application/yaml; charset=utf-8",
        "cache_control": "public, max-age=600, stale-while-revalidate=3600",
        "metadata": {"source": SOURCE, "source-sha256": digest, "source-commit": commit},
    }


def upload(body: bytes, digest: str, commit: str) -> None:
    # Imported here: the render job runs this module's tests without the OSS SDK.
    import alibabacloud_oss_v2 as oss

    config = oss.config.load_default()
    config.region = REGION
    config.credentials_provider = oss.credentials.StaticCredentialsProvider(
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"],
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"],
        os.environ["ALIBABA_CLOUD_SECURITY_TOKEN"],
    )
    oss.Client(config).put_object(
        oss.PutObjectRequest(bucket=BUCKET, key=KEY, body=body, **object_request_fields(digest, commit))
    )


def public_sha256(cache_buster: str) -> str:
    # The query string keeps any cache between the runner and OSS out of the check.
    with urllib.request.urlopen(f"{PUBLIC_URL}?verify={cache_buster}", timeout=30) as response:
        return hashlib.sha256(response.read()).hexdigest()


def head_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def main(argv: list[str]) -> int:
    if argv not in ([], ["--apply"]):
        print("Usage: mirror-catalog-cn.py [--apply]  (destination and source are fixed)", file=sys.stderr)
        return 2
    body = (ROOT / "skills.yaml").read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    summary = {
        "mode": "apply" if argv else "dry-run",
        "target": PUBLIC_URL,
        "skills": validate(body.decode("utf-8")),
        "bytes": len(body),
        "sha256": digest,
        "commit": head_commit(),
    }
    if not argv:
        summary["mirror_sha256"] = public_sha256(digest)
        print(json.dumps(summary))
        print("DRY RUN: in sync" if summary["mirror_sha256"] == digest else "DRY RUN: mirror differs; no upload performed")
        return 0
    upload(body, digest, summary["commit"])
    if public_sha256(digest) != digest:
        print(json.dumps(summary))
        print("Public readback SHA-256 differs from skills.yaml; the mirror is not verified", file=sys.stderr)
        return 1
    print(json.dumps(summary))
    print("APPLIED: public readback SHA-256 matches skills.yaml")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
