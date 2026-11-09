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
        at = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return at if at.tzinfo else at.replace(tzinfo=timezone.utc)


def note(missed, what):
    missed[what] = missed.get(what, 0) + 1


def lines_setting_models(root, missed):
    for folder, dirs, files in os.walk(root, onerror=lambda _error: note(missed, "folders that could not be listed")):
        for name in list(dirs):
            if name in SKIP_DIRS:
                dirs.remove(name)
                note(missed, "folders skipped by name (" + ", ".join(sorted(SKIP_DIRS)) + ")")
            elif os.path.islink(os.path.join(folder, name)):
                note(missed, "linked folders not followed")
        for name in files:
            path = os.path.join(folder, name)
            setting = SETTING_PROSE if os.path.splitext(name)[1].lower() in PROSE else SETTING_CODE
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    note(missed, "files over 1 MB")
                    continue
                with open(path, encoding="utf-8") as handle:
                    found = [(number, line.strip(), MODEL_ID.findall(line)) for number, line in enumerate(handle, 1)
                             if MODEL_ID.search(line) or setting.search(line)]
            except (OSError, UnicodeDecodeError):
                note(missed, "files that are not readable text")
                continue
            for number, text, ids in found:
                yield os.path.relpath(path, root), number, text, ids


def under(path, root):
    if not path:
        return False
    try:
        path = os.path.normcase(os.path.abspath(path))
        return os.path.commonpath([path, os.path.normcase(root)]) == os.path.normcase(root)
    except (ValueError, TypeError):
        return False


def session_rows(parts, marker, since, missed):
    """Parsed lines holding `marker`, dated since `since`, from the session files under ~/parts."""
    top = os.path.join(HOME, *parts)
    unlisted = lambda _error: note(missed, "session folders that could not be listed")
    for folder, dirs, files in os.walk(top, onerror=unlisted) if os.path.lexists(top) else ():
        for name in dirs:
            if os.path.islink(os.path.join(folder, name)):
                note(missed, "linked session folders not followed")
        for name in files:
            path = os.path.join(folder, name)
            try:
                if not name.endswith(".jsonl") or os.path.getmtime(path) < since.timestamp():
                    continue
                with open(path, encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        if marker not in line:
                            continue
                        try:
                            row = json.loads(line)
                            at = when(row.get("timestamp"))
                            if not at:
                                raise ValueError
                        except (ValueError, AttributeError):
                            note(missed, "session lines that could not be parsed")
                            continue
                        if at >= since:
                            yield row
            except OSError:
                note(missed, "session files that could not be opened")


def sessions(root, since, missed):
    """{(provider, model, effort): requests} for sessions whose working directory is under root."""
    out, seen = {}, set()

    def count(provider, key, cwd, model, effort):
        if key not in seen and under(cwd, root):
            seen.add(key)
            entry = (provider, str(model or "unknown"), str(effort or "not recorded"))
            out[entry] = out.get(entry, 0) + 1

    for row in session_rows((".claude", "projects"), '"usage"', since, missed):
        message = row.get("message")
        if message is not None and not isinstance(message, dict):
            note(missed, "session lines that could not be parsed")
        elif message and message.get("model"):
            count("claude", ("claude", message.get("id"), row.get("requestId")), row.get("cwd"),
                  message["model"], row.get("effort") or row.get("perTurnEffort"))
    for row in session_rows((".codex", "sessions"), '"turn_context"', since, missed):
        payload = row.get("payload")
        if row.get("type") != "turn_context":
            continue
        if not isinstance(payload, dict):
            note(missed, "session lines that could not be parsed")
            continue
        count("codex", ("codex", payload.get("turn_id") or row.get("timestamp")), payload.get("cwd"),
              payload.get("model"), payload.get("effort") or payload.get("reasoning_effort"))
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
    lines = list(lines_setting_models(root, missed))
    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    ran = sessions(root, since, missed)

    print(f"Lines under {root} that name a model or set an effort")
    by_id = {}
    for path, number, text, ids in lines:
        for model in ids:
            by_id[model] = by_id.get(model, 0) + 1
        mark = "" if ids or VALUE.search(text) else "   <- value not on this line: trace it by hand"
        if "test" in path.lower():
            mark += "   (in a test)"
        print(f"  {path}:{number}: {text[:160]}{mark}")
    print(f"  {len(lines)} lines. Models named: " + (", ".join(f"{m} x{n}" for m, n in sorted(by_id.items())) or "none"))

    print(f"\nModels recorded for sessions run from under this folder, last {args.days:g} days, this machine")
    for (provider, model, effort), requests in sorted(ran.items()):
        unit = "requests" if provider == "claude" else "turns"
        print(f"  {provider}: {model}, effort {effort}: {requests} {unit}")
    if not ran:
        print("  none found")

    print("\nNot seen")
    print("  - Choices set outside this folder: harness defaults, user settings, environment variables,")
    print("    arguments passed by whatever starts the workflow.")
    print("  - Sessions run on another machine, by a provider other than Claude Code and Codex, or from a")
    print("    working directory outside this folder, which is where a launcher that sets its own leaves them.")
    for what, count in sorted(missed.items()):
        print(f"  - {count} {what}: left out of the lists above.")
    print("\nReport complete.")


if __name__ == "__main__":
    main()
