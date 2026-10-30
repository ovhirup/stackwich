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
| `gate.human` | A human decision: approve, reject, or pending. A later line for the same work id and gate replaces the earlier decision. |
| `delivery.estimate` | Estimated hours returned. |
| `retro.effectiveness` | A 1–5 score for one named tool. |
| `iteration.item` | A committed item and whether it is done. Not done is carryover. A later line for the same work id and item id replaces the earlier state. |
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

Gates, iteration items, and risks are reported as current state, one per entity:

| Entity | Identity | Current state |
|---|---|---|
| Human gate | `(work_id, gate)` | The latest decision. Gate pass rate is approve ÷ (approve + reject). |
| Iteration item | `(work_id, item_id)` | The latest line. Committed counts items whose latest line is committed; done counts those also done; carryover is committed minus done. An item whose latest line is not committed is not counted. |
| Risk | `(work_id, risk_id)` | The latest open or closed state. |

"Latest" means the last line in the log, not the latest `ts`. The log is
append-only and `ts` can tie or be supplied by the caller, so line order is the
order of record. A gate that moves pending → approve is one approved gate and no
pending gate. A story logged not done and then done is one committed, one done,
and no carryover.

History is reported separately: gate decision events and item update events
count every line, so repeated decisions and re-logged items stay visible without
inflating current state.

The report covers the whole log it is given. To report one sprint or period,
point it at that period's log.

`measured/examples/sprint.jsonl` is a public demo log.

## Approval and separation of duties

`measured/approve.py` is the human gate for one named change. It stores a local
ledger. It does not edit the product tree except to write a single marker after
an approved execute.

Four roles must have different names: planner, writer, verifier, and approver.
The planner records a dry run. The approver is the only role that can approve.
The writer is the only role that can execute, and only after approval. A dry run
prints the decision and writes nothing. A second execute is refused.

This is the regulated-environment shape: a human gate, an audit ledger, no silent
write, and no name holding two sides of the same change.

The gate checks the names it is given. It does not authenticate the people behind
them, so one person can supply four names. Approval records a summary and a list
of file paths, not a commit or patch, so a change made after approval is not
detected. Execute writes a marker file; it does not apply the diff. The ledger is
a local JSON file with no tamper evidence. Treat the gate as a workflow check and
an audit trail. Where separation of duties must hold against a determined person,
pair it with authenticated review bound to the change, such as protected branches
with required reviews. [enforcement.md](enforcement.md) lists every mode's
mechanical and instructed checks.

## What this base does not do

It does not install a dashboard service, scan old repositories, or open a tracker.
The Stackwich skill still installs the policy. This layer only records work the
team chooses to log.
