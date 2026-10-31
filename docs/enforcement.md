# What Stackwich enforces

Stackwich is mostly policy: instructions a model reads and is expected to follow. A few
boundaries are mechanical: the runtime or a script refuses the action whatever the model does.
This page lists which is which, per mode, so nobody relies on a guarantee that is not there.

Three kinds of claim:

- **Mechanical**: a tool list, sandbox, or script refuses the action. It holds even if the model
  ignores its instructions.
- **Instructed**: the policy or agent file tells the model what to do. It holds only as long as
  the model complies. Nothing checks it afterwards.
- **Not provided**: neither. Do not assume it.

## Claude Code plugin

| Behavior | Kind | Detail |
|---|---|---|
| `advisor` and `verifier` have no `Edit` or `Write` tool | Mechanical | Their frontmatter grants `Read, Glob, Grep, Bash` and `Read, Bash, Grep, Glob`. Claude Code does not give them the edit tools. |
| `advisor` and `verifier` do not write through `Bash` | Instructed | Both keep `Bash` so they can inspect and run tests. A shell can write, move, delete, install, or push; only the instructions say not to. |
| Only `executor` changes product files | Instructed | Follows from the two rows above. `executor` itself has every tool it needs to write anywhere. |
| `executor` stays inside the plan's declared file scope | Instructed | Nothing compares the diff with the scope unless `verifier` is asked to and does. |
| Each agent's model tier | Mechanical, as configuration | Set by `model:` in each agent's frontmatter. Which agent gets used for a task is instructed. |
| Plan → execute → verify → review for risky changes | Instructed | The main session decides when a change is risky and whether to run the sandwich. |
| Verdict lines (`GATE: PASS`, `APPROVE`, `REVISE:`) | Instructed | They are fixed strings so routing does not depend on reading prose, but the main session does the routing. |
| Failure loops capped at 2 cycles | Instructed | No counter exists outside the conversation. |
| Nothing "done" until verified | Instructed | The policy requires reporting the command and its output. No tool checks that a claim matches a run. |

## Codex port

| Behavior | Kind | Detail |
|---|---|---|
| `advisor` and `verifier` cannot write files | Mechanical, where Codex honors the setting | Their templates set `sandbox_mode = "read-only"`, so Codex runs their commands in its read-only sandbox. |
| `executor` stays in scope and does not push, deploy, or publish | Instructed | `executor` has no `sandbox_mode` in its template and inherits the session's sandbox and approval settings. |
| Sandwich, verdict routing, 2-cycle cap, two-strike rule | Instructed | Same as the Claude Code plugin. |
| Model choice | Not pinned | The templates set reasoning effort and sandbox only, so they stay portable across accounts. |

A read-only sandbox also blocks legitimate writes. A test, build, or coverage run that needs to
write output can fail inside `verifier`. That is a sandbox limit, not a failed change; the
verifier's instructions say to label environment problems as such.

## Grok port

| Behavior | Kind | Detail |
|---|---|---|
| Single writer, PLAN/VERIFY/REVIEW never edit | Instructed | The port runs the sandwich as phases inside one agent. There is no separate role with fewer tools. |
| Sandwich, 2-cycle cap, verification before "done" | Instructed | Same policy as the parent, carried by `grok/SKILL.md`. |

## Measured approval gate (`measured/approve.py`)

| Behavior | Kind | Detail |
|---|---|---|
| Planner, writer, verifier, and approver are four different names | Mechanical | The script refuses a plan, approval, or execute where the names it was given collide. |
| Order: dry run → approval → one execute | Mechanical | Execute is refused before approval and refused a second time. A dry run writes nothing. |
| Only the named writer can execute | Mechanical, by name | The `--actor` string must equal the recorded writer. |
| The four names are four different people | Not provided | Names are strings passed on the command line. One person can type four names. Nothing authenticates who ran each step. |
| Approval covers an exact diff | Not provided | The ledger records a summary and a list of file paths, not a commit, hash, or patch. A change made after approval is not detected. |
| Execute applies the change | Not provided | Execute writes one marker file, `applied.txt`. Applying the real diff stays with the writer. |
| The ledger is tamper-evident | Not provided | It is a local JSON file. Anyone who can write it can change it. |

Use the gate as a local workflow check and an audit trail of what people said they did. Where
separation of duties must hold against a determined person, pair it with something that
authenticates identity and binds approval to a change, such as protected branches with required
reviews.

The measured event log has the same shape. `log_event.py` validates each event and only
appends, but the JSONL file itself is an ordinary file.

## Dynamic LLM Router integration

[Dynamic LLM Router](https://github.com/ovhirup/dynamic-llm-router#optional-stackwich-verification)
can run a worker under the same plan → execute → verify → review contract. Its checks are
mechanical: `run-job` requires a report with `PASS` and `APPROVE`, planned and changed product
paths that match exactly, successful command evidence, a passing router-configured test
command, and no more than two correction cycles. It rejects changes to report evidence or
product contents during its own tests, unexpected worker commits, and staged scope mismatches.

The plan, execute, verify, and review stages still run inside one worker session. The router's
tests and scope checks are independent; the review is not an independent model review. Claims
about Router-verified work should say that.

## What "read-only" protects

Read-only roles protect product source and external state: repository files, configuration,
installed packages, remote branches, deployments, and live services. They do not promise that no
byte is ever written. Running real tests, lint, and builds legitimately creates caches, build
output, coverage files, and temporary files, and a verifier that cannot run the project's real
commands is not a gate.

So the line Stackwich draws is between artifacts the verification command produces and edits to
the product. A verifier that runs `npm test` and leaves a coverage directory is within policy. A
verifier that fixes a failing line is not. Under the Claude Code plugin and the Grok port that
line is instructed; under Codex the sandbox draws a stricter line that can also block
artifacts; under the Router, report files are excluded from commits and the scope check covers
everything else.

## Verification records (`tools/verify_gate.py`)

Optional. These rows hold only in setups that run the tool, and only where someone (a person, CI,
or a hook) runs `check` before treating a change as done. See [verify-gate.md](verify-gate.md).

| Behavior | Kind | Detail |
|---|---|---|
| A PASS names the files it tested | Mechanical | Each record holds the commit and a hash of every product file, committed or not. |
| An edit after a PASS is caught | Mechanical, when `check` runs | `check` fails and names each added, modified, or removed file. |
| The verification command does not edit product files | Mechanical, during `run` | A run whose command changed product files is `GATE: FAIL`, whatever its exit code. |
| Failure loops capped at 2 cycles | Mechanical, when runs go through the tool | After the first run and 2 failed correction cycles, `run` refuses until a person records a reset. |
| The agent uses the tool | Instructed | Nothing makes the model call `run`. A `check` that you run is what it cannot skip. |
| The command is a good verification | Not provided | The tool records the verdict of whatever command it is given. |
| The record is tamper-evident | Not provided | `.stackwich/verify.jsonl` is a local file. |

## What would make more of this mechanical

These are research ideas, not shipped features. See H1 in
[next-version-research.md](next-version-research.md). `tools/verify_gate.py` covers binding a
verdict to the tested tree and the failure cap. Scope checks against a plan, signed records, and
running `check` automatically remain open.
