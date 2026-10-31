#!/usr/bin/env python3
"""Report what Stackwich has installed, where, and what conflicts.

Looks at the user scope (~/.claude) and the project scope (./.claude) and prints
the policy revision in each CLAUDE.md, the agents it finds and whether they are
Stackwich's, and known conflicts. It prints names, paths, and revisions only:
never file contents, so nothing in CLAUDE.md or an agent body is echoed.

It reads files only. Exit 0 when no problem is found, 1 when one is.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from check_install import CLOSE, CREDIT, OPEN, REV, ROLES, SKILL, _frontmatter, canonical_block


@dataclass
class Scope:
    label: str
    root: Path
    policy: str = "none"
    revision: str | None = None
    agents: dict[str, bool] = field(default_factory=dict)
    legacy_clone: bool = False


def current_revision() -> str:
    return next(m.group(1) for m in (REV.match(line) for line in canonical_block(SKILL)) if m)


def inspect(label: str, root: Path) -> Scope:
    scope = Scope(label, root)
    claude_md = root / "CLAUDE.md"
    if claude_md.is_file():
        lines = claude_md.read_text(encoding="utf-8", errors="replace").splitlines()
        opens, closes = lines.count(OPEN), lines.count(CLOSE)
        if opens == 1 and closes == 1:
            scope.policy = "installed"
        elif opens or closes:
            scope.policy = f"malformed ({opens} opening, {closes} closing marker)"
        revs = [m.group(1) for m in (REV.match(line) for line in lines) if m]
        scope.revision = ", ".join(revs) or None
    agents = root / "agents"
    if agents.is_dir():
        for path in sorted(agents.glob("*.md")):
            fields = _frontmatter(path.read_text(encoding="utf-8", errors="replace")) or {}
            name = fields.get("name") or path.stem
            scope.agents[name] = CREDIT in fields.get("author", "")
    scope.legacy_clone = (root / "skills" / "stackwich").exists()
    return scope


def problems(scopes: list[Scope], want: str) -> list[str]:
    found = []
    installed = [s for s in scopes if s.policy == "installed"]
    for s in scopes:
        if s.policy.startswith("malformed"):
            found.append(f"{s.label}: CLAUDE.md policy block is {s.policy}; re-run /stackwich:stackwich "
                         "and confirm the block boundary when asked")
        if s.policy == "installed" and s.revision != want:
            found.append(f"{s.label}: policy-rev {s.revision}, current is {want}; re-run /stackwich:stackwich")
        if s.legacy_clone:
            found.append(f"{s.label}: pre-3.0 clone at {s.root / 'skills' / 'stackwich'} — two skills named "
                         "stackwich; remove it as README 'Upgrading from 2.x' describes")
        mine = [name for name, ours in s.agents.items() if ours]
        if s.policy == "none" and mine:
            found.append(f"{s.label}: Stackwich agents ({', '.join(mine)}) but no policy block that refers to them")
    if len(installed) == 2:
        found.append("policy block installed at both user and project level; the project copy is read in "
                     "addition to the user copy, so keep one unless that is intended")
    by_name: dict[str, list[str]] = {}
    for s in scopes:
        for name in s.agents:
            by_name.setdefault(name, []).append(s.label)
    for name in ROLES:
        if len(by_name.get(name, [])) == 2:
            found.append(f"agent {name!r} defined at both levels; the project definition takes precedence")
    return found


def render(scopes: list[Scope], want: str) -> str:
    lines = [f"Stackwich policy-rev in this checkout: {want}", ""]
    for s in scopes:
        lines.append(f"{s.label} ({s.root})")
        lines.append(f"  CLAUDE.md policy: {s.policy}" + (f", policy-rev {s.revision}" if s.revision else ""))
        if s.agents:
            for name, ours in s.agents.items():
                lines.append(f"  agent {name}: {'Stackwich' if ours else 'not Stackwich'}")
        else:
            lines.append("  agents: none")
        lines.append("")
    found = problems(scopes, want)
    if found:
        lines.append("Problems:")
        lines.extend(f"  - {item}" for item in found)
    else:
        lines.append("Problems: none found")
    lines.append("")
    lines.append("For a line-by-line check of one scope, run tools/check_install.py on it.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report Stackwich installs and conflicts")
    parser.add_argument("--user", default="~/.claude", help="User scope directory (default ~/.claude)")
    parser.add_argument("--project", default="./.claude", help="Project scope directory (default ./.claude)")
    args = parser.parse_args(argv)
    want = current_revision()
    user = Path(args.user).expanduser().resolve()
    project = Path(args.project).expanduser().resolve()
    scopes = [inspect("user", user)]
    if project != user:
        scopes.append(inspect("project", project))
    print(render(scopes, want))
    return 1 if problems(scopes, want) else 0


if __name__ == "__main__":
    sys.exit(main())
