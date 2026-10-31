import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = Path(__file__).with_name("verify_gate.py")
sys.path.insert(0, str(ROOT / "measured"))

from log_event import EventError, validate_event  # noqa: E402
from report import load_events, summarize  # noqa: E402

PASSING = "python3 -c 'import sys; sys.exit(0)'"
FAILING = "python3 -c 'import sys; sys.exit(1)'"


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "feature")
        (self.repo / ".gitignore").write_text("build/\n")
        (self.repo / "app.py").write_text("print('v1')\n")
        self.git("add", ".")
        self.git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)

    def gate(self, *args):
        return subprocess.run([sys.executable, str(GATE), "--repo", str(self.repo), *args],
                              capture_output=True, text=True, check=False)

    def records(self):
        path = self.repo / ".stackwich" / "verify.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]

    def test_pass_records_commit_and_tree_and_check_passes(self):
        out = self.gate("run", "--", PASSING)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("GATE: PASS", out.stdout)
        record = self.records()[-1]
        head = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        self.assertEqual(record["head"], head)
        self.assertEqual(record["change"], "feature")
        self.assertEqual(len(record["tree"]), 64)
        self.assertIn("app.py", record["files"])
        ok = self.gate("check")
        self.assertEqual(ok.returncode, 0, ok.stdout)
        self.assertIn("VERIFIED", ok.stdout)

    def test_uncommitted_changes_are_part_of_the_tested_tree(self):
        (self.repo / "app.py").write_text("print('v2, not committed')\n")
        self.gate("run", "--", PASSING)
        self.assertEqual(self.gate("check").returncode, 0)
        self.git("checkout", "--", "app.py")
        stale = self.gate("check")
        self.assertEqual(stale.returncode, 1)
        self.assertIn("modified app.py", stale.stdout)

    def test_any_product_change_after_pass_makes_check_fail(self):
        self.gate("run", "--", PASSING)
        (self.repo / "app.py").write_text("print('edited after review')\n")
        (self.repo / "new.py").write_text("x = 1\n")
        stale = self.gate("check")
        self.assertEqual(stale.returncode, 1)
        self.assertIn("STALE", stale.stdout)
        self.assertIn("modified app.py", stale.stdout)
        self.assertIn("added new.py", stale.stdout)

    def test_deleted_file_after_pass_makes_check_fail(self):
        self.gate("run", "--", PASSING)
        (self.repo / "app.py").unlink()
        stale = self.gate("check")
        self.assertEqual(stale.returncode, 1)
        self.assertIn("removed app.py", stale.stdout)

    def test_artifacts_and_ignored_output_do_not_invalidate(self):
        writes = ("python3 -c \"import pathlib; "
                  "pathlib.Path('coverage').mkdir(exist_ok=True); pathlib.Path('coverage/r.txt').write_text('x'); "
                  "pathlib.Path('build').mkdir(exist_ok=True); pathlib.Path('build/o.bin').write_text('y')\"")
        out = self.gate("run", "--artifacts", "coverage", "--", writes)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        (self.repo / "coverage" / "later.txt").write_text("z")
        self.assertEqual(self.gate("check").returncode, 0)

    def test_command_that_edits_product_files_fails(self):
        out = self.gate("run", "--", "python3 -c \"open('app.py','w').write('patched by verifier')\"")
        self.assertEqual(out.returncode, 1)
        self.assertIn("GATE: FAIL", out.stdout)
        self.assertIn("modified app.py", out.stdout)
        self.assertEqual(self.records()[-1]["changed_during_run"], ["modified app.py"])
        self.assertEqual(self.gate("check").returncode, 1)

    def test_third_failure_blocks_further_runs_until_reset(self):
        for attempt, left in ((1, "2 correction cycle(s) left"), (2, "1 correction cycle(s) left"),
                              (3, "no correction cycles left")):
            out = self.gate("run", "--", FAILING)
            self.assertEqual(out.returncode, 1)
            self.assertIn(left, out.stdout)
            self.assertEqual(self.records()[-1]["attempt"], attempt)
        refused = self.gate("run", "--", PASSING)
        self.assertEqual(refused.returncode, 3)
        self.assertIn("refuse", refused.stderr)
        self.assertEqual(len(self.records()), 3)
        self.assertEqual(self.gate("reset", "--by", "lead", "--reason", "").returncode, 2)
        self.assertEqual(self.gate("reset", "--by", "lead", "--reason", "re-planned").returncode, 0)
        again = self.gate("run", "--", PASSING)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)

    def test_pass_clears_the_failure_count(self):
        self.gate("run", "--", FAILING)
        self.gate("run", "--", FAILING)
        self.gate("run", "--", PASSING)
        self.gate("run", "--", FAILING)
        self.assertEqual(self.records()[-1]["attempt"], 1)

    def test_changes_are_counted_separately(self):
        for _ in range(3):
            self.gate("run", "--change", "a", "--", FAILING)
        self.assertEqual(self.gate("run", "--change", "a", "--", PASSING).returncode, 3)
        self.assertEqual(self.gate("run", "--change", "b", "--", PASSING).returncode, 0)
        self.assertEqual(self.gate("check", "--change", "b").returncode, 0)
        self.assertEqual(self.gate("check", "--change", "a").returncode, 1)

    def test_check_without_a_pass(self):
        none = self.gate("check")
        self.assertEqual(none.returncode, 1)
        self.assertIn("no verification recorded", none.stdout)
        self.gate("run", "--", FAILING)
        failed = self.gate("check")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("last verification", failed.stdout)

    def test_measured_log_gets_a_verified_event_with_the_tree(self):
        log = Path(self.tmp.name) / "events.jsonl"
        self.gate("run", "--log", str(log), "--", PASSING)
        self.gate("run", "--log", str(log), "--", FAILING)
        events = load_events(log)
        self.assertEqual([e["verdict"] for e in events], ["PASS", "FAIL"])
        self.assertEqual(events[0]["tree"], self.records()[0]["tree"])
        self.assertEqual(summarize(events)["verification"], {"pass": 1, "fail": 1})

    def test_usage_errors(self):
        self.assertEqual(self.gate("run").returncode, 2)
        outside = subprocess.run([sys.executable, str(GATE), "--repo", self.tmp.name, "check"],
                                 capture_output=True, text=True, check=False)
        self.assertEqual(outside.returncode, 2)


class TreeField(unittest.TestCase):
    def test_tree_is_validated(self):
        base = {"event": "sandwich.verified", "actor": "verifier", "work_id": "w", "verdict": "PASS"}
        validate_event(dict(base, tree="a" * 64))
        for bad in ("A" * 64, "a" * 63, 7):
            with self.assertRaises(EventError):
                validate_event(dict(base, tree=bad))
        with self.assertRaises(EventError):
            validate_event({"event": "sandwich.planned", "actor": "advisor", "work_id": "w", "tree": "a" * 64})


if __name__ == "__main__":
    unittest.main()
