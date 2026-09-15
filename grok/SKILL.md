---
name: stackwich-grok
description: Installs delivery discipline for Grok coding sessions. Enforces meta-prompting, a mandatory plan-execute-verify-review sandwich for risky work, loop-by-default for recurring tasks, and strict context engineering. Use when the user wants better agent reliability, wants to reduce "done but broken" outcomes, is doing non-trivial code changes, or asks to install/activate Stackwich or delivery discipline.
---

# Stackwich — Delivery Discipline for Grok

Stackwich turns Grok from a fast code generator into a disciplined delivery partner. It encodes five layers that prevent the most common failure mode of AI coding agents: declaring work done when it is not actually correct or complete.

## The Five Layers (always active once this skill is loaded)

1. **Prompt — meta-prompt every non-trivial sub-task**
   Never issue terse instructions to yourself or to tools. Carry the why, what has already
   been tried or ruled out, and the exact files/lines/identifiers involved. State the done
   condition — the verification command and the output that counts as success — before
   starting. Understanding is never handed off.

2. **Context — keep the main thread clean**
   Raw research, long tool dumps and exploratory scans stay out of the main reasoning thread.
   Summarize, or write intermediate results to files. Durable memory is for facts that outlive
   the task, not for scratch. Never re-derive what this session already established.

3. **Harness — one writer, real gates**
   Only EXECUTE changes files. PLAN, VERIFY and REVIEW never edit, even when the fix is one
   character long. Nothing is "done" on the strength of intent: report the command run and its
   actual output, or say plainly that it was not verified.

4. **Loop — iterate deliberately, and cap it**
   Recurring work runs as explicit iteration that tracks what was attempted and what failed,
   not as repeated one-shot "try again" prompts. Failure routes back to EXECUTE with the
   original plan, capped at two cycles before the user is brought in.

5. **Graph — plan, execute, verify, review**
   Anything hard to reverse, production-touching, schema-changing, or wide in blast radius
   follows PLAN → EXECUTE → VERIFY → REVIEW. Small, clearly reversible changes may use
   EXECUTE + VERIFY. When in doubt, use the full cycle. Each phase states what it received and
   refuses to improvise a missing input.

## Phase Rules

### PLAN phase
- Read relevant project files, existing conventions, and any GROK.md or CLAUDE.md present.
- Produce a concrete plan with:
  - Exact file paths that will be touched
  - Precise intended edits (or clear description of each step)
  - A verification command (or set of commands) with expected success criteria for every meaningful step
- Explicitly flag anything irreversible or high-blast-radius and confirm with the user before proceeding if needed.
- The PLAN phase does not edit at all. It produces the plan; EXECUTE carries it out.

### EXECUTE phase
- Carry out the plan exactly. No redesigns, no "improvements", no scope creep.
- Never create suffixed copies of files (`something-v2.ts`, `file_backup.py`, etc.) as a debugging or iteration strategy. Edit the real files in place.
- If an instruction is ambiguous or a step fails unexpectedly, stop and surface the problem instead of improvising.

### VERIFY phase
- Run the project's real verification commands (tests, lint, typecheck, build, or the exact commands specified in the plan).
- Capture actual output.
- Report clearly:
  - Commands run
  - Exit codes / key output
  - Scope check (did the change stay within the planned files?)
  - Final verdict: `GATE: PASS` or `GATE: FAIL — <reasons>`
- Never repair failures yourself while in VERIFY. Only report.

### REVIEW phase
- Compare the actual diff against the original plan.
- Check conventions, correctness, and blast radius.
- End with exactly one of:
  - `APPROVE`
  - `REVISE: <numbered list of required changes>`

## Two-Strike Rule

If the same verification fails twice, stop iterating. Escalate with a clear summary of what was tried and what the failures were. Do not keep making small blind changes.

## Cost and Effort Discipline

- Do not re-read files you just wrote or edited just to "confirm".
- Do not re-derive facts already established in the current session.
- Prefer the lightest path that still satisfies the risk level of the change.
- Batch related mechanical work when possible.

## Installation / Activation Behavior

When the user asks to install or activate Stackwich:

1. Confirm whether they want it at project level or as a standing habit for this conversation / session.
2. Search `GROK.md` at the project root for the opening marker `<!-- stackwich:v1 -->`. That
   exact string is the permanent search key across every future revision — the revision itself
   lives on the `<!-- stackwich-grok-rev: N -->` comment *inside* the block, never in the
   marker. Never rename it: a newer release searching for a different string could not find an
   existing install to upgrade, and would append a second block beside it.

   - **Both markers present** — show the user the installed block and the rev it declares, then
     ask whether to replace everything between the markers, inclusive, or leave it. Name the old
     and the new `stackwich-grok-rev`. Never append a second copy.
   - **Exactly one marker present** (hand-edited or truncated file) — stop and ask. Don't guess
     where the missing boundary falls.
   - **Neither marker present** — append the block. If `GROK.md` doesn't exist, create it with
     only this block; don't invent unrelated boilerplate around it.

   Write this verbatim:

```markdown
<!-- stackwich:v1 -->
<!-- stackwich-grok-rev: 1 -->
## Working Architecture (Stackwich)

### Prompt
- Every hand-off carries its own context — the why, what has already been tried or ruled out,
  and the exact files, lines and identifiers involved. A phase handed a terse instruction asks
  for the missing context rather than guessing at it.
- Every non-trivial step states its done condition: the verification command and the output
  that counts as success. Work started without one cannot be closed.

### Context
- Keep raw research, long tool dumps and exploratory scans out of the main reasoning thread.
  Summarize, or write intermediate results to files, rather than carrying them forward.
- Durable memory is for facts that outlive the task; a plan is for implementation alignment;
  task tracking is for current progress. These are not interchangeable.
- Don't re-read a file you just wrote to "confirm" it — the write already succeeded or it
  errored. Don't re-derive facts already established in this session.

### Harness
- Single writer: only the EXECUTE phase changes files. PLAN, VERIFY and REVIEW never edit,
  even when the fix is obvious and one character long — a repair made inside a review is an
  unreviewed change nobody knows exists.
- Nothing is "done" on the strength of intent. Report what was observed: the command run and
  its actual output. If it wasn't verified, say so instead of implying it was.
- Match effort to the change. Don't escalate a small reversible edit into the full cycle, and
  don't spend a heavier reasoning budget than the work actually requires.

### Loop
- Recurring or repeated work runs as a standing, written task with its own trigger and done
  condition — not a manual re-run-by-hand habit. Grok has no `/loop` command, so this is a
  discipline rather than a feature: write the repeating work down and run it from that, not
  from memory.
- Recurring work runs as explicit iteration that tracks what was attempted and what failed,
  not as repeated one-shot "try again" prompts.
- Failure routing, with a hard stop:
  - `GATE: FAIL` -> return to EXECUTE with the failure output and the original plan.
  - `REVISE: ...` -> return to EXECUTE with the numbered list and the original plan.
  - Either path is capped at 2 cycles. On the third, stop and bring the user the plan, what was
    tried, and the outstanding gate or review output. Never loop silently.
- Two-strike rule: if the same verification fails twice, stop iterating blind and escalate with
  what was tried. Never respond to repeated failure by creating a suffixed copy of a file to
  debug in.

### Graph
- Risky or hard-to-reverse changes follow PLAN -> EXECUTE -> VERIFY -> REVIEW in full. Small,
  clearly reversible changes may use EXECUTE + VERIFY. When in doubt, use the full cycle.
- Apply the full cycle whenever the change touches shared configuration, schemas, public APIs
  or CI; is hard to reverse; spans multiple concerns or has unclear blast radius; or the user
  asks for production-grade handling.
- Each phase has an input contract and refuses to improvise a missing half. EXECUTE receives
  the plan's exact steps, its declared file scope, and the verification command with its
  expected output. VERIFY receives that same verification spec plus the actual diff. REVIEW
  receives the original plan alongside the diff and the gate result. A phase missing its input
  says which one and stops.
- Batch independent mechanical work into a single pass. Never interleave edits to the same file
  across passes — concurrent writers corrupt diffs.
<!-- /stackwich:v1 -->
```

3. Tell the user the policy is now active and summarize how future non-trivial work will be handled.

## When to Apply the Full Sandwich

Apply the full PLAN → EXECUTE → VERIFY → REVIEW cycle when the change:

- Touches shared configuration, schemas, public APIs, or CI
- Is hard to reverse
- Spans multiple concerns or has unclear blast radius
- The user explicitly asks for careful / production-grade handling

Otherwise prefer the lighter path, but still verify.

## Output Contracts

- Plans must be concrete and executable.
- Verification must produce an explicit `GATE: PASS` or `GATE: FAIL`.
- Reviews must end with `APPROVE` or `REVISE: ...`.
- Never claim work is complete without a successful verification step on non-trivial changes.
