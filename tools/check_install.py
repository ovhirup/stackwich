#!/usr/bin/env python3
"""Check an installed Stackwich scope against what SKILL.md promises.

The Stackwich skill is carried out by a model, so its install cannot be replayed
here. This script checks the result instead: the files a finished install leaves
in a scope directory (~/.claude or ./.claude). It reads the expected policy block
from SKILL.md, prints one line per check, and exits 1 if any check fails.

It reads files only. It does not write, call a network, or call a model. A pass
means the files match the contract; it says nothing about how the agents behave.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "stackwich" / "skills" / "stackwich" / "SKILL.md"
OPEN = "<!-- stackwich:v1 -->"
CLOSE = "<!-- /stackwich:v1 -->"
REV = re.compile(r"^<!-- policy-rev: (\d+) -->$")
ROLES = ("advisor", "executor", "verifier")
AGENT_FIELDS = ("name", "description", "model", "tools")
CREDIT = "part of the Stackwich architecture"


class CheckError(ValueError):
    """The inputs cannot be checked at all."""


@dataclass
class Report:
    results: list[tuple[bool, str, str]] = field(default_factory=list)

    def add(self, ok: bool, check: str, detail: str = "") -> None:
        self.results.append((ok, check, detail))

    @property
    def ok(self) -> bool:
        return all(ok for ok, _, _ in self.results)

    def render(self) -> str:
        lines = []
        for ok, check, detail in self.results:
            line = f"{'PASS' if ok else 'FAIL'}: {check}"
            if detail:
                line += f" — {detail}"
            lines.append(line)
        lines.append("INSTALL: PASS" if self.ok else "INSTALL: FAIL")
        return "\n".join(lines)


def canonical_block(skill: Path = SKILL) -> list[str]:
    lines = skill.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(OPEN)
        end = lines.index(CLOSE, start)
    except ValueError as exc:
        raise CheckError(f"{skill} has no complete policy block") from exc
    return lines[start:end + 1]


def rename(lines: list[str], names: dict[str, str]) -> list[str]:
    if not names:
        return list(lines)
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, names)) + r")\b")
    return [pattern.sub(lambda m: names[m.group(1)], line) for line in lines]


def _outside(lines: list[str]) -> list[str]:
    """The lines outside one complete block, with blank-line runs collapsed."""
    if OPEN in lines and CLOSE in lines[lines.index(OPEN):]:
        start = lines.index(OPEN)
        end = lines.index(CLOSE, start)
        lines = lines[:start] + [""] + lines[end + 1:]
    collapsed: list[str] = []
    for line in (line.rstrip() for line in lines):
        if line or (collapsed and collapsed[-1]):
            collapsed.append(line)
    while collapsed and not collapsed[-1]:
        collapsed.pop()
    return collapsed


def _frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    fields = {}
    for line in lines[1:end]:
        key, sep, value = line.partition(":")
        if sep and key.strip() and not key.startswith(" "):
            fields[key.strip()] = value.strip()
    return fields


def check_policy(claude_md: Path, report: Report, names: dict[str, str], before: Path | None, skill: Path) -> None:
    if not claude_md.is_file():
        report.add(False, "CLAUDE.md exists", f"not found: {claude_md}")
        return
    lines = claude_md.read_text(encoding="utf-8").splitlines()
    opens = [i for i, line in enumerate(lines) if line == OPEN]
    closes = [i for i, line in enumerate(lines) if line == CLOSE]
    if len(opens) == 1 and not closes:
        report.add(False, "markers", f"opening marker on line {opens[0] + 1} has no closing marker {CLOSE}; "
                   "the block boundary must be confirmed by a person before anything is replaced")
        return
    if len(opens) != 1 or len(closes) != 1:
        report.add(False, "markers", f"expected exactly one {OPEN} and one {CLOSE} as whole lines, "
                   f"found {len(opens)} and {len(closes)}")
        return
    if closes[0] < opens[0]:
        report.add(False, "markers", "closing marker comes before the opening marker")
        return
    report.add(True, "markers", f"one block, lines {opens[0] + 1}–{closes[0] + 1}")

    block = lines[opens[0]:closes[0] + 1]
    expected = rename(canonical_block(skill), names)
    revs = [m.group(1) for m in (REV.match(line) for line in block) if m]
    want_rev = next(m.group(1) for m in (REV.match(line) for line in expected) if m)
    stale = [m.group(1) for m in (REV.match(line) for line in lines) if m and m.group(1) != want_rev]
    if revs == [want_rev] and not stale:
        report.add(True, "policy-rev", f"policy-rev {want_rev}")
    else:
        report.add(False, "policy-rev", f"expected exactly one policy-rev {want_rev} and no other revision; "
                   f"found {', '.join(revs) or 'none'} inside the block"
                   + (f" and {', '.join(stale)} in the file" if stale else ""))

    if block == expected:
        report.add(True, "policy block matches SKILL.md")
    else:
        for number, (got, want) in enumerate(zip(block, expected), opens[0] + 1):
            if got != want:
                detail = f"first difference at line {number}: expected {want!r}, found {got!r}"
                break
        else:
            detail = f"block has {len(block)} lines, SKILL.md has {len(expected)}"
        report.add(False, "policy block matches SKILL.md", detail)

    if names:
        leftover = sorted(old for old in names
                          if any(re.search(rf"\b{re.escape(old)}\b", line) for line in block))
        if leftover:
            report.add(False, "renamed agents in policy", f"old name(s) still in the block: {', '.join(leftover)}")
        else:
            report.add(True, "renamed agents in policy", ", ".join(f"{k} → {v}" for k, v in names.items()))

    if before is not None:
        old = _outside(before.read_text(encoding="utf-8").splitlines()) if before.is_file() else []
        new = _outside(lines)
        if old == new:
            report.add(True, "unrelated content preserved")
        else:
            missing = [line for line in old if line and line not in new]
            added = [line for line in new if line and line not in old]
            detail = []
            if missing:
                detail.append(f"lost {missing[0]!r}" + (f" and {len(missing) - 1} more" if len(missing) > 1 else ""))
            if added:
                detail.append(f"added {added[0]!r}" + (f" and {len(added) - 1} more" if len(added) > 1 else ""))
            report.add(False, "unrelated content preserved", "; ".join(detail) or "line order changed")


def check_agents(agents: Path, report: Report, names: dict[str, str]) -> None:
    for role in ROLES:
        name = names.get(role, role)
        path = agents / f"{name}.md"
        if not path.is_file():
            report.add(False, f"agent {name}", f"not found: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        fields = _frontmatter(text)
        if fields is None:
            report.add(False, f"agent {name}", "no YAML frontmatter between --- lines")
            continue
        missing = [key for key in AGENT_FIELDS if not fields.get(key)]
        problems = []
        if missing:
            problems.append(f"frontmatter missing {', '.join(missing)}")
        if fields.get("name") and fields["name"] != name:
            problems.append(f"name is {fields['name']!r}, expected {name!r}")
        if CREDIT not in fields.get("author", ""):
            problems.append("author line edited or removed")
        report.add(not problems, f"agent {name}", "; ".join(problems))


def check(scope: Path, *, agents: bool, names: dict[str, str] | None = None,
          before: Path | None = None, skill: Path = SKILL) -> Report:
    names = names or {}
    unknown = sorted(set(names) - set(ROLES))
    if unknown:
        raise CheckError(f"unknown agent role(s): {', '.join(unknown)}; renames apply to {', '.join(ROLES)}")
    report = Report()
    check_policy(scope / "CLAUDE.md", report, names, before, skill)
    if agents:
        check_agents(scope / "agents", report, names)
    return report


def _parse_renames(values: list[str]) -> dict[str, str]:
    names = {}
    for value in values:
        old, sep, new = value.partition("=")
        if not sep or not old or not new:
            raise CheckError(f"--rename takes ROLE=NAME, got {value!r}")
        names[old] = new
    return names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an installed Stackwich scope")
    parser.add_argument("scope", help="The scope directory: ~/.claude or ./.claude")
    parser.add_argument("--no-agents", action="store_true", help="Policy-only install: skip agent checks")
    parser.add_argument("--rename", action="append", default=[], metavar="ROLE=NAME",
                        help="An agent renamed for a collision, e.g. executor=builder")
    parser.add_argument("--before", help="A copy of CLAUDE.md from before the install, to check unrelated content")
    args = parser.parse_args(argv)
    try:
        report = check(Path(args.scope).expanduser(), agents=not args.no_agents,
                       names=_parse_renames(args.rename),
                       before=Path(args.before).expanduser() if args.before else None)
    except CheckError as exc:
        print(f"check_install: {exc}", file=sys.stderr)
        return 2
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
