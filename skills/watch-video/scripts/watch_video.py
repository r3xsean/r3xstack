#!/usr/bin/env python3
"""Watch a video: transcript, details and what is on screen.

    watch_video.py <url-or-file> [--transcript-only] [-l LANG] [-o FILE] [--no-timestamps]
    watch_video.py <run-dir> --at TIMES      full frames: 494, 8:14, 1:02:05.5, 7:50-8:50 (4 frames), 7:50-8:50/12
    watch_video.py <run-dir> --scan RANGES   contact sheets of a stretch: 50:00-60:00, or all

Captions come first; without usable captions the audio is transcribed locally with
faster-whisper. A video run also saves overview sheets (4x4 contact sheets of evenly
spaced tiles) and index.txt, mapping each tile to the speech around it. Runs live in
<temp>/watch-video/ and are pruned after 3 days. No API key is used.

The overview, --at and --scan are adapted from vidscribe (MIT, Copyright (c) 2026
Samuel Zhang); its notice is in NOTICE-vidscribe.md beside this script.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

if os.name == "nt":
    import msvcrt
else:
    import fcntl
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.request import Request, urlopen

try:
    import yt_dlp
except ImportError:  # pragma: no cover - exercised only on incomplete setups
    yt_dlp = None

NAME = "watch-video"
RUNS = Path(tempfile.gettempdir()) / NAME
KEEP_DAYS = 3
MAX_ENTRIES = 10  # videos in one post; more than this is a playlist or channel
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class WatchError(RuntimeError):
    """An expected, actionable failure."""


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    language: str
    method: str
    segments: list[Segment] = field(default_factory=list)


TAG_RE = re.compile(r"<[^>]+>")
TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[.,]\d{3}|\d{1,2}:\d{2}[.,]\d{3})"
    r"\s+-->\s+"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[.,]\d{3}|\d{1,2}:\d{2}[.,]\d{3})"
)


# ------------------------------------------------------------------ captions


def clean_text(value: str) -> str:
    value = html.unescape(TAG_RE.sub("", value))
    return re.sub(r"\s+", " ", value).strip()


def normalized_caption_language(language: str) -> str:
    language = language.lower()
    return language[:-5] if language.endswith("-orig") else language


def language_rank(track_language: str, preferred: str) -> tuple[int, str]:
    """Rank exact language first, same primary language second, then all others."""
    track = normalized_caption_language(track_language)
    wanted = preferred.lower()
    if track == wanted:
        return (0, track)
    if track.split("-")[0] == wanted.split("-")[0]:
        return (1, track)
    return (2, track)


def select_caption(info: dict[str, Any], preferred: str | None) -> tuple[str, dict[str, Any], str] | None:
    """Choose the most useful JSON3/VTT caption track with stable priorities."""
    target = preferred or info.get("original_language") or info.get("language")
    candidates: list[tuple[tuple[int, int, int, int, str], str, dict[str, Any], str, bool, int]] = []
    for source_rank, (collection_name, method) in enumerate(
        (("subtitles", "manual captions"), ("automatic_captions", "automatic captions"))
    ):
        for language, tracks in (info.get(collection_name) or {}).items():
            for track in tracks or []:
                extension = track.get("ext", "")
                if extension not in {"json3", "vtt"} or not track.get("url"):
                    continue
                original = language.lower().endswith("-orig") or "(original)" in track.get("name", "").lower()
                language_priority, language_name = language_rank(language, target) if target else (0, language.lower())
                candidates.append((
                    (language_priority, source_rank, 0 if original else 1, 0 if extension == "json3" else 1, language_name),
                    language, track, method, original, source_rank,
                ))
    if not candidates:
        return None
    if not target:
        manual = [candidate for candidate in candidates if candidate[5] == 0]
        original = [candidate for candidate in candidates if candidate[4]]
        if manual:
            candidates = manual
        elif original:
            candidates = original
        elif len({normalized_caption_language(candidate[1]) for candidate in candidates}) > 1:
            return None
    _, language, track, method, _, _ = min(candidates, key=lambda item: item[0])
    return normalized_caption_language(language), track, method


def download_caption(track: dict[str, Any]) -> bytes:
    request = Request(track["url"], headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=45) as response:
        return response.read()


def parse_timestamp(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    hours, minutes, seconds = parts
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def parse_json3(payload: bytes) -> list[Segment]:
    data = json.loads(payload.decode("utf-8-sig"))
    segments: list[Segment] = []
    for event in data.get("events", []):
        text = clean_text("".join(piece.get("utf8", "") for piece in event.get("segs") or []))
        if not text:
            continue
        start = event.get("tStartMs", 0) / 1000
        segments.append(Segment(start, start + event.get("dDurationMs", 0) / 1000, text))
    return deduplicate_segments(segments)


def parse_vtt(payload: bytes) -> list[Segment]:
    lines = payload.decode("utf-8-sig", errors="replace").replace("\r", "").split("\n")
    segments: list[Segment] = []
    index = 0
    while index < len(lines):
        timing = TIMESTAMP_RE.search(lines[index])
        if not timing:
            index += 1
            continue
        text_lines: list[str] = []
        index += 1
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index])
            index += 1
        text = clean_text(" ".join(text_lines))
        if text:
            segments.append(Segment(parse_timestamp(timing["start"]), parse_timestamp(timing["end"]), text))
    return deduplicate_segments(segments)


def deduplicate_segments(segments: Iterable[Segment]) -> list[Segment]:
    """Remove exact repeats common in auto-caption streams without merging words."""
    result: list[Segment] = []
    previous = ""
    for segment in segments:
        if segment.text != previous:
            result.append(segment)
            previous = segment.text
    return result


def caption_transcript(info: dict[str, Any], preferred_language: str | None) -> Transcript | None:
    selected = select_caption(info, preferred_language)
    if not selected:
        return None
    language, track, method = selected
    try:
        payload = download_caption(track)
        segments = parse_json3(payload) if track.get("ext") == "json3" else parse_vtt(payload)
    except (OSError, UnicodeError, ValueError) as exc:
        raise WatchError(f"Could not retrieve the selected {method}: {exc}") from exc
    return Transcript(language, method, segments) if segments else None


# ------------------------------------------------------------------ local speech recognition


def run_whisper(audio_path: Path, model_name: str, requested_language: str | None) -> tuple[str, list[Segment]]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    language = requested_language.split("-")[0] if requested_language else None
    stream, detected = model.transcribe(
        str(audio_path), language=language, beam_size=5, vad_filter=True, condition_on_previous_text=False
    )
    segments = [Segment(item.start, item.end, clean_text(item.text)) for item in stream if clean_text(item.text)]
    return getattr(detected, "language", requested_language or "unknown"), segments


def exclusive_lock(handle) -> None:
    if os.name == "nt":
        # msvcrt.locking gives up after ~10 seconds; a first-time model install
        # can hold the lock far longer than that, so keep retrying.
        while True:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                return
            except OSError:
                time.sleep(1)
    else:
        fcntl.flock(handle, fcntl.LOCK_EX)


def asr_runtime_python() -> Path:
    """Create and maintain the isolated ASR runtime only when it is needed."""
    # Kept at the skill's former name on purpose: existing installs on both machines live here,
    # and a venv can't be moved (its scripts hold absolute paths).
    runtime = Path.home() / ".cache" / "transcribe-youtube"
    environment = runtime / "venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime / "install.lock").open("w") as lock_file:
        exclusive_lock(lock_file)
        ready = python.is_file() and subprocess.run(
            [str(python), "-c", "import faster_whisper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=NO_WINDOW,
        ).returncode == 0
        try:
            if not python.is_file():
                subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
            if not ready:
                subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "faster-whisper"], check=True)
        except subprocess.CalledProcessError as exc:
            raise WatchError(f"Could not install the local ASR fallback: {exc}") from exc
    return python


def run_asr(media: Path, args: argparse.Namespace) -> Transcript:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        command = [str(asr_runtime_python()), str(Path(__file__).resolve()), "--asr-worker",
                   "--audio", str(media), "--model", args.model]
        if args.language:
            command.extend(["--language", args.language])
        completed = subprocess.run(command, capture_output=True, text=True, creationflags=NO_WINDOW)
        if completed.returncode:
            raise WatchError(f"Local ASR failed: {completed.stderr.strip() or 'no error message'}")
        try:
            result = json.loads(completed.stdout)
            language, segments = result["language"], [Segment(**segment) for segment in result["segments"]]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise WatchError("Local ASR returned an invalid result.") from exc
    else:
        try:
            language, segments = run_whisper(media, args.model, args.language)
        except Exception as exc:
            raise WatchError(f"Local ASR failed: {exc}") from exc
    return Transcript(language, f"local ASR ({args.model})", segments)


# ------------------------------------------------------------------ media


def ffmpeg(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *args],
                          capture_output=True, cwd=cwd, creationflags=NO_WINDOW)


def streams(media: Path) -> set[str]:
    """Stream kinds in a file: 'audio' and/or 'video' (cover art is not video)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type:stream_disposition=attached_pic",
         "-of", "json", str(media)], capture_output=True, text=True, creationflags=NO_WINDOW,
    )
    if out.returncode:
        raise WatchError(f"ffprobe could not read {media.name}: {out.stderr.strip()[-300:]}")
    kinds = set()
    for stream in json.loads(out.stdout or "{}").get("streams", []):
        if stream.get("codec_type") == "video" and stream.get("disposition", {}).get("attached_pic"):
            continue
        kinds.add(stream.get("codec_type"))
    return kinds


def duration_of(media: Path) -> float:
    """Seconds, or 0.0 when the container gives no usable length."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1",
                          str(media)], capture_output=True, text=True, creationflags=NO_WINDOW)
    try:
        return max(0.0, float(out.stdout.strip())) if out.returncode == 0 else 0.0
    except ValueError:  # "N/A"
        return 0.0


def clock(seconds: float) -> str:
    """mm:ss.s, minutes unbounded (104:10.0); --at reads it back."""
    seconds = round(seconds, 1)
    return f"{int(seconds // 60):02d}:{seconds % 60:04.1f}"


def ydl_options(args: argparse.Namespace, **extra: Any) -> dict[str, Any]:
    options: dict[str, Any] = {"quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True, **extra}
    if args.cookies:
        options["cookiefile"] = str(args.cookies)
    return options


def download(args: argparse.Namespace, entry: int | None, run: Path, stem: str, fmt: str) -> Path:
    options = ydl_options(args, format=fmt, outtmpl=str(run / f"{stem}.%(ext)s"), merge_output_format="mp4")
    if entry:
        options["playlist_items"] = str(entry)
    for attempt in (1, 2):  # YouTube sometimes answers 403 once and serves the retry
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([args.source])
            break
        except Exception as exc:
            if attempt == 2:
                raise WatchError(f"download failed: {exc}") from exc
            for partial in run.glob(f"{stem}.*"):
                partial.unlink(missing_ok=True)
    found = [path for path in run.glob(f"{stem}.*") if not path.name.endswith((".part", ".ytdl"))]
    if len(found) != 1:
        raise WatchError(f"download finished but {stem}.* could not be found in {run}")
    return found[0]


# ------------------------------------------------------------------ sheets, frames and scans


def sheets(video: Path, times: list[float], prefix: Path) -> list[float]:
    """One 318x178 tile per time on 4x4 sheets of 1280x720 (prefix01.jpg, ...). Returns the times that gave a
    picture and reports the rest on stderr; raises when none did."""
    for old in prefix.parent.glob(prefix.name + "*.jpg"):
        old.unlink()
    with tempfile.TemporaryDirectory(prefix=NAME + "-") as tmp:
        def grab(item: tuple[int, float]) -> bool:
            index, moment = item
            tile = Path(tmp) / f"{index:04d}.jpg"
            done = ffmpeg("-ss", f"{moment:.2f}", "-i", str(video), "-frames:v", "1", "-q:v", "2", "-vf",
                          "scale=318:178:force_original_aspect_ratio=decrease,pad=318:178:(ow-iw)/2:(oh-ih)/2", str(tile))
            return done.returncode == 0 and tile.is_file() and tile.stat().st_size > 0
        with ThreadPoolExecutor(4) as pool:
            got = list(pool.map(grab, enumerate(times)))
        kept = [moment for moment, ok in zip(times, got) if ok]
        for number, index in enumerate(i for i, ok in enumerate(got) if ok):  # renumber without gaps
            (Path(tmp) / f"{index:04d}.jpg").rename(Path(tmp) / f"s{number:04d}.jpg")
        if kept:
            made = ffmpeg("-framerate", "1", "-i", str(Path(tmp) / "s%04d.jpg"), "-vf",
                          "tile=4x4:padding=2:margin=1:color=white", "-q:v", "3", str(prefix).replace("%", "%%") + "%02d.jpg")
            if made.returncode:
                raise WatchError(f"could not build sheets: {made.stderr.decode(errors='replace').strip()[-300:]}")
    missed = [moment for moment, ok in zip(times, got) if not ok]
    if not kept:
        raise WatchError(f"no picture could be read at any of {len(times)} times")
    if missed:
        print(f"no picture at {len(missed)} of {len(times)} times ({', '.join(clock(t) for t in missed[:8])}"
              f"{', ...' if len(missed) > 8 else ''}): those tiles are left out", file=sys.stderr)
    return kept


def speech_near(segments: list[Segment], moment: float) -> tuple[str, str]:
    """The speech around a moment: the segment at it plus one either side within 10 s, from real segment times."""
    hit = next((i for i, s in enumerate(segments) if s.start <= moment < s.end), None)
    if hit is None:  # in a pause: the segment that ended within 5 s before it
        hit = next((i for i in range(len(segments) - 1, -1, -1)
                    if segments[i].start <= moment and moment - segments[i].end < 5), None)
    if hit is None:
        return "-", ""
    window = [s for i, s in enumerate(segments[max(0, hit - 1):hit + 2], max(0, hit - 1))
              if i == hit or (s.start - moment <= 10 and moment - s.end <= 10)]
    return f"{clock(window[0].start)}-{clock(window[-1].end)}", " ".join(s.text for s in window)


def overview(run: Path, video: Path, length: float, segments: list[Segment]) -> str:
    if length <= 0:
        raise WatchError("the video's length is unknown, so no tiles could be placed")
    count = 16 * min(6, max(1, math.floor(length / 160 + 0.5)))  # every sheet full: one per ~160 s, 1 to 6
    kept = sheets(video, [length * (i + 0.5) / count for i in range(count)], run / "overview_")
    lines = []
    for position, moment in enumerate(kept):
        span, text = speech_near(segments, moment)
        lines.append("\t".join((clock(moment), f"overview_{position // 16 + 1:02d}.jpg#{position % 16 + 1:02d}", span, text)))
    (run / "index.txt").write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    pages = math.ceil(len(kept) / 16)
    return f"{len(kept)} tiles on {pages} sheet{'s' * (pages != 1)}, one every {length / count:.1f} s"


def to_seconds(text: str) -> float:
    total = 0.0
    for part in text.split(":"):
        total = total * 60 + float(part)
    return total


def parse_times(spec: str, length: float, scan: bool) -> list[tuple[float, float, int]]:
    """'494,8:14,7:50-8:50,7:50-8:50/12' -> (start, end, count); scan takes ranges or 'all'."""
    if scan and spec.strip() == "all":
        return [(0.0, length, 0)]
    one = r"\d+(?::[0-5]?\d){0,2}(?:\.\d+)?"
    result, previous = [], ""
    for item in [part.strip() for part in spec.split(",")]:
        if re.fullmatch(r"\d{3}", item) and re.fullmatch(r"\d+:\d+:\d+", previous):
            raise WatchError(f'"{previous},{item}" looks like an srt time: use a dot ({previous}.{item})')
        previous = item
        match = re.fullmatch(rf"({one})(?:-({one}))?(?:/(\d+))?", item)
        if not match:
            usage = "50:00-60:00 or all" if scan else "494, 8:14, 1:02:05, 7:50-8:50 or 7:50-8:50/8"
            raise WatchError(f'bad time "{item}" (use {usage})')
        start = to_seconds(match[1])
        end = to_seconds(match[2]) if match[2] else start
        count = int(match[3]) if match[3] else 4
        if scan and (not match[2] or match[3]):
            raise WatchError(f'"{item}": --scan takes plain ranges (use --at for single times)')
        if match[3] and (not match[2] or not 1 <= count <= 40):
            raise WatchError(f'"{item}": a count needs a range and must be 1-40')
        if match[2] and end <= start:
            raise WatchError(f"range {item} ends before it starts")
        if end > length or (end == length and not scan):
            raise WatchError(f"{item} is past the end of the video ({int(length)} s)")
        result.append((start, end, count))
    return result


def at(run: Path, video: Path, length: float, spec: str) -> None:
    seen: set[str] = set()
    made = 0
    for start, end, count in parse_times(spec, length, scan=False):
        for moment in [start] if start == end else [start + (end - start) * (j + 0.5) / count for j in range(count)]:
            frame = run / f"at_{clock(moment).replace(':', 'm')}s.jpg"
            if frame.name in seen:
                continue
            seen.add(frame.name)
            done = ffmpeg("-ss", f"{moment:.2f}", "-i", str(video), "-frames:v", "1", "-q:v", "3", "-vf", "scale=-2:720", str(frame))
            if done.returncode == 0 and frame.is_file() and frame.stat().st_size:
                print(f"{clock(moment)}\t{frame}")
                made += 1
            else:
                print(f"no frame at {clock(moment)}", file=sys.stderr)
    if not made:
        raise WatchError("no frame could be read at any requested time")


def scene_ends(run: Path, video: Path, start: float, end: float) -> list[float]:
    """The last 2 fps sample before each scene change (score > 0.3) in start..end."""
    begin = math.floor(start * 2) / 2
    note = f"scene_{secrets.token_hex(4)}.txt"  # relative, with cwd=run: an absolute Windows path breaks the filtergraph
    done = ffmpeg("-ss", f"{begin:.3f}", "-t", f"{end - begin:.3f}", "-i", str(video), "-an", "-vf",
                  f"fps=2,scale=160:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score:file={note}",
                  "-f", "null", "-", cwd=run)
    path = run / note
    if done.returncode or not path.is_file():
        print(f"scan: scene detection failed, even tiles only ({done.stderr.decode(errors='replace').strip()[-200:]})",
              file=sys.stderr)
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    path.unlink()
    times = [float(x) + begin for x in re.findall(r"pts_time:([\d.]+)", text)]
    scores = [float(x) for x in re.findall(r"scene_score=([\d.]+)", text)]
    return sorted({times[i - 1] for i in range(1, min(len(times), len(scores)))
                   if scores[i] > 0.3 and start <= times[i - 1] < end})


def scan(run: Path, video: Path, length: float, spec: str) -> None:
    """Scene ends plus even fill so no gap exceeds 10 s, rounded up to full sheets of 16."""
    for start, end, _ in parse_times(spec, length, scan=True):
        ends = scene_ends(run, video, start, end)
        edges = [start, *ends, end]
        gaps = [b - a for a, b in zip(edges, edges[1:])]
        fill = [max(0, math.ceil(gap / 10) - 1) for gap in gaps]
        total = len(ends) + sum(fill)
        for _ in range(max(16, -(-total // 16) * 16) - total):  # a sheet costs the same with 5 tiles as with 16
            widest = max(range(len(gaps)), key=lambda i: gaps[i] / (fill[i] + 1))
            fill[widest] += 1
        times = sorted(ends + [a + (b - a) * j / (m + 1) for a, b, m in zip(edges, edges[1:], fill) for j in range(1, m + 1)])
        prefix = run / f"scan_{clock(start).replace(':', 'm')}s-{clock(end).replace(':', 'm')}s_"
        kept = sheets(video, times, prefix)
        print(f"{clock(start)}-{clock(end)}: {len(kept)} tiles, {math.ceil(len(kept) / 16)} sheets", file=sys.stderr)
        for page in range(math.ceil(len(kept) / 16)):
            print(f"{prefix}{page + 1:02d}.jpg\t" + " ".join(clock(t) for t in kept[page * 16:(page + 1) * 16]))


# ------------------------------------------------------------------ runs


def write_manifest(run: Path, **fields: Any) -> None:
    (run / "manifest.json").write_text(json.dumps({"tool": NAME, **fields}), encoding="utf-8")


def stamp(path: Path) -> list[int]:
    info = path.stat()
    return [info.st_size, info.st_mtime_ns]


def prune() -> None:
    """Delete this script's runs, finished or not, unused for KEEP_DAYS. A local source is never inside one."""
    cutoff = time.time() - KEEP_DAYS * 86400
    for run in RUNS.glob("*"):
        manifest = run / "manifest.json"
        try:  # another run may be pruning the same folder
            owned = json.loads(manifest.read_text(encoding="utf-8")).get("tool") == NAME
            if owned and manifest.stat().st_mtime < cutoff:
                shutil.rmtree(run, ignore_errors=True)
        except (OSError, ValueError, AttributeError):
            continue


def new_run(key: str, source: str) -> Path:
    """A fresh folder per run, so a retry or a parallel run never touches an earlier one."""
    slug = re.sub(r"[^\w-]+", "_", key)[:40].strip("_") or "video"
    run = RUNS / f"{slug}-{hashlib.sha1(key.encode()).hexdigest()[:6]}-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(2)}"
    run.mkdir(parents=True)
    write_manifest(run, source=source)
    return run


def video_of(run: Path) -> tuple[Path, float]:
    manifest = run / "manifest.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    video = Path(data["video"]) if data.get("video") else None
    if not video or not video.is_file():
        raise WatchError(f"no video for {run} (runs are pruned after {KEEP_DAYS} days; a local original may have "
                         "moved): run the skill on the source again")
    if stamp(video) != data.get("stamp"):
        raise WatchError(f"{video} has changed since this run: run the skill on it again")
    os.utime(manifest)  # in use: keep it another KEEP_DAYS
    return video, float(data["length"])


def header(info: dict[str, Any], source: str, transcript: Transcript, length: float) -> list[str]:
    def known(value: Any) -> str:
        return str(value) if value not in (None, "") else "unknown"

    date = info.get("upload_date")
    lines = [
        f"# {info.get('title') or Path(source).stem}", "",
        f"Source: {info.get('webpage_url') or source}",
        f"Channel: {known(info.get('uploader') or info.get('channel'))}",
        f"Uploaded: {f'{date[:4]}-{date[4:6]}-{date[6:]}' if date and len(date) == 8 else 'unknown'}",
        f"Length: {clock(length) if length else 'unknown'}",
        f"Language: {transcript.language}",
        f"Transcript: {transcript.method}",
    ]
    chapters = info.get("chapters") or []
    if chapters:
        lines += ["", "Chapters:"] + [f"- {clock(c.get('start_time') or 0)} {c.get('title') or ''}" for c in chapters]
    return lines + [""]


def render(lines: list[str], segments: list[Segment], timestamps: bool) -> str:
    body = [(f"[{clock(s.start)}] " if timestamps else "") + s.text for s in segments]
    return "\n".join(lines + body).rstrip() + "\n"


def entries_of(args: argparse.Namespace) -> list[tuple[int | None, dict[str, Any] | None, str | None]]:
    """One (entry number, info, error) per video: a post with several videos gives several."""
    if yt_dlp is None:
        raise WatchError("yt-dlp is not installed for this Python. Install it with: python -m pip install -U yt-dlp")
    try:
        with yt_dlp.YoutubeDL(ydl_options(args, skip_download=True, extract_flat="in_playlist")) as downloader:
            info = downloader.extract_info(args.source, download=False)
    except Exception as exc:
        raise WatchError(f"Could not access the video: {exc}") from exc
    if info.get("_type") not in ("playlist", "multi_video"):
        return [(None, info, None)]  # a single video is extracted in full even with extract_flat
    count = len(list(info.get("entries") or []))
    if not count or count > MAX_ENTRIES:
        raise WatchError(f"this link is a playlist or channel ({count} entries): pass one video's link")
    found: list[tuple[int | None, dict[str, Any] | None, str | None]] = []
    for number in range(1, count + 1):
        try:
            with yt_dlp.YoutubeDL(ydl_options(args, skip_download=True, playlist_items=str(number))) as downloader:
                entry = downloader.extract_info(args.source, download=False)
            entry = (list(entry.get("entries") or []) or [entry])[0] if entry.get("_type") else entry
            found.append((number, entry, None))
        except Exception as exc:
            found.append((number, None, f"Could not access this video: {exc}"))
    return found


def watch(args: argparse.Namespace, number: int | None, info: dict[str, Any], local: Path | None) -> None:
    key = str(local) if local else f"{info.get('extractor_key', '')}-{info.get('id') or args.source}"
    run = new_run(key, args.source)
    transcript = None if (args.force_asr or local) else caption_transcript(info, args.language)
    media = local
    visual_error = None
    if not local:
        if args.transcript_only:
            if transcript is None:
                media = download(args, number, run, "audio", "bestaudio/best")
        else:
            # Video only when captions cover the words; with audio when the speech must be transcribed.
            fmt = "bv[height<=720]/b[height<=720]/b" if transcript else "bv[height<=720]+ba/b[height<=720]/b"
            try:
                media = download(args, number, run, "video", fmt)
            except WatchError as exc:
                if transcript is None:
                    raise
                visual_error = str(exc)
    kinds = streams(media) if media else set()
    if transcript is None:
        if "audio" in kinds:
            try:
                transcript = run_asr(media, args)
                if not transcript.segments:
                    transcript.method += ": no speech found"
            except WatchError as exc:
                if "video" not in kinds or args.transcript_only:
                    raise
                transcript = Transcript("unknown", f"none ({exc})")  # the frames are still worth having
        else:
            transcript = Transcript("none", "none (no audio stream)")
    length = (duration_of(media) if media else 0.0) or float(info.get("duration") or 0)
    text = render(header(info, args.source, transcript, length), transcript.segments, not args.no_timestamps)
    destination = run / "transcript.md"
    destination.write_text(text, encoding="utf-8")
    if args.output:
        out = args.output.expanduser().resolve()
        if number:
            out = out.with_name(f"{out.stem}-{number}{out.suffix}")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        destination = out
    keep = media if media and "video" in kinds and not args.transcript_only else None
    write_manifest(run, source=args.source, entry=number, length=length,
                   video=str(keep.resolve()) if keep else None, stamp=stamp(keep) if keep else None)
    if number:
        print(f"video {number}: {info.get('title') or ''}")
    print(f"transcript: {destination}")
    if args.transcript_only:
        if media and media != local:
            media.unlink(missing_ok=True)
        return
    if visual_error:
        print(f"frames: none ({visual_error})")
    elif "video" not in kinds:
        print("frames: none (no video stream)")
    else:
        try:
            print(f"frames: {run} ({overview(run, media, length, transcript.segments)})")
        except WatchError as exc:
            print(f"frames: none ({exc})")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch a video: transcript, details and what is on screen.")
    parser.add_argument("source", help="Video URL or local file; with --at/--scan, a run folder")
    inspect = parser.add_mutually_exclusive_group()
    inspect.add_argument("--at", metavar="TIMES", help="Full frames from a run: 494,8:14,7:50-8:50,7:50-8:50/12")
    inspect.add_argument("--scan", metavar="RANGES", help="Contact sheets of a stretch of a run: 50:00-60:00 or all")
    inspect.add_argument("--transcript-only", action="store_true", help="Transcript and details, no frames")
    parser.add_argument("--language", "-l", help="Prefer this language (for example en or es-MX)")
    parser.add_argument("--output", "-o", type=Path, help="Also write the transcript to this file")
    parser.add_argument("--no-timestamps", action="store_true", help="Omit per-line timestamps")
    parser.add_argument("--force-asr", action="store_true", help="Skip caption tracks")
    parser.add_argument("--model", default="base", help="faster-whisper model for the audio fallback (default: base)")
    parser.add_argument("--cookies", type=Path, help="Netscape-format cookie file for videos requiring login")
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    try:
        missing = [tool for tool in ("ffmpeg", "ffprobe") if not shutil.which(tool)]
        if missing:
            raise WatchError(f"{' and '.join(missing)} not on PATH: install ffmpeg (winget install Gyan.FFmpeg, "
                             "or brew install ffmpeg)")
        if args.at or args.scan:
            run = Path(args.source).expanduser().resolve()
            video, length = video_of(run)
            at(run, video, length, args.at) if args.at else scan(run, video, length, args.scan)
            return 0
        if args.cookies and not args.cookies.is_file():
            raise WatchError(f"Cookie file does not exist: {args.cookies}")
        local = Path(args.source).expanduser()
        if args.output:
            out = args.output.expanduser().resolve()
            runs = RUNS.resolve()
            same = local.is_file() and (out == local.resolve() or (out.exists() and os.path.samefile(out, local)))
            if same or out == runs or runs in out.parents:
                raise WatchError("--output must not be the source video or inside the run folders")
        RUNS.mkdir(parents=True, exist_ok=True)
        prune()
        if local.is_file():
            watch(args, None, {"title": local.stem}, local.resolve())
            return 0
        failed = 0
        for number, info, error in entries_of(args):
            try:
                if error:
                    raise WatchError(error)
                watch(args, number, info, None)
            except (WatchError, OSError) as exc:
                if number is None:
                    raise
                failed += 1
                print(f"video {number}: failed ({exc})")
        return 2 if failed else 0
    except WatchError as exc:
        print(f"{NAME}: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print(f"{NAME}: interrupted", file=sys.stderr)
        return 130


def asr_worker() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--language")
    args = parser.parse_args(sys.argv[2:])
    try:
        language, segments = run_whisper(args.audio, args.model, args.language)
        json.dump({"language": language, "segments": [vars(item) for item in segments]}, sys.stdout)
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(asr_worker() if len(sys.argv) > 1 and sys.argv[1] == "--asr-worker" else main())
