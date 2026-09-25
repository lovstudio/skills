from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "table2image", ROOT / "scripts" / "table2image.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05"
    b"\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
)


class Handler(BaseHTTPRequestHandler):
    payload = None
    authorization = None

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        Handler.payload = json.loads(self.rfile.read(length))
        Handler.authorization = self.headers.get("Authorization")
        body = json.dumps(
            {
                "image_url": f"http://127.0.0.1:{self.server.server_port}/image.png",
                "format": "png",
                "width": 1520,
                "height": 344,
                "layout_width": 760,
                "model": "Asge8oUog7I",
                "credits_spent": 3,
                "credits_remaining": 97,
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(PNG)))
        self.end_headers()
        self.wfile.write(PNG)

    def log_message(self, format, *args):
        return


class Table2ImageTest(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_returns_url_and_downloads_png(self):
        markdown = "| 项目 | 状态 |\n| --- | --- |\n| Mable | Ready |"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "table.png"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = MODULE.main(
                    [
                        "--markdown",
                        markdown,
                        "--model",
                        "Asge8oUog7I",
                        "--api-base",
                        f"http://127.0.0.1:{self.server.server_port}",
                        "--token",
                        "sk_live_test",
                        "--output",
                        str(output),
                    ]
                )
            result = json.loads(stdout.getvalue())
            self.assertEqual(code, 0)
            self.assertTrue(result["image_url"].endswith("/image.png"))
            self.assertEqual(result["model"], "Asge8oUog7I")
            self.assertEqual(result["credits_spent"], 3)
            self.assertEqual(Handler.authorization, "Bearer sk_live_test")
            self.assertEqual(output.read_bytes(), PNG)
            self.assertEqual(Handler.payload["markdown"], markdown)
            self.assertNotIn("layout", Handler.payload)

    def test_rejects_non_table_input(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = MODULE.main(
                [
                    "--markdown",
                    "not a table",
                    "--api-base",
                    f"http://127.0.0.1:{self.server.server_port}",
                    "--token",
                    "sk_live_test",
                ]
            )
        self.assertEqual(code, 1)
        self.assertIn("表头、分隔行", stderr.getvalue())

    def test_requires_lovstudio_token(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = MODULE.main(
                [
                    "--markdown",
                    "| 项目 | 状态 |\n| --- | --- |\n| Mable | Ready |",
                    "--api-base",
                    f"http://127.0.0.1:{self.server.server_port}",
                ]
            )
        self.assertEqual(code, 1)
        self.assertIn("MABLE_API_TOKEN", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
