---
name: transcribe-youtube
description: Transcribe a YouTube video into a timestamped text file. Use when a user provides a YouTube URL and needs its transcript, captions, quotes, or searchable video text.
---

# YouTube transcription

Run the helper in this skill's `scripts/` folder with the video's URL, using Python 3 (`py -3` on Windows, `python3` elsewhere):

```
python3 <this skill's folder>/scripts/transcribe_youtube.py "<youtube-url>"
```

It prints one absolute output path. Read that file rather than returning the transcript through a tool. The file header records the source language and whether supplied captions, automatic captions, or local ASR produced it.

Pass `--language en` to prefer a language, `--output transcript.md` to choose the destination, or `--no-timestamps` for continuous text. The helper uses captions first and automatically installs and uses its local ASR fallback when captions are unavailable.
