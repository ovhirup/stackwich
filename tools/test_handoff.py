import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HANDOFF = Path(__file__).with_name("handoff.py")
GATE = Path(__file__).with_name("verify_gate.py")


class HandoffTests(unittest.TestCase):
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

    def run_tool(self, tool, *args):
        return subprocess.run([sys.executable, str(tool), "--repo", str(self.repo), *args],
                              capture_output=True, text=True, check=False)

    def save(self, *extra):
        return self.run_tool(HANDOFF, "save", "--stage", "executing", "--next", "Finish step 3 of the plan",
                             "--plan", "specs/feature.md", *extra)

    def test_resume_without_a_handoff(self):
        out = self.run_tool(HANDOFF, "resume")
        self.assertEqual(out.returncode, 2)
        self.assertIn("NO HANDOFF", out.stdout)

    def test_save_records_stage_plan_commit_and_status(self):
        (self.repo / "app.py").write_text("print('v2, uncommitted')\n")
        out = self.save("--note", "Ask about the retry limit")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        text = (self.repo / ".stackwich" / "handoff.md").read_text()
        for expected in ("- Change: feature", "- Stage: executing", "- Next step: Finish step 3 of the plan",
                         "- Plan: specs/feature.md", "- Last gate: none recorded", " M app.py",
                         "Ask about the retry limit"):
            self.assertIn(expected, text)
        self.assertNotIn(".stackwich", text.split("```")[1])

    def test_resume_unchanged(self):
        self.save()
        out = self.run_tool(HANDOFF, "resume")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("- Next step: Finish step 3 of the plan", out.stdout)
        self.assertIn("UNCHANGED", out.stdout)

    def test_resume_names_every_change_since_the_handoff(self):
        self.save()
        (self.repo / "app.py").write_text("print('edited between sessions')\n")
        (self.repo / "new.py").write_text("x = 1\n")
        (self.repo / "build").mkdir()
        (self.repo / "build" / "out.bin").write_text("ignored output")
        out = self.run_tool(HANDOFF, "resume")
        self.assertEqual(out.returncode, 1)
        self.assertIn("CHANGED SINCE HANDOFF: 2 product file(s)", out.stdout)
        self.assertIn("modified app.py", out.stdout)
        self.assertIn("added new.py", out.stdout)
        self.assertNotIn("build/out.bin", out.stdout)

    def test_resume_reports_a_moved_commit_and_removed_file(self):
        self.save()
        self.git("rm", "-q", "app.py")
        self.git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "remove")
        out = self.run_tool(HANDOFF, "resume")
        self.assertEqual(out.returncode, 1)
        self.assertIn("Commit moved:", out.stdout)
        self.assertIn("removed app.py", out.stdout)

    def test_resume_reports_whether_the_last_pass_still_holds(self):
        self.run_tool(GATE, "run", "--", "python3 -c 'pass'")
        self.save()
        text = (self.repo / ".stackwich" / "handoff.md").read_text()
        self.assertIn("- Last gate: PASS", text)
        self.assertIn("VERIFIED", self.run_tool(HANDOFF, "resume").stdout)
        (self.repo / "app.py").write_text("print('changed')\n")
        out = self.run_tool(HANDOFF, "resume")
        self.assertIn("STALE", out.stdout)

    def test_hand_written_handoff(self):
        (self.repo / ".stackwich").mkdir()
        (self.repo / ".stackwich" / "handoff.md").write_text("# Notes\n\nStage: reviewing\n")
        out = self.run_tool(HANDOFF, "resume")
        self.assertEqual(out.returncode, 1)
        self.assertIn("Stage: reviewing", out.stdout)
        self.assertIn("UNCHECKED", out.stdout)

    def test_bad_input(self):
        self.assertEqual(self.run_tool(HANDOFF, "save", "--stage", "executing", "--next", " ").returncode, 2)
        self.assertEqual(self.run_tool(HANDOFF, "save", "--stage", "nowhere", "--next", "x").returncode, 2)
        self.save()
        (self.repo / ".stackwich" / "handoff-files.json").write_text("not json")
        corrupt = self.run_tool(HANDOFF, "resume")
        self.assertEqual(corrupt.returncode, 2)
        self.assertIn("not a handoff fingerprint", corrupt.stderr)


if __name__ == "__main__":
    unittest.main()
