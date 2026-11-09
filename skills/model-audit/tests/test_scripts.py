"""Tests for the model-audit helper scripts. Each runs a script against records in a throwaway home.

  python tests/test_scripts.py            (from the skill's folder)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

SCRIPTS = os.environ.get("MODEL_AUDIT_SCRIPTS") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
NOW = datetime.now(timezone.utc).replace(microsecond=0)
RESET = 1794340800


def stamp(minutes):
    return (NOW + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class Home(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def write(self, relative, lines, raw=None):
        path = os.path.join(self.home, *relative.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if raw is not None:
            with open(path, "wb") as handle:
                handle.write(raw)
        else:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n")
        return path

    def run_script(self, name, *args, fails=False):
        env = dict(os.environ, USERPROFILE=self.home, HOME=self.home)
        done = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, name), *args],
                              env=env, capture_output=True, text=True)
        if not fails:
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertTrue(done.stdout.rstrip().endswith("Report complete."), done.stdout)
        return done

    def meter_line(self, minutes, percent, reset=RESET, window="seven_day"):
        info = {"rateLimitType": window, "utilization": percent, "resetsAt": reset,
                "unifiedWindows": {window: {"utilization": percent, "resetsAt": reset}}}
        event = {"provider": "claudeAgent", "event": {"payload": {"type": "rate_limit_event", "rate_limit_info": info}}}
        return f"[{stamp(minutes)}] NTIVE: {json.dumps(event)}"

    def claude_row(self, minutes, model, output=0, cwd="C:\\elsewhere", key="1", effort="high"):
        return json.dumps({"timestamp": stamp(minutes), "requestId": "r" + key, "cwd": cwd, "effort": effort,
                           "message": {"id": "m" + key, "model": model, "usage": {"output_tokens": output}}})

    def codex_count(self, minutes, total, last, percent=10.0):
        usage = lambda t: {"input_tokens": t[0], "cached_input_tokens": 0, "output_tokens": t[1]}
        return json.dumps({"timestamp": stamp(minutes), "type": "event_msg", "payload": {
            "type": "token_count", "info": {"total_token_usage": usage(total), "last_token_usage": usage(last)},
            "rate_limits": {"primary": {"used_percent": percent, "window_minutes": 10080, "resets_at": RESET}}}})


class Meter(Home):
    def test_a_step_one_model_had_to_itself_gives_its_rate(self):
        self.write(".t3/userdata/logs/provider/events.log",
                   [self.meter_line(-30, 0.10), self.meter_line(-25, 0.10), self.meter_line(-20, 0.11)])
        self.write(".claude/projects/p/s.jsonl", [self.claude_row(-22, "claude-opus-5-5", output=1_000_000)])
        out = self.run_script("meter.py").stdout
        self.assertIn("claude-opus-5-5: estimate $20.00 per 1%", out)

    def test_a_rise_across_a_reset_is_not_a_step(self):
        self.write(".t3/userdata/logs/provider/events.log",
                   [self.meter_line(-30, 0.05), self.meter_line(-20, 0.07, reset=RESET + 7 * 86400)])
        self.write(".claude/projects/p/s.jsonl", [self.claude_row(-25, "claude-opus-5-5", output=1_000_000)])
        out = self.run_script("meter.py").stdout
        self.assertNotIn("estimate", out)
        self.assertIn("no step had one priced model to itself", out)

    def test_a_codex_session_that_inherits_totals_is_priced_per_request(self):
        context = json.dumps({"timestamp": stamp(-31), "type": "turn_context",
                              "payload": {"model": "gpt-6.1-sol", "turn_id": "t1", "cwd": "C:\\elsewhere"}})
        self.write(".codex/sessions/2026/11/10/a.jsonl", [
            context,
            self.codex_count(-30, total=(5_000_000, 600_000), last=(1_000_000, 200_000)),
            self.codex_count(-20, total=(6_000_000, 800_000), last=(1_000_000, 200_000))])
        out = self.run_script("meter.py").stdout
        self.assertIn("gpt-6.1-sol $8.00", out)

    def test_prices_need_all_five_rates(self):
        prices = self.write("prices.json", [json.dumps({"some-model": [1, 2]})])
        done = self.run_script("meter.py", "--prices", prices, fails=True)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("five non-negative numbers", done.stderr)
        prices = self.write("prices.json", ["[]"])
        done = self.run_script("meter.py", "--prices", prices, fails=True)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("one JSON object", done.stderr)

    def test_lines_it_could_not_read_are_reported_and_make_the_rate_provisional(self):
        self.write(".t3/userdata/logs/provider/events.log",
                   [self.meter_line(-30, 0.10), self.meter_line(-25, 0.10), self.meter_line(-20, 0.11)])
        self.write(".claude/projects/p/s.jsonl", [
            self.claude_row(-22, "claude-opus-5-5", output=1_000_000),
            '{"usage": broken',
            json.dumps({"timestamp": stamp(-21), "message": "not an object", "usage": 1}),
            json.dumps({"timestamp": stamp(-21), "requestId": "r9", "message": {
                "id": "m9", "model": "claude-opus-5-5", "usage": {"output_tokens": ""}}})])
        out = self.run_script("meter.py").stdout
        self.assertIn("Claude: 3 usage lines that could not be parsed", out)
        self.assertNotIn("Codex:", out.split("Not seen")[1])
        self.assertIn("provisional, some of this provider's records could not be read", out)

    def test_a_codex_record_with_no_usage_keeps_the_baseline(self):
        context = json.dumps({"timestamp": stamp(-31), "type": "turn_context",
                              "payload": {"model": "gpt-6.1-sol", "turn_id": "t1", "cwd": "C:\\elsewhere"}})
        meter_only = json.dumps({"timestamp": stamp(-25), "type": "event_msg", "payload": {
            "type": "token_count", "info": None,
            "rate_limits": {"primary": {"used_percent": 10.0, "window_minutes": 10080, "resets_at": RESET}}}})
        self.write(".codex/sessions/2026/11/10/a.jsonl", [
            context,
            self.codex_count(-30, total=(1_000_000, 200_000), last=(1_000_000, 200_000)),
            meter_only,
            self.codex_count(-20, total=(2_000_000, 400_000), last=(1_000_000, 200_000))])
        out = self.run_script("meter.py").stdout
        self.assertIn("gpt-6.1-sol $8.00", out)


class Inventory(Home):
    def setUp(self):
        super().setUp()
        self.root = os.path.join(self.home, "workflow")
        os.makedirs(self.root)

    def test_codex_effort_setting_is_found(self):
        self.write("workflow/config.toml", ['model_reasoning_effort = "low"'])
        out = self.run_script("inventory.py", self.root).stdout
        self.assertIn("config.toml:1", out)

    def test_recorded_effort_is_shown_and_old_records_are_left_out(self):
        self.write(".claude/projects/p/s.jsonl", [
            self.claude_row(-60 * 24 * 60, "claude-sonnet-5-5", cwd=self.root, key="old"),
            self.claude_row(-5, "claude-opus-5-5", cwd=self.root, key="new")])
        out = self.run_script("inventory.py", self.root).stdout
        self.assertIn("claude: claude-opus-5-5, effort high: 1 requests", out)
        self.assertNotIn("claude-sonnet-5-5", out)

    def test_a_record_with_an_empty_working_directory_is_not_this_folders(self):
        self.write(".claude/projects/p/s.jsonl", [self.claude_row(-5, "claude-opus-5-5", cwd="")])
        done = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "inventory.py"), "."], cwd=self.root,
                              env=dict(os.environ, USERPROFILE=self.home, HOME=self.home),
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("none found", done.stdout)

    @unittest.skipUnless(os.name == "nt", "Windows paths ignore case")
    def test_a_working_directory_spelled_in_another_case_still_counts(self):
        self.write(".claude/projects/p/s.jsonl", [self.claude_row(-5, "claude-opus-5-5", cwd=self.root.upper())])
        out = self.run_script("inventory.py", self.root.lower()).stdout
        self.assertIn("claude: claude-opus-5-5, effort high: 1 requests", out)

    def test_a_turn_copied_into_a_second_session_counts_once(self):
        turn = json.dumps({"timestamp": stamp(-5), "type": "turn_context",
                           "payload": {"model": "gpt-6.1-sol", "effort": "high", "turn_id": "t1", "cwd": self.root}})
        self.write(".codex/sessions/2026/11/10/a.jsonl", [turn])
        self.write(".codex/sessions/2026/11/10/b.jsonl", [turn])
        out = self.run_script("inventory.py", self.root).stdout
        self.assertIn("codex: gpt-6.1-sol, effort high: 1 turns", out)

    def test_files_it_could_not_read_are_reported(self):
        self.write("workflow/blob.cfg", None, raw=b"\xff\xfe model = \x80\x81")
        out = self.run_script("inventory.py", self.root).stdout
        self.assertIn("1 files that are not readable text", out)


if __name__ == "__main__":
    unittest.main()
