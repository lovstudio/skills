#!/usr/bin/env python3
"""Refresh lovstudio.ai after main's catalog changes and confirm the commit it read.

The site caches skills.yaml and the free Skill documents mirrored under skills/ for
ten minutes. It reads both at the commit main points to and answers /api/revalidate
with that commit (lovstudio/lovstudio-home#148), so a refresh can follow a push at
once. A response without the commit means the site fell back to
raw.githubusercontent.com's main, which keeps the previous file for up to five
minutes: wait that out, then refresh once more.

CI-only: reads REVALIDATE_SECRET (the site's secret) and GH_TOKEN from the environment.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

SITE = "https://lovstudio.ai"
REPO = "lovstudio/skills"
# The publish step's catalog refresh without its per-Skill tags.
BODY = {"tags": ["skills-index"], "paths": ["/skills"]}
ATTEMPTS = 4
RETRY_DELAY = 15
RAW_MAIN_MAX_AGE = 300
TIMEOUT = 120
# Cloudflare in front of lovstudio.ai answers Python's default User-Agent with 403 (error 1010).
USER_AGENT = "lovstudio-skills-ci (+https://github.com/lovstudio/skills)"


class Rejected(Exception):
    """The site refused the secret, so another attempt cannot succeed."""


def revalidate(secret: str) -> dict:
    request = urllib.request.Request(
        f"{SITE}/api/revalidate",
        data=json.dumps(BODY).encode(),
        headers={"content-type": "application/json", "user-agent": USER_AGENT, "x-revalidate-secret": secret},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        body = " ".join(error.read(300).decode(errors="replace").split())
        message = f"{SITE}/api/revalidate answered {error.code}: {body}"
        if error.code == 401:
            raise Rejected(message) from None
        raise RuntimeError(message) from None


def main_commit(token: str) -> str:
    headers = {"Accept": "application/vnd.github.sha", "User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com/repos/{REPO}/commits/main", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode().strip()


def annotate(level: str, title: str, message: str) -> None:
    print(f"::{level} title={title}::{message}")


def report(text: str) -> None:
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(text + "\n")


def main() -> int:
    secret = os.environ.get("REVALIDATE_SECRET", "")
    if not secret:
        annotate("warning", "Website not refreshed",
                 "Set the LOVSTUDIO_REVALIDATE_SECRET repository secret to lovstudio.ai's REVALIDATE_SECRET.")
        report("lovstudio.ai was not refreshed: the `LOVSTUDIO_REVALIDATE_SECRET` secret is not set.")
        return 0
    token = os.environ.get("GH_TOKEN", "")
    waited = False
    problem = ""
    for attempt in range(1, ATTEMPTS + 1):
        delay = RETRY_DELAY
        try:
            result = revalidate(secret)
            read = (result.get("catalog_commits") or {}).get(REPO)
            head = main_commit(token)
        except Rejected as error:
            annotate("error", "Website refresh rejected",
                     f"{error} LOVSTUDIO_REVALIDATE_SECRET must equal the site's REVALIDATE_SECRET.")
            return 1
        except (OSError, RuntimeError, ValueError) as error:
            problem = str(error)
        else:
            sync = result.get("pricing_sync")
            if isinstance(sync, dict) and sync.get("status") == "deferred":
                annotate("warning", "Catalog pricing sync deferred",
                         "lovstudio.ai could not sync Skill pricing from the catalog; see the site's logs.")
            done = f"Pricing sync: `{json.dumps(sync, separators=(',', ':'))}`."
            if read == head:
                report(f"lovstudio.ai read `{REPO}@{head[:7]}`, the commit `main` points to. {done}")
                return 0
            if read is None and waited:
                annotate("warning", "Website commit not confirmed",
                         f"lovstudio.ai named no {REPO} commit, so it reads main through raw.githubusercontent.com; "
                         "check the site's GITHUB_TOKEN. It was refreshed after the raw cache expired.")
                report(f"lovstudio.ai refreshed from raw `main` after {RAW_MAIN_MAX_AGE} s, commit unconfirmed. {done}")
                return 0
            if read is None:
                problem = "lovstudio.ai named no commit, so it read raw main, which can lag a push by 5 minutes"
                delay = RAW_MAIN_MAX_AGE
                waited = True
            else:
                problem = f"lovstudio.ai read {read[:7]} while main is {head[:7]}"
        if attempt < ATTEMPTS:
            print(f"Attempt {attempt}: {problem}; refreshing again in {delay} s.")
            time.sleep(delay)
    annotate("error", "Website reads an old catalog", f"After {ATTEMPTS} refreshes: {problem}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
