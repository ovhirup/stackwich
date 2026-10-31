#!/usr/bin/env python3
"""Remove what Stackwich installed in one scope, and nothing else.

Removes the <!-- stackwich:v1 --> block from CLAUDE.md and the agent files whose
author line carries the Stackwich credit, whatever they were renamed to. Agents
without that credit are left alone, even if they are named advisor, executor, or
verifier. A malformed block is refused rather than guessed at.

Without --apply it only prints what it would do. With --apply it first copies
CLAUDE.md to CLAUDE.md.stackwich-backup. Removing the plugin itself stays a
Claude Code command: /plugin uninstall stackwich.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from check_install import CLOSE, CREDIT, OPEN, _frontmatter


class UninstallError(ValueError):
    """The scope cannot be cleaned without a person deciding something."""


def plan(scope: Path) -> tuple[list[str] | None, list[Path], list[Path]]:
    """Return the new CLAUDE.md lines (None if unchanged), agents to remove, agents kept."""
    new_lines = None
    claude_md = scope / "CLAUDE.md"
    if claude_md.is_file():
        lines = claude_md.read_text(encoding="utf-8").splitlines()
        opens = [i for i, line in enumerate(lines) if line == OPEN]
        closes = [i for i, line in enumerate(lines) if line == CLOSE]
        if opens or closes:
            if len(opens) != 1 or len(closes) != 1 or closes[0] < opens[0]:
                raise UninstallError(
                    f"{claude_md} has {len(opens)} opening and {len(closes)} closing marker(s); "
                    "remove the block by hand or re-run /stackwich:stackwich to repair it first")
            before = lines[:opens[0]]
            after = lines[closes[0] + 1:]
            while before and not before[-1].strip():
                before.pop()
            while after and not after[0].strip():
                after.pop(0)
            new_lines = before + ([""] if before and after else []) + after
    remove, keep = [], []
    agents = scope / "agents"
    if agents.is_dir():
        for path in sorted(agents.glob("*.md")):
            fields = _frontmatter(path.read_text(encoding="utf-8", errors="replace")) or {}
            (remove if CREDIT in fields.get("author", "") else keep).append(path)
    return new_lines, remove, keep


def run(scope: Path, apply: bool) -> list[str]:
    new_lines, remove, keep = plan(scope)
    claude_md = scope / "CLAUDE.md"
    verb = "removed" if apply else "would remove"
    out = []
    if new_lines is None:
        out.append(f"{claude_md}: no Stackwich block")
    elif not new_lines:
        out.append(f"{claude_md}: {verb} the Stackwich block; nothing else is in the file, so {verb} the file")
    else:
        out.append(f"{claude_md}: {verb} the Stackwich block; {len(new_lines)} other line(s) kept")
    for path in remove:
        out.append(f"{path}: {verb} (Stackwich agent)")
    for path in keep:
        out.append(f"{path}: kept (not a Stackwich agent)")
    if apply:
        if new_lines is not None:
            backup = claude_md.with_name("CLAUDE.md.stackwich-backup")
            shutil.copy2(claude_md, backup)
            out.append(f"backup: {backup}")
            if new_lines:
                claude_md.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            else:
                claude_md.unlink()
        for path in remove:
            path.unlink()
    else:
        out.append("dry run: nothing changed; re-run with --apply to make these changes")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remove Stackwich's policy block and agents from one scope")
    parser.add_argument("scope", help="The scope directory: ~/.claude or ./.claude")
    parser.add_argument("--apply", action="store_true", help="Make the changes (default: only print them)")
    args = parser.parse_args(argv)
    try:
        print("\n".join(run(Path(args.scope).expanduser(), args.apply)))
    except UninstallError as exc:
        print(f"uninstall: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
