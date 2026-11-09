#!/usr/bin/env python3
"""Where a workflow sets its models and efforts, and what its sessions ran. Read-only.

  python inventory.py <workflow root> [--days 14]

Prints every line under the root that names a model or sets an effort, then the
models recorded for agent sessions whose working directory was under the root.
A text search shows where a choice may be set, not what runs: a value passed
through a variable, an environment override or a harness default is marked for
tracing by hand, and the session records are the check.
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", ".next", ".venv", "venv", "__pycache__"}
MAX_BYTES = 1_000_000
MODEL_ID = re.compile(r"\b(?:claude-(?:fable|mythos|opus|sonnet|haiku)-[\w.\-]+|gpt-\d[\w.\-]*|gemini-[\w.\-]+|grok-[\w.\-]+)")
KEYS = r"(?:model_reasoning_effort|reasoning_?effort|reasoningEffort|advisorModel|effortLevel|model|effort)"
FLAGS = (r"--model\b|--effort\b|\bANTHROPIC_(?:MODEL|DEFAULT_\w+_MODEL)\b"
         r"|\bCLAUDE_CODE_(?:SUBAGENT_MODEL|EFFORT_LEVEL)\b")
# In prose files a key counts only at the start of a line (front matter); in code, anywhere,
# including as the tail of a longer name such as default_model.
SETTING_PROSE = re.compile(FLAGS + r"|^\s*[\"']?" + KEYS + r"[\"']?\s*[:=]", re.IGNORECASE)
SETTING_CODE = re.compile(FLAGS + r"|(?<![A-Za-z0-9])" + KEYS + r"[\"']?\s*[:=]", re.IGNORECASE)
PROSE = {".md", ".mdx", ".txt", ".rst"}
VALUE = re.compile(r"\b(?:minimal|low|medium|high|xhigh|max|ultra|opus|sonnet|haiku|fable|mythos|inherit)\b",
                   re.IGNORECASE)
HOME = os.path.expanduser("~")


def when(text):
    try:
        return datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None


def lines_setting_models(root, missed):
    def unlisted(_error):
        missed["folders that could not be listed"] = missed.get("folders that could not be listed", 0) + 1

    for folder, dirs, files in os.walk(root, onerror=unlisted):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = os.path.join(folder, name)
            setting = SETTING_PROSE if os.path.splitext(name)[1].lower() in PROSE else SETTING_CODE
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    missed["files over 1 MB"] = missed.get("files over 1 MB", 0) + 1
                    continue
                with open(path, encoding="utf-8") as handle:
                    found = [(number, line.strip(), MODEL_ID.findall(line)) for number, line in enumerate(handle, 1)
                             if MODEL_ID.search(line) or setting.search(line)]
            except (OSError, UnicodeDecodeError):
                missed["files that are not readable text"] = missed.get("files that are not readable text", 0) + 1
                continue
            for number, text, ids in found:
                yield os.path.relpath(path, root), number, text, ids


def under(path, root):
    try:
        return bool(path) and os.path.commonpath([os.path.abspath(path), root]) == root
    except ValueError:
        return False


def sessions(root, since, missed):
    """{(provider, model, effort): requests} for sessions whose working directory is under root."""
    out, seen = {}, set()

    def count(provider, model, effort):
        key = (provider, model or "unknown", effort or "not recorded")
        out[key] = out.get(key, 0) + 1

    def rows(pattern, marker):
        for path in glob.glob(pattern, recursive=True):
            try:
                if os.path.getmtime(path) < since.timestamp():
                    continue
                with open(path, encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        if marker not in line:
                            continue
                        try:
                            row = json.loads(line)
                        except ValueError:
                            missed["session lines that could not be parsed"] = missed.get(
                                "session lines that could not be parsed", 0) + 1
                            continue
                        at = when(row.get("timestamp", ""))
                        if at and at >= since:
                            yield row
            except OSError:
                missed["session files that could not be opened"] = missed.get(
                    "session files that could not be opened", 0) + 1

    for row in rows(os.path.join(HOME, ".claude", "projects", "**", "*.jsonl"), '"usage"'):
        message = row.get("message") or {}
        key = ("claude", message.get("id"), row.get("requestId"))
        if message.get("model") and key not in seen and under(row.get("cwd"), root):
            seen.add(key)
            count("claude", message["model"], row.get("effort") or row.get("perTurnEffort"))
    for row in rows(os.path.join(HOME, ".codex", "sessions", "**", "*.jsonl"), '"turn_context"'):
        payload = row.get("payload") or {}
        key = ("codex", payload.get("turn_id") or row.get("timestamp"))
        if row.get("type") == "turn_context" and key not in seen and under(payload.get("cwd"), root):
            seen.add(key)
            count("codex", payload.get("model"), payload.get("effort") or payload.get("reasoning_effort"))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("root", help="the workflow's folder")
    parser.add_argument("--days", type=float, default=14, help="how far back to read session records (default 14)")
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.exit(f"not a folder: {root}")
    missed = {}

    print(f"Lines under {root} that name a model or set an effort")
    found, by_id = 0, {}
    for path, number, text, ids in lines_setting_models(root, missed):
        found += 1
        for model in ids:
            by_id[model] = by_id.get(model, 0) + 1
        note = "" if ids or VALUE.search(text) else "   <- value not on this line: trace it by hand"
        if "test" in path.lower():
            note += "   (in a test)"
        print(f"  {path}:{number}: {text[:160]}{note}")
    print(f"  {found} lines. Models named: " + (", ".join(f"{m} x{n}" for m, n in sorted(by_id.items())) or "none"))

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    print(f"\nModels recorded for sessions run from under this folder, last {args.days:g} days, this machine")
    ran = sessions(root, since, missed)
    for (provider, model, effort), requests in sorted(ran.items()):
        unit = "requests" if provider == "claude" else "turns"
        print(f"  {provider}: {model}, effort {effort}: {requests} {unit}")
    if not ran:
        print("  none found")

    print("\nNot seen")
    print("  - Choices set outside this folder: harness defaults, user settings, environment variables,")
    print("    arguments passed by whatever starts the workflow.")
    print("  - Sessions run on another machine, or from a working directory outside this folder, which is")
    print("    where a launcher that sets its own working directory leaves them.")
    for what, count in sorted(missed.items()):
        print(f"  - {count} {what}: left out of the lists above.")


if __name__ == "__main__":
    main()
