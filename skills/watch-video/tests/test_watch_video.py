"""Offline checks for watch_video.py: synthetic ffmpeg media, no network.

    python3 tests/test_watch_video.py      (py -3 on Windows)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "watch_video.py"
sys.path.insert(0, str(SCRIPT.parent))
import watch_video as wv  # noqa: E402


def make(path: Path, seconds: int, audio: bool) -> Path:
    """Colour-bar video that changes every 5 s (scene cuts), optionally with a tone."""
    inputs = ["-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=10:duration={seconds}",
              "-f", "lavfi", "-i", f"color=c=red:size=640x360:rate=10:duration={seconds}"]
    graph = "[0:v][1:v]blend=all_expr='if(lt(mod(T,10),5),A,B)'[v]"
    args = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *inputs]
    if audio:
        args += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}"]
    args += ["-filter_complex", graph, "-map", "[v]"] + (["-map", "2:a"] if audio else []) + ["-shortest", str(path)]
    subprocess.run(args, check=True)
    return path


def run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env)


class TimeSyntax(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(wv.parse_times("494,8:14,1:02:05.5", 4000, scan=False),
                         [(494, 494, 4), (494, 494, 4), (3725.5, 3725.5, 4)])
        self.assertEqual(wv.parse_times("7:50-8:50/12", 600, scan=False), [(470, 530, 12)])
        self.assertEqual(wv.parse_times("all", 90, scan=True), [(0.0, 90, 0)])

    def test_rejects(self):
        for spec, length, scan in (("00:08:14,500", 900, False), ("9:00", 300, False), ("8:14", 900, True),
                                   ("8:14/3", 900, False), ("8:50-7:50", 900, False), ("1:00-2:00/41", 900, False),
                                   ("abc", 900, False)):
            with self.subTest(spec=spec), self.assertRaises(wv.WatchError):
                wv.parse_times(spec, length, scan)

    def test_clock_rounds_before_splitting(self):
        self.assertEqual(wv.clock(119.97), "02:00.0")
        self.assertEqual(wv.clock(6250), "104:10.0")


class Speech(unittest.TestCase):
    def test_window_and_pause(self):
        segments = [wv.Segment(0, 2, "a"), wv.Segment(2, 4, "b"), wv.Segment(4, 6, "c"), wv.Segment(20, 22, "d")]
        self.assertEqual(wv.speech_near(segments, 3), ("00:00.0-00:06.0", "a b c"))
        self.assertEqual(wv.speech_near(segments, 8), ("00:02.0-00:06.0", "b c"))  # pause just after "c"
        self.assertEqual(wv.speech_near(segments, 15), ("-", ""))


class LocalFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.env = dict(os.environ, TMP=cls.tmp.name, TEMP=cls.tmp.name, TMPDIR=cls.tmp.name)
        folder = Path(cls.tmp.name) / "a folder with spaces"
        folder.mkdir()
        cls.silent = make(folder / "silent clip.mp4", 200, audio=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def frames_dir(self, out: str) -> Path:
        line = next(line for line in out.splitlines() if line.startswith("frames: "))
        return Path(line[len("frames: "):].rsplit(" (", 1)[0])

    def test_silent_video_gets_frames_and_index(self):
        done = run(str(self.silent), env=self.env)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("none (no audio stream)", Path(done.stdout.split("transcript: ")[1].splitlines()[0]).read_text("utf-8"))
        run_dir = self.frames_dir(done.stdout)
        index = (run_dir / "index.txt").read_text("utf-8").splitlines()
        self.assertEqual(len(index), 16)  # 200 s: round(200/160) = 1 sheet
        self.assertEqual(index[0].split("\t")[1], "overview_01.jpg#01")
        self.assertEqual(sorted(p.name for p in run_dir.glob("overview_*.jpg")), ["overview_01.jpg"])
        self.assertEqual(json.loads((run_dir / "manifest.json").read_text("utf-8"))["video"], str(self.silent.resolve()))

        at = run(str(run_dir), "--at", "0:30,1:00-1:20/3", env=self.env)
        self.assertEqual(at.returncode, 0, at.stderr)
        frames = [Path(line.split("\t")[1]) for line in at.stdout.splitlines()]
        self.assertEqual(len(frames), 4)
        self.assertTrue(all(f.is_file() and f.stat().st_size for f in frames))

        scan = run(str(run_dir), "--scan", "0:00-1:00", env=self.env)
        self.assertEqual(scan.returncode, 0, scan.stderr)
        self.assertNotIn("scene detection failed", scan.stderr)
        times = scan.stdout.split("\t", 1)[1].split()
        self.assertEqual(len(times), 16)  # 60 s: scene ends + fill, padded to a full sheet
        for cut in ("00:04.5", "00:09.5", "00:14.5"):  # the last 2 fps sample before each 5 s cut
            self.assertIn(cut, times)
        self.assertTrue(Path(scan.stdout.split("\t")[0]).is_file())

        again = run(str(self.silent), env=self.env)  # a rerun gets its own folder and keeps the first
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertNotEqual(self.frames_dir(again.stdout), run_dir)
        self.assertTrue((run_dir / "index.txt").is_file())

    def test_changed_source_is_refused(self):
        clip = make(Path(self.tmp.name) / "changing.mp4", 20, audio=False)
        done = run(str(clip), env=self.env)
        self.assertEqual(done.returncode, 0, done.stderr)
        make(clip, 30, audio=False)
        at = run(str(self.frames_dir(done.stdout)), "--at", "0:05", env=self.env)
        self.assertEqual(at.returncode, 2)
        self.assertIn("has changed since this run", at.stderr)

    def test_output_cannot_overwrite_the_source(self):
        before = self.silent.read_bytes()
        link = Path(self.tmp.name) / "hardlink.md"
        os.link(self.silent, link)
        for target in (self.silent, link):  # the same path, or another name for the same file
            done = run(str(self.silent), "-o", str(target), env=self.env)
            self.assertEqual(done.returncode, 2)
            self.assertEqual(self.silent.read_bytes(), before)

    def test_transcript_only_has_no_frames(self):
        done = run(str(self.silent), "--transcript-only", env=self.env)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn("frames:", done.stdout)

    def test_missing_video_is_actionable(self):
        empty = Path(self.tmp.name) / "not-a-run"
        empty.mkdir(exist_ok=True)
        done = run(str(empty), "--at", "0:01", env=self.env)
        self.assertEqual(done.returncode, 2)
        self.assertIn("run the skill on the source again", done.stderr)

    def test_prune_leaves_originals_and_foreign_folders(self):
        runs = Path(self.tmp.name) / "watch-video"
        old, foreign = runs / "old-run", runs / "not-ours"
        for folder in (old, foreign):
            folder.mkdir(parents=True, exist_ok=True)
        (old / "manifest.json").write_text(json.dumps({"tool": "watch-video", "video": str(self.silent)}), encoding="utf-8")
        (foreign / "manifest.json").write_text(json.dumps({"video": str(self.silent)}), encoding="utf-8")
        stale = time.time() - 4 * 86400
        for folder in (old, foreign):
            os.utime(folder / "manifest.json", (stale, stale))
        done = run(str(self.silent), "--transcript-only", env=self.env)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertFalse(old.exists())
        self.assertTrue(foreign.exists())
        self.assertTrue(self.silent.is_file())


if __name__ == "__main__":
    unittest.main()
