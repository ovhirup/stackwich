#!/usr/bin/env python3
"""Run the repository checks that CI's skill-lint job runs, locally, with one command.

  python3 tools/validate.py            # from anywhere in a checkout
  python3 tools/validate.py --root DIR # check another copy of the repository

Each category prints "<category> OK" or one "::error::" line per problem, in the
format GitHub Actions turns into annotations. Every category runs, so one call shows
every failing category; the exit code is 1 if any failed. A category that came from
a shell step stops at its first problem, as the step did.

Marker and revision checks match whole lines on purpose (CONTRIBUTING.md rule 4):
SKILL.md quotes its own marker in prose, and a substring check would pass on that.
It reads files only. Needs PyYAML: python3 -m pip install pyyaml.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import pathlib
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - depends on the environment
    yaml = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
S = "plugins/stackwich/skills/stackwich/SKILL.md"
A = "plugins/stackwich/skills/stackwich/assets"
PLUGIN = "plugins/stackwich/.claude-plugin/plugin.json"
MARKET = ".claude-plugin/marketplace.json"
LAYERS = ("Prompt", "Context", "Harness", "Loop", "Graph")


class Failed(Exception):
    """A shell-derived check stops at its first problem, as `exit 1` did in the workflow."""


def _lines(root: pathlib.Path, path: str) -> list[str]:
    return (root / path).read_text(encoding="utf-8").splitlines()


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise Failed(message)


def _block(lines: list[str], start: str, end: str) -> list[str]:
    """Like awk '/^start$/,/^end$/': from the first whole-line start to the next whole-line end."""
    if start not in lines:
        return []
    i = lines.index(start)
    j = lines.index(end, i + 1) if end in lines[i + 1:] else len(lines) - 1
    return lines[i:j + 1]


def _json(root: pathlib.Path, path: str):
    try:
        return json.loads((root / path).read_text(encoding="utf-8"))
    except ValueError:
        return None


def manifests(root: pathlib.Path) -> str:
    _require((root / MARKET).is_file(), "marketplace.json missing")
    _require((root / PLUGIN).is_file(), "plugin.json missing")
    market, plugin = _json(root, MARKET), _json(root, PLUGIN)
    _require(market is not None, "marketplace.json is not valid JSON")
    _require(plugin is not None, "plugin.json is not valid JSON")
    plugins = market.get("plugins") or []
    _require(len(plugins) == 1, "marketplace must list exactly one plugin")
    _require(plugins[0].get("source") == "./plugins/stackwich", "marketplace entry source must be ./plugins/stackwich")
    _require(plugins[0].get("name") == plugin.get("name"), "marketplace entry name and plugin.json name disagree")
    pv = str(plugin.get("version"))
    sv = next((m.group(1) for m in map(re.compile(r"^\s*version:\s*(.*)$").match, _lines(root, S)) if m), "")
    _require(pv == sv, f"plugin.json version ({pv}) != SKILL.md version ({sv})")
    _require(filecmp.cmp(root / "LICENSE", root / "plugins/stackwich/LICENSE", shallow=False),
             "plugins/stackwich/LICENSE has drifted from the root LICENSE")
    _require(any(line.startswith(f"## {pv} ") for line in _lines(root, "CHANGELOG.md")),
             f"CHANGELOG.md has no '## {pv}' heading — a shipped version with no release note")
    return "manifests OK"


def plugin_shape(root: pathlib.Path) -> str:
    _require(not (root / "SKILL.md").exists(), "a root SKILL.md reappeared — the canonical skill lives at "
             "plugins/stackwich/skills/stackwich/SKILL.md and must not be duplicated")
    _require(not (root / "assets").exists(),
             "a root assets/ reappeared — the scaffolding source lives inside the skill directory")
    _require(not (root / "plugins/stackwich/agents").exists(), "the plugin must NOT ship agents/ — plugin agents "
             "install namespaced (stackwich:advisor) and the policy block references bare names; the skill "
             "scaffolds them instead")
    _require(len(list((root / "plugins/stackwich/skills").iterdir())) == 1,
             "plugins/stackwich/skills must contain exactly one skill directory")
    return "plugin shape OK"


def skill_structure(root: pathlib.Path) -> str:
    _require((root / S).is_file(), f"{S} missing")
    s = _lines(root, S)
    _require(s[:1] == ["---"], "missing frontmatter opener")
    _require(any(line.startswith("name: stackwich") for line in s), "frontmatter name missing")
    _require(any(line.startswith("description:") for line in s), "frontmatter description missing")
    _require(any(re.match(r"\s*author:", line) for line in s), "frontmatter author missing")
    _require(s.count("<!-- stackwich:v1 -->") == 1, "SKILL.md must contain exactly one whole-line opening marker")
    _require(s.count("<!-- /stackwich:v1 -->") == 1, "SKILL.md must contain exactly one whole-line closing marker")
    _require(sum(bool(re.fullmatch(r"<!-- policy-rev: [0-9]+ -->", line)) for line in s) == 1,
             "SKILL.md must contain exactly one whole-line policy-rev comment")
    block = _block(s, "<!-- stackwich:v1 -->", "<!-- /stackwich:v1 -->")
    for h in LAYERS:
        _require(any(line.startswith(f"### {h}") for line in block), f"policy block missing the {h} layer")
    return "SKILL.md OK"


def frontmatter(root: pathlib.Path) -> list[str]:
    targets = {S: "stackwich", "grok/SKILL.md": "stackwich-grok", "codex/SKILL.md": "stackwich-codex"}
    bad = []
    for path, expect in targets.items():
        text = (root / path).read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            bad.append(f"{path} has no frontmatter block"); continue
        block = text.split("---\n", 2)[1]
        try:
            fm = yaml.safe_load(block)
        except yaml.YAMLError as e:
            bad.append(f"{path} frontmatter is not valid YAML: {e}"); continue
        if fm.get("name") != expect:
            bad.append(f"{path} name is {fm.get('name')!r}, expected {expect!r}")
        desc = fm.get("description") or ""
        if not desc:
            bad.append(f"{path} has no description")
        elif len(desc) > 1024:
            bad.append(f"{path} description is {len(desc)} chars, over the 1024 limit")
        if not fm.get("author") and not (fm.get("metadata") or {}).get("author"):
            bad.append(f"{path} has no author — every distributed copy must name one")
    return bad


def revisions(root: pathlib.Path) -> list[str]:
    bad = []
    def lines(p): return _lines(root, p)
    def region(ls, start, end, path):
        if ls.count(start) != 1 or ls.count(end) != 1:
            bad.append(f"{path} needs exactly one whole-line {start} and {end}"); return []
        return ls[ls.index(start) + 1:ls.index(end)]
    def one(ls, pattern, what):
        hits = [m.group(1) for m in map(re.compile(pattern).fullmatch, ls) if m]
        if len(hits) != 1:
            bad.append(f"{what}: expected exactly one, found {len(hits)}"); return None
        return hits[0]
    s = lines(S)
    rev = one(region(s, "<!-- stackwich:v1 -->", "<!-- /stackwich:v1 -->", S), r"<!-- policy-rev: (\d+) -->",
              f"{S} policy-rev comment inside the block")
    fm = s[1:s.index("---", 1)] if s[:1] == ["---"] and "---" in s[1:] else []
    md = [k for k, x in enumerate(fm) if x == "metadata:"]
    if len(md) != 1:
        bad.append(f"{S} frontmatter needs exactly one whole-line metadata: key, found {len(md)}"); meta = None
    else:
        e = next((k for k in range(md[0] + 1, len(fm)) if fm[k].strip() and not fm[k][0].isspace()), len(fm))
        meta = one(fm[md[0] + 1:e], r"  policy-rev: (\d+)", f"{S} frontmatter policy-rev directly under metadata")
    h = "## 4. Verify the install"
    i = s.index(h) if h in s else len(s)
    j = next((k for k in range(i + 1, len(s)) if s[k].startswith("## ")), len(s))
    step4 = one(s[i + 1:j], r"2\. `policy-rev: (\d+)` is present inside the block.*", f"{S} step 4 check 2")
    for label, val in (("frontmatter metadata.policy-rev", meta), ("step 4 check 2", step4)):
        if None not in (rev, val) and val != rev:
            bad.append(f"{S} {label} is {val}, but the block's policy-rev comment is {rev}")
    evals = {e["id"]: e for e in json.loads((root / "evals/evals.json").read_text(encoding="utf-8"))["evals"]}
    for cid in (1, 2):
        case = evals.get(cid, {})
        found = {n for t in [case.get("expected_output", ""), *case.get("assertions", [])]
                 for n in re.findall(r"policy-rev:? (\d+)", t)}
        if not found:
            bad.append(f"evals/evals.json case {cid} names no policy-rev number")
        for n in sorted(found - {rev}):
            bad.append(f"evals/evals.json case {cid} says policy-rev {n}, but the block says {rev}")
    for port, path, readme, a, b in (
            ("grok", "grok/SKILL.md", "grok/README.md", "<!-- stackwich:v1 -->", "<!-- /stackwich:v1 -->"),
            ("codex", "codex/references/templates.md", "codex/README.md",
             "<!-- stackwich-codex:v1 -->", "<!-- /stackwich-codex:v1 -->")):
        prev = one(region(lines(path), a, b, path), rf"<!-- stackwich-{port}-rev: (\d+) -->",
                   f"{path} stackwich-{port}-rev comment inside the block")
        said = re.findall(rf"`stackwich-{port}-rev (\d+)`", (root / readme).read_text(encoding="utf-8"))
        if len(said) != 1:
            bad.append(f"{readme}: expected exactly one `stackwich-{port}-rev N` mention, found {len(said)}")
        elif prev is not None and said[0] != prev:
            bad.append(f"{readme} says stackwich-{port}-rev {said[0]}, but {path} says {prev}")
    return bad


def agent_assets(root: pathlib.Path) -> str:
    for a in ("advisor", "executor", "verifier"):
        path = f"{A}/{a}.md"
        _require((root / path).is_file(), f"{path} missing")
        ls = _lines(root, path)
        _require(any(line.startswith(f"name: {a}") for line in ls), f"{path} name wrong")
        _require(any(line.startswith("model:") for line in ls), f"{path} model missing")
        _require(any(line.startswith("tools:") for line in ls), f"{path} tools missing")
    return "assets OK"


def grok_port(root: pathlib.Path) -> str:
    path = "grok/SKILL.md"
    _require((root / path).is_file(), "grok/SKILL.md missing")
    g = _lines(root, path)
    _require("name: stackwich-grok" in g, "grok port name must be stackwich-grok")
    _require(g.count("<!-- stackwich:v1 -->") == 1, "grok needs exactly one whole-line opening marker")
    _require(g.count("<!-- /stackwich:v1 -->") == 1, "grok needs exactly one whole-line closing marker")
    _require(sum(line.startswith("```") for line in g) == 2, "grok policy block fence unbalanced")
    _require(sum(bool(re.fullmatch(r"<!-- stackwich-grok-rev: [0-9]+ -->", line)) for line in g) == 1,
             "grok policy block needs exactly one whole-line rev comment")
    block = _block(g, "<!-- stackwich:v1 -->", "<!-- /stackwich:v1 -->")
    for h in LAYERS:
        _require(any(line.startswith(f"### {h}") for line in block), f"grok policy block missing the {h} layer")
    return "grok port OK"


def codex_port(root: pathlib.Path) -> str:
    _require((root / "codex/SKILL.md").is_file(), "codex/SKILL.md missing")
    _require("name: stackwich-codex" in _lines(root, "codex/SKILL.md"), "codex port name must be stackwich-codex")
    t = "codex/references/templates.md"
    _require((root / t).is_file(), "codex/references/templates.md missing — SKILL.md depends on it")
    c = _lines(root, t)
    _require(c.count("<!-- stackwich-codex:v1 -->") == 1, "codex templates need exactly one whole-line opening marker")
    _require(c.count("<!-- /stackwich-codex:v1 -->") == 1,
             "codex templates need exactly one whole-line closing marker")
    _require(sum(bool(re.fullmatch(r"<!-- stackwich-codex-rev: [0-9]+ -->", line)) for line in c) == 1,
             "codex policy block needs exactly one whole-line rev comment")
    block = _block(c, "<!-- stackwich-codex:v1 -->", "<!-- /stackwich-codex:v1 -->")
    for h in LAYERS:
        _require(any(line.startswith(f"### {h}") for line in block), f"codex policy block missing the {h} layer")
    for a in ("advisor", "executor", "verifier"):
        _require(any(re.match(rf"## {a}.toml", line) for line in c), f"templates missing {a}.toml section")
    _require((root / "codex/agents/openai.yaml").is_file(), "codex/agents/openai.yaml missing")
    _require((root / "codex/LICENSE").is_file(), "codex/LICENSE missing")
    return "codex port OK"


def hero_image(root: pathlib.Path) -> str:
    _require((root / "docs/sandwich.jpg").is_file(), "docs/sandwich.jpg missing")
    return "docs OK"


CHECKS = (
    (manifests, None), (plugin_shape, None), (skill_structure, None),
    (frontmatter, "frontmatter OK"), (revisions, "revisions OK"),
    (agent_assets, None), (grok_port, None), (codex_port, None), (hero_image, None),
)


def run(root: pathlib.Path = ROOT) -> tuple[bool, list[str]]:
    """Run every category. Returns whether all passed, and the lines to print."""
    out, ok = [], True
    for check, done in CHECKS:
        try:
            result = check(root)
        except Failed as exc:
            out.append(f"::error::{exc}"); ok = False; continue
        except (OSError, ValueError, KeyError, IndexError) as exc:
            out.append(f"::error::{check.__name__}: {exc}"); ok = False; continue
        if isinstance(result, list):
            out.extend(f"::error::{msg}" for msg in result)
            ok = ok and not result
            if not result:
                out.append(done)
        else:
            out.append(result)
    return ok, out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the repository checks CI's skill-lint job runs")
    parser.add_argument("--root", default=str(ROOT), help="Repository root to check (default: this checkout)")
    args = parser.parse_args(argv)
    if yaml is None:
        print("::error::PyYAML is not installed; run: python3 -m pip install pyyaml", file=sys.stderr)
        return 2
    ok, lines = run(pathlib.Path(args.root).resolve())
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
