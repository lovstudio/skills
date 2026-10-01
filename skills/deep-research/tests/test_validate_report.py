import importlib.util
import tempfile
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_report.py"
SPEC = importlib.util.spec_from_file_location("validate_report", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _report(mode: str, figures: str) -> str:
    return f"""---
mode: {mode}
---

# Report

## Executive Summary

Summary [1].

{figures}

## References

[1] Org (2026). "Title". https://example.com
"""


class FigureCheckTests(unittest.TestCase):
    def _validator(self, text: str, files=()):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        for name in files:
            path = base / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"x")
        report = base / "report.md"
        report.write_text(text)
        return MODULE.ReportValidator(report)

    def test_deep_report_without_figures_fails(self):
        validator = self._validator(_report("deep", ""))
        self.assertFalse(validator._check_figures())
        self.assertTrue(any("No figures" in e for e in validator.errors))

    def test_missing_figure_file_fails(self):
        validator = self._validator(_report("standard", "![a](figures/a.png)\n*图 1：说明。*"))
        self.assertFalse(validator._check_figures())
        self.assertTrue(any("Missing figure files" in e for e in validator.errors))

    def test_captioned_local_figures_pass_with_count_warning(self):
        figs = "\n\n".join(f"![f{i}](figures/f{i}.png)\n*图 {i}：说明。*" for i in range(1, 3))
        validator = self._validator(_report("deep", figs), files=[f"figures/f{i}.png" for i in range(1, 3)])
        self.assertTrue(validator._check_figures())
        self.assertTrue(any("Only 2 figures" in w for w in validator.warnings))

    def test_uncaptioned_figure_warns(self):
        validator = self._validator(_report("quick", "![a](figures/a.png)\n\nText."), files=["figures/a.png"])
        self.assertTrue(validator._check_figures())
        self.assertTrue(any("caption" in w for w in validator.warnings))


if __name__ == "__main__":
    unittest.main()
