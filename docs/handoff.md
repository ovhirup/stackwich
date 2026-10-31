# Handoffs

Work that stops partway through plan → execute → verify → review used to restart cold: the next
session had to guess where things stood, could trust a PASS from before the break, and could not
tell whether anyone changed the code in between.

Since `policy-rev 7`, the policy asks the agent to keep `.stackwich/handoff.md` current at each
stage change when work may outlive the session, and to read it first when resuming. The handoff
records:

- the plan and where it lives (a file, ticket, or URL);
- the stage reached and the next step;
- the last gate verdict and the command that produced it;
- the commit and `git status --short` at that moment.

On resuming, anything that differs from the handoff is treated as unverified, and the gate runs
again before anything builds on an earlier PASS. Add `.stackwich/` to `.gitignore`.

## The helper: `tools/handoff.py`

The agent can write the handoff by hand. The helper also saves a fingerprint of every product
file, so resuming can name exactly what changed. It counts files the same way as
[verification records](verify-gate.md): tracked files, untracked files that are not ignored, and
not `.stackwich/` or declared `--artifacts` directories.

```bash
python3 ~/stackwich-tools/tools/handoff.py save --stage executing \
  --next "Fix the discount in cart.py, then re-run the gate" --plan "specs/checkout.md"
python3 ~/stackwich-tools/tools/handoff.py resume
```

Stages are `planned`, `executing`, `verifying`, `reviewing`, `blocked`, and `done`. The change
id defaults to the current branch; `--note` adds anything else the next session needs.

`resume` prints the handoff, then one of:

- `UNCHANGED: every product file matches the handoff.` (exit 0)
- `CHANGED SINCE HANDOFF:` followed by each added, modified, or removed file (exit 1)
- `UNCHECKED:` for a handoff written by hand, which has no fingerprint (exit 1)
- `NO HANDOFF` when there is nothing to resume (exit 2)

It also reports a moved commit and, if `verify_gate` has records for the change, whether the last
PASS still holds.

## Example

Recorded on 2026-10-31 against [the first-task demo](first-task.md), after a failed gate:

```text
$ python3 handoff.py save --stage executing --next "Fix the discount in cart.py, then re-run the gate" --plan "docs/first-task.md step 4"
saved .stackwich/handoff.md: fix-discount at stage executing, tree 4b61aec8e7cc

$ python3 handoff.py resume
# Stackwich handoff

- Change: fix-discount
- Stage: executing
- Next step: Fix the discount in cart.py, then re-run the gate
- Plan: docs/first-task.md step 4
- Last gate: FAIL — `python3 -m unittest` at 2026-10-31T06:48:46Z (tree 4b61aec8e7cc)
- Saved: 2026-10-31T06:48:46Z
- Commit: 9e87bf8138cceecc7e2753c2b95407ae7285c8ac

Working tree (`git status --short`):

    (clean)

UNCHANGED: every product file matches the handoff.
UNVERIFIED: the last verification of 'fix-discount' failed (2026-10-31T06:48:46Z, exit 1)

# someone edits cart.py between sessions

$ python3 handoff.py resume
...
CHANGED SINCE HANDOFF: 1 product file(s). Treat them as unverified and re-run the gate before building on an earlier PASS:
  modified cart.py
```

## Limits

- Writing and reading the handoff is instructed, not enforced: see
  [enforcement.md](enforcement.md).
- The stage and next step are whatever the writer recorded. The fingerprint is checked; the prose
  is not.
- The handoff is a local file, not a signed record.
