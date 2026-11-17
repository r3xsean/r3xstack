"""Adversarial checks for the second-round run/failure changes only."""
import io
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


class SecondRound(unittest.TestCase):
    setUp = boundaries.Boundaries.setUp
    invoke = boundaries.Boundaries.invoke
    transcript = boundaries.Boundaries.transcript

    def ready(self, name="ready", length=5):
        run = wv.new_run(name, str(self.local))
        wv.write_manifest(run, source=str(self.local), complete=True,
                          video=str(self.local), length=length, stamp=wv.stamp(self.local))
        return run

    @staticmethod
    def picture(*args, **kwargs):
        Path(str(args[-1]).replace("%02d", "01").replace("%%", "%")).write_bytes(b"picture")
        return subprocess.CompletedProcess([], 0, b"", b"")

    @staticmethod
    def no_picture(*args, **kwargs):
        return subprocess.CompletedProcess([], 0, b"", b"")

    def native_clip(self, name="real.mp4"):
        video = self.root / name
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        "color=c=red:s=80x60:r=10:d=2", str(video)], check=True, capture_output=True)
        return video

    def test_cancelled_run_is_owned_prunable_and_retry_is_separate(self):
        with patch.object(wv, "streams", side_effect=KeyboardInterrupt):
            code, out, err = self.invoke(self.local)
        self.assertEqual((code, out), (130, ""))
        self.assertIn("interrupted", err)
        cancelled = next(self.runs.iterdir())
        manifest = cancelled / "manifest.json"
        data = json.loads(manifest.read_text("utf-8"))
        self.assertEqual((data["tool"], data.get("video")), ("watch-video", None))
        with patch.object(wv, "streams", return_value=set()), patch.object(wv, "duration_of", return_value=5):
            code, out, err = self.invoke(self.local, "--transcript-only")
        self.assertEqual(code, 0, err)
        self.assertIn("no audio stream", self.transcript(out))
        self.assertEqual(len(list(self.runs.iterdir())), 2)
        stale = time.time() - 4 * 86400
        os.utime(manifest, (stale, stale))
        wv.prune()
        self.assertFalse(cancelled.exists())
        self.assertTrue(self.local.is_file())
        self.assertIn("no audio stream", self.transcript(out))

    def test_older_finishing_after_newer_keeps_both_printed_results(self):
        source = "https://example.test/same-video"
        info = {"id": "same", "title": "Same"}
        newer = []
        nested = False

        def captions(*args):
            nonlocal nested
            if not nested:
                nested = True
                newer.append(self.invoke(source, "--transcript-only"))
                return wv.Transcript("en", "manual captions", [wv.Segment(0, 1, "older finishes last")])
            return wv.Transcript("en", "manual captions", [wv.Segment(0, 1, "newer finishes first")])

        with patch.object(wv, "entries_of", return_value=[(None, info, None)]), patch.object(wv, "caption_transcript", side_effect=captions):
            old_code, old_out, old_err = self.invoke(source, "--transcript-only")
        new_code, new_out, new_err = newer[0]
        self.assertEqual((old_code, new_code), (0, 0), old_err + new_err)
        self.assertNotEqual(old_out, new_out)
        self.assertIn("older finishes last", self.transcript(old_out))
        self.assertIn("newer finishes first", self.transcript(new_out))

    def test_followup_refreshes_retention_by_manifest_not_folder_time(self):
        run = self.ready()
        stale = time.time() - 4 * 86400
        os.utime(run / "manifest.json", (stale, stale))
        os.utime(run, (stale, stale))
        with patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, out, err = self.invoke(run, "--at", "1")
        self.assertEqual(code, 0, err)
        path = Path(out.strip().split("\t")[1])
        wv.prune()
        self.assertEqual(path.read_bytes(), b"picture")

    def test_partial_post_extraction_continues_and_retry_keeps_previous_evidence(self):
        fail = True

        class Downloader:
            def __init__(self, options):
                self.options = options
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def extract_info(self, *args, **kwargs):
                number = self.options.get("playlist_items")
                if not number:
                    return {"_type": "multi_video", "entries": [{}, {}]}
                if number == "1" and fail:
                    raise RuntimeError("entry unavailable")
                return {"id": number, "title": "Entry " + number}

        caption = wv.Transcript("en", "manual captions", [wv.Segment(0, 1, "saved speech")])
        with patch.object(wv.yt_dlp, "YoutubeDL", Downloader), patch.object(wv, "caption_transcript", return_value=caption):
            code, out, err = self.invoke("https://example.test/post", "--transcript-only")
            self.assertEqual(code, 2, err)
            self.assertIn("video 1: failed (Could not access this video: entry unavailable)", out)
            self.assertIn("video 2: Entry 2", out)
            self.assertIn("saved speech", self.transcript(out))
            fail = False
            retry, retry_out, retry_err = self.invoke("https://example.test/post", "--transcript-only")
        self.assertEqual(retry, 0, retry_err)
        self.assertNotIn("failed", retry_out)
        self.assertIn("video 1: Entry 1", retry_out)
        self.assertIn("video 2: Entry 2", retry_out)
        self.assertIn("saved speech", self.transcript(out))

    def test_partial_post_transcription_failure_continues(self):
        entries = [(1, {"id": "1"}, None), (2, {"id": "2"}, None)]
        caption = wv.Transcript("en", "manual captions", [wv.Segment(0, 1, "second survives")])
        with patch.object(wv, "entries_of", return_value=entries), patch.object(wv, "caption_transcript", side_effect=[wv.WatchError("caption expired"), caption]):
            code, out, err = self.invoke("https://example.test/post", "--transcript-only")
        self.assertEqual(code, 2, err)
        self.assertIn("video 1: failed (caption expired)", out)
        self.assertIn("second survives", self.transcript(out))

    def test_asr_transcript_only_failure_is_nonzero_and_retry_can_recover(self):
        with patch.object(wv, "streams", return_value={"video", "audio"}), patch.object(wv, "run_asr", side_effect=wv.WatchError("model unavailable")):
            code, out, err = self.invoke(self.local, "--transcript-only")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("model unavailable", err)
        with patch.object(wv, "streams", return_value={"video", "audio"}), patch.object(wv, "duration_of", return_value=5), patch.object(wv, "run_asr", return_value=wv.Transcript("en", "local ASR", [wv.Segment(0, 1, "recovered")])):
            code, out, err = self.invoke(self.local, "--transcript-only")
        self.assertEqual(code, 0, err)
        self.assertIn("recovered", self.transcript(out))

    def test_partial_at_prints_only_survivor_warns_and_retry_recovers(self):
        run = self.ready()

        def partial(*args, **kwargs):
            return self.picture(*args, **kwargs) if args[1] == "1.00" else self.no_picture()

        with patch.object(wv, "ffmpeg", side_effect=partial):
            code, out, err = self.invoke(run, "--at", "1,2")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(out.splitlines()), 1)
        self.assertIn("no frame at 00:02.0", err)
        self.assertTrue(Path(out.strip().split("\t")[1]).is_file())
        with patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, out, err = self.invoke(run, "--at", "2")
        self.assertEqual(code, 0, err)
        self.assertIn("00:02.0\t", out)

    def test_scan_no_tiles_is_nonzero_and_retry_recovers(self):
        run = self.ready()
        with patch.object(wv, "scene_ends", return_value=[]), patch.object(wv, "ffmpeg", side_effect=self.no_picture):
            code, out, err = self.invoke(run, "--scan", "all")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("no picture could be read", err)
        with patch.object(wv, "scene_ends", return_value=[]), patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, out, err = self.invoke(run, "--scan", "all")
        self.assertEqual(code, 0, err)
        self.assertIn("16 tiles", err)
        self.assertTrue(Path(out.strip().split("\t")[0]).is_file())

    def test_failed_overview_keeps_transcript_and_followup_media(self):
        with patch.object(wv, "streams", return_value={"video"}), patch.object(wv, "duration_of", return_value=5), patch.object(wv, "ffmpeg", side_effect=self.no_picture):
            code, out, err = self.invoke(self.local)
        self.assertEqual(code, 0, err)
        self.assertIn("frames: none (no picture could be read", out)
        self.assertIn("no audio stream", self.transcript(out))
        run = next(self.runs.iterdir())
        with patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, out, err = self.invoke(run, "--at", "1")
        self.assertEqual(code, 0, err)
        self.assertTrue(Path(out.strip().split("\t")[1]).is_file())

    def test_partial_sheet_omits_failed_tile_and_maps_remaining_speech(self):
        segments = [wv.Segment(0, 1, "near"), wv.Segment(20, 22, "distant")]
        def partial(*args, **kwargs):
            if args[0] == "-ss" and float(args[1]) > 0.5:
                return self.no_picture()
            return self.picture(*args, **kwargs)
        with patch.object(wv, "ffmpeg", side_effect=partial), patch("sys.stderr", new_callable=io.StringIO) as err:
            result = wv.overview(self.root, self.local, 8, segments)
        self.assertIn("1 tiles on 1 sheet", result)
        self.assertIn("15 of 16", err.getvalue())
        self.assertEqual((self.root / "index.txt").read_text("utf-8"), "00:00.2\toverview_01.jpg#01\t00:00.0-00:01.0\tnear\n")

    def test_output_guard_rejects_run_tree_then_accepts_external_output(self):
        for destination in (self.runs, self.runs / "prior" / "transcript.md"):
            with self.subTest(destination=destination):
                code, out, err = self.invoke(self.local, "-o", destination)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("--output must not", err)
        chosen = self.root / "chosen.md"
        with patch.object(wv, "streams", return_value=set()), patch.object(wv, "duration_of", return_value=5):
            code, out, err = self.invoke(self.local, "--transcript-only", "-o", chosen)
        self.assertEqual(code, 0, err)
        self.assertIn(f"transcript: {chosen}", out)
        self.assertIn("no audio stream", chosen.read_text("utf-8"))

    def test_changed_source_scan_refuses_then_fresh_run_recovers(self):
        run = self.ready()
        self.local.write_bytes(b"different length")
        code, out, err = self.invoke(run, "--scan", "all")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("has changed since this run: run the skill on it again", err)
        with patch.object(wv, "streams", return_value={"video"}), patch.object(wv, "duration_of", return_value=5), patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, out, err = self.invoke(self.local)
        self.assertEqual(code, 0, err)
        self.assertIn("frames: ", out)
        fresh = next(p for p in self.runs.iterdir() if p != run)
        with patch.object(wv, "ffmpeg", side_effect=self.picture):
            code, out, err = self.invoke(fresh, "--at", "1")
        self.assertEqual(code, 0, err)


    def test_retry_at_without_new_picture_must_not_return_old_file(self):
        self.local = self.native_clip()
        run = self.ready(length=2)
        first_code, first_out, first_err = self.invoke(run, "--at", "1.9")
        self.assertEqual(first_code, 0, first_err)
        # At 10 fps the last picture is at 1.9 s. 1.94 has none, but shares its rounded filename.
        code, out, err = self.invoke(run, "--at", "1.94")
        self.assertEqual((code, out), (2, ""), "retry printed the previous frame as a new success: " + out)


    def test_overlapping_scans_keep_their_own_scene_metadata(self):
        run = self.ready()
        inner = []
        nested = False

        def detect(*args, cwd=None):
            nonlocal nested
            if cwd is None:
                return self.picture(*args)
            note = next(a for a in args if "file=" in a).rsplit("file=", 1)[1]
            (cwd / note).write_text("frame:0 pts:0 pts_time:0.5\nlavfi.scene_score=0\n"
                                    "frame:1 pts:1 pts_time:1\nlavfi.scene_score=0.9\n", encoding="utf-8")
            if not nested:
                nested = True
                inner.append(self.invoke(run, "--scan", "1-4"))
            return subprocess.CompletedProcess([], 0, b"", b"")

        with patch.object(wv, "ffmpeg", side_effect=detect):
            outer_code, outer_out, outer_err = self.invoke(run, "--scan", "0-5")
        inner_code, inner_out, inner_err = inner[0]
        self.assertEqual((outer_code, inner_code), (0, 0), outer_err + inner_err)
        self.assertNotIn("scene detection failed", outer_err + inner_err)
        self.assertIn("00:00.5", outer_out.split("\t", 1)[1].split())
        self.assertIn("00:01.5", inner_out.split("\t", 1)[1].split())
        for out in (outer_out, inner_out):
            self.assertTrue(Path(out.split("\t", 1)[0]).is_file())


if __name__ == "__main__":
    unittest.main()
