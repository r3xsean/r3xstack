"""Third-round checks for the changed failure, retention and source guards.

Run from the repo with TEMP/TMP set to an owned directory.
"""
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import test_watch_video_additional as boundaries
import watch_video as wv


class ThirdRound(unittest.TestCase):
    setUp = boundaries.Boundaries.setUp
    invoke = boundaries.Boundaries.invoke
    transcript = boundaries.Boundaries.transcript

    @staticmethod
    def picture(*args, **kwargs):
        Path(str(args[-1]).replace("%02d", "01").replace("%%", "%")).write_bytes(b"picture")
        return subprocess.CompletedProcess([], 0, b"", b"")

    def saved_run(self, output):
        return Path(next(line.removeprefix("transcript: ") for line in output.splitlines()
                         if line.startswith("transcript: "))).parent

    def test_asr_failure_evidence_and_retry(self):
        with patch.object(wv, "streams", return_value={"audio", "video"}), \
                patch.object(wv, "duration_of", return_value=5), \
                patch.object(wv, "ffmpeg", side_effect=self.picture), \
                patch.object(wv, "run_asr", side_effect=wv.WatchError("Local ASR failed: model unavailable")):
            code, out, err = self.invoke(self.local)
        self.assertEqual(code, 0, err)
        self.assertIn("Transcript: none (Local ASR failed: model unavailable)\n", self.transcript(out))
        self.assertNotIn("no speech found", self.transcript(out))
        run = self.saved_run(out)
        self.assertEqual((run / "overview_01.jpg").read_bytes(), b"picture")
        self.assertEqual(len((run / "index.txt").read_text("utf-8").splitlines()), 16)
        with patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, at_out, err = self.invoke(run, "--at", "1")
        self.assertEqual(code, 0, err)
        self.assertEqual(Path(at_out.strip().split("\t")[1]).read_bytes(), b"picture")
        with patch.object(wv, "streams", return_value={"audio", "video"}), \
                patch.object(wv, "duration_of", return_value=5), \
                patch.object(wv, "run_asr", return_value=wv.Transcript("en", "local ASR", [wv.Segment(0, 1, "recovered speech")])):
            code, retry_out, err = self.invoke(self.local, "--transcript-only")
        self.assertEqual(code, 0, err)
        self.assertIn("recovered speech", self.transcript(retry_out))
        self.assertNotIn("no speech found", self.transcript(retry_out))
        self.assertIn("model unavailable", self.transcript(out))

    def test_audio_only_asr_failure_then_empty_success(self):
        with patch.object(wv, "streams", return_value={"audio"}), \
                patch.object(wv, "run_asr", side_effect=wv.WatchError("Local ASR failed: model unavailable")):
            code, out, err = self.invoke(self.local)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("model unavailable", err)
        self.assertNotIn("no speech found", err)
        with patch.object(wv, "streams", return_value={"audio"}), \
                patch.object(wv, "duration_of", return_value=5), \
                patch.object(wv, "run_asr", return_value=wv.Transcript("en", "local ASR (base)")):
            code, out, err = self.invoke(self.local)
        self.assertEqual(code, 0, err)
        self.assertIn("Transcript: local ASR (base): no speech found", self.transcript(out))
        self.assertIn("frames: none (no video stream)", out)

    def test_each_missing_tool_prevents_work_and_restored_path_recovers(self):
        real_which = wv.shutil.which
        for missing in ({"ffmpeg"}, {"ffprobe"}, {"ffmpeg", "ffprobe"}):
            for mode in ((), ("--transcript-only",), ("--at", "1"), ("--scan", "all")):
                with self.subTest(missing=missing, mode=mode), \
                        patch.object(wv.shutil, "which", side_effect=lambda tool: None if tool in missing else real_which(tool)):
                    code, out, err = self.invoke(self.local, *mode)
                self.assertEqual((code, out), (2, ""))
                self.assertIn(" and ".join(tool for tool in ("ffmpeg", "ffprobe") if tool in missing) + " not on PATH", err)
                self.assertIn("winget install Gyan.FFmpeg", err)
                self.assertIn("brew install ffmpeg", err)
                self.assertEqual(list(self.runs.iterdir()), [])
                self.assertEqual(self.local.read_bytes(), b"fixture")
        with patch.object(wv, "streams", return_value=set()), patch.object(wv, "duration_of", return_value=5):
            code, out, err = self.invoke(self.local, "--transcript-only")
        self.assertEqual(code, 0, err)
        self.assertIn("no audio stream", self.transcript(out))

    def test_same_size_same_second_source_edit_refuses_followups_then_rerun_recovers(self):
        first_ns = 1700000000123456700  # NTFS has 100 ns resolution.
        os.utime(self.local, ns=(first_ns, first_ns))
        with patch.object(wv, "streams", return_value={"video"}), \
                patch.object(wv, "duration_of", return_value=5), \
                patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, out, err = self.invoke(self.local)
        self.assertEqual(code, 0, err)
        old_run = self.saved_run(out)
        before = self.local.stat()
        self.local.write_bytes(b"changed")  # Same length as "fixture".
        os.utime(self.local, ns=(first_ns + 100, first_ns + 100))
        after = self.local.stat()
        self.assertEqual(before.st_size, after.st_size)
        self.assertEqual(int(before.st_mtime), int(after.st_mtime))
        self.assertNotEqual(before.st_mtime_ns, after.st_mtime_ns)
        with patch.object(wv, "ffmpeg", side_effect=self.picture):
            for mode in (("--at", "1"), ("--scan", "all")):
                code, followup_out, err = self.invoke(old_run, *mode)
                self.assertEqual((code, followup_out), (2, ""))
                self.assertIn("has changed since this run: run the skill on it again", err)
        with patch.object(wv, "streams", return_value={"video"}), \
                patch.object(wv, "duration_of", return_value=5), \
                patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, out, err = self.invoke(self.local)
            self.assertEqual(code, 0, err)
            fresh = self.saved_run(out)
            code, out, err = self.invoke(fresh, "--at", "1")
        self.assertNotEqual(fresh, old_run)
        self.assertEqual(code, 0, err)
        self.assertEqual(Path(out.strip().split("\t")[1]).read_bytes(), b"picture")
        self.assertEqual(self.local.read_bytes(), b"changed")

    def test_prune_manifest_vanishes_between_read_and_stat(self):
        old = wv.new_run("old", str(self.local))
        manifest = old / "manifest.json"
        stale = time.time() - 4 * 86400
        os.utime(manifest, (stale, stale))
        real_stat = Path.stat
        raced = []

        def concurrent_prune(path, *args, **kwargs):
            if path == manifest and not raced:
                raced.append(True)
                wv.shutil.rmtree(old)
            return real_stat(path, *args, **kwargs)

        with patch.object(Path, "stat", concurrent_prune), \
                patch.object(wv, "streams", return_value=set()), \
                patch.object(wv, "duration_of", return_value=5):
            code, out, err = self.invoke(self.local, "--transcript-only")
        self.assertEqual(raced, [True])
        self.assertEqual(code, 0, err)
        self.assertEqual(err, "")
        self.assertIn("no audio stream", self.transcript(out))
        self.assertFalse(old.exists())
        self.assertEqual(self.local.read_bytes(), b"fixture")

    def test_manifests_without_complete_allow_retry_inspection_and_pruning(self):
        with patch.object(wv, "streams", side_effect=KeyboardInterrupt):
            code, out, err = self.invoke(self.local)
        self.assertEqual((code, out), (130, ""))
        self.assertIn("interrupted", err)
        cancelled = next(self.runs.iterdir())
        self.assertNotIn("complete", json.loads((cancelled / "manifest.json").read_text("utf-8")))
        with patch.object(wv, "streams", return_value={"video"}), \
                patch.object(wv, "duration_of", return_value=5), \
                patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, out, err = self.invoke(self.local)
            self.assertEqual(code, 0, err)
            ready = self.saved_run(out)
            self.assertNotIn("complete", json.loads((ready / "manifest.json").read_text("utf-8")))
            for mode in (("--at", "1"), ("--scan", "all")):
                with patch.object(wv, "scene_ends", return_value=[]):
                    code, out, err = self.invoke(ready, *mode)
                self.assertEqual(code, 0, err)
                self.assertTrue(out.strip())
        stale = time.time() - 4 * 86400
        os.utime(cancelled / "manifest.json", (stale, stale))
        wv.prune()
        self.assertFalse(cancelled.exists())
        self.assertTrue((ready / "overview_01.jpg").is_file())
        self.assertEqual(self.local.read_bytes(), b"fixture")

    def test_output_entry_failure_can_retry_without_losing_saved_evidence(self):
        entries = [(1, {"id": "one", "title": "First"}, None), (2, {"id": "two", "title": "Second"}, None)]
        captions = wv.Transcript("en", "manual captions", [wv.Segment(0, 1, "words")])
        output = self.root / "chosen.md"
        blocked = self.root / "chosen-1.md"
        blocked.mkdir()
        with patch.object(wv, "entries_of", return_value=entries), patch.object(wv, "caption_transcript", return_value=captions):
            code, out, err = self.invoke("https://example.test/post", "--transcript-only", "-o", output)
            self.assertEqual(code, 2, err)
            self.assertIn("video 1: failed (", out)
            self.assertIn("video 2: Second", out)
            self.assertIn("# Second", (self.root / "chosen-2.md").read_text("utf-8"))
            saved = {path: path.read_bytes() for path in self.runs.glob("*/transcript.md")}
            blocked.rmdir()
            code, out, err = self.invoke("https://example.test/post", "--transcript-only", "-o", output)
        self.assertEqual(code, 0, err)
        self.assertNotIn("failed", out)
        for number, title in ((1, "First"), (2, "Second")):
            self.assertIn(f"video {number}: {title}", out)
            self.assertIn(f"# {title}", (self.root / f"chosen-{number}.md").read_text("utf-8"))
        for path, content in saved.items():
            self.assertEqual(path.read_bytes(), content)

    def test_source_hardlink_refusal_can_retry_to_new_output(self):
        alias = self.root / "alias.md"
        os.link(self.local, alias)
        code, out, err = self.invoke(self.local, "--transcript-only", "-o", alias)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("--output must not be the source video", err)
        self.assertEqual(self.local.read_bytes(), b"fixture")
        self.assertEqual(list(self.runs.iterdir()), [])
        chosen = self.root / "safe.md"
        with patch.object(wv, "streams", return_value=set()), patch.object(wv, "duration_of", return_value=5):
            code, out, err = self.invoke(self.local, "--transcript-only", "-o", chosen)
        self.assertEqual(code, 0, err)
        self.assertIn(f"transcript: {chosen}", out)
        self.assertIn("no audio stream", chosen.read_text("utf-8"))
        self.assertEqual(alias.read_bytes(), b"fixture")



if __name__ == "__main__":
    unittest.main()
