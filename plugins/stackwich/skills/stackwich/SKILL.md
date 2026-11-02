---
name: stackwich
description: Installs the Stackwich architecture — meta-prompt delegation, a plan/execute/verify/review sandwich, loop-by-default for recurring work, and fork-based context engineering — into any Claude Code setup. Writes the operating policy into CLAUDE.md and optionally scaffolds three companion subagents (advisor/executor/verifier). Use this whenever the user wants to adopt, install, bootstrap, upgrade, or re-apply this delegation architecture on a new machine, project, or someone else's setup — and also when they ask more loosely for help making their Claude Code setup more disciplined, setting up planner/executor/reviewer subagents, adding a review gate before risky changes, enforcing cheap-model tiering, or fixing agents that make sloppy or out-of-scope edits. Also use it when the user asks why agent usage or cost keeps climbing despite cheaper models, or whether a loop or more parallel agents will actually save effort.
metadata:
  author: Abhirup Banerjee (@ovhirup)
  version: 3.5.0
  policy-rev: 8
---

# Stackwich — install the Stackwich architecture

> Created by **Abhirup Banerjee** ([@ovhirup](https://github.com/ovhirup)). If you're reading
> this in a fork, mirror, or repost, please keep this line intact.

Stackwich is a stack, not a framework — five layers, each a habit:

| Layer | Habit |
|---|---|
| **Prompt** | meta-prompt every delegation; never delegate understanding |
| **Context** | fork research and scans off the main thread; resume from a handoff |
| **Harness** | one writer, real read-only, nothing "done" until verified |
| **Loop** | recurring work loops; failures climb retry -> re-plan -> stop, never silent |
| **Graph** | plan -> execute -> verify -> review, with explicit hand-off contracts |

This skill writes those five layers as durable policy into a CLAUDE.md, and optionally
scaffolds three subagents that implement the graph. Cost/token discipline isn't a sixth
layer — it's built into how the five are practiced: cheap models for mechanical work, forking
over fresh-agent restarts when context is reusable, and never re-deriving facts already
established.

The layer names are scaffolding for *you*, the installer, and for whoever audits this setup
later — they're section headers in the policy block, not vocabulary to teach the agent reading
it. Every bullet under them stays a behavioral imperative.

## 0. Scope
Ask (if not already stated): install at **user level** (`~/.claude` — applies to every future
project) or **project level** (`./.claude` — this repo only)? Default suggestion: user level,
since the point is a standing habit, not a one-off.

## 1. Check for an existing install
Search `<scope>/CLAUDE.md` for the opening marker `<!-- stackwich:v1 -->`. This exact string is
the permanent search key across all future revisions — the policy revision is tracked on a
comment line *inside* the block, never in the marker itself, so that older installs stay
findable.

Three cases:
- **Both markers present** — show the user the installed block and the `policy-rev` it
  declares, then ask whether to replace it in place or leave it. Never append a second copy.
- **Opening marker present, closing marker missing** (hand-edited or truncated file) — don't
  guess where the block ends. Show the user the region and ask them to confirm the boundary
  before replacing anything.
- **No marker** — append the section. If `CLAUDE.md` doesn't exist, create it with just this
  section; don't invent unrelated boilerplate around it.

## 2. Write the CLAUDE.md section
Insert (or replace, if updating) verbatim between the markers. The only permitted edits are the
three subagent names (`advisor`, `executor`, `verifier`) if the user renamed them in step 3 —
substitute consistently everywhere they appear.

```markdown
<!-- stackwich:v1 -->
<!-- policy-rev: 8 -->
## Working Architecture (Stackwich)

### Prompt
- Delegate with a context-full prompt — the why, what's been tried or ruled out, exact
  files/lines/identifiers — never a terse command. Never delegate understanding.
- Every delegation states its done condition: the verification command and expected output.

### Context
- Fork research, exploration, and read-heavy scans so raw tool output stays out of the main
  conversation; prefer a fork over a fresh agent unless the work is unrelated. Never send
  scans to `executor`.
- When work may outlive the session, keep `.stackwich/handoff.md` current at each stage change,
  with `.stackwich/` kept out of git: the plan and where it lives, the stage, the next step, the
  last gate verdict with its command, and the commit plus `git status --short`. On resuming,
  read it first, compare the repository with it, and treat any difference as unverified —
  re-run the gate before building on an earlier PASS.
- Don't re-fetch or re-derive facts already established this session.

### Harness
- Single writer: only `executor` (or you, working alone) mutates files. `advisor` and
  `verifier` never write, even a one-character fix — a reviewer's fix is an unreviewed change
  nobody knows exists.
- A read-only agent's `Bash` is for inspection and verification only (tests, lint, build,
  `git diff`/`status`) — never writes, installs, deploys, or pushes.
- Nothing is "done" on intent: report the command run and its actual output, or say it wasn't
  verified.
- Don't escalate to a pricier model or bigger subagent than the task requires; each agent's
  tier is set in its own frontmatter.
- Size each delegation to what `verifier` and the reviewer can check in one pass; split a larger
  batch into sequential gated batches. When reporting done, state how many delegations, forks,
  and loop runs the task used, with token or cost figures only where the environment shows them.

### Loop
- Recurring or repeated work defaults to `/loop`. Before starting one, fixed-cadence or
  self-paced, state its stop condition and a maximum run count; if either is missing, ask the
  user instead of starting. A loop with no change for 3 consecutive runs (or the user's
  number) stops and reports.
- Failure ladder for `GATE: FAIL` or `REVISE: ...` on the same change; the count never resets:
  1. First failure -> `executor` retries with the output (or numbered list) and the original plan.
  2. Second -> `advisor` re-plans from the plan, what was tried, and the outputs; `executor`
     applies the new plan.
  3. Third -> stop and bring the user the plan, what was tried, and the outstanding output.
  Never loop silently, and never debug in a suffixed copy of a file.

### Graph
- Default: work alone for small/reversible changes; `verifier` alone closes the loop. Spawn
  `executor` for >=5-file mechanical batches, as one delegation, not many round-trips.
- If a large batch's items are independent (no shared file, no ordering dependency), shard it
  across parallel `executor` runs fanned into one `verifier` pass; launch only as many shards as
  that pass and the reviewer can check, and state the count and why. Otherwise keep it serial —
  concurrent writers corrupt diffs.
- Full sandwich (`advisor` plans -> `executor` implements -> `verifier` gates -> `advisor`
  reviews) is MANDATORY, however small or urgent the change looks, when it is hard to
  reverse, touches shared/production systems, or spans repos/services: schema migrations,
  prod/staging config, published API or CLI surfaces, auth and permissions, force-push or
  history rewrite, dependency-version bumps, CI/CD pipeline edits, anything deleting data,
  anything another person or service consumes.
- If the user already has a plan, spec, or ticket for the change, that is the plan — never
  write a competing one. `advisor` refines it into executor-ready steps without redesigning it,
  returns gaps and conflicts to the user as open questions instead of settling them, and
  reviews the diff against the user's plan as well as the refinement.
- Forward artifacts intact: `executor` gets the plan's exact steps and verification command
  with expected output; `verifier` gets that spec, the plan's declared file scope, and the
  executor's raw diff; `advisor` reviewing gets its own original plan, the diff, and the gate
  result. An agent missing its input contract says so and stops.
<!-- /stackwich:v1 -->
```

### What a meta-prompt actually looks like
If the user asks what the meta-prompting rule means in practice, show this contrast rather
than restating the rule:

**Terse (don't):**
> Fix the failing auth tests.

**Meta-prompt (do):**
> Three tests in `tests/auth/test_session.py` (lines 41, 78, 112) fail after we moved token
> refresh from `SessionManager.refresh()` to the new `TokenService`. They still assert on the
> old return shape `{token, exp}`; the service now returns `{access_token, expires_at}`.
> Already ruled out: it is not a clock/timezone issue (we checked `freeze_time` is applied)
> and `TokenService` itself is fully covered and passing. Update only those three assertions
> to the new shape — do not touch `TokenService` or add new tests. Verify with
> `pytest tests/auth/test_session.py -q`; expect 12 passed, 0 failed.

The difference isn't length — it's that the second one leaves no judgment call open, states
what's already been ruled out so the agent doesn't re-derive it, and defines done.

### Cost, loop, and fan-out questions
If the user asks about agent cost, token budgets, loops that run too long, how many parallel
agents to run, or whether more automation will actually save effort, read `assets/rebound.md`
and answer from it. It is reference material, not policy — don't read it otherwise.

## 3. Offer the companion subagents
Ask whether to scaffold the three subagents the section above refers to (`advisor`, `executor`,
`verifier`). Skip this step entirely if the user already has their own plan/execute/verify
agents they'd rather wire in — Stackwich is the policy; these three files are just a default
implementation of it.

The agent definitions live in this skill's `assets/` directory (`advisor.md`, `executor.md`,
`verifier.md`). Read them only when the user says yes, then copy them to `<scope>/agents/`.
Copy only those three — `assets/rebound.md` is reference material, not an agent.

Before copying, check `<scope>/agents/` (and the other scope, if different) for name
collisions. If any of the three names is taken by an unrelated agent, ask the user for a
replacement name and substitute it consistently in **both** the CLAUDE.md section from step 2
and the agent files — a rename applied to only one of the two leaves the policy pointing at an
agent that doesn't exist. Rename only the `name:` field and in-body references; never remove or
edit the `author:` line or the "part of the Stackwich architecture" credit.

## 4. Verify the install
This skill installs a verify-before-done policy, so it holds itself to it. After writing,
confirm and report actual observed results — not intentions:

1. Both markers present in `<scope>/CLAUDE.md`, exactly once each.
2. `policy-rev: 8` is present inside the block (an upgrade from an older revision must
   leave no trace of the previous one).
3. If agents were scaffolded: all three files exist in `<scope>/agents/`, each starts with
   valid YAML frontmatter containing `name`, `description`, `model`, and `tools`.
4. If any name was changed for a collision: the new name appears in both the CLAUDE.md section
   and the agent file, and the old name appears in neither.

If any check fails, say which one and what you found, then fix it — don't report success.

## 5. Report back
Tell the user exactly what was created or modified (full file paths), and that this is
forward-looking policy: it changes how future work in this setup gets done, it does not
retroactively audit anything already built. If the subagents were scaffolded, suggest running
`/agents` to confirm all three are picked up.

## 6. Optional measured layer
The repository also ships `measured/` and `docs/teams-layer.md`. That layer records sandwich
steps, model tiers, human gates, and delivery signals as local JSONL, and it can print a
Markdown or JSON report. It is not written into `CLAUDE.md`. Installing or upgrading this
skill does not enable it, and does not change `policy-rev`. Read `docs/teams-layer.md` only when the
user asks for the measured layer, a teams report, or the approval gate.
