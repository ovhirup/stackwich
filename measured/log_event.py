#!/usr/bin/env python3
"""Append one measured-layer event. Never rewrites earlier lines."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

FORBIDDEN_KEYS = {
    "token",
    "secret",
    "password",
    "api_key",
    "account_number",
    "customer_id",
    "authorization",
}

ACTORS = {"human", "advisor", "executor", "verifier", "orchestrator"}

# Extra fields required for each event, beyond ts, event, actor, and work_id.
EVENT_FIELDS = {
    "sandwich.planned": set(),
    "sandwich.executed": {"dry_run"},
    "sandwich.verified": {"verdict"},
    "sandwich.reviewed": {"verdict"},
    "model.tier": {"role", "tier"},
    "gate.human": {"gate", "decision", "approver_role"},
    "retro.effectiveness": {"tool", "score"},
    "delivery.estimate": {"hours_returned"},
    "iteration.item": {"item_id", "committed", "done"},
    "dora.signal": {"kind", "value"},
    "risk.item": {"risk_id", "severity", "open", "summary"},
}

ALLOWED_KEYS = {
    "ts",
    "event",
    "actor",
    "work_id",
    "dry_run",
    "verdict",
    "role",
    "tier",
    "gate",
    "decision",
    "approver_role",
    "tool",
    "score",
    "hours_returned",
    "item_id",
    "committed",
    "done",
    "kind",
    "value",
    "risk_id",
    "severity",
    "open",
    "summary",
}

VERIFY_VERDICTS = {"PASS", "FAIL"}
REVIEW_VERDICTS = {"APPROVE", "REVISE"}
TIERS = {"plan", "execute", "verify", "review"}
DECISIONS = {"approve", "reject", "pending"}
SEVERITIES = {"low", "medium", "high"}
DORA_KINDS = {"deploy", "change_fail", "lead_time_hours", "restore_hours"}


class EventError(ValueError):
    """The event is not safe to append."""


def _walk_keys(value, found: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            found.append(str(key))
            _walk_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _walk_keys(child, found)


def validate_event(event: dict) -> dict:
    if not isinstance(event, dict):
        raise EventError("event must be a JSON object")
    found: list[str] = []
    _walk_keys(event, found)
    forbidden = sorted({key for key in found if key.lower() in FORBIDDEN_KEYS})
    if forbidden:
        raise EventError("forbidden key(s): " + ", ".join(forbidden))
    unknown = sorted(set(event) - ALLOWED_KEYS)
    if unknown:
        raise EventError("unknown field(s): " + ", ".join(unknown))
    missing = [name for name in ("event", "actor", "work_id") if not event.get(name)]
    if missing:
        raise EventError("missing field(s): " + ", ".join(missing))
    name = event["event"]
    if name not in EVENT_FIELDS:
        raise EventError(f"unknown event: {name}")
    if event["actor"] not in ACTORS:
        raise EventError("actor must be human, advisor, executor, verifier, or orchestrator")
    if not isinstance(event["work_id"], str) or not event["work_id"].strip():
        raise EventError("work_id must be a non-empty string")
    cleaned = dict(event)
    if not cleaned.get("ts"):
        cleaned["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif not isinstance(cleaned["ts"], str) or "T" not in cleaned["ts"]:
        raise EventError("ts must be an ISO-8601 string")
    extra = [field for field in sorted(EVENT_FIELDS[name]) if field not in cleaned]
    if extra:
        raise EventError(f"{name} missing field(s): " + ", ".join(extra))
    _check_values(name, cleaned)
    return cleaned


def _number(value, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EventError(f"{label} must be a number")


def _check_values(name: str, event: dict) -> None:
    if name == "sandwich.executed" and not isinstance(event["dry_run"], bool):
        raise EventError("dry_run must be a boolean")
    if name == "sandwich.verified" and event["verdict"] not in VERIFY_VERDICTS:
        raise EventError("verdict must be PASS or FAIL")
    if name == "sandwich.reviewed" and event["verdict"] not in REVIEW_VERDICTS:
        raise EventError("verdict must be APPROVE or REVISE")
    if name == "model.tier" and event["tier"] not in TIERS:
        raise EventError("tier must be plan, execute, verify, or review")
    if name == "gate.human" and event["decision"] not in DECISIONS:
        raise EventError("decision must be approve, reject, or pending")
    if name == "retro.effectiveness":
        score = event["score"]
        if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
            raise EventError("score must be an integer from 1 to 5")
    if name == "delivery.estimate":
        _number(event["hours_returned"], "hours_returned")
        if event["hours_returned"] < 0:
            raise EventError("hours_returned must be >= 0")
    if name == "iteration.item":
        if not isinstance(event["committed"], bool) or not isinstance(event["done"], bool):
            raise EventError("committed and done must be booleans")
    if name == "dora.signal":
        if event["kind"] not in DORA_KINDS:
            raise EventError("kind is not a recorded DORA signal")
        _number(event["value"], "value")
    if name == "risk.item":
        if event["severity"] not in SEVERITIES:
            raise EventError("severity must be low, medium, or high")
        if not isinstance(event["open"], bool):
            raise EventError("open must be a boolean")


def append_event(path: Path, event: dict) -> dict:
    """Validate and append a single line. Existing bytes are never rewritten."""
    cleaned = validate_event(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        with path.open("rb") as handle:
            handle.seek(-1, os_seek_end())
            if handle.read(1) != b"\n":
                raise EventError("log has no trailing newline; refusing to append")
    line = json.dumps(cleaned, separators=(",", ":"), sort_keys=True) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
    return cleaned


def os_seek_end() -> int:
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append one measured-layer event")
    parser.add_argument("--log", required=True, help="JSONL file to append to")
    parser.add_argument("--json", help="Event object. Reads stdin when omitted.")
    args = parser.parse_args(argv)
    raw = args.json if args.json is not None else sys.stdin.read()
    try:
        payload = json.loads(raw)
        append_event(Path(args.log), payload)
    except (EventError, json.JSONDecodeError) as exc:
        print(f"log_event: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
