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


if __name__ == "__main__":
    unittest.main()
