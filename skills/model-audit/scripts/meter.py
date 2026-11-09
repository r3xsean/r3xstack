#!/usr/bin/env python3
"""What 1% of a plan's limit costs, per model, on this machine. Read-only.

Pairs the plan-meter readings an agent harness logged with the token usage of
each request, priced at list API prices, and reports list-price dollars per 1%
of each meter for every model that had a meter step to itself.

  python meter.py [--days 7] [--since 2026-11-04T04:00:00+08:00] [--prices FILE]

It reads only this machine's records:
  Claude  meter: ~/.t3/userdata/logs/provider/*.log*  (rate_limit_event)
          usage: ~/.claude/projects/**/*.jsonl
  Codex   meter and usage: ~/.codex/sessions/**/*.jsonl  (token_count)
Usage on another machine or app moves the same meters and is not counted here.
"""
import argparse
import glob
import json
import math
import os
import re
import statistics
import sys
from datetime import datetime, timedelta, timezone

# USD per million tokens: input, output, cache read, 5-minute cache write, 1-hour cache write.
PRICES = {
    "claude-fable-5-2": (8, 40, 0.20, 10, 16),
    "claude-fable-5-1": (10, 50, 0.25, 12.5, 20),
    "claude-opus-5-5": (4, 20, 0.20, 5, 8),
    "claude-sonnet-5-5": (2, 10, 0.10, 2.5, 4),
    "claude-haiku-5-5": (0.1, 0.5, 0.01, 0.125, 0.2),
    "gpt-6.1-sol": (2, 10, 0.10, 0, 0),
    "gpt-6-astra": (10, 50, 1, 0, 0),
    "gpt-6.1-terra": (1, 5, 0.05, 0, 0),
}
MAX_GAP_MIN = 15      # a step counts only if the meter was seen this recently before it
MIN_SHARE = 0.98      # ...and one model made at least this share of the priced cost in it
SAME_RESET_S = 300    # reset times this close belong to the same window
HOME = os.path.expanduser("~")
STAMP = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)")


class Missed:
    """Sources that could not be read, so the report can say its figures leave them out."""

    def __init__(self):
        self.counts = {}

    def add(self, what):
        self.counts[what] = self.counts.get(what, 0) + 1


def when(text):
    try:
        return datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None


def recent(paths, since, missed):
    for path in paths:
        try:
            if os.path.getmtime(path) >= since.timestamp():
                yield path
        except OSError:
            missed.add("files that could not be opened")


def lines_of(path, missed):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            yield from handle
    except OSError:
        missed.add("files that could not be opened")


def claude_meter(since, missed):
    """{window: {time: (percent, reset time)}} from T3's provider logs."""
    out = {}
    for path in recent(glob.glob(os.path.join(HOME, ".t3", "userdata", "logs", "provider", "*.log*")), since, missed):
        for line in lines_of(path, missed):
            if '"rate_limit_event"' not in line:
                continue
            stamp = STAMP.search(line[:80])
            at = when(stamp.group(1)) if stamp else None
            start = line.find('{"provider"')
            try:
                info = json.loads(line[start:])["event"]["payload"]["rate_limit_info"]
            except (ValueError, KeyError, TypeError):
                missed.add("meter lines that could not be parsed")
                continue
            if not at:
                missed.add("meter lines that could not be parsed")
                continue
            if at < since:
                continue
            windows = dict(info.get("unifiedWindows") or {})
            if info.get("rateLimitType") and info.get("utilization") is not None:
                windows.setdefault(info["rateLimitType"], info)
            for name, window in windows.items():
                level = (window or {}).get("utilization")
                if level is not None:
                    out.setdefault(name, {})[at] = (round(level * 100, 2), window.get("resetsAt") or 0)
    return out


def claude_usage(since, prices, unpriced, missed):
    """[(time, model, cost)] from Claude Code session records, one per API message."""
    seen, out = set(), []
    pattern = os.path.join(HOME, ".claude", "projects", "**", "*.jsonl")
    for path in recent(glob.glob(pattern, recursive=True), since, missed):
        for line in lines_of(path, missed):
            if '"usage"' not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                missed.add("usage lines that could not be parsed")
                continue
            message = row.get("message") or {}
            usage, model, at = message.get("usage"), message.get("model"), when(row.get("timestamp", ""))
            if not usage or not model or not at or at < since:
                continue
            key = (message.get("id"), row.get("requestId"))
            if key in seen:
                continue
            seen.add(key)
            split = usage.get("cache_creation") or {}
            write_5m = split.get("ephemeral_5m_input_tokens") or 0
            write_1h = split.get("ephemeral_1h_input_tokens") or 0
            if not write_5m + write_1h:
                write_5m = usage.get("cache_creation_input_tokens") or 0
            tokens = (usage.get("input_tokens") or 0, usage.get("output_tokens") or 0,
                      usage.get("cache_read_input_tokens") or 0, write_5m, write_1h)
            out.append(priced(at, model, tokens, prices, unpriced))
    return sorted(out, key=lambda r: r[0])


def window_name(minutes):
    return {10080: "weekly", 300: "five-hour"}.get(minutes, f"{minutes}-minute")


def counts(usage):
    return (usage.get("input_tokens") or 0, usage.get("cached_input_tokens") or 0, usage.get("output_tokens") or 0)


def codex_records(since, prices, unpriced, missed):
    """({window: {time: (percent, reset time)}}, [(time, model, cost)]) from Codex session records."""
    meters, out, seen = {}, [], set()
    pattern = os.path.join(HOME, ".codex", "sessions", "**", "*.jsonl")
    for path in recent(glob.glob(pattern, recursive=True), since, missed):
        model, last = "unknown", None
        for line in lines_of(path, missed):
            if '"turn_context"' not in line and '"token_count"' not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                missed.add("usage lines that could not be parsed")
                continue
            payload = row.get("payload") or {}
            if row.get("type") == "turn_context" and payload.get("model"):
                model = payload["model"]
            if payload.get("type") != "token_count":
                continue
            at = when(row.get("timestamp", ""))
            if not at:
                missed.add("usage lines that could not be parsed")
                continue
            for slot in ("primary", "secondary"):
                window = (payload.get("rate_limits") or {}).get(slot) or {}
                if window.get("used_percent") is not None and at >= since:
                    name = window_name(window.get("window_minutes"))
                    meters.setdefault(name, {})[at] = (float(window["used_percent"]), window.get("resets_at") or 0)
            info = payload.get("info") or {}
            total = counts(info.get("total_token_usage") or {})
            # A session that continues or forks another starts with the totals it inherited, and
            # copies the parent's records: price the request alone there, and each record once.
            if last is not None and all(a >= b for a, b in zip(total, last)):
                spent = tuple(a - b for a, b in zip(total, last))
            elif info.get("last_token_usage"):
                spent = counts(info["last_token_usage"])
            else:
                spent = (0, 0, 0)
                missed.add("Codex sessions whose first record has no per-request usage")
            last = total
            key = (row.get("timestamp"), total)
            if key in seen or at < since or not any(spent):
                continue
            seen.add(key)
            tokens = (max(spent[0] - spent[1], 0), spent[2], spent[1], 0, 0)
            out.append(priced(at, model, tokens, prices, unpriced))
    return meters, sorted(out, key=lambda r: r[0])


def priced(at, model, tokens, prices, unpriced):
    if not any(tokens):
        return (at, model, 0.0)
    rate = prices.get(model)
    if rate is None:
        unpriced[model] = unpriced.get(model, 0) + sum(tokens)
        return (at, model, None)
    return (at, model, sum(t * r for t, r in zip(tokens, rate)) / 1e6)


def same_window(a, b):
    return abs(a - b) <= SAME_RESET_S


def steps(readings):
    """[(first seen at old level, first seen at new level, old, new, minutes unobserved)], never across a reset."""
    times, out, start, level = sorted(readings), [], None, None
    for index, at in enumerate(times):
        percent, reset = readings[at]
        if level is None or not same_window(reset, readings[times[index - 1]][1]):
            start, level = at, percent
        elif percent != level:
            gap = (at - times[index - 1]).total_seconds() / 60
            out.append((start, at, level, percent, gap))
            start, level = at, percent
    return out


def rate_per_model(readings, usage):
    """{model: [dollars per 1%]} from the steps one priced model had to itself."""
    found, skipped = {}, 0
    for start, end, old, new, gap in steps(readings):
        rise = new - old
        inside = [(model, cost) for at, model, cost in usage if start < at <= end]
        if rise <= 0 or gap > MAX_GAP_MIN or not inside or any(cost is None for _, cost in inside):
            skipped += 1
            continue
        by_model = {}
        for model, cost in inside:
            by_model[model] = by_model.get(model, 0) + cost
        total = sum(by_model.values())
        model, most = max(by_model.items(), key=lambda item: item[1])
        if total <= 0 or most / total < MIN_SHARE:
            skipped += 1
            continue
        found.setdefault(model, []).append(total / rise)
    return found, skipped


def most_at_one_level(readings, usage):
    """{model: the most it cost between readings while the meter stayed at one level}."""
    times, best, run, index = sorted(readings), {}, {}, 0
    for before, after in zip(times, times[1:]):
        while index < len(usage) and usage[index][0] <= before:
            index += 1
        if readings[before] != readings[after]:
            run = {}
            continue
        while index < len(usage) and usage[index][0] <= after:
            _, model, cost = usage[index]
            run[model] = run.get(model, 0) + (cost or 0)
            best[model] = max(best.get(model, 0), run[model])
            index += 1
    return best


def report(name, readings, usage):
    latest = max(readings)
    print(f"  {name}: {readings[latest][0]:.0f}% used at {latest.isoformat(timespec='minutes')} "
          f"({len(readings)} readings)")
    found, skipped = rate_per_model(readings, usage)
    still = most_at_one_level(readings, usage)
    for model, values in sorted(found.items()):
        values.sort()
        # Usage this machine can't see only ever makes a step look cheaper, so the upper
        # quartile is the estimate and the median is shown beside it.
        rate = values[-(-3 * len(values) // 4) - 1]
        doubt = (f"; but ${still[model]:.2f} was spent at one level, so this meter may not count this model"
                 if still.get(model, 0) > 2 * values[-1] else "")
        print(f"    {model}: estimate ${rate:.2f} per 1%  (upper quartile of {len(values)} clean steps; "
              f"median ${statistics.median(values):.2f}, range ${values[0]:.2f} to ${values[-1]:.2f}{doubt})")
    if not found:
        print("    no step had one priced model to itself; no rate can be given")
    for model, cost in sorted(still.items()):
        if model not in found and cost > 0:
            print(f"    {model}: no rate; up to ${cost:.2f} was spent while this meter stayed at one level")
    print(f"    steps left out (mixed models, unpriced usage, or a gap over {MAX_GAP_MIN} min): {skipped}")


def totals(usage):
    out = {}
    for _, model, cost in usage:
        out[model] = out.get(model, 0) + (cost or 0)
    return ", ".join(f"{m} ${c:,.2f}" for m, c in sorted(out.items()) if c) or "none"


def load_prices(path):
    try:
        with open(path, encoding="utf-8") as handle:
            added = json.load(handle)
    except (OSError, ValueError) as error:
        sys.exit(f"--prices could not be read: {error}")
    for model, rates in added.items():
        good = (isinstance(rates, list) and len(rates) == 5 and all(
            isinstance(r, (int, float)) and not isinstance(r, bool) and math.isfinite(r) and r >= 0 for r in rates))
        if not good:
            sys.exit(f"--prices: {model} needs five non-negative numbers: input, output, cache read, "
                     "5-minute cache write, 1-hour cache write")
    return {model: tuple(rates) for model, rates in added.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--days", type=float, default=7, help="how far back to read (default 7)")
    parser.add_argument("--since", help="ISO time to read from; overrides --days")
    parser.add_argument("--prices", help="JSON file of {model: [input, output, read, write5m, write1h]} to add")
    args = parser.parse_args()
    since = when(args.since) if args.since else datetime.now(timezone.utc) - timedelta(days=args.days)
    if since is None:
        sys.exit("--since is not an ISO time")
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    prices = dict(PRICES)
    if args.prices:
        prices.update(load_prices(args.prices))
    unpriced, missed = {}, Missed()

    print(f"Reading from {since.isoformat(timespec='minutes')}. Dollars are list API prices, not plan charges.")
    print("A plan can have more than one meter, such as a sub-limit that counts only some models.")
    print("\nClaude")
    usage = claude_usage(since, prices, unpriced, missed)
    meters = claude_meter(since, missed)
    print(f"  usage on this machine: {totals(usage)}")
    for name in sorted(meters):
        report(name, meters[name], usage)
    if not meters:
        print("  no meter readings found in ~/.t3/userdata/logs/provider")

    print("\nCodex")
    meters, usage = codex_records(since, prices, unpriced, missed)
    print(f"  usage on this machine: {totals(usage)}")
    for name in sorted(meters):
        report(name, meters[name], usage)
    if not meters:
        print("  no meter readings found in ~/.codex/sessions")

    print("\nNot seen")
    print("  - Any other machine or app on the same plans. Its usage moves these meters and makes a step")
    print("    here look cheaper than it was; run this there too, and treat a rate from few clean steps")
    print("    as provisional.")
    for model, count in sorted(unpriced.items()):
        print(f"  - {model}: {count:,} tokens with no price; steps containing it were left out. Add it with --prices.")
    for what, count in sorted(missed.counts.items()):
        print(f"  - {count} {what}: the figures above leave them out and may be incomplete.")
    print("  - Precision: a meter moves in whole percents, so one step's rate can be off by its own size.")
    print("    Rely on a median of several clean steps, and on none from a single step.")


if __name__ == "__main__":
    main()
