import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate import run

ROOT = Path(__file__).resolve().parent.parent
SKILL = Path("plugins/stackwich/skills/stackwich/SKILL.md")


class Validate(unittest.TestCase):
    """The repository checks CI runs, against a copy of this checkout with one thing broken."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"))

    def tearDown(self):
        self.tmp.cleanup()

    def edit(self, path, old, new):
        full = self.root / path
        text = full.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture drifted: {old!r} not in {path}")
        full.write_text(text.replace(old, new, 1), encoding="utf-8")

    def errors(self):
        ok, lines = run(self.root)
        self.assertFalse(ok, "\n".join(lines))
        return "\n".join(line for line in lines if line.startswith("::error::"))

    def test_this_checkout_passes(self):
        ok, lines = run(self.root)
        self.assertTrue(ok, "\n".join(lines))
        for done in ("manifests OK", "plugin shape OK", "SKILL.md OK", "frontmatter OK", "revisions OK",
                     "assets OK", "grok port OK", "codex port OK", "docs OK"):
            self.assertIn(done, lines)

    def test_marker_only_in_prose_fails(self):
        """CONTRIBUTING rule 4: the prose mention of the marker must not satisfy the check."""
        self.edit(SKILL, "\n<!-- stackwich:v1 -->\n", "\n")
        self.assertIn("`<!-- stackwich:v1 -->`", (self.root / SKILL).read_text(encoding="utf-8"))
        self.assertIn("SKILL.md must contain exactly one whole-line opening marker", self.errors())

    def test_frontmatter_policy_rev_disagrees_with_block(self):
        rev = re.search(r"^<!-- policy-rev: (\d+) -->$", (self.root / SKILL).read_text(), re.M).group(1)
        self.edit(SKILL, f"  policy-rev: {rev}\n", f"  policy-rev: {int(rev) - 1}\n")
        self.assertIn(f"frontmatter metadata.policy-rev is {int(rev) - 1}, but the block's policy-rev comment is {rev}",
                      self.errors())

    def test_port_readme_disagrees_with_port(self):
        readme = (self.root / "grok/README.md").read_text(encoding="utf-8")
        rev = re.search(r"`stackwich-grok-rev (\d+)`", readme).group(1)
        self.edit("grok/README.md", f"`stackwich-grok-rev {rev}`", f"`stackwich-grok-rev {int(rev) + 1}`")
        self.assertIn(f"grok/README.md says stackwich-grok-rev {int(rev) + 1}, but grok/SKILL.md says {rev}",
                      self.errors())

    def test_missing_agent_asset(self):
        (self.root / SKILL.parent / "assets" / "verifier.md").unlink()
        self.assertIn("plugins/stackwich/skills/stackwich/assets/verifier.md missing", self.errors())

    def test_plugin_must_not_ship_agents(self):
        (self.root / "plugins/stackwich/agents").mkdir()
        self.assertIn("the plugin must NOT ship agents/", self.errors())

    def test_version_mismatch(self):
        self.edit("plugins/stackwich/.claude-plugin/plugin.json", '"version": "', '"version": "9')
        self.assertIn("plugin.json version (9", self.errors())

    def test_cli_exit_code_and_annotations(self):
        self.edit("codex/references/templates.md", "## executor.toml", "## builder.toml")
        out = subprocess.run([sys.executable, str(Path(__file__).with_name("validate.py")), "--root", str(self.root)],
                             capture_output=True, text=True, check=False)
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertIn("::error::templates missing executor.toml section", out.stdout)
        self.assertIn("grok port OK", out.stdout)


if __name__ == "__main__":
    unittest.main()
