#!/usr/bin/env python3
"""Decode every QR code in a rendered card at several scales.

Payloads are hidden by default: the report lists each code's host (for URLs)
and a short SHA-256 prefix, which is enough to compare against the expected
asset without printing personal links. Pass --show-payload to print them.

usage: verify_qr.py IMAGE [--scales 1,0.66,0.5,0.33] [--expect-count N]
                    [--expect-host HOST ...] [--expect-same-as QR.png] [--show-payload]

exit codes: 0 pass, 1 error, 2 verification failed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


def load(path: Path):
    import cv2  # noqa: WPS433 - optional dependency checked by caller
    import numpy as np

    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"cannot read image: {path.name}")
    if img.ndim == 3 and img.shape[2] == 4:  # flatten transparency onto white
        alpha = img[:, :, 3:4].astype("float32") / 255.0
        img = (img[:, :, :3] * alpha + 255 * (1 - alpha)).astype("uint8")
    return img


def decode(img) -> list[str]:
    import cv2

    detector = cv2.QRCodeDetector()
    found: list[str] = []
    try:
        ok, infos, _, _ = detector.detectAndDecodeMulti(img)
        if ok:
            found = [s for s in infos if s]
    except cv2.error:
        found = []
    if not found:
        text, _, _ = detector.detectAndDecode(img)
        if text:
            found = [text]
    return found


def describe(payload: str, show: bool) -> dict:
    parsed = urlparse(payload)
    item = {"host": parsed.netloc if parsed.scheme in ("http", "https") else None,
            "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]}
    if show:
        item["payload"] = payload
    return item


def main() -> int:
    ap = argparse.ArgumentParser(description="Decode QR codes in a card PNG at several scales.")
    ap.add_argument("image")
    ap.add_argument("--scales", default="1,0.66,0.5,0.33")
    ap.add_argument("--expect-count", type=int, default=1)
    ap.add_argument("--expect-host", action="append", default=[], help="URL host that must decode; repeatable")
    ap.add_argument("--expect-same-as", action="append", default=[],
                    help="source QR image whose payload must appear in the card; repeatable")
    ap.add_argument("--show-payload", action="store_true")
    args = ap.parse_args()

    try:
        import cv2
    except ImportError:
        print(json.dumps({"status": "unverified", "error": "OpenCV not installed (pip install opencv-python)"}))
        return 1
    try:
        img = load(Path(args.image))
        scales = [float(s) for s in args.scales.split(",") if s.strip()]
        expected_hashes = []
        for src in args.expect_same_as:
            payloads = decode(load(Path(src)))
            if not payloads:
                raise ValueError(f"source QR did not decode: {Path(src).name}")
            expected_hashes.append(describe(payloads[0], False)["sha256"])
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1

    report, failures = [], []
    for scale in scales:
        view = img if scale == 1 else cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        codes = [describe(p, args.show_payload) for p in decode(view)]
        hosts = {c["host"] for c in codes}
        hashes = {c["sha256"] for c in codes}
        entry = {"scale": scale, "pixels": [int(view.shape[1]), int(view.shape[0])], "decoded": len(codes), "codes": codes}
        problems = []
        if len(codes) < args.expect_count:
            problems.append(f"decoded {len(codes)} < expected {args.expect_count}")
        problems += [f"missing host {h}" for h in args.expect_host if h not in hosts]
        problems += [f"missing source payload {h}" for h in expected_hashes if h not in hashes]
        if problems:
            entry["problems"] = problems
            failures.append(scale)
        report.append(entry)

    status = "pass" if not failures else "fail"
    print(json.dumps({"status": status, "image": Path(args.image).name, "failed_scales": failures, "scales": report},
                     ensure_ascii=False, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
