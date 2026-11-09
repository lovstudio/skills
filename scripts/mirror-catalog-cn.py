#!/usr/bin/env python3
"""Mirror skills.yaml and the free Skills' documents to the Aliyun OSS objects lovstudio.cn reads.

GitHub raw is slow or unreachable from mainland China, so the China site reads
the catalog, and every free Skill's SKILL.md, README.md and skill-card.yaml,
from OSS instead. CI uploads after every catalog push and nightly; each upload
also refreshes the objects' Last-Modified, which the site treats as a heartbeat:
a copy older than 48 hours means this job stopped, and the site goes back to
GitHub first.

The bucket, object keys and sources are fixed. Nothing here changes ACLs or the
bucket policy, and the only credentials used are the STS session CI assumes
through GitHub OIDC (ALIBABA_CLOUD_* variables).

Usage:
    python3 scripts/mirror-catalog-cn.py            # validate, compare with the live mirror
    python3 scripts/mirror-catalog-cn.py --apply    # upload, then verify the public copies
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from catalog_entries import is_installable

ROOT = Path(__file__).resolve().parent.parent
BUCKET = "lovstudio-downloads"
REGION = "cn-hangzhou"
KEY = "catalogs/skills.yaml"
SOURCE = "https://raw.githubusercontent.com/lovstudio/skills/main/skills.yaml"
PUBLIC_BASE = f"https://{BUCKET}.oss-{REGION}.aliyuncs.com"
PUBLIC_URL = f"{PUBLIC_BASE}/{KEY}"
DOCS_PREFIX = "catalogs/skills"
DOCS_SOURCE = "https://raw.githubusercontent.com/lovstudio/skills/main/skills"
DOC_TYPES = {
    "SKILL.md": "text/markdown; charset=utf-8",
    "README.md": "text/markdown; charset=utf-8",
    "skill-card.yaml": "application/yaml; charset=utf-8",
}
SKILL_NAME = re.compile(r"[a-z0-9][a-z0-9-]*", re.ASCII)
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


def document_plan(catalog_text: str) -> tuple[list[tuple[str, bytes]], list[str]]:
    """Objects to upload and keys to delete for every Skill mirrored under ./skills/.

    These are the entries lovstudio.cn may read from OSS. A document the mirror no
    longer has is deleted, so the site never serves a copy its source dropped.
    """
    uploads, deletes = [], []
    for entry in yaml.safe_load(catalog_text)["skills"]:
        if entry.get("test") or not is_installable(entry):
            continue
        name = entry["name"]
        if not SKILL_NAME.fullmatch(name):
            raise ValueError(f"skill name cannot be an object key: {name!r}")
        for file in DOC_TYPES:
            path = ROOT / "skills" / name / file
            if path.is_symlink():
                raise ValueError(f"refusing to publish a symlink: skills/{name}/{file}")
            key = f"{DOCS_PREFIX}/{name}/{file}"
            if path.is_file():
                uploads.append((key, path.read_bytes()))
            else:
                deletes.append(key)
    return uploads, deletes


def document_request_fields(key: str, body: bytes, commit: str) -> dict:
    relative = key.removeprefix(f"{DOCS_PREFIX}/")
    return {
        "content_type": DOC_TYPES[relative.rsplit("/", 1)[1]],
        "cache_control": "public, max-age=600, stale-while-revalidate=3600",
        "metadata": {
            "source": f"{DOCS_SOURCE}/{relative}",
            "source-sha256": hashlib.sha256(body).hexdigest(),
            "source-commit": commit,
        },
    }


def object_request_fields(digest: str, commit: str) -> dict:
    return {
        "content_type": "application/yaml; charset=utf-8",
        "cache_control": "public, max-age=600, stale-while-revalidate=3600",
        "metadata": {"source": SOURCE, "source-sha256": digest, "source-commit": commit},
    }


def oss_client():
    # Imported here: the render job runs this module's tests without the OSS SDK.
    import alibabacloud_oss_v2 as oss

    config = oss.config.load_default()
    config.region = REGION
    config.credentials_provider = oss.credentials.StaticCredentialsProvider(
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"],
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"],
        os.environ["ALIBABA_CLOUD_SECURITY_TOKEN"],
    )
    return oss, oss.Client(config)


def upload(body: bytes, digest: str, commit: str) -> None:
    oss, client = oss_client()
    client.put_object(
        oss.PutObjectRequest(bucket=BUCKET, key=KEY, body=body, **object_request_fields(digest, commit))
    )


def upload_documents(uploads: list[tuple[str, bytes]], deletes: list[str], commit: str) -> None:
    oss, client = oss_client()

    def put(item: tuple[str, bytes]) -> None:
        key, body = item
        client.put_object(oss.PutObjectRequest(bucket=BUCKET, key=key, body=body, **document_request_fields(key, body, commit)))

    def delete(key: str) -> None:
        client.delete_object(oss.DeleteObjectRequest(bucket=BUCKET, key=key))

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(put, uploads))
        list(pool.map(delete, deletes))


def public_document_mismatches(uploads: list[tuple[str, bytes]], deletes: list[str], cache_buster: str) -> list[str]:
    """Keys whose anonymous copy is not what this commit should publish."""

    def read(key: str) -> bytes | None:
        # Hundreds of reads cross the Pacific from CI; retry dropped connections, not answers.
        for attempt in range(3):
            try:
                with urllib.request.urlopen(f"{PUBLIC_BASE}/{key}?verify={cache_buster}", timeout=30) as response:
                    return response.read()
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    return None
                raise
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                if attempt == 2:
                    raise
        raise AssertionError("unreachable")

    def uploaded(item: tuple[str, bytes]) -> str | None:
        key, body = item
        return None if read(key) == body else key

    def deleted(key: str) -> str | None:
        return None if read(key) is None else key

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(uploaded, uploads)) + list(pool.map(deleted, deletes))
    return [key for key in results if key]


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
    uploads, deletes = document_plan(body.decode("utf-8"))
    summary.update(documents=len(uploads), deleted_documents=len(deletes))
    if not argv:
        summary["mirror_sha256"] = public_sha256(digest)
        summary["documents_out_of_sync"] = len(public_document_mismatches(uploads, deletes, digest))
        print(json.dumps(summary))
        in_sync = summary["mirror_sha256"] == digest and not summary["documents_out_of_sync"]
        print("DRY RUN: in sync" if in_sync else "DRY RUN: mirror differs; no upload performed")
        return 0

    # Documents go first so a fresh catalog means they were attempted in the same run. Their
    # failure must not stop the catalog upload: its Last-Modified is the heartbeat the site checks.
    try:
        upload_documents(uploads, deletes, summary["commit"])
        mismatches = public_document_mismatches(uploads, deletes, digest)
        document_error = f"{len(mismatches)} public copies differ, e.g. {mismatches[:5]}" if mismatches else None
    except Exception as error:  # noqa: BLE001 - reported after the catalog upload below
        document_error = repr(error)
    upload(body, digest, summary["commit"])
    catalog_verified = public_sha256(digest) == digest
    print(json.dumps(summary))
    if not catalog_verified:
        print("Public readback SHA-256 differs from skills.yaml; the mirror is not verified", file=sys.stderr)
    if document_error:
        print(f"Skill documents are not verified: {document_error}", file=sys.stderr)
    if not catalog_verified or document_error:
        return 1
    print("APPLIED: public readback SHA-256 matches skills.yaml and every Skill document")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
