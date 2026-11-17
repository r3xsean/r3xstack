"""Offline boundary tests; no network, ASR installation, or user's cache writes.

Run with Python 3. Set TEMP/TMP to an owned folder before running.
"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import watch_video as wv


class Boundaries(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.runs = self.root / "watch-video"
        self.runs.mkdir()
        self.local = self.root / "clip.mp4"
        self.local.write_bytes(b"fixture")
        self.patcher = patch.object(wv, "RUNS", self.runs)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", [str(wv.__file__), *map(str, args)]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = wv.main()
        return code, out.getvalue(), err.getvalue()

    def transcript(self, stdout):
        path = next(line.removeprefix("transcript: ") for line in stdout.splitlines() if line.startswith("transcript: "))
        return Path(path).read_text("utf-8")

    def test_caption_details_survive_video_download_failure(self):
        """C1/C4: report available captions/details and why frames are absent."""
        info = {"id": "captioned", "title": "A title", "uploader": "A channel", "upload_date": "20260102",
                "duration": 20, "webpage_url": "https://example.test/video", "chapters": [{"start_time": 10, "title": "Demo"}]}
        captions = wv.Transcript("en", "manual captions", [wv.Segment(1, 3, "Visible speech")])
        with patch.object(wv, "entries_of", return_value=[(None, info, None)]), patch.object(wv, "caption_transcript", return_value=captions), patch.object(wv, "download", side_effect=wv.WatchError("download failed: HTTP 403")):
            code, out, err = self.invoke("https://example.test/video")
        self.assertEqual(code, 0, err)
        self.assertIn("frames: none (download failed: HTTP 403)", out)
        text = self.transcript(out)
        for expected in ("Channel: A channel", "Uploaded: 2026-01-02", "Length: 00:20.0", "Transcript: manual captions", "- 00:10.0 Demo", "[00:01.0] Visible speech"):
            self.assertIn(expected, text)
        self.assertIsNone(json.loads(next(self.runs.glob("*/manifest.json")).read_text("utf-8"))["video"])

    def test_preferred_caption_language_needs_no_media_for_transcript_only(self):
        """C1/C6: caption selection/parsing reaches the file the agent reads."""
        info = {"id": "captions", "title": "Captioned", "language": "en",
                "subtitles": {"es": [{"ext": "json3", "url": "https://example.test/es"}]},
                "automatic_captions": {"en": [{"ext": "json3", "url": "https://example.test/en"}]}}

        def caption(track):
            words = "Hello &amp; world" if track["url"].endswith("/en") else "Hola mundo"
            return json.dumps({"events": [{"tStartMs": 1000, "dDurationMs": 2000, "segs": [{"utf8": words}]}]}).encode("utf-8")

        with patch.object(wv, "entries_of", return_value=[(None, info, None)]), patch.object(wv, "download_caption", side_effect=caption), patch.object(wv, "download", side_effect=AssertionError("caption-only must not download media")):
            code, out, err = self.invoke("https://example.test/video", "--transcript-only", "--language", "en")
        self.assertEqual(code, 0, err)
        text = self.transcript(out)
        self.assertIn("Language: en", text)
        self.assertIn("Transcript: automatic captions", text)
        self.assertIn("[00:01.0] Hello & world", text)
        self.assertNotIn("frames:", out)

    def test_multiple_videos_have_distinct_numbered_outputs(self):
        """C1/C7: both entries' printed destinations keep their own content."""
        entries = [(1, {"id": "one", "title": "First"}, None), (2, {"id": "two", "title": "Second"}, None)]
        captions = wv.Transcript("en", "manual captions", [wv.Segment(0, 1, "words")])
        output = self.root / "chosen.md"
        with patch.object(wv, "entries_of", return_value=entries), patch.object(wv, "caption_transcript", return_value=captions):
            code, out, err = self.invoke("https://example.test/post", "--transcript-only", "-o", output)
        self.assertEqual(code, 0, err)
        self.assertIn("video 1: First", out)
        self.assertIn("video 2: Second", out)
        for number, title in ((1, "First"), (2, "Second")):
            path = output.with_name(f"chosen-{number}.md")
            self.assertIn(f"transcript: {path}", out)
            self.assertTrue(path.read_text("utf-8").startswith(f"# {title}\n"))

    def test_no_speech_is_not_an_asr_failure(self):
        """C2: audio with no recognized speech has an explicit successful outcome."""
        with patch.object(wv, "streams", return_value={"audio"}), patch.object(wv, "duration_of", return_value=5), patch.object(wv, "run_asr", return_value=wv.Transcript("en", "local ASR (base)")):
            code, out, err = self.invoke(self.local)
        self.assertEqual(code, 0, err)
        self.assertIn("Transcript: local ASR (base): no speech found", self.transcript(out))
        self.assertIn("frames: none (no video stream)", out)

    def test_index_preserves_real_speech_spans_and_omits_distant_speech(self):
        """C3: an overview tile points to actual cue bounds, including a pause."""
        segments = [wv.Segment(0, 2, "one"), wv.Segment(2, 4, "two"), wv.Segment(4, 6, "three"), wv.Segment(20, 22, "far away")]
        with patch.object(wv, "sheets", return_value=[3, 8, 15]):
            wv.overview(self.root, self.local, 30, segments)
        self.assertEqual((self.root / "index.txt").read_text("utf-8"),
                         "00:03.0\toverview_01.jpg#01\t00:00.0-00:06.0\tone two three\n"
                         "00:08.0\toverview_01.jpg#02\t00:02.0-00:06.0\ttwo three\n"
                         "00:15.0\toverview_01.jpg#03\t-\t\n")

    def test_download_retry_discards_partial_and_returns_fresh_file(self):
        """C4/C5: a transient failure retries once without reusing partial bytes."""
        args = wv.parse_args(["https://example.test/video"])
        attempts = []
        root = self.root

        class Downloader:
            def __init__(self, options):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def download(self, sources):
                attempts.append(sources)
                if len(attempts) == 1:
                    (root / "video.mp4").write_bytes(b"broken")
                    (root / "video.mp4.part").write_bytes(b"partial")
                    raise OSError("HTTP 403")
                if (root / "video.mp4.part").exists():
                    raise OSError("partial was reused")
                (root / "video.mp4").write_bytes(b"fresh")

        with patch.object(wv.yt_dlp, "YoutubeDL", Downloader):
            result = wv.download(args, None, self.root, "video", "best")
        self.assertEqual(result.read_bytes(), b"fresh")
        self.assertEqual(len(attempts), 2)
        self.assertFalse((self.root / "video.mp4.part").exists())

    def test_interrupt_is_explicit_and_retry_succeeds(self):
        """C5: interruption never prints completed paths, and a retry works."""
        with patch.object(wv, "streams", side_effect=KeyboardInterrupt):
            code, out, err = self.invoke(self.local)
        self.assertEqual((code, out), (130, ""))
        self.assertIn("watch-video: interrupted", err)
        with patch.object(wv, "streams", return_value={"video"}), patch.object(wv, "duration_of", return_value=5):
            code, out, err = self.invoke(self.local, "--transcript-only")
        self.assertEqual(code, 0, err)
        self.assertIn("none (no audio stream)", self.transcript(out))

    def test_asr_worker_bad_result_is_actionable(self):
        """C2/C4: invalid worker JSON is an error rather than empty-success speech."""
        args = wv.parse_args([str(self.local)])
        with patch.dict(sys.modules, {"faster_whisper": None}), patch.object(wv, "asr_runtime_python", return_value=Path(sys.executable)), patch.object(wv.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "not JSON", "")):
            with self.assertRaisesRegex(wv.WatchError, "Local ASR returned an invalid result"):
                wv.run_asr(self.local, args)

    def test_moved_local_original_can_be_restored_and_retried(self):
        """C4/C5: persisted references are refreshable without copying/deleting source."""
        run = self.runs / "old"
        run.mkdir()
        missing = self.root / "moved.mp4"
        manifest = run / "manifest.json"
        manifest.write_text(json.dumps({"tool": "watch-video", "video": str(missing), "length": 5, "stamp": wv.stamp(self.local)}), encoding="utf-8")
        code, out, err = self.invoke(run, "--at", "1")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("run the skill on the source again", err)
        self.local.rename(missing)

        def frame(*args, **kwargs):
            Path(args[-1]).write_bytes(b"picture")
            return subprocess.CompletedProcess([], 0, b"", b"")

        with patch.object(wv, "duration_of", return_value=5), patch.object(wv, "ffmpeg", side_effect=frame):
            code, out, err = self.invoke(run, "--at", "1")
        self.assertEqual(code, 0, err)
        self.assertTrue(Path(out.strip().split("\t")[1]).is_file())
        self.assertTrue(missing.exists())

    def test_scan_prints_detected_scene_ends_and_fills_gaps(self):
        """C3: the scan exposes scene evidence, not just 16 arbitrary tiles."""
        run = self.runs / "scan"
        run.mkdir()
        (run / "manifest.json").write_text(json.dumps({"tool": "watch-video", "video": str(self.local), "length": 50, "stamp": wv.stamp(self.local)}), encoding="utf-8")

        def detect(*args, cwd=None):
            note = next(a for a in args if "file=" in a).rsplit("file=", 1)[1]
            (cwd / note).write_text(
                "frame:0 pts:0 pts_time:0\nlavfi.scene_score=0\n"
                "frame:1 pts:1 pts_time:5.5\nlavfi.scene_score=0\n"
                "frame:2 pts:2 pts_time:6\nlavfi.scene_score=0.9\n"
                "frame:3 pts:3 pts_time:17.5\nlavfi.scene_score=0\n"
                "frame:4 pts:4 pts_time:18\nlavfi.scene_score=0.9\n", encoding="utf-8")
            return subprocess.CompletedProcess([], 0, b"", b"")

        def sheets(video, times, prefix):
            for page in range((len(times) + 15) // 16):
                Path(f"{prefix}{page + 1:02d}.jpg").write_bytes(b"sheet")
            return times

        with patch.object(wv, "duration_of", return_value=50), patch.object(wv, "ffmpeg", side_effect=detect), patch.object(wv, "sheets", side_effect=sheets):
            code, out, err = self.invoke(run, "--scan", "10-40")
        self.assertEqual(code, 0, err)
        printed = []
        for line in out.splitlines():
            path, times = line.split("\t")
            self.assertTrue(Path(path).is_file())
            printed.extend(times.split())
        self.assertIn("00:15.5", printed)
        self.assertIn("00:27.5", printed)
        self.assertEqual(len(printed) % 16, 0)
        moments = [10] + [wv.to_seconds(value) for value in printed] + [40]
        self.assertLessEqual(max(b - a for a, b in zip(moments, moments[1:])), 10)

    def test_interrupt_after_transcript_keeps_evidence_for_followup(self):
        """C4/C5: a cancelled overview leaves its printed transcript readable."""
        with patch.object(wv, "streams", return_value={"video"}), patch.object(wv, "duration_of", return_value=5), patch.object(wv, "overview", side_effect=KeyboardInterrupt):
            code, out, err = self.invoke(self.local)
        self.assertEqual(code, 130)
        self.assertIn("none (no audio stream)", self.transcript(out))
        self.assertIn("watch-video: interrupted", err)
        self.assertNotIn("frames:", out)
        run = next(self.runs.iterdir())
        self.assertEqual(wv.video_of(run)[0], self.local.resolve())

    def test_asr_failure_keeps_frames(self):
        """C2: a failed transcription still gives the video's frames, and says why speech is missing."""
        with patch.object(wv, "streams", return_value={"audio", "video"}), patch.object(wv, "duration_of", return_value=5), \
                patch.object(wv, "run_asr", side_effect=wv.WatchError("Local ASR failed: model unavailable")), \
                patch.object(wv, "overview", return_value="16 tiles on 1 sheet"):
            code, out, err = self.invoke(self.local)
        self.assertEqual(code, 0, err)
        self.assertIn("Transcript: none (Local ASR failed: model unavailable)\n", self.transcript(out))  # no "no speech found"
        self.assertIn("frames: ", out)
        self.assertNotIn("frames: none", out)

    def test_at_with_no_frame_fails(self):
        """C3: --at that writes no frame is a failure, not an empty success."""
        run = self.runs / "noframe"
        run.mkdir()
        (run / "manifest.json").write_text(json.dumps({"tool": "watch-video", "video": str(self.local), "length": 5,
                                                       "stamp": wv.stamp(self.local)}), encoding="utf-8")
        with patch.object(wv, "ffmpeg", return_value=subprocess.CompletedProcess([], 1, b"", b"bad")):
            code, out, err = self.invoke(run, "--at", "1")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("no frame could be read", err)

    def test_missing_ffmpeg_is_actionable(self):
        """C8: without ffmpeg on PATH the error says what to install."""
        real = wv.shutil.which
        with patch.object(wv.shutil, "which", side_effect=lambda tool: None if tool == "ffprobe" else real(tool)):
            for args in ((self.local,), (self.runs, "--at", "1")):
                code, out, err = self.invoke(*args)
                self.assertEqual(code, 2)
                self.assertIn("ffprobe not on PATH: install ffmpeg", err)

    def test_output_error_on_one_video_spares_the_next(self):
        """C3: a filesystem error writing video 1's -o file is that video's failure; video 2 still runs."""
        entries = [(1, {"id": "one", "title": "First"}, None), (2, {"id": "two", "title": "Second"}, None)]
        captions = wv.Transcript("en", "manual captions", [wv.Segment(0, 1, "words")])
        output = self.root / "chosen.md"
        (self.root / "chosen-1.md").mkdir()
        with patch.object(wv, "entries_of", return_value=entries), patch.object(wv, "caption_transcript", return_value=captions):
            code, out, err = self.invoke("https://example.test/post", "--transcript-only", "-o", output)
        self.assertEqual(code, 2)
        self.assertIn("video 1: failed (", out)
        self.assertIn("video 2: Second", out)
        self.assertTrue((self.root / "chosen-2.md").is_file())

    def test_real_sheet_and_full_frame_dimensions(self):
        """C3/C6: native ffmpeg writes the promised sheet/frame geometry."""
        video = self.root / "short clip.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        "color=c=red:s=80x60:r=30:d=2", str(video)], check=True, capture_output=True)
        code, out, err = self.invoke(video)
        self.assertEqual(code, 0, err)
        run = next(self.runs.iterdir())
        self.assertIn("16 tiles on 1 sheet", out)

        def dimensions(path):
            done = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "json", str(path)],
                                  check=True, capture_output=True, text=True)
            info = json.loads(done.stdout)["streams"][0]
            return info["width"], info["height"]

        self.assertEqual(dimensions(run / "overview_01.jpg"), (1280, 720))
        code, out, err = self.invoke(run, "--at", "1")
        self.assertEqual(code, 0, err)
        frame = Path(out.strip().split("\t")[1])
        self.assertEqual(dimensions(frame)[1], 720)


if __name__ == "__main__":
    unittest.main()
