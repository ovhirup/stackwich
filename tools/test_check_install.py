import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_install import REV, ROLES, check, canonical_block, rename

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "plugins" / "stackwich" / "skills" / "stackwich" / "assets"
BLOCK = canonical_block()
CURRENT = next(m.group(1) for m in map(REV.match, BLOCK) if m)
NOTES = ["# My project", "", "- Use tabs.", "- Never commit secrets."]
FOOTER = ["## Local notes", "", "Deploys go through the release train."]


def old_block(rev: str = "4") -> list[str]:
    """A previous revision: same markers, older policy-rev, one bullet missing."""
    lines = [line.replace(f"policy-rev: {CURRENT}", f"policy-rev: {rev}") for line in BLOCK]
    return lines[:6] + lines[7:]


def write(path: Path, lines: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def scaffold(scope: Path, names: dict[str, str] | None = None) -> None:
    names = names or {}
    for role in ROLES:
        name = names.get(role, role)
        text = (ASSETS / f"{role}.md").read_text(encoding="utf-8")
        text = text.replace(f"name: {role}\n", f"name: {name}\n", 1)
        (scope / "agents").mkdir(parents=True, exist_ok=True)
        (scope / "agents" / f"{name}.md").write_text(text, encoding="utf-8")


def failures(report) -> dict[str, str]:
    return {check: detail for ok, check, detail in report.results if not ok}


class InstallFixtures(unittest.TestCase):
    """The five install paths from evals/evals.json, checked on their resulting files."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.scope = Path(self.tmp.name) / ".claude"
        self.before = Path(self.tmp.name) / "before.md"

    def tearDown(self):
        self.tmp.cleanup()

    def test_fresh_install(self):
        write(self.scope / "CLAUDE.md", BLOCK)
        scaffold(self.scope)
        report = check(self.scope, agents=True)
        self.assertTrue(report.ok, report.render())

    def test_fresh_install_into_existing_claude_md(self):
        write(self.before, NOTES)
        write(self.scope / "CLAUDE.md", NOTES + [""] + BLOCK)
        scaffold(self.scope)
        report = check(self.scope, agents=True, before=self.before)
        self.assertTrue(report.ok, report.render())

    def test_upgrade_replaces_block_in_place(self):
        write(self.before, NOTES + [""] + old_block() + [""] + FOOTER)
        write(self.scope / "CLAUDE.md", NOTES + [""] + BLOCK + [""] + FOOTER)
        scaffold(self.scope)
        report = check(self.scope, agents=True, before=self.before)
        self.assertTrue(report.ok, report.render())

    def test_collision_rename(self):
        names = {"executor": "builder"}
        write(self.scope / "CLAUDE.md", rename(BLOCK, names))
        scaffold(self.scope, names)
        write(self.scope / "agents" / "executor.md", ["---", "name: executor", "description: unrelated", "---"])
        report = check(self.scope, agents=True, names=names)
        self.assertTrue(report.ok, report.render())
        self.assertIn("unrelated", (self.scope / "agents" / "executor.md").read_text())

    def test_policy_only_install(self):
        write(self.scope / "CLAUDE.md", BLOCK)
        report = check(self.scope, agents=False)
        self.assertTrue(report.ok, report.render())
        self.assertFalse((self.scope / "agents").exists())
        self.assertFalse(any("agent" in check for _, check, _ in report.results))

    def test_missing_closing_marker_is_named(self):
        write(self.scope / "CLAUDE.md", NOTES + [""] + BLOCK[:-1] + FOOTER)
        report = check(self.scope, agents=False)
        self.assertFalse(report.ok)
        self.assertIn("no closing marker", failures(report)["markers"])
        self.assertIn("confirmed by a person", failures(report)["markers"])


class BrokenInstalls(unittest.TestCase):
    """Deliberately broken results must fail, and say what is wrong."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.scope = Path(self.tmp.name) / ".claude"
        self.before = Path(self.tmp.name) / "before.md"

    def tearDown(self):
        self.tmp.cleanup()

    def test_upgrade_that_appended_a_second_block(self):
        write(self.scope / "CLAUDE.md", old_block() + [""] + BLOCK)
        failed = failures(check(self.scope, agents=False))
        self.assertIn("found 2 and 2", failed["markers"])

    def test_stale_policy_rev(self):
        write(self.scope / "CLAUDE.md", old_block())
        failed = failures(check(self.scope, agents=False))
        self.assertIn(f"policy-rev {CURRENT}", failed["policy-rev"])
        self.assertIn("found 4", failed["policy-rev"])
        self.assertIn("policy block matches SKILL.md", failed)

    def test_edited_policy_block(self):
        edited = list(BLOCK)
        edited[10] = edited[10] + " (edited)"
        write(self.scope / "CLAUDE.md", edited)
        failed = failures(check(self.scope, agents=False))
        self.assertIn("first difference at line 11", failed["policy block matches SKILL.md"])

    def test_unrelated_content_lost(self):
        write(self.before, NOTES + [""] + old_block() + [""] + FOOTER)
        write(self.scope / "CLAUDE.md", NOTES + [""] + BLOCK)
        failed = failures(check(self.scope, agents=False, before=self.before))
        self.assertIn("lost '## Local notes'", failed["unrelated content preserved"])

    def test_rename_applied_to_agent_file_only(self):
        names = {"executor": "builder"}
        write(self.scope / "CLAUDE.md", BLOCK)
        scaffold(self.scope, names)
        failed = failures(check(self.scope, agents=True, names=names))
        self.assertIn("executor", failed["renamed agents in policy"])
        self.assertIn("policy block matches SKILL.md", failed)

    def test_rename_applied_to_policy_only(self):
        names = {"executor": "builder"}
        write(self.scope / "CLAUDE.md", rename(BLOCK, names))
        scaffold(self.scope)
        failed = failures(check(self.scope, agents=True, names=names))
        self.assertIn("not found", failed["agent builder"])

    def test_agent_missing_frontmatter_field_and_credit(self):
        write(self.scope / "CLAUDE.md", BLOCK)
        scaffold(self.scope)
        path = self.scope / "agents" / "verifier.md"
        text = path.read_text(encoding="utf-8")
        text = "\n".join(line for line in text.splitlines()
                         if not line.startswith(("tools:", "author:"))) + "\n"
        path.write_text(text, encoding="utf-8")
        detail = failures(check(self.scope, agents=True))["agent verifier"]
        self.assertIn("frontmatter missing tools", detail)
        self.assertIn("author line edited or removed", detail)

    def test_missing_claude_md(self):
        failed = failures(check(self.scope, agents=False))
        self.assertIn("not found", failed["CLAUDE.md exists"])


class Cli(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(Path(__file__).with_name("check_install.py")), *args],
            capture_output=True, text=True, check=False,
        )

    def test_exit_codes_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = Path(tmp) / ".claude"
            write(scope / "CLAUDE.md", BLOCK)
            ok = self.run_cli(str(scope), "--no-agents")
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertIn("INSTALL: PASS", ok.stdout)
            bad = self.run_cli(str(scope))
            self.assertEqual(bad.returncode, 1)
            self.assertIn("FAIL: agent advisor", bad.stdout)
            self.assertIn("INSTALL: FAIL", bad.stdout)
            usage = self.run_cli(str(scope), "--rename", "planner=thinker")
            self.assertEqual(usage.returncode, 2)
            self.assertIn("unknown agent role", usage.stderr)


if __name__ == "__main__":
    unittest.main()
