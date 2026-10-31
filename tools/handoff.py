#!/usr/bin/env python3
"""Save where interrupted work stands, and check what changed before resuming it.

  save    Write .stackwich/handoff.md (stage, next step, plan, last gate verdict,
          commit, git status) and a fingerprint of every product file beside it.
  resume  Print the handoff, then list every product file changed, added, or removed
          since it was saved, and whether the last verify_gate PASS still holds.

It runs git and reads files only. Product files are counted exactly as
tools/verify_gate.py counts them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from verify_gate import STATE_DIR, GateError, check, default_change, diff, git, head, manifest, now, records, repo_root, tree_hash

HANDOFF = "handoff.md"
FILES = "handoff-files.json"
STAGES = ("planned", "executing", "verifying", "reviewing", "blocked", "done")


def last_gate(root: Path, change: str) -> str:
    mine = [r for r in records(root) if r.get("change") == change and r.get("kind") == "verify"]
    if not mine:
        return "none recorded by verify_gate"
    last = mine[-1]
    return f"{last['verdict']} — `{last['command']}` at {last['ts']} (tree {last['tree'][:12]})"


def save(root: Path, change: str, stage: str, next_step: str, plan: str | None, note: str | None,
         artifacts: list[str]) -> list[str]:
    if not next_step.strip():
        raise GateError("--next must say what the next session should do first")
    files = manifest(root, artifacts)
    status = git(root, "status", "--short", "--", ".", f":(exclude){STATE_DIR}").rstrip()
    lines = [
        "# Stackwich handoff",
        "",
        f"- Change: {change}",
        f"- Stage: {stage}",
        f"- Next step: {next_step.strip()}",
        f"- Plan: {plan or 'not recorded'}",
        f"- Last gate: {last_gate(root, change)}",
        f"- Saved: {now()}",
        f"- Commit: {head(root)}",
        "",
        "Working tree (`git status --short`):",
        "",
        "```",
        status or "(clean)",
        "```",
    ]
    if note:
        lines += ["", "Note:", "", note.strip()]
    state = root / STATE_DIR
    state.mkdir(parents=True, exist_ok=True)
    (state / HANDOFF).write_text("\n".join(lines) + "\n", encoding="utf-8")
    (state / FILES).write_text(json.dumps({"change": change, "head": head(root), "tree": tree_hash(files),
                                           "files": files, "artifacts": artifacts}, indent=1) + "\n",
                               encoding="utf-8")
    return [f"saved {state / HANDOFF}: {change} at stage {stage}, tree {tree_hash(files)[:12]}"]


def resume(root: Path) -> tuple[int, list[str]]:
    state = root / STATE_DIR
    handoff = state / HANDOFF
    if not handoff.is_file():
        return 2, ["NO HANDOFF: nothing saved in .stackwich/handoff.md; start from the user's request."]
    lines = [handoff.read_text(encoding="utf-8").rstrip(), ""]
    saved_path = state / FILES
    if not saved_path.is_file():
        lines.append("UNCHECKED: this handoff was written by hand, so there is no fingerprint to compare. "
                     "Compare its commit and status with `git log -1` and `git status --short` before relying on it.")
        return 1, lines
    try:
        saved = json.loads(saved_path.read_text(encoding="utf-8"))
        old_files, artifacts = saved["files"], saved.get("artifacts", [])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise GateError(f"{saved_path} is not a handoff fingerprint: {exc}") from exc
    changes = diff(old_files, manifest(root, artifacts))
    moved = saved.get("head") != head(root)
    if moved:
        lines.append(f"Commit moved: {str(saved.get('head'))[:12]} → {head(root)[:12]}")
    if changes:
        lines.append(f"CHANGED SINCE HANDOFF: {len(changes)} product file(s). Treat them as unverified and "
                     "re-run the gate before building on an earlier PASS:")
        lines.extend(f"  {item}" for item in changes[:30])
        if len(changes) > 30:
            lines.append(f"  … and {len(changes) - 30} more")
    else:
        lines.append("UNCHANGED: every product file matches the handoff.")
    change = saved.get("change")
    if change and any(r.get("change") == change for r in records(root)):
        lines.append(check(root, change)[1][0])
    return (1 if changes else 0), lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Save and resume interrupted Stackwich work")
    parser.add_argument("--repo", default=".", help="Any path inside the git repository (default: .)")
    sub = parser.add_subparsers(dest="action", required=True)
    save_cmd = sub.add_parser("save", help="Record where the work stands")
    save_cmd.add_argument("--change", help="Change id (default: current branch)")
    save_cmd.add_argument("--stage", required=True, choices=STAGES)
    save_cmd.add_argument("--next", required=True, help="What the next session should do first")
    save_cmd.add_argument("--plan", help="Where the plan lives: a path, ticket, or URL")
    save_cmd.add_argument("--note", help="Anything else the next session needs")
    save_cmd.add_argument("--artifacts", action="append", default=[], metavar="DIR",
                          help="Build or test output directory to leave out (repeatable)")
    sub.add_parser("resume", help="Print the handoff and what changed since")
    args = parser.parse_args(argv)
    try:
        root = repo_root(Path(args.repo).expanduser())
        if args.action == "save":
            code, lines = 0, save(root, args.change or default_change(root), args.stage, args.next,
                                  args.plan, args.note, args.artifacts)
        else:
            code, lines = resume(root)
    except GateError as exc:
        print(f"handoff: {exc}", file=sys.stderr)
        return 2
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
