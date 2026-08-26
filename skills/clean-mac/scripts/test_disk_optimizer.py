#!/usr/bin/env python3
"""Regression tests for guarded rollback-item handling."""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).with_name("disk_optimizer.py")
SPEC = importlib.util.spec_from_file_location("disk_optimizer", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"无法加载测试目标：{SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def call_json(function, args):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = function(args)
    return code, json.loads(output.getvalue())


class StagedCleanupTests(unittest.TestCase):
    def test_path_guard_accepts_only_top_level_cleanup_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "trash"
            root.mkdir()
            valid = root / "build-target.cleanup"
            valid.mkdir()
            self.assertEqual(MODULE.staged_path(valid, root), valid)

            with self.assertRaises(MODULE.OptimizerError):
                MODULE.staged_path(root / "keep.txt", root)
            with self.assertRaises(MODULE.OptimizerError):
                MODULE.staged_path(root / "nested" / "build-target.cleanup", root)

    def test_stage_cleanup_rolls_back_when_a_later_move_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "workspace"
            root.mkdir()
            first = root / ".next"
            second = root / "node_modules"
            first.mkdir()
            second.mkdir()
            (first / "cache.bin").write_bytes(b"first")
            (second / "module.bin").write_bytes(b"second")
            rollback_root = Path(temp_dir) / "trash"
            real_move = MODULE.shutil.move

            def move_with_fixture_failure(source, destination):
                if Path(source).resolve() == second.resolve():
                    raise OSError("locked fixture")
                return real_move(source, destination)

            with patch.object(MODULE.shutil, "move", side_effect=move_with_fixture_failure):
                code, result = call_json(
                    MODULE.run_stage_cleanup,
                    argparse.Namespace(
                        path=[first, second],
                        protected=[],
                        rollback_root=rollback_root,
                        recreate=True,
                        execute=True,
                        confirm="STAGE_REBUILDABLES",
                        output=None,
                    ),
                )

            self.assertEqual(code, 2)
            self.assertEqual(result["status"], "rolled-back")
            self.assertEqual([item["status"] for item in result["items"]], ["rolled-back", "not-started"])
            self.assertTrue((first / "cache.bin").exists())
            self.assertTrue((second / "module.bin").exists())
            self.assertFalse(rollback_root.exists() and any(rollback_root.iterdir()))

    def test_list_and_purge_preserve_other_trash_items(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "trash"
            root.mkdir()
            cleanup = root / "cache.cleanup"
            cleanup.mkdir()
            (cleanup / "payload.bin").write_bytes(b"rebuildable")
            keep = root / "camera.CR3"
            keep.write_bytes(b"keep")

            list_code, listed = call_json(
                MODULE.run_list_staged,
                argparse.Namespace(rollback_root=root, output=None),
            )
            self.assertEqual(list_code, 0)
            self.assertEqual(
                [Path(item["path"]).resolve() for item in listed["items"]],
                [cleanup.resolve()],
            )

            preview_code, preview = call_json(
                MODULE.run_purge_staged,
                argparse.Namespace(
                    path=[cleanup],
                    rollback_root=root,
                    execute=False,
                    confirm="",
                    output=None,
                ),
            )
            self.assertEqual(preview_code, 0)
            self.assertEqual(preview["method"], "direct-filesystem")
            self.assertFalse(preview["finder"])
            self.assertTrue(cleanup.exists())

            purge_code, result = call_json(
                MODULE.run_purge_staged,
                argparse.Namespace(
                    path=[cleanup],
                    rollback_root=root,
                    execute=True,
                    confirm="PURGE_STAGED",
                    output=None,
                ),
            )
            self.assertEqual(purge_code, 0)
            self.assertEqual(result["status"], "purged")
            self.assertFalse(cleanup.exists())
            self.assertTrue(keep.exists())


class ProtectedWorkspaceTests(unittest.TestCase):
    def test_screen_studio_recordings_and_containing_parent_are_protected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            screen_studio = Path(temp_dir) / "Screen Studio"
            recordings = screen_studio / "Screen Studio Recordings"
            recording_cache = recordings / "Current Recording" / "Caches"
            with patch.object(MODULE, "builtin_protected_paths", return_value=(recordings.resolve(),)):
                self.assertTrue(MODULE.protected(screen_studio, []))
                self.assertTrue(MODULE.protected(recordings, []))
                self.assertTrue(MODULE.protected(recording_cache, []))

    def test_stage_cleanup_rejects_rebuildable_name_inside_protected_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            recordings = Path(temp_dir) / "Screen Studio Recordings"
            recording_cache = recordings / "Current Recording" / "Caches"
            recording_cache.mkdir(parents=True)
            with patch.object(MODULE, "builtin_protected_paths", return_value=(recordings.resolve(),)):
                with self.assertRaisesRegex(MODULE.OptimizerError, "候选命中保护边界"):
                    MODULE.run_stage_cleanup(
                        argparse.Namespace(
                            path=[recording_cache],
                            protected=[],
                            rollback_root=Path(temp_dir) / "trash",
                            recreate=False,
                            execute=False,
                            confirm="",
                            output=None,
                        )
                    )

    def test_migrate_rejects_protected_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            recordings = Path(temp_dir) / "Screen Studio Recordings"
            recordings.mkdir()
            archive = Path(temp_dir) / "archive"
            archive.mkdir()
            with patch.object(MODULE, "builtin_protected_paths", return_value=(recordings.resolve(),)):
                with self.assertRaisesRegex(MODULE.OptimizerError, "迁移源命中保护边界"):
                    MODULE.run_migrate(
                        argparse.Namespace(source=recordings, archive_root=archive, protected=[])
                    )

    def test_explicit_protected_child_also_blocks_parent_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir) / "parent"
            protected_child = parent / "keep"
            self.assertTrue(MODULE.protected(parent, [protected_child]))

    def test_symlinked_protected_workspace_keeps_its_original_parent_protected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            screen_studio = Path(temp_dir) / "Screen Studio"
            screen_studio.mkdir()
            recordings_link = screen_studio / "Screen Studio Recordings"
            external_recordings = Path(temp_dir) / "external-recordings"
            external_recordings.mkdir()
            recordings_link.symlink_to(external_recordings, target_is_directory=True)
            with patch.object(MODULE, "builtin_protected_paths", return_value=(recordings_link,)):
                self.assertTrue(MODULE.protected(screen_studio, []))
                self.assertTrue(MODULE.protected(external_recordings, []))


if __name__ == "__main__":
    unittest.main()
