#!/usr/bin/env python3
"""Create a timestamped transcript from an accessible YouTube video.

The fast path reads YouTube caption tracks exposed through yt-dlp.  When no
track is usable, the optional local faster-whisper dependency transcribes a
temporary audio download.  No API key is required.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time

if os.name == "nt":
    import msvcrt
else:
    import fcntl
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.request import Request, urlopen

try:
    import yt_dlp
except ImportError:  # pragma: no cover - exercised only on incomplete setups
    yt_dlp = None


class TranscriptError(RuntimeError):
    """An expected, actionable transcription failure."""


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    title: str
    video_url: str
    language: str
    method: str
    segments: list[Segment]


TAG_RE = re.compile(r"<[^>]+>")
TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[.,]\d{3}|\d{1,2}:\d{2}[.,]\d{3})"
    r"\s+-->\s+"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[.,]\d{3}|\d{1,2}:\d{2}[.,]\d{3})"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a caption-first transcript from an accessible YouTube video."
    )
    parser.add_argument("url", help="YouTube video URL or video ID")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--output", "-o", type=Path, help="Write to this file")
    destination.add_argument("--stdout", action="store_true", help="Print transcript text instead of writing a file")
    parser.add_argument("--language", "-l", help="Prefer this BCP-47 language tag (for example en or es-MX)")
    parser.add_argument("--format", choices=("markdown", "text"), default="markdown")
    parser.add_argument("--no-timestamps", action="store_true", help="Omit per-segment timestamps")
    parser.add_argument("--force-asr", action="store_true", help="Skip supplied and automatic caption tracks")
    parser.add_argument("--model", default="base", help="faster-whisper model for the audio fallback (default: base)")
    parser.add_argument("--cookies", type=Path, help="Netscape-format cookie file for videos requiring login")
    return parser.parse_args()


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
    candidates: list[
        tuple[tuple[int, int, int, int, str], str, dict[str, Any], str, bool, int]
    ] = []
    for source_rank, (collection_name, method) in enumerate(
        (("subtitles", "manual captions"), ("automatic_captions", "automatic captions"))
    ):
        collection = info.get(collection_name) or {}
        for language, tracks in collection.items():
            for track in tracks or []:
                extension = track.get("ext", "")
                if extension not in {"json3", "vtt"} or not track.get("url"):
                    continue
                format_rank = 0 if extension == "json3" else 1
                original = language.lower().endswith("-orig") or "(original)" in track.get("name", "").lower()
                language_priority, language_name = language_rank(language, target) if target else (0, language.lower())
                candidates.append(
                    (
                        (language_priority, source_rank, 0 if original else 1, format_rank, language_name),
                        language,
                        track,
                        method,
                        original,
                        source_rank,
                    )
                )
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
        pieces = event.get("segs") or []
        text = clean_text("".join(piece.get("utf8", "") for piece in pieces))
        if not text:
            continue
        start = event.get("tStartMs", 0) / 1000
        end = start + event.get("dDurationMs", 0) / 1000
        segments.append(Segment(start, end, text))
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
            segments.append(
                Segment(parse_timestamp(timing["start"]), parse_timestamp(timing["end"]), text)
            )
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


def extract_info(url: str, cookie_file: Path | None) -> dict[str, Any]:
    if yt_dlp is None:
        raise TranscriptError("yt-dlp is not installed. Install it with: python -m pip install -U yt-dlp")
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "skip_download": True,
    }
    if cookie_file:
        if not cookie_file.is_file():
            raise TranscriptError(f"Cookie file does not exist: {cookie_file}")
        options["cookiefile"] = str(cookie_file)
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            return downloader.extract_info(url, download=False)
    except Exception as exc:
        raise TranscriptError(f"Could not access video metadata: {exc}") from exc


def caption_transcript(info: dict[str, Any], preferred_language: str | None) -> Transcript | None:
    selected = select_caption(info, preferred_language)
    if not selected:
        return None
    language, track, method = selected
    try:
        payload = download_caption(track)
        segments = parse_json3(payload) if track.get("ext") == "json3" else parse_vtt(payload)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise TranscriptError(f"Could not retrieve the selected {method}: {exc}") from exc
    if not segments:
        raise TranscriptError(f"The selected {method} track was empty.")
    return Transcript(info.get("title", "Untitled video"), info.get("webpage_url", ""), language, method, segments)


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
    runtime = Path.home() / ".cache" / "transcribe-youtube"
    environment = runtime / "venv"
    if os.name == "nt":
        python = environment / "Scripts" / "python.exe"
    else:
        python = environment / "bin" / "python"
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime / "install.lock").open("w") as lock_file:
        exclusive_lock(lock_file)
        ready = python.is_file() and subprocess.run(
            [str(python), "-c", "import faster_whisper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).returncode == 0
        try:
            if not python.is_file():
                subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
            if not ready:
                subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "faster-whisper"], check=True)
        except subprocess.CalledProcessError as exc:
            raise TranscriptError(f"Could not install the local ASR fallback: {exc}") from exc
    return python


def run_asr(audio_path: Path, args: argparse.Namespace) -> tuple[str, list[Segment]]:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        python = asr_runtime_python()
        command = [
            str(python), str(Path(__file__).resolve()), "--asr-worker", "--audio", str(audio_path), "--model", args.model,
        ]
        if args.language:
            command.extend(["--language", args.language])
        completed = subprocess.run(
            command, capture_output=True, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if completed.returncode:
            message = completed.stderr.strip() or "ASR worker exited without an error message."
            raise TranscriptError(f"Local ASR failed: {message}")
        try:
            result = json.loads(completed.stdout)
            return result["language"], [Segment(**segment) for segment in result["segments"]]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise TranscriptError("Local ASR returned an invalid result.") from exc
    try:
        return run_whisper(audio_path, args.model, args.language)
    except Exception as exc:
        raise TranscriptError(f"Local ASR failed: {exc}") from exc


def audio_transcript(info: dict[str, Any], args: argparse.Namespace) -> Transcript:
    if yt_dlp is None:
        raise TranscriptError("yt-dlp is not installed. Install it with: python -m pip install -U yt-dlp")
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "format": "bestaudio/best",
    }
    if args.cookies:
        options["cookiefile"] = str(args.cookies)
    with tempfile.TemporaryDirectory(prefix="youtube-transcript-") as temporary_directory:
        options["outtmpl"] = str(Path(temporary_directory) / "audio.%(ext)s")
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                downloaded = downloader.extract_info(args.url, download=True)
                audio_path = Path(downloader.prepare_filename(downloaded))
        except Exception as exc:
            raise TranscriptError(f"Could not download audio for local transcription: {exc}") from exc
        if not audio_path.is_file():
            matches = list(Path(temporary_directory).glob("audio.*"))
            if len(matches) != 1:
                raise TranscriptError("Audio download completed but the temporary media file could not be located.")
            audio_path = matches[0]
        language, segments = run_asr(audio_path, args)
    if not segments:
        raise TranscriptError("Local ASR returned no speech segments.")
    return Transcript(
        info.get("title", "Untitled video"),
        info.get("webpage_url", ""),
        language,
        f"local ASR ({args.model})",
        segments,
    )


def format_time(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def render(transcript: Transcript, output_format: str, timestamps: bool) -> str:
    lines: list[str] = []
    if output_format == "markdown":
        lines.extend(
            [
                f"# {transcript.title}",
                "",
                f"Source: {transcript.video_url}",
                f"Language: {transcript.language}",
                f"Method: {transcript.method}",
                "",
            ]
        )
    for segment in transcript.segments:
        prefix = f"[{format_time(segment.start)}] " if timestamps else ""
        lines.append(prefix + segment.text)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    try:
        info = extract_info(args.url, args.cookies)
        transcript = None if args.force_asr else caption_transcript(info, args.language)
        if transcript is None:
            transcript = audio_transcript(info, args)
        content = render(transcript, args.format, not args.no_timestamps)
        if args.stdout:
            sys.stdout.write(content)
        else:
            if args.output:
                destination = args.output.expanduser().resolve()
                destination.parent.mkdir(parents=True, exist_ok=True)
            else:
                suffix = ".md" if args.format == "markdown" else ".txt"
                descriptor, generated_path = tempfile.mkstemp(prefix="youtube-transcript-", suffix=suffix)
                Path(generated_path).chmod(0o600)
                destination = Path(generated_path)
                # mkstemp returns an open descriptor; close it before write_text replaces its contents.
                os.close(descriptor)
            destination.write_text(content, encoding="utf-8")
            print(str(destination))
        return 0
    except TranscriptError as exc:
        print(f"transcribe-youtube: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("transcribe-youtube: interrupted", file=sys.stderr)
        return 130


def asr_worker() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--language")
    args = parser.parse_args(sys.argv[2:])
    try:
        language, segments = run_whisper(args.audio, args.model, args.language)
        json.dump(
            {"language": language, "segments": [{"start": item.start, "end": item.end, "text": item.text} for item in segments]},
            sys.stdout,
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(asr_worker() if len(sys.argv) > 1 and sys.argv[1] == "--asr-worker" else main())
