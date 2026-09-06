import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_wechat_channel.py"
FIXTURE = ROOT / "cases" / "fixtures" / "wechat-channel-component.html"


def load_module():
    spec = importlib.util.spec_from_file_location("render_wechat_channel", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WechatChannelRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.dom = FIXTURE.read_text(encoding="utf-8")

    def test_dom_round_trip_preserves_component_contract(self):
        component = self.module.parse_dom(self.dom)
        dsl = self.module.render_markdown(component)
        reparsed = self.module.parse_dsl(dsl)
        self.assertEqual(reparsed, component)
        self.assertIn('nickname="示例视频号"', dsl)
        self.assertIn('description="示例视频号内容"', dsl)

    def test_dsl_renders_native_html(self):
        component = self.module.parse_dom(self.dom)
        native = self.module.render_html(component)
        self.assertEqual(native.count("<mp-common-videosnap"), 1)
        self.assertIn('data-pluginname="mpvideosnap"', native)
        self.assertIn('data-id="export/example-video"', native)
        self.assertIn('<template shadowrootmode="open">', native)
        self.assertIn(':host{all:initial;display:block!important', native)
        self.assertIn('.weui-play-btn_primary{position:absolute', native)
        self.assertIn('.wxw_wechannel_card_ft{position:absolute', native)
        self.assertIn('margin:0 auto', native)
        self.assertIn('style="width: 282px"', native)
        self.assertIn('height: 338px', native)

    def test_existing_file_requires_one_marker(self):
        component = self.module.parse_dom(self.dom)
        dsl = self.module.render_markdown(component)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "article.md"
            target.write_text("before\n<!-- lovpen-wechat-channel -->\nafter\n", encoding="utf-8")
            self.module.materialize(str(target), dsl, self.module.DEFAULT_MARKER, "md")
            rendered = target.read_text(encoding="utf-8")
            self.assertIn(dsl, rendered)
            self.assertNotIn(self.module.DEFAULT_MARKER, rendered)

    def test_cli_json_reports_real_artifact(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(FIXTURE), "--format", "html", "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["input_kind"], "dom")
        self.assertEqual(len(payload["sha256"]), 64)
        self.assertIn("<mp-common-videosnap", payload["content"])

    def test_existing_file_preserves_line_endings_and_mode(self):
        component = self.module.parse_dom(self.dom)
        dsl = self.module.render_markdown(component)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "article.md"
            with target.open("w", encoding="utf-8", newline="") as handle:
                handle.write("before\r\n<!-- lovpen-wechat-channel -->\r\nafter\r\n")
            target.chmod(0o640)
            self.module.materialize(str(target), dsl, self.module.DEFAULT_MARKER, "md")
            with target.open("r", encoding="utf-8", newline="") as handle:
                rendered = handle.read()
            self.assertIn("before\r\n", rendered)
            self.assertIn("\r\nafter\r\n", rendered)
            if os.name != "nt":
                self.assertEqual(target.stat().st_mode & 0o777, 0o640)

    def test_rejects_multiple_components(self):
        with self.assertRaises(self.module.ComponentError):
            self.module.parse_dom(self.dom + self.dom)


if __name__ == "__main__":
    unittest.main()
