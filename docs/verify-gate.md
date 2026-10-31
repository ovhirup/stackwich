# Verification records

`tools/verify_gate.py` ties a verification verdict to the exact files it tested. Without it, a
`GATE: PASS` is a line of text in a conversation: an edit made after the verifier ran still looks
verified. With it, a later edit makes `check` fail, and a third failed attempt on the same change
is refused until a person looks at it.

It is optional and local. It changes nothing in the installed policy. It runs only the command
you give it, and needs Python 3 and git.

## Use

From inside the repository you are changing:

```bash
python3 ~/stackwich-tools/tools/verify_gate.py run -- python3 -m unittest
python3 ~/stackwich-tools/tools/verify_gate.py check
```

- `run -- <command>` runs your verification command and appends the verdict to
  `.stackwich/verify.jsonl`, with the commit and a hash of every product file, committed or not.
  It prints `GATE: PASS` or `GATE: FAIL` and exits 0 or 1.
- `check` exits 0 only if the latest record is a PASS and the files still match it. Otherwise it
  prints `UNVERIFIED` or `STALE` with each added, modified, or removed file, and exits 1.
- `reset --by NAME --reason TEXT` records that a person reviewed a change that ran out of cycles.

The change id defaults to the current branch; pass `--change ID` to name it yourself. Add
`.stackwich/` to `.gitignore`. The tool leaves it out of the fingerprint either way.

## Example

Recorded on 2026-10-31 against [the first-task demo](first-task.md). The test runner's own output
is left out.

```text
$ python3 verify_gate.py run -- python3 -m unittest
GATE: FAIL
command exited 1
change fix-discount, commit 1b1a4d6486dc, tree 4b61aec8e7cc
2 correction cycle(s) left

# fix cart.py

$ python3 verify_gate.py run -- python3 -m unittest
GATE: PASS
change fix-discount, commit 1b1a4d6486dc, tree 38ac6218b2aa

$ python3 verify_gate.py check
VERIFIED: 'fix-discount' matches the tree that passed `python3 -m unittest` at 2026-10-31T06:10:58Z (commit 1b1a4d6486dc, tree 38ac6218b2aa)

# a "small" review edit to cart.py, not re-verified

$ python3 verify_gate.py check
STALE: 1 product change(s) since the PASS at 2026-10-31T06:10:58Z (tree 38ac6218b2aa):
  modified cart.py
Run the verification again.
```

## Rules

| Rule | What the tool does |
|---|---|
| What counts as product | Every file git lists as tracked, or untracked and not ignored. Uncommitted edits count. |
| Test and build output | Ignored files, and directories passed with `--artifacts DIR`, are not product. |
| A command that edits product files | The run is `GATE: FAIL` and lists the files, even if the command exited 0. A verifier that fixes code has verified nothing. |
| Change after a PASS | `check` fails and names each file. Run the verification again. |
| Failure cap | The first run plus 2 correction cycles. After a third failure, `run` refuses (exit 3) until `reset`. A PASS or a reset starts the count again. |
| Separate changes | Each change id has its own records and its own count. |
| Measured layer | `run --log events.jsonl` also appends a `sandwich.verified` event with the tree hash, which `measured/report.py` counts. |

Exit codes: 0 pass or verified, 1 fail, stale, or unverified, 2 usage error, 3 refused.

## With the Stackwich agents

The policy is unchanged; using the tool is a choice you make in the request. For example, ask
the verifier to run `python3 ~/stackwich-tools/tools/verify_gate.py run -- <command>` instead of
the bare command. Then run `check` yourself, or in CI or a pre-push hook, before treating the
change as done. The check is what makes it mechanical: a model can skip a tool it was asked to
use, but a check that you run cannot be skipped by the model.

## What it does not do

- It does not decide which command is the right verification. A weak command still passes.
- It does not stop anyone from editing `.stackwich/verify.jsonl`. It is a local record, not a
  signed one.
- It does not check scope against a plan. The Dynamic LLM Router does that for its own workers;
  see [enforcement.md](enforcement.md).
- It does not run in the agent's place. If nobody runs `check`, nothing is enforced.
