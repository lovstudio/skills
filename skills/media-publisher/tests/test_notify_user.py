from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "notify_user.py"
SPEC = importlib.util.spec_from_file_location("notify_user", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
notify_user = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(notify_user)


class SpeakTests(unittest.TestCase):
    def test_auto_prefers_volcengine_when_it_succeeds(self):
        with patch.object(
            notify_user,
            "speak_volcengine",
            return_value={"spoken": True, "provider": "volcengine"},
        ) as volcengine, patch.object(notify_user, "speak_system") as system:
            result = notify_user.speak("已准备好", "auto")

        self.assertTrue(result["spoken"])
        self.assertEqual(result["provider"], "volcengine")
        volcengine.assert_called_once_with("已准备好")
        system.assert_not_called()

    def test_auto_falls_back_to_system_voice(self):
        with patch.object(
            notify_user,
            "speak_volcengine",
            return_value={
                "spoken": False,
                "provider": "volcengine",
                "reason": "credentials unavailable",
            },
        ), patch.object(
            notify_user,
            "speak_system",
            return_value={"spoken": True, "provider": "system"},
        ) as system:
            result = notify_user.speak("请上传封面", "auto", "Tingting")

        self.assertTrue(result["spoken"])
        self.assertEqual(result["provider"], "system")
        system.assert_called_once_with("请上传封面", "Tingting")

    def test_explicit_volcengine_does_not_fall_back(self):
        failed = {
            "spoken": False,
            "provider": "volcengine",
            "reason": "credentials unavailable",
        }
        with patch.object(notify_user, "speak_volcengine", return_value=failed), patch.object(
            notify_user, "speak_system"
        ) as system:
            result = notify_user.speak("请登录", "volcengine")

        self.assertEqual(result, failed)
        system.assert_not_called()


if __name__ == "__main__":
    unittest.main()
