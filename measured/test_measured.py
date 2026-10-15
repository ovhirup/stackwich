import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from log_event import EventError, append_event
from report import summarize, render_markdown

ROOT = Path(__file__).resolve().parent
FIXTURE = [
    {"event": "sandwich.planned", "actor": "advisor", "work_id": "demo-sprint", "ts": "2026-10-15T00:00:00Z"},
    {"event": "sandwich.executed", "actor": "executor", "work_id": "demo-sprint", "ts": "2026-10-15T00:01:00Z", "dry_run": False},
    {"event": "sandwich.verified", "actor": "verifier", "work_id": "demo-sprint", "ts": "2026-10-15T00:02:00Z", "verdict": "PASS"},
    {"event": "sandwich.verified", "actor": "verifier", "work_id": "demo-sprint", "ts": "2026-10-15T00:02:30Z", "verdict": "FAIL"},
    {"event": "sandwich.reviewed", "actor": "advisor", "work_id": "demo-sprint", "ts": "2026-10-15T00:03:00Z", "verdict": "APPROVE"},
    {"event": "model.tier", "actor": "orchestrator", "work_id": "demo-sprint", "ts": "2026-10-15T00:04:00Z", "role": "executor", "tier": "execute"},
    {"event": "gate.human", "actor": "human", "work_id": "demo-sprint", "ts": "2026-10-15T00:05:00Z", "gate": "release", "decision": "approve", "approver_role": "change-approver"},
    {"event": "gate.human", "actor": "human", "work_id": "demo-sprint", "ts": "2026-10-15T00:05:30Z", "gate": "prod", "decision": "reject", "approver_role": "change-approver"},
    {"event": "retro.effectiveness", "actor": "human", "work_id": "demo-retro", "ts": "2026-10-15T00:06:00Z", "tool": "claude", "score": 4},
    {"event": "delivery.estimate", "actor": "human", "work_id": "demo-sprint", "ts": "2026-10-15T00:07:00Z", "hours_returned": 3.5},
    {"event": "iteration.item", "actor": "human", "work_id": "demo-sprint", "ts": "2026-10-15T00:08:00Z", "item_id": "story-1", "committed": True, "done": False},
    {"event": "iteration.item", "actor": "human", "work_id": "demo-sprint", "ts": "2026-10-15T00:08:30Z", "item_id": "story-2", "committed": True, "done": True},
    {"event": "dora.signal", "actor": "orchestrator", "work_id": "demo-sprint", "ts": "2026-10-15T00:09:00Z", "kind": "lead_time_hours", "value": 6},
    {"event": "risk.item", "actor": "human", "work_id": "demo-sprint", "ts": "2026-10-15T00:10:00Z", "risk_id": "r1", "severity": "low", "open": True, "summary": "Public demo risk"},
]


class MeasuredTests(unittest.TestCase):
    def test_append_only_and_forbidden_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "events.jsonl"
            first = append_event(log, dict(FIXTURE[0]))
            before = log.read_bytes()
            append_event(log, dict(FIXTURE[1]))
            self.assertTrue(log.read_bytes().startswith(before))
            self.assertEqual(first["event"], "sandwich.planned")
            with self.assertRaises(EventError):
                append_event(log, {"event": "sandwich.planned", "actor": "advisor", "work_id": "x", "api_key": "nope"})
            with self.assertRaises(EventError):
                append_event(log, {"event": "not.real", "actor": "advisor", "work_id": "x"})

    def test_report_rates(self):
        summary = summarize(FIXTURE)
        self.assertEqual(summary["verification_pass_rate"], 0.5)
        self.assertEqual(summary["gate_pass_rate"], 0.5)
        self.assertEqual(summary["hours_returned"], 3.5)
        self.assertEqual(summary["iteration"]["carryover"], 1)
        self.assertEqual(summary["retro"]["claude"]["mean_score"], 4)
        text = render_markdown(summary)
        self.assertIn("Verification pass rate: 50%", text)
        self.assertIn("Carryover: 1", text)
        self.assertNotIn("api_key", text)

    def test_cli_report_and_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "events.jsonl"
            for event in FIXTURE:
                append_event(log, dict(event))
            report = subprocess.run(
                [sys.executable, str(ROOT / "report.py"), "--log", str(log), "--format", "json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(report.returncode, 0, report.stderr)
            body = json.loads(report.stdout)
            self.assertEqual(body["events"], len(FIXTURE))
            gate = subprocess.run(
                [sys.executable, str(ROOT / "approve.py"), "--self-check"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(gate.returncode, 0, gate.stderr)
            self.assertIn("SOD: PASS", gate.stdout)


if __name__ == "__main__":
    unittest.main()
