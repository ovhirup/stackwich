#!/usr/bin/env python3
"""Dry-run and human approval gate with separation of duties.

The gate authorizes a change. It does not edit the product tree except to write
a single marker file after a successful execute. Applying the real diff stays
with the designated writer, and only after this command exits 0.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


class GateError(Exception):
    """The gate refused the action. Nothing was applied."""


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"changes": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("changes"), dict):
        raise GateError("state file is not a measured approval ledger")
    return data


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def plan(state_path: Path, change_id: str, planner: str, writer: str, verifier: str, summary: str, files: list[str]) -> None:
    if planner == writer:
        raise GateError("refuse: planner and writer must be different people")
    if verifier == writer:
        raise GateError("refuse: verifier and writer must be different people")
    if planner == verifier:
        raise GateError("refuse: planner and verifier must be different people")
    state = load_state(state_path)
    if change_id in state["changes"]:
        raise GateError(f"refuse: change {change_id} already exists")
    state["changes"][change_id] = {
        "status": "dry_run",
        "planner": planner,
        "writer": writer,
        "verifier": verifier,
        "approver": None,
        "summary": summary,
        "files": files,
        "regulated": True,
    }
    save_state(state_path, state)
    print(f"planned: {change_id} status=dry_run")


def approve(state_path: Path, change_id: str, approver: str) -> None:
    state = load_state(state_path)
    change = _require(state, change_id)
    if change["status"] != "dry_run":
        raise GateError(f"refuse: {change_id} is {change['status']}, not awaiting approval")
    if approver in {change["planner"], change["writer"], change["verifier"]}:
        raise GateError("refuse: approver must not be the planner, writer, or verifier")
    change["approver"] = approver
    change["status"] = "approved"
    save_state(state_path, state)
    print(f"approved: {change_id} by {approver}")


def execute(state_path: Path, change_id: str, actor: str, target: Path, dry_run: bool) -> None:
    state = load_state(state_path)
    change = _require(state, change_id)
    if change["status"] == "executed":
        raise GateError(f"refuse: {change_id} is already executed")
    if change["status"] != "approved":
        raise GateError(f"refuse: {change_id} is not approved")
    if actor != change["writer"]:
        raise GateError("refuse: only the designated writer can execute")
    if actor in {change["planner"], change["approver"], change["verifier"]}:
        raise GateError("refuse: writer must not be the planner, approver, or verifier")
    if dry_run:
        print(f"dry-run: change {change_id} not applied")
        return
    target.mkdir(parents=True, exist_ok=True)
    marker = target / "applied.txt"
    marker.write_text(f"change_id: {change_id}\nactor: {actor}\n", encoding="utf-8")
    change["status"] = "executed"
    save_state(state_path, state)
    print(f"executed: {change_id} marker={marker}")


def _require(state: dict, change_id: str) -> dict:
    try:
        return state["changes"][change_id]
    except KeyError as exc:
        raise GateError(f"refuse: unknown change {change_id}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measured-layer approval gate")
    parser.add_argument("--self-check", action="store_true")
    sub = parser.add_subparsers(dest="command")

    plan_cmd = sub.add_parser("plan")
    plan_cmd.add_argument("--state", required=True)
    plan_cmd.add_argument("--id", required=True)
    plan_cmd.add_argument("--planner", required=True)
    plan_cmd.add_argument("--writer", required=True)
    plan_cmd.add_argument("--verifier", required=True)
    plan_cmd.add_argument("--summary", required=True)
    plan_cmd.add_argument("--file", action="append", default=[])

    approve_cmd = sub.add_parser("approve")
    approve_cmd.add_argument("--state", required=True)
    approve_cmd.add_argument("--id", required=True)
    approve_cmd.add_argument("--approver", required=True)

    execute_cmd = sub.add_parser("execute")
    execute_cmd.add_argument("--state", required=True)
    execute_cmd.add_argument("--id", required=True)
    execute_cmd.add_argument("--actor", required=True)
    execute_cmd.add_argument("--target", required=True)
    execute_cmd.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    try:
        if args.command == "plan":
            plan(Path(args.state), args.id, args.planner, args.writer, args.verifier, args.summary, args.file)
        elif args.command == "approve":
            approve(Path(args.state), args.id, args.approver)
        elif args.command == "execute":
            execute(Path(args.state), args.id, args.actor, Path(args.target), args.dry_run)
        else:
            parser.print_help()
            return 2
    except (GateError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


def self_check() -> int:
    """Exercise the CLI against a temp ledger. The repo tree is not touched."""
    script = str(Path(__file__).resolve())
    with tempfile.TemporaryDirectory(prefix="stackwich-sod-") as tmp:
        root = Path(tmp)
        state = root / "ledger.json"
        target = root / "target"
        change = "demo-change-1"

        def run(args: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, script, *args],
                capture_output=True,
                text=True,
                check=False,
            )

        refused = run([
            "plan", "--state", str(state), "--id", "bad-same",
            "--planner", "planner-1", "--writer", "planner-1",
            "--verifier", "verifier-1", "--summary", "same person",
        ])
        if refused.returncode == 0:
            print("SOD self-check: same person was allowed to plan and write", file=sys.stderr)
            return 1
        refused = run([
            "plan", "--state", str(state), "--id", "bad-verifier",
            "--planner", "planner-1", "--writer", "writer-1",
            "--verifier", "writer-1", "--summary", "verifier is writer",
        ])
        if refused.returncode == 0:
            print("SOD self-check: verifier was allowed to be the writer", file=sys.stderr)
            return 1
        planned = run([
            "plan", "--state", str(state), "--id", change,
            "--planner", "planner-1", "--writer", "writer-1",
            "--verifier", "verifier-1", "--summary", "Public demo change",
            "--file", "README.md",
        ])
        if planned.returncode != 0 or target.exists():
            print(planned.stderr, file=sys.stderr)
            print("SOD self-check: plan wrote the target or failed", file=sys.stderr)
            return 1
        for bad in ("planner-1", "writer-1", "verifier-1"):
            denied = run(["approve", "--state", str(state), "--id", change, "--approver", bad])
            if denied.returncode == 0:
                print(f"SOD self-check: {bad} was allowed to approve", file=sys.stderr)
                return 1
        early = run([
            "execute", "--state", str(state), "--id", change,
            "--actor", "writer-1", "--target", str(target),
        ])
        if early.returncode == 0 or target.exists():
            print("SOD self-check: execute ran before approval", file=sys.stderr)
            return 1
        ok = run(["approve", "--state", str(state), "--id", change, "--approver", "approver-1"])
        if ok.returncode != 0:
            print(ok.stderr, file=sys.stderr)
            return 1
        dry = run([
            "execute", "--state", str(state), "--id", change,
            "--actor", "writer-1", "--target", str(target), "--dry-run",
        ])
        if dry.returncode != 0 or "dry-run:" not in dry.stdout or target.exists():
            print(dry.stdout, dry.stderr, file=sys.stderr)
            print("SOD self-check: dry-run applied or failed", file=sys.stderr)
            return 1
        wrong = run([
            "execute", "--state", str(state), "--id", change,
            "--actor", "approver-1", "--target", str(target),
        ])
        if wrong.returncode == 0 or target.exists():
            print("SOD self-check: approver was allowed to execute", file=sys.stderr)
            return 1
        applied = run([
            "execute", "--state", str(state), "--id", change,
            "--actor", "writer-1", "--target", str(target),
        ])
        marker = target / "applied.txt"
        if applied.returncode != 0 or not marker.is_file():
            print(applied.stderr, file=sys.stderr)
            print("SOD self-check: designated writer could not execute", file=sys.stderr)
            return 1
        text = marker.read_text(encoding="utf-8")
        if "demo-change-1" not in text or "writer-1" not in text:
            print("SOD self-check: marker missing change id", file=sys.stderr)
            return 1
        again = run([
            "execute", "--state", str(state), "--id", change,
            "--actor", "writer-1", "--target", str(target),
        ])
        if again.returncode == 0:
            print("SOD self-check: change executed twice", file=sys.stderr)
            return 1
    print("SOD: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
