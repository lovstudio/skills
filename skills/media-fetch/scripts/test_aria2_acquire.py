#!/usr/bin/env python3
"""Regression tests for aria2-first command routing."""

from __future__ import annotations

import argparse
import unittest
from pathlib import Path
from unittest.mock import patch

import aria2_acquire


def command_args(input_value: str, output_name: str | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        input=input_value,
        output_name=output_name,
        listen_port=0,
        max_peers=200,
        summary_interval=15,
    )


class Aria2RoutingTests(unittest.TestCase):
    def test_classifies_direct_and_bittorrent_inputs(self) -> None:
        self.assertEqual(aria2_acquire.classify_input("https://example.test/movie.mp4"), "direct")
        self.assertEqual(aria2_acquire.classify_input("magnet:?xt=urn:btih:abc"), "bittorrent")
        self.assertEqual(aria2_acquire.classify_input("https://example.test/file.torrent"), "bittorrent")

    def test_direct_command_uses_http_options_without_bt_listeners(self) -> None:
        args = command_args("https://example.test/download?id=1", "Movie.mp4")
        command = aria2_acquire.build_command(
            args,
            Path("/tmp/media-fetch-test"),
            "/usr/bin/aria2c",
            [],
            "direct",
            None,
            41001,
        )
        self.assertIn("--split=16", command)
        self.assertIn("--out=Movie.mp4", command)
        self.assertFalse(any(item.startswith("--listen-port=") for item in command))
        self.assertFalse(any(item.startswith("--bt-tracker=") for item in command))

    def test_bittorrent_command_enables_swarm_features(self) -> None:
        args = command_args("magnet:?xt=urn:btih:abc")
        command = aria2_acquire.build_command(
            args,
            Path("/tmp/media-fetch-test"),
            "/usr/bin/aria2c",
            ["udp://tracker.example:80/announce"],
            "bittorrent",
            41002,
            41003,
        )
        self.assertIn("--enable-dht=true", command)
        self.assertIn("--enable-peer-exchange=true", command)
        self.assertIn("--listen-port=41002", command)
        self.assertIn("--rpc-listen-port=41003", command)

    def test_auto_ports_are_separate(self) -> None:
        listen_port, rpc_port = aria2_acquire.resolve_ports("job-a", "bittorrent", 0, None)
        self.assertIsNotNone(listen_port)
        self.assertNotEqual(listen_port, rpc_port)

    def test_output_name_rejects_paths(self) -> None:
        with self.assertRaises(SystemExit):
            aria2_acquire.validate_output_name("nested/Movie.mp4")

    def test_rpc_uses_stopped_task_to_detect_completion(self) -> None:
        stopped = [
            {
                "status": "complete",
                "completedLength": "2048",
                "totalLength": "2048",
                "downloadSpeed": "0",
            }
        ]
        with patch.object(aria2_acquire, "rpc_request", side_effect=[[], stopped]):
            transfer = aria2_acquire.rpc_transfer(41003)
        self.assertIsNotNone(transfer)
        assert transfer is not None
        self.assertTrue(transfer["rpc_complete"])
        self.assertEqual(transfer["rpc_source"], "stopped")
        self.assertEqual(transfer["completed_bytes"], 2048)


if __name__ == "__main__":
    unittest.main()
