# Checks and evals

Stackwich has two kinds of test. They answer different questions, and only the first runs in
CI.

| Kind | What it answers | Runs where | Depends on a model |
|---|---|---|---|
| Deterministic checks | Do the files an install leaves behind match what `SKILL.md` promises? Does the measured layer compute what it documents? | CI, on every push and pull request | No |
| Behavior evals | Does an agent, given the policy, actually do what it says: ask before replacing, cap loops, size batches? | By hand, against a named runtime and model | Yes |

A passing check or eval is evidence about one setup at one time. Neither is an enforcement
guarantee; [enforcement.md](enforcement.md) lists what is mechanical in each mode.

## Deterministic checks

### Install results: `tools/check_install.py`

The skill is carried out by the model, so the install itself cannot be replayed in CI. The
checker reads what a finished install left in a scope directory and compares it with
`SKILL.md`:

- exactly one opening and one closing marker, as whole lines, in order;
- a missing closing marker is named, and the checker says a person must confirm the boundary;
- exactly one `policy-rev`, the current one, with no older revision left anywhere in the file;
- the block matches `SKILL.md` line for line, allowing only agent renames;
- after a rename, the old name is gone from the block and the agent file carries the new name;
- with `--before`, everything outside the block is unchanged;
- unless `--no-agents`, each agent file has `name`, `description`, `model`, and `tools`, and
  keeps its author credit.

Run it on your own install:

```bash
python3 tools/check_install.py ~/.claude                         # user level, with agents
python3 tools/check_install.py ./.claude --no-agents             # policy only
python3 tools/check_install.py ./.claude --rename executor=builder
cp ./.claude/CLAUDE.md /tmp/before.md   # before installing, then afterwards:
python3 tools/check_install.py ./.claude --before /tmp/before.md
```

It prints one `PASS` or `FAIL` line per check, then `INSTALL: PASS` or `INSTALL: FAIL`. It
exits 0 on pass, 1 on a failed check, and 2 when it cannot check at all. It only reads files.

`tools/test_check_install.py` builds fixtures from the current `SKILL.md` and agent assets, so
they cannot drift from the release:

| Fixture | Expected |
|---|---|
| Fresh install, empty scope | Pass |
| Fresh install into an existing `CLAUDE.md` | Pass; unrelated content kept |
| Upgrade from an older `policy-rev`, replaced in place | Pass; content before and after the block kept |
| Name collision: `executor` renamed to `builder` | Pass; the user's own `executor.md` untouched |
| Policy only, agents declined | Pass; no agent checks run |
| Opening marker without a closing marker | Fail, naming the missing marker |
| Upgrade that appended a second block | Fail: two marker pairs |
| Stale `policy-rev` | Fail: names the expected and found revision |
| Edited policy block | Fail: names the first differing line |
| Unrelated content lost | Fail: names a lost line |
| Rename applied to only one side | Fail: names the leftover name or the missing agent file |
| Agent file missing `tools` or its author credit | Fail: names each problem |

### Diagnostics, uninstall, and the demo: `tools/test_tools.py`

- `diagnose.py` reports stale or malformed policy blocks, a pre-3.0 clone, policy at both
  levels, Stackwich agents with no policy, and agents defined at both levels, and never prints
  file contents.
- `uninstall.py` changes nothing without `--apply`, keeps unrelated `CLAUDE.md` content and
  agents without the Stackwich credit, backs up `CLAUDE.md`, and refuses a malformed block.
- The [first-task](first-task.md) demo must fail exactly as the walkthrough shows and pass
  after the fix it shows.

### Measured layer: `measured/test_measured.py`

Covers the append-only log, report rates, latest-state reporting for gates, items, and risks,
and the approval gate's self-check.

### Running them

```bash
(cd tools && python3 -m unittest discover -v)
(cd measured && python3 -m unittest -v test_measured && python3 approve.py --self-check)
```

`.github/workflows/validate.yml` runs both after its structural checks.

## Behavior evals: `evals/evals.json`

Seven scenarios describe what an agent should do. Their assertions are about conversation and
behavior, so a model has to be run and its transcript read.

| Case | Scenario | What `check_install.py` can confirm | What needs the transcript |
|---|---|---|---|
| 1 | Fresh user-level install | Markers, `policy-rev`, block, agent files | Verification results reported |
| 2 | Update an existing install | One marker pair, current `policy-rev` (with `--before`, content kept) | Block shown and user asked before replacing |
| 3 | Name collision | Rename consistent; agent file present | Collision raised before any write |
| 4 | Policy only | Block written (with `--no-agents`) | Agent checks skipped, not failed; assets not read |
| 5 | Missing closing marker | The broken state is detected | Region shown; no replacement before confirmation |
| 6 | Unbounded loop request | Nothing | Stop condition, run cap, and no-change stop stated before starting |
| 7 | Large parallel batch | Nothing | Shard count and reason; batches fit one verifier pass; run counts reported |

### How to run one

1. Use a disposable setup: a fresh project directory for project-level cases, and a separate
   user account, container, or VM for user-level cases. Do not run them against a `~/.claude`
   you rely on.
2. Install the plugin as the README describes. For cases 2, 3, and 5, first create the starting
   state the scenario implies, and copy `CLAUDE.md` aside for `--before`.
3. Send the case's `prompt` and answer questions as a user would.
4. Record the Claude Code version, the model, the date, and token or cost figures if the
   runtime shows them.
5. Grade every assertion in the case as pass or fail from the transcript. For cases 1–5, also
   run `check_install.py` on the resulting scope.
6. Report failures with the transcript excerpt. Do not drop a failed run from the record.

## Not covered yet

Tracked in [#12](https://github.com/ovhirup/stackwich/issues/12):

- runtime evals for missing hand-offs, scope violations, skipped verification, and retry
  exhaustion;
- running behavior evals automatically, with recorded runtime and model versions.

The Dynamic LLM Router already checks scope, evidence, and the two-cycle cap mechanically for
its own workers; see [enforcement.md](enforcement.md).
