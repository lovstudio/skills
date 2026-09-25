#!/usr/bin/env python3
"""Unit tests for the deterministic Markdown and PicGo Server integration."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "upload_image.py"
SPEC = importlib.util.spec_from_file_location("lov_upload_image", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PicGoHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/heartbeat":
            response = {"success": True, "result": "alive"}
        elif self.path == "/upload":
            response = {
                "success": True,
                "result": [
                    "https://img.example.test/" + Path(item).name
                    for item in payload.get("list", [])
                ],
            }
        else:
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


class UploadImageTests(unittest.TestCase):
    def test_picgo_three_json_shape_is_supported(self):
        self.assertEqual(
            MODULE._extract_response_urls(
                {"origin": "/tmp/a.png", "imgUrl": "https://img.example.test/a.png"}
            ),
            ["https://img.example.test/a.png"],
        )

    def test_markdown_output_preflight_protects_source_and_dry_run_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "article.md"
            source.write_text("content", encoding="utf-8")
            same_target = argparse.Namespace(
                in_place=False,
                output=str(source),
                no_backup=False,
                force=False,
                dry_run=False,
            )
            with self.assertRaises(MODULE.UploadImageError):
                MODULE._resolve_markdown_destinations(same_target, source)

            planned = root / "new-directory" / "result.md"
            dry_run = argparse.Namespace(
                in_place=False,
                output=str(planned),
                no_backup=False,
                force=False,
                dry_run=True,
            )
            output, backup = MODULE._resolve_markdown_destinations(dry_run, source)
            self.assertEqual(output, planned.resolve())
            self.assertIsNone(backup)
            self.assertFalse(planned.parent.exists())

    def test_markdown_scan_deduplicates_and_skips_remote_and_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "图 片.png"
            image.write_bytes(b"png")
            markdown = root / "article.md"
            text = (
                "![一](<图 片.png>)\n"
                "![远程](https://example.com/a.png)\n"
                "<img src=\"%E5%9B%BE%20%E7%89%87.png\">\n"
                "`![代码](图%20片.png)`\n"
                "```md\n![围栏](图%20片.png)\n```\n"
            )
            resolved = MODULE.resolve_markdown_occurrences(text, markdown)
            self.assertEqual(len(resolved), 2)
            self.assertEqual(MODULE.unique_paths(resolved), [image.resolve()])
            rewritten = MODULE.rewrite_markdown(
                text,
                resolved,
                {str(image.resolve()): "https://cdn.test/image.png"},
            )
            self.assertIn("![一](<https://cdn.test/image.png>)", rewritten)
            self.assertIn('<img src="https://cdn.test/image.png">', rewritten)
            self.assertIn("`![代码](图%20片.png)`", rewritten)
            self.assertIn("![围栏](图%20片.png)", rewritten)

    def test_reference_and_wiki_images_are_rewritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.png").write_bytes(b"a")
            (root / "b.png").write_bytes(b"b")
            markdown = root / "article.md"
            text = "![图][hero]\n[hero]: a.png \"标题\"\n![[b.png|示意图]]\n"
            resolved = MODULE.resolve_markdown_occurrences(text, markdown)
            urls = {
                str((root / "a.png").resolve()): "https://cdn.test/a.png",
                str((root / "b.png").resolve()): "https://cdn.test/b.png",
            }
            rewritten = MODULE.rewrite_markdown(text, resolved, urls)
            self.assertIn('[hero]: https://cdn.test/a.png "标题"', rewritten)
            self.assertIn("![示意图](https://cdn.test/b.png)", rewritten)

    def test_missing_reference_fails_before_upload(self):
        with tempfile.TemporaryDirectory() as temporary:
            markdown = Path(temporary) / "article.md"
            with self.assertRaises(MODULE.UploadImageError):
                MODULE.resolve_markdown_occurrences("![x](missing.png)", markdown)

    def test_picgo_server_contract_preserves_input_order(self):
        server = HTTPServer(("127.0.0.1", 0), PicGoHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                paths = [Path(temporary) / "a.png", Path(temporary) / "b.png"]
                for path in paths:
                    path.write_bytes(b"x")
                results = MODULE.upload_via_server(
                    paths, "http://127.0.0.1:%d" % server.server_port, 3, None
                )
                self.assertEqual(
                    [result.url for result in results],
                    ["https://img.example.test/a.png", "https://img.example.test/b.png"],
                )
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
