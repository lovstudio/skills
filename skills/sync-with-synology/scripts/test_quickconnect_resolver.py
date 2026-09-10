#!/usr/bin/env python3
"""Unit test for the QuickConnect relay resolver success path."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import requests


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def get(self, url, **kwargs):
        return FakeResponse({"success": True})

    def post(self, url, **kwargs):
        if url == "https://global.quickconnect.cn/Serv.php":
            return FakeResponse([{
                "errno": 0,
                "server": {
                    "serverID": "my-id",
                    "pingpong_path": "/webman/pingpong.cgi?action=cors&quickconnect=true",
                },
                "env": {"control_host": "control.example", "relay_region": ""},
            }])
        if url == "https://control.example/Serv.php":
            return FakeResponse([{
                "errno": 0,
                "server": {
                    "serverID": "my-id",
                    "pingpong_path": "/webman/pingpong.cgi?action=cors&quickconnect=true",
                },
                "env": {"control_host": "control.example", "relay_region": "us1"},
            }])
        raise AssertionError(f"unexpected URL: {url}")


def load_module():
    path = Path(__file__).with_name("synology_cli.py")
    spec = importlib.util.spec_from_file_location("synology_cli", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    with patch.object(requests, "Session", return_value=FakeSession()):
        origin, headers, session = module.resolve_quickconnect(
            "my-id", "cn", verify=False, timeout=5
        )
    assert origin == "https://my-id.us1.quickconnect.cn", origin
    assert headers["Origin"] == "https://my-id.quickconnect.cn", headers
    assert session is not None
    print("PASS: QuickConnect relay resolver success path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
