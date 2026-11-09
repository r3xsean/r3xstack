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
KEYS = r"(?:model|effort|reasoning_?effort|reasoningEffort|advisorModel|effortLevel)"
FLAGS = (r"--model\b|--effort\b|\bANTHROPIC_(?:MODEL|DEFAULT_\w+_MODEL)\b"
         r"|\bCLAUDE_CODE_(?:SUBAGENT_MODEL|EFFORT_LEVEL)\b")
# In prose files a key counts only at the start of a line (front matter); in code, anywhere.
SETTING_PROSE = re.compile(FLAGS + r"|^\s*[\"']?" + KEYS + r"[\"']?\s*[:=]", re.IGNORECASE)
SETTING_CODE = re.compile(FLAGS + r"|\b" + KEYS + r"\b[\"']?\s*[:=]", re.IGNORECASE)
PROSE = {".md", ".mdx", ".txt", ".rst"}
VALUE = re.compile(r"\b(?:low|medium|high|xhigh|max|opus|sonnet|haiku|fable|mythos|inherit)\b", re.IGNORECASE)
HOME = os.path.expanduser("~")


def lines_setting_models(root):
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = os.path.join(folder, name)
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    continue
                setting = SETTING_PROSE if os.path.splitext(name)[1].lower() in PROSE else SETTING_CODE
                with open(path, encoding="utf-8") as handle:
                    for number, line in enumerate(handle, 1):
                        ids = MODEL_ID.findall(line)
                        if ids or setting.search(line):
                            yield os.path.relpath(path, root), number, line.strip(), ids
            except (OSError, UnicodeDecodeError):
                continue


def under(path, root):
    try:
        return os.path.commonpath([os.path.abspath(path), root]) == root
    except ValueError:
        return False


def sessions(root, since):
    """{(provider, model, effort): requests} for sessions whose working directory is under root."""
    out = {}

    def count(provider, model, effort):
        key = (provider, model or "unknown", effort or "not recorded")
        out[key] = out.get(key, 0) + 1

    for path in glob.glob(os.path.join(HOME, ".claude", "projects", "**", "*.jsonl"), recursive=True):
        if os.path.getmtime(path) < since.timestamp():
            continue
        seen = set()
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if '"usage"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                message = row.get("message") or {}
                key = (message.get("id"), row.get("requestId"))
                if not message.get("model") or key in seen or not under(row.get("cwd") or "", root):
                    continue
                seen.add(key)
                count("claude", message["model"], None)
    for path in glob.glob(os.path.join(HOME, ".codex", "sessions", "**", "*.jsonl"), recursive=True):
        if os.path.getmtime(path) < since.timestamp():
            continue
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if '"turn_context"' not in line:
                    continue
                try:
                    payload = json.loads(line).get("payload") or {}
                except ValueError:
                    continue
                if under(payload.get("cwd") or "", root):
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

    print(f"Lines under {root} that name a model or set an effort")
    found, by_id = 0, {}
    for path, number, text, ids in lines_setting_models(root):
        found += 1
        for model in ids:
            by_id[model] = by_id.get(model, 0) + 1
        note = "" if ids or VALUE.search(text) else "   <- value not on this line: trace it by hand"
        print(f"  {path}:{number}: {text[:160]}{note}")
    print(f"  {found} lines. Models named: " + (", ".join(f"{m} x{n}" for m, n in sorted(by_id.items())) or "none"))

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    print(f"\nModels recorded for sessions run from under this folder, last {args.days:g} days, this machine")
    ran = sessions(root, since)
    for (provider, model, effort), requests in sorted(ran.items()):
        unit = "requests" if provider == "claude" else "turns"
        print(f"  {provider}: {model}, effort {effort}: {requests} {unit}")
    if not ran:
        print("  none found")

    print("\nNot seen")
    print("  - Choices set outside this folder: harness defaults, user settings, environment variables,")
    print("    arguments passed by whatever starts the workflow.")
    print("  - Sessions run on another machine, or from a working directory outside this folder.")
    print("  - Claude Code records no effort per request; read it from the launch arguments or settings.")


if __name__ == "__main__":
    main()
