import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from diagnose import inspect, problems
from test_check_install import BLOCK, FOOTER, NOTES, old_block, scaffold, write
from uninstall import UninstallError, run

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "first-task"


class Diagnose(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.user = Path(self.tmp.name) / "home" / ".claude"
        self.project = Path(self.tmp.name) / "repo" / ".claude"

    def tearDown(self):
        self.tmp.cleanup()

    def scopes(self):
        return [inspect("user", self.user), inspect("project", self.project)]

    def test_clean_user_install(self):
        write(self.user / "CLAUDE.md", NOTES + [""] + BLOCK)
        scaffold(self.user)
        scopes = self.scopes()
        self.assertEqual(scopes[0].policy, "installed")
        self.assertEqual(scopes[0].revision, "5")
        self.assertEqual(scopes[0].agents, {"advisor": True, "executor": True, "verifier": True})
        self.assertEqual(problems(scopes, "5"), [])

    def test_reports_each_conflict(self):
        write(self.user / "CLAUDE.md", old_block())
        scaffold(self.user)
        write(self.project / "CLAUDE.md", BLOCK[:-1])
        write(self.project / "agents" / "executor.md", ["---", "name: executor", "description: mine", "---"])
        (self.user / "skills" / "stackwich").mkdir(parents=True)
        found = "\n".join(problems(self.scopes(), "5"))
        self.assertIn("user: policy-rev 4, current is 5", found)
        self.assertIn("project: CLAUDE.md policy block is malformed", found)
        self.assertIn("pre-3.0 clone", found)
        self.assertIn("agent 'executor' defined at both levels", found)

    def test_policy_at_both_levels_and_orphan_agents(self):
        write(self.user / "CLAUDE.md", BLOCK)
        write(self.project / "CLAUDE.md", BLOCK)
        found = "\n".join(problems(self.scopes(), "5"))
        self.assertIn("both user and project level", found)
        shutil.rmtree(self.project)
        (self.user / "CLAUDE.md").unlink()
        scaffold(self.user)
        self.assertIn("no policy block", "\n".join(problems(self.scopes(), "5")))

    def test_output_never_contains_file_contents(self):
        write(self.user / "CLAUDE.md", ["SECRET_TOKEN=abc123", ""] + BLOCK)
        scaffold(self.user)
        out = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("diagnose.py")),
             "--user", str(self.user), "--project", str(self.project)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertNotIn("abc123", out.stdout)
        self.assertNotIn("Working Architecture", out.stdout)
        self.assertIn("policy-rev 5", out.stdout)


class Uninstall(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.scope = Path(self.tmp.name) / ".claude"

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_changes_nothing(self):
        write(self.scope / "CLAUDE.md", NOTES + [""] + BLOCK)
        scaffold(self.scope)
        before = {p: p.read_bytes() for p in self.scope.rglob("*") if p.is_file()}
        out = "\n".join(run(self.scope, apply=False))
        self.assertIn("dry run", out)
        self.assertEqual(before, {p: p.read_bytes() for p in self.scope.rglob("*") if p.is_file()})

    def test_apply_keeps_unrelated_content_and_agents(self):
        names = {"executor": "builder"}
        write(self.scope / "CLAUDE.md", NOTES + [""] + BLOCK + [""] + FOOTER)
        scaffold(self.scope, names)
        mine = write(self.scope / "agents" / "executor.md", ["---", "name: executor", "description: mine", "---"])
        run(self.scope, apply=True)
        self.assertEqual((self.scope / "CLAUDE.md").read_text(), "\n".join(NOTES + [""] + FOOTER) + "\n")
        self.assertEqual(sorted(p.name for p in (self.scope / "agents").iterdir()), ["executor.md"])
        self.assertIn("mine", mine.read_text())
        backup = (self.scope / "CLAUDE.md.stackwich-backup").read_text()
        self.assertIn("<!-- stackwich:v1 -->", backup)

    def test_apply_removes_file_that_held_only_the_block(self):
        write(self.scope / "CLAUDE.md", BLOCK)
        run(self.scope, apply=True)
        self.assertFalse((self.scope / "CLAUDE.md").exists())
        self.assertTrue((self.scope / "CLAUDE.md.stackwich-backup").exists())

    def test_refuses_malformed_block(self):
        original = NOTES + [""] + BLOCK[:-1] + FOOTER
        write(self.scope / "CLAUDE.md", original)
        with self.assertRaises(UninstallError):
            run(self.scope, apply=True)
        self.assertEqual((self.scope / "CLAUDE.md").read_text(), "\n".join(original) + "\n")


class FirstTaskExample(unittest.TestCase):
    """The walkthrough's fail → correct → pass sequence must stay true."""

    def unittest_in(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-m", "unittest"], cwd=path,
                              capture_output=True, text=True, check=False)

    def test_fails_as_shipped_and_passes_after_the_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "first-task"
            shutil.copytree(EXAMPLE, work, ignore=shutil.ignore_patterns("__pycache__"))
            broken = self.unittest_in(work)
            self.assertNotEqual(broken.returncode, 0)
            self.assertIn("AssertionError: -270.0 != 27.0", broken.stderr)
            self.assertIn("FAILED (failures=1)", broken.stderr)
            cart = work / "cart.py"
            text = cart.read_text()
            self.assertEqual(text.count("subtotal * discount_percent, 2)"), 1)
            cart.write_text(text.replace("subtotal * discount_percent, 2)", "subtotal * discount_percent / 100, 2)"))
            fixed = self.unittest_in(work)
            self.assertEqual(fixed.returncode, 0, fixed.stderr)
            self.assertIn("Ran 3 tests", fixed.stderr)


if __name__ == "__main__":
    unittest.main()
