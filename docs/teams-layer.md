# Stackwich for Teams — measured layer

This is a local add-on beside the Stackwich skill. It records the sandwich, the
model tier, human gates, and a small set of delivery signals. It does not replace
the Claude Code install path, and it does not write the policy block.

Nothing here phones home. Logs stay on disk. The commands refuse secret-shaped
field names. Example records use public demo identifiers only.

## What is instrumented

Each line in a JSONL log is one event. `measured/schema.json` lists the fields.
`measured/log_event.py` checks the event and appends one line. It never rewrites
earlier lines.

| Event | What it records |
|---|---|
| `sandwich.planned` / `executed` / `verified` / `reviewed` | The four sandwich steps. Execute says whether it was a dry run. Verify is `PASS` or `FAIL`. Review is `APPROVE` or `REVISE`. |
| `model.tier` | Which role ran at which tier: plan, execute, verify, or review. |
| `gate.human` | A human decision: approve, reject, or pending. |
| `delivery.estimate` | Estimated hours returned. |
| `retro.effectiveness` | A 1–5 score for one named tool. |
| `iteration.item` | A committed item and whether it is done. Not done is carryover. |
| `dora.signal` | One recorded number: deploy, change fail, lead time hours, or restore hours. |
| `risk.item` | An open or closed risk and a low, medium, or high severity. A later line for the same work and risk id replaces the earlier state. |

Actors are `human`, `advisor`, `executor`, `verifier`, and `orchestrator`.

## How data is collected

- Local JSONL, one file the team chooses. No network client is included.
- Optional co-author rate: `report.py --repo <checkout>` counts commits whose
  message contains a `Co-authored-by:` trailer. The report prints counts only.
- Azure DevOps and Jira are not called. Export the JSON report and attach it to
  the work item or the sprint review.

## Reports

`measured/report.py` reads a log and prints Markdown or JSON. The Markdown report
is the leadership view: verification pass rate, review approve rate, human gate
pass rate, hours returned, retro scores, commitment versus carryover, DORA
numbers, and open risks. Pending gates are counted and are not treated as passes.

`measured/examples/sprint.jsonl` is a public demo log.

## Approval and separation of duties

`measured/approve.py` is the human gate for one named change. It stores a local
ledger. It does not edit the product tree except to write a single marker after
an approved execute.

Four roles must be different people: planner, writer, verifier, and approver.
The planner records a dry run. The approver is the only role that can approve.
The writer is the only role that can execute, and only after approval. A dry run
prints the decision and writes nothing. A second execute is refused.

This is the regulated-environment shape: a human gate, an audit ledger, no silent
write, and no person holding two sides of the same change.

## What this base does not do

It does not install a dashboard service, scan old repositories, or open a tracker.
The Stackwich skill still installs the policy. This layer only records work the
team chooses to log.
