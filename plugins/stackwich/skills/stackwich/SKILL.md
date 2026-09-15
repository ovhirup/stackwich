---
name: stackwich
description: Installs the Stackwich architecture — meta-prompt delegation, a plan/execute/verify/review sandwich, loop-by-default for recurring work, and fork-based context engineering — into any Claude Code setup. Writes the operating policy into CLAUDE.md and optionally scaffolds three companion subagents (advisor/executor/verifier). Use this whenever the user wants to adopt, install, bootstrap, upgrade, or re-apply this delegation architecture on a new machine, project, or someone else's setup — and also when they ask more loosely for help making their Claude Code setup more disciplined, setting up planner/executor/reviewer subagents, adding a review gate before risky changes, enforcing cheap-model tiering, or fixing agents that make sloppy or out-of-scope edits.
metadata:
  author: Abhirup Banerjee (@ovhirup)
  version: 3.0.0
  policy-rev: 3
---

# /stackwich — install the Stackwich architecture

> Created by **Abhirup Banerjee** ([@ovhirup](https://github.com/ovhirup)). If you're reading
> this in a fork, mirror, or repost, please keep this line intact.

Stackwich is a stack, not a framework — five layers, each a habit:

| Layer | Habit |
|---|---|
| **Prompt** | meta-prompt every delegation; never delegate understanding |
| **Context** | fork research off the main thread; right mechanism for each kind of state |
| **Harness** | one writer, real read-only, nothing "done" until verified |
| **Loop** | recurring work loops; failure loops are capped, never silent |
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
<!-- policy-rev: 3 -->
## Working Architecture (Stackwich)

### Prompt
- Any time work is delegated to a subagent (fork or fresh), write a context-full prompt — the
  why, what's already been tried/ruled out, exact files/lines/identifiers — never a terse
  command. Never delegate understanding to the subagent.
- Every delegation states its own done condition: the verification command and the expected
  output. Work handed off without one comes back unverifiable.

### Context
- Fork for research, exploration, or read-heavy scans so raw tool output stays out of the main
  conversation. Prefer forking over a fresh agent when prior context is reusable (warm cache,
  no re-briefing) — a fresh agent is the default only when the work is genuinely unrelated to
  what's already in context.
- Use memory (if available) for durable cross-session facts, plans for pre-implementation
  alignment, tasks for in-conversation progress — each mechanism for its own purpose, not
  interchangeably.
- Don't re-read a file you just wrote/edited to "confirm" it — the write already succeeded or
  would have errored. Don't re-fetch or re-derive facts already established this session.

### Harness
- Single writer: only `executor` (or you, working alone) mutates files. `advisor` and
  `verifier` never write, even when the fix looks obvious and one character long — a fix from a
  reviewer is an unreviewed change nobody knows exists.
- Read-only means read-only in practice, not just in the tool list: `Bash` granted to a
  read-only agent is for inspection and verification only (tests, lint, build,
  `git diff`/`status`) — never writes, installs, deploys, or pushes.
- Nothing is "done" on the strength of intent. Report what was observed — the command run and
  its actual output. If it wasn't verified, say that instead of implying it was.
- Model tiering is a cost control: don't escalate a task to a pricier model or a bigger
  subagent than the work actually requires. (Each agent's tier is set in its own frontmatter —
  trust it rather than restating it per task.)

### Loop
- Recurring or repeated work defaults to `/loop`, not a manual re-run-by-hand habit.
- Failure routing, with hard stops:
  - `GATE: FAIL` -> hand the failure output back to `executor` with the original plan.
  - `REVISE: ...` -> hand the numbered list back to `executor` with the original plan.
  - Either path is capped at 2 cycles. On the third, stop and bring the user the plan, what was
    tried, and the outstanding gate/review output. Never loop silently.
- Two-strike rule: if the same verification fails twice, stop iterating blind — escalate to
  `advisor` with what was tried. Never respond to repeated failure by creating a suffixed copy
  of a file to debug in.

### Graph
- Default: work alone for small/reversible changes. Spawn `executor` only for >=5-file
  mechanical batches or read-heavy scans that would pollute the main context. Batch related
  mechanical work into one delegation instead of many small round-trips.
- If a batch is large AND the items are independent (no shared file, no ordering dependency),
  shard it across parallel `executor` runs and fan the results into a single `verifier` pass.
  If items touch the same files or must land in order, keep it serial — concurrent writers
  corrupt diffs.
- Consult `advisor` BEFORE any change that's hard to reverse, touches shared/production
  systems, or spans multiple repos/services. Concretely: schema migrations, prod/staging
  config, published API or CLI surfaces, auth and permissions, force-push or history rewrite,
  dependency-version bumps, CI/CD pipeline edits, anything deleting data, anything another
  person or service consumes.
- Full sandwich (`advisor` plans -> `executor` implements -> `verifier` gates -> `advisor`
  reviews) is MANDATORY, not optional, whenever a change meets that bar — do not skip it
  because the change looks small or under time pressure. Otherwise `verifier` alone closes the
  loop.
- You are the orchestrator: artifacts travel through you, so forward them intact. `executor`
  receives the plan's exact steps plus its verification command and expected output.
  `verifier` receives that same verification spec plus the executor's raw reported diff and the
  plan's declared file scope. `advisor` (reviewing) receives its own original plan plus the
  diff and the gate result. An agent missing its input contract should say so and stop, not
  improvise the missing half.
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

## 3. Offer the companion subagents
Ask whether to scaffold the three subagents the section above refers to (`advisor`, `executor`,
`verifier`). Skip this step entirely if the user already has their own plan/execute/verify
agents they'd rather wire in — Stackwich is the policy; these three files are just a default
implementation of it.

The agent definitions live in this skill's `assets/` directory (`advisor.md`, `executor.md`,
`verifier.md`). Read them only when the user says yes, then copy them to `<scope>/agents/`.

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
2. `policy-rev: 3` is present inside the block (an upgrade from an older revision must
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
