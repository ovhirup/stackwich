#!/usr/bin/env python3
"""Record which tree a verification ran against, and refuse stale or exhausted gates.

  run    Fingerprint the product files, run the verification command, fingerprint
         again, and append the verdict with the commit and tree hash to
         .stackwich/verify.jsonl. FAIL if the command fails or changes product files.
         After 3 failures (the first run plus the policy's 2 correction cycles) it
         refuses to run again until a person records a reset.
  check  Exit 0 only if the latest record is a PASS and the tree still matches it;
         otherwise name what is missing or what changed.
  reset  A person acknowledges an exhausted change so its cycles start again.

Product files are what git lists as tracked or untracked-and-not-ignored. Ignored
files, declared --artifacts directories, and .stackwich/ itself are not product.
The tool runs only the command it is given; it does not call a network or a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = ".stackwich"
RECORDS = "verify.jsonl"
MAX_FAILURES = 3
DELETED = "deleted"


class GateError(Exception):
    """The gate cannot run or refuses to."""


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise GateError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def repo_root(start: Path) -> Path:
    return Path(git(start, "rev-parse", "--show-toplevel").strip())


def head(root: Path) -> str:
    try:
        return git(root, "rev-parse", "HEAD").strip()
    except GateError:
        return "none"


def default_change(root: Path) -> str:
    try:
        name = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    except GateError:
        name = ""
    if not name or name == "HEAD":
        raise GateError("no branch to name the change after; pass --change")
    return name


def _excluded(path: str, artifacts: list[str]) -> bool:
    for prefix in [STATE_DIR, *artifacts]:
        prefix = prefix.strip("/")
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def manifest(root: Path, artifacts: list[str]) -> dict[str, str]:
    listed = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    files = {}
    for path in sorted(set(filter(None, listed.split("\0")))):
        if _excluded(path, artifacts):
            continue
        full = root / path
        if full.is_symlink():
            digest = hashlib.sha256(os.readlink(full).encode()).hexdigest()
        elif full.is_file():
            digest = hashlib.sha256(full.read_bytes()).hexdigest()
        else:
            digest = DELETED
        files[path] = digest
    return files


def tree_hash(files: dict[str, str]) -> str:
    body = "".join(f"{path}\0{digest}\n" for path, digest in sorted(files.items()))
    return hashlib.sha256(body.encode()).hexdigest()


def diff(old: dict[str, str], new: dict[str, str]) -> list[str]:
    changes = []
    for path in sorted(set(old) | set(new)):
        before, after = old.get(path), new.get(path)
        if before == after:
            continue
        if before is None or before == DELETED and after != DELETED:
            changes.append(f"added {path}")
        elif after is None or after == DELETED:
            changes.append(f"removed {path}")
        else:
            changes.append(f"modified {path}")
    return changes


def records(root: Path) -> list[dict]:
    path = root / STATE_DIR / RECORDS
    if not path.is_file():
        return []
    out = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise GateError(f"{path} line {number} is not JSON: {exc}") from exc
    return out


def append(root: Path, record: dict) -> None:
    path = root / STATE_DIR / RECORDS
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def failures_since_reset(history: list[dict], change: str) -> int:
    count = 0
    for record in history:
        if record.get("change") != change:
            continue
        if record.get("kind") == "reset" or record.get("verdict") == "PASS":
            count = 0
        elif record.get("verdict") == "FAIL":
            count += 1
    return count


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_measured(log: Path, change: str, verdict: str, tree: str) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "measured"))
    from log_event import EventError, append_event

    try:
        append_event(log, {"event": "sandwich.verified", "actor": "verifier", "work_id": change,
                           "verdict": verdict, "tree": tree})
    except EventError as exc:
        raise GateError(f"measured log: {exc}") from exc


def run(root: Path, change: str, command: str, artifacts: list[str], log: Path | None) -> tuple[int, list[str]]:
    history = records(root)
    failed = failures_since_reset(history, change)
    if failed >= MAX_FAILURES:
        raise GateError(
            f"refuse: change {change!r} has failed verification {failed} times "
            f"(the first run and {MAX_FAILURES - 1} correction cycles). "
            f"A person must review it and run: verify_gate.py reset --change {change} --by NAME --reason TEXT")
    before = manifest(root, artifacts)
    proc = subprocess.run(command, shell=True, cwd=root, check=False)
    after = manifest(root, artifacts)
    changed = diff(before, after)
    verdict = "PASS" if proc.returncode == 0 and not changed else "FAIL"
    record = {
        "kind": "verify",
        "ts": now(),
        "change": change,
        "command": command,
        "exit_code": proc.returncode,
        "verdict": verdict,
        "head": head(root),
        "tree": tree_hash(before),
        "files": before,
        "artifacts": artifacts,
        "attempt": failed + 1,
    }
    if changed:
        record["changed_during_run"] = changed
    append(root, record)
    if log is not None:
        log_measured(log, change, verdict, record["tree"])
    lines = [f"GATE: {verdict}"]
    if proc.returncode != 0:
        lines.append(f"command exited {proc.returncode}")
    if changed:
        lines.append("the command changed product files, so this run verified nothing:")
        lines.extend(f"  {item}" for item in changed[:20])
        lines.append("If these are build or test output, add them to .gitignore or pass --artifacts DIR.")
    lines.append(f"change {change}, commit {record['head'][:12]}, tree {record['tree'][:12]}")
    if verdict == "FAIL":
        left = MAX_FAILURES - record["attempt"]
        lines.append(f"{left} correction cycle(s) left" if left else
                     "no correction cycles left: a person must review before another run")
    return (0 if verdict == "PASS" else 1), lines


def check(root: Path, change: str) -> tuple[int, list[str]]:
    mine = [r for r in records(root) if r.get("change") == change and r.get("kind") == "verify"]
    if not mine:
        return 1, [f"UNVERIFIED: no verification recorded for change {change!r}"]
    last = mine[-1]
    if last["verdict"] != "PASS":
        return 1, [f"UNVERIFIED: the last verification of {change!r} failed ({last['ts']}, "
                   f"exit {last['exit_code']})"]
    current = manifest(root, last.get("artifacts", []))
    changes = diff(last["files"], current)
    if changes:
        lines = [f"STALE: {len(changes)} product change(s) since the PASS at {last['ts']} "
                 f"(tree {last['tree'][:12]}):"]
        lines.extend(f"  {item}" for item in changes[:20])
        if len(changes) > 20:
            lines.append(f"  … and {len(changes) - 20} more")
        lines.append("Run the verification again.")
        return 1, lines
    return 0, [f"VERIFIED: {change!r} matches the tree that passed `{last['command']}` at {last['ts']} "
               f"(commit {last['head'][:12]}, tree {last['tree'][:12]})"]


def reset(root: Path, change: str, by: str, reason: str) -> list[str]:
    if not by.strip() or not reason.strip():
        raise GateError("reset needs --by and --reason")
    append(root, {"kind": "reset", "ts": now(), "change": change, "by": by, "reason": reason})
    return [f"reset: {change!r} by {by}; correction cycles start again"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bind verification verdicts to the tree they tested")
    parser.add_argument("--repo", default=".", help="Any path inside the git repository (default: .)")
    sub = parser.add_subparsers(dest="action", required=True)
    run_cmd = sub.add_parser("run", help="Run a verification command and record the verdict")
    run_cmd.add_argument("--change", help="Change id (default: current branch)")
    run_cmd.add_argument("--artifacts", action="append", default=[], metavar="DIR",
                         help="Directory the command may write to, e.g. coverage/ (repeatable)")
    run_cmd.add_argument("--log", help="Also append a sandwich.verified event to this measured log")
    run_cmd.add_argument("command", nargs=argparse.REMAINDER, help="The verification command, after --")
    check_cmd = sub.add_parser("check", help="Exit 0 only if the last PASS still matches the tree")
    check_cmd.add_argument("--change", help="Change id (default: current branch)")
    reset_cmd = sub.add_parser("reset", help="Allow new cycles after a person has reviewed a change")
    reset_cmd.add_argument("--change", help="Change id (default: current branch)")
    reset_cmd.add_argument("--by", required=True)
    reset_cmd.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        root = repo_root(Path(args.repo).expanduser())
        change = args.change or default_change(root)
        if args.action == "run":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            if not command:
                raise GateError("give the verification command after --, e.g. run -- python3 -m unittest")
            text = command[0] if len(command) == 1 else shlex.join(command)
            code, lines = run(root, change, text, args.artifacts,
                              Path(args.log).expanduser() if args.log else None)
        elif args.action == "check":
            code, lines = check(root, change)
        else:
            code, lines = 0, reset(root, change, args.by, args.reason)
    except GateError as exc:
        print(f"verify_gate: {exc}", file=sys.stderr)
        return 3 if str(exc).startswith("refuse:") else 2
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
