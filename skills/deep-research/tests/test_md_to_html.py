import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "md_to_html.py"
SPEC = importlib.util.spec_from_file_location("md_to_html", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class MarkdownToHtmlTests(unittest.TestCase):
    def test_repository_link_inside_table_is_clickable(self):
        markdown = """# Report

## Executive Summary

| Project | Evidence |
|---|---|
| [Example](https://github.com/example/repo) | [Code](https://github.com/example/repo/blob/abc/file.py) |
"""

        content, _ = MODULE.convert_markdown_to_html(markdown)

        self.assertIn(
            '<a href="https://github.com/example/repo" target="_blank" rel="noreferrer">Example</a>',
            content,
        )
        self.assertNotIn("[Example](https://github.com/example/repo)", content)

    def test_non_http_scheme_is_not_activated(self):
        markdown = """# Report

## Executive Summary

[Unsafe](javascript:alert(1))
"""

        content, _ = MODULE.convert_markdown_to_html(markdown)

        self.assertNotIn('href="javascript:', content)

    def test_figure_with_caption_becomes_figure_element(self):
        markdown = """# Report

## Executive Summary

![South gate at dusk](figures/fig01-gate.jpg)
*图 1：南城门是保存最完整的一段城墙。来源：实地拍摄。*

Body text.
"""

        content, _ = MODULE.convert_markdown_to_html(markdown)

        self.assertIn('<figure class="report-figure">', content)
        self.assertIn('src="figures/fig01-gate.jpg"', content)
        self.assertIn("<figcaption>图 1：南城门是保存最完整的一段城墙。来源：实地拍摄。</figcaption>", content)
        self.assertNotIn("<em>图 1", content)

    def test_unsafe_image_scheme_is_not_rendered(self):
        markdown = """# Report

## Executive Summary

![x](javascript:alert(1))
"""

        content, _ = MODULE.convert_markdown_to_html(markdown)

        self.assertNotIn("<img", content)

    def test_embed_images_inlines_local_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "figures").mkdir()
            (base / "figures" / "dot.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            markdown = """# Report

## Executive Summary

![dot](figures/dot.png)
*Figure 1: A dot.*
"""
            content, _ = MODULE.convert_markdown_to_html(markdown, base_dir=base, embed_images=True)

        self.assertIn('src="data:image/png;base64,', content)


if __name__ == "__main__":
    unittest.main()
