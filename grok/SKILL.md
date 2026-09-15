---
name: stackwich-grok
description: Installs delivery discipline for Grok coding sessions. Enforces meta-prompting, a mandatory plan-execute-verify-review sandwich for risky work, loop-by-default for recurring tasks, and strict context engineering. Use when the user wants better agent reliability, wants to reduce "done but broken" outcomes, is doing non-trivial code changes, or asks to install/activate Stackwich or delivery discipline.
---

# Stackwich — Delivery Discipline for Grok

Stackwich turns Grok from a fast code generator into a disciplined delivery partner. It encodes four habits that prevent the most common failure mode of AI coding agents: declaring work done when it is not actually correct or complete.

## Core Habits (always active once this skill is loaded)

1. **Meta-prompt every non-trivial sub-task**  
   Never issue terse commands to yourself or to tools. Always include the why, what has already been tried or ruled out, and the exact files/lines/identifiers involved. Understanding is never delegated.

2. **Sandwich risky work**  
   Anything hard to reverse, production-touching, schema-changing, cross-file with high blast radius, or spanning multiple concerns must follow:

   PLAN → EXECUTE → VERIFY → REVIEW

   Small, clearly reversible changes may use a lighter path (execute + verify only). When in doubt, use the full sandwich.

3. **Loop by default for recurring work**  
   Prefer explicit iteration over one-shot "try again" prompts. Track what was attempted and what failed.

4. **Context engineering**  
   Keep raw research, long tool dumps, and exploratory scans out of the main reasoning thread. Summarize, write to files, or use memory only for durable facts. Prefer writing intermediate results to files over stuffing the conversation.

## Phase Rules

### PLAN phase
- Read relevant project files, existing conventions, and any GROK.md or CLAUDE.md present.
- Produce a concrete plan with:
  - Exact file paths that will be touched
  - Precise intended edits (or clear description of each step)
  - A verification command (or set of commands) with expected success criteria for every meaningful step
- Explicitly flag anything irreversible or high-blast-radius and confirm with the user before proceeding if needed.
- Do not start editing until the plan is clear.

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
2. Write a short, durable policy block into a file named `GROK.md` at the project root (or update it if it already exists). Use clear markers so it can be updated later:

```markdown
<!-- stackwich:v1 -->
## Working Architecture (Stackwich)

- Meta-prompt every non-trivial sub-task. Never hand off understanding.
- Risky or hard-to-reverse changes must follow PLAN → EXECUTE → VERIFY → REVIEW.
- Small reversible changes may use execute + verify only.
- Always run real project verification commands. Report GATE: PASS or GATE: FAIL.
- Two-strike rule: same verification fails twice → stop and escalate.
- Never create suffixed file copies as a workaround.
- Keep research and raw tool output out of the main thread.
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
