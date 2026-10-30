#!/usr/bin/env python3
"""Render an auditable measured-layer report from a local JSONL log.

The report reads events already accepted by log_event.py. It does not call a
network, a tracker, or a model. An optional local git scan counts Co-authored-by
trailers and prints only the counts.

Gates, iteration items, and risks are reported as current state: one entity per
(work_id, gate), (work_id, item_id), or (work_id, risk_id), taking the latest
line in the log. Order is log order, not ts, because the log is append-only and
ts may tie or be supplied by the caller. Event counts for gates and items are
reported separately as history. The report covers the whole log it is given.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from log_event import EventError, validate_event


class ReportError(ValueError):
    """The log or git scan cannot be reported."""


def load_events(path: Path) -> list[dict]:
    if not path.is_file():
        raise ReportError(f"log not found: {path}")
    events = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            events.append(validate_event(payload))
        except (EventError, json.JSONDecodeError) as exc:
            raise ReportError(f"line {number}: {exc}") from exc
    return events


def _rate(passed: int, failed: int) -> float | None:
    decided = passed + failed
    if decided == 0:
        return None
    return passed / decided


def summarize(events: list[dict]) -> dict:
    verified_pass = verified_fail = 0
    review_approve = review_revise = 0
    gate_events = {"approve": 0, "reject": 0, "pending": 0}
    latest_gates: dict[tuple[str, str], str] = {}
    hours = 0.0
    retros: dict[str, list[int]] = {}
    iteration_events = 0
    latest_items: dict[tuple[str, str], tuple[bool, bool]] = {}
    dora = []
    latest_risks: dict[tuple[str, str], bool] = {}
    tiers: dict[str, int] = {}
    sandwich = {"planned": 0, "executed": 0, "executed_dry_run": 0, "verified": 0, "reviewed": 0}
    for event in events:
        name = event["event"]
        if name == "sandwich.planned":
            sandwich["planned"] += 1
        elif name == "sandwich.executed":
            sandwich["executed"] += 1
            if event["dry_run"]:
                sandwich["executed_dry_run"] += 1
        elif name == "sandwich.verified":
            sandwich["verified"] += 1
            if event["verdict"] == "PASS":
                verified_pass += 1
            else:
                verified_fail += 1
        elif name == "sandwich.reviewed":
            sandwich["reviewed"] += 1
            if event["verdict"] == "APPROVE":
                review_approve += 1
            else:
                review_revise += 1
        elif name == "gate.human":
            gate_events[event["decision"]] += 1
            latest_gates[(event["work_id"], event["gate"])] = event["decision"]
        elif name == "delivery.estimate":
            hours += float(event["hours_returned"])
        elif name == "retro.effectiveness":
            retros.setdefault(event["tool"], []).append(event["score"])
        elif name == "iteration.item":
            iteration_events += 1
            latest_items[(event["work_id"], event["item_id"])] = (bool(event["committed"]), bool(event["done"]))
        elif name == "dora.signal":
            dora.append({"kind": event["kind"], "value": event["value"], "work_id": event["work_id"]})
        elif name == "risk.item":
            latest_risks[(event["work_id"], event["risk_id"])] = bool(event["open"])
        elif name == "model.tier":
            key = f"{event['role']}:{event['tier']}"
            tiers[key] = tiers.get(key, 0) + 1
    gates = {decision: 0 for decision in ("approve", "reject", "pending")}
    for decision in latest_gates.values():
        gates[decision] += 1
    committed = sum(1 for is_committed, _ in latest_items.values() if is_committed)
    done = sum(1 for is_committed, is_done in latest_items.values() if is_committed and is_done)
    risks = {
        "open": sum(1 for is_open in latest_risks.values() if is_open),
        "closed": sum(1 for is_open in latest_risks.values() if not is_open),
    }
    retro_rows = {
        tool: {"count": len(scores), "mean_score": sum(scores) / len(scores)}
        for tool, scores in sorted(retros.items())
    }
    return {
        "events": len(events),
        "sandwich": sandwich,
        "verification_pass_rate": _rate(verified_pass, verified_fail),
        "verification": {"pass": verified_pass, "fail": verified_fail},
        "review_approve_rate": _rate(review_approve, review_revise),
        "review": {"approve": review_approve, "revise": review_revise},
        "gate_pass_rate": _rate(gates["approve"], gates["reject"]),
        "gates": gates,
        "gate_events": gate_events,
        "hours_returned": hours,
        "retro": retro_rows,
        "iteration": {"committed": committed, "done": done, "carryover": committed - done},
        "iteration_events": iteration_events,
        "dora": dora,
        "risks": risks,
        "model_tier": tiers,
    }


def coauthor_rate(repo: Path) -> dict:
    if not (repo / ".git").exists():
        raise ReportError(f"not a git checkout: {repo}")
    proc = subprocess.run(
        ["git", "-C", str(repo), "log", "--pretty=%B%x1e"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or "git log failed"
        raise ReportError(detail)
    bodies = [body for body in proc.stdout.split("\x1e") if body.strip()]
    coauthored = sum(1 for body in bodies if "Co-authored-by:" in body)
    total = len(bodies)
    return {
        "commits": total,
        "coauthored_commits": coauthored,
        "coauthor_rate": (coauthored / total) if total else None,
    }


def _percent(rate: float | None) -> str:
    if rate is None:
        return "n/a"
    return f"{rate:.0%}"


def render_markdown(summary: dict) -> str:
    sandwich = summary["sandwich"]
    iteration = summary["iteration"]
    lines = [
        "# Measured delivery report",
        "",
        f"Events: {summary['events']}",
        "",
        "## Sandwich",
        f"- Planned: {sandwich['planned']}",
        f"- Executed: {sandwich['executed']} ({sandwich['executed_dry_run']} dry-run)",
        f"- Verified: {sandwich['verified']}",
        f"- Reviewed: {sandwich['reviewed']}",
        "",
        "## Verification and review",
        f"- Verification pass rate: {_percent(summary['verification_pass_rate'])} "
        f"({summary['verification']['pass']} pass, {summary['verification']['fail']} fail)",
        f"- Review approve rate: {_percent(summary['review_approve_rate'])} "
        f"({summary['review']['approve']} approve, {summary['review']['revise']} revise)",
        "",
        "## Human gates",
        f"- Gate pass rate: {_percent(summary['gate_pass_rate'])} "
        f"({summary['gates']['approve']} approve, {summary['gates']['reject']} reject, "
        f"{summary['gates']['pending']} pending)",
        f"- Gate decision events: {sum(summary['gate_events'].values())} "
        f"({summary['gate_events']['approve']} approve, {summary['gate_events']['reject']} reject, "
        f"{summary['gate_events']['pending']} pending)",
        "",
        "## Hours returned",
        f"- Estimated hours returned: {summary['hours_returned']}",
        "",
        "## Retro effectiveness",
    ]
    if summary["retro"]:
        for tool, row in summary["retro"].items():
            lines.append(f"- {tool}: mean {row['mean_score']:.1f} across {row['count']} score(s)")
    else:
        lines.append("- No retro scores recorded.")
    lines.extend([
        "",
        "## Commitment and carryover",
        f"- Committed: {iteration['committed']}",
        f"- Done: {iteration['done']}",
        f"- Carryover: {iteration['carryover']}",
        f"- Item update events: {summary['iteration_events']}",
        "",
        "## DORA signals",
    ])
    if summary["dora"]:
        for row in summary["dora"]:
            lines.append(f"- {row['kind']}: {row['value']} ({row['work_id']})")
    else:
        lines.append("- No DORA signals recorded.")
    lines.extend([
        "",
        "## Risks",
        f"- Open: {summary['risks']['open']}",
        f"- Closed: {summary['risks']['closed']}",
        "",
        "## Model tier",
    ])
    if summary["model_tier"]:
        for key, count in sorted(summary["model_tier"].items()):
            lines.append(f"- {key}: {count}")
    else:
        lines.append("- No tier events recorded.")
    if "coauthor" in summary:
        rate = summary["coauthor"]["coauthor_rate"]
        lines.extend([
            "",
            "## AI co-author rate",
            f"- Commits: {summary['coauthor']['commits']}",
            f"- Commits with a Co-authored-by trailer: {summary['coauthor']['coauthored_commits']}",
            f"- Rate: {_percent(rate)}",
        ])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a measured-layer report")
    parser.add_argument("--log", required=True)
    parser.add_argument("--repo", help="Local git checkout for the co-author count")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)
    try:
        summary = summarize(load_events(Path(args.log)))
        if args.repo:
            summary["coauthor"] = coauthor_rate(Path(args.repo))
    except ReportError as exc:
        print(f"report: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(render_markdown(summary), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
