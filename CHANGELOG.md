# Changelog

## 2.1.0 — policy-rev 3

Restructures the policy block under the five engineering layers and promotes **harness** to a
named layer. Marker unchanged; v1 and v2 installs upgrade in place.

- Policy block reorganized from twelve flat bullets into `### Prompt / Context / Harness / Loop
  / Graph`. Future audits become mechanical — "what's my harness rule?" now has an address.
- **Harness promoted to a stated layer.** In v2 it existed only as scattered implementation
  (tool scoping in agent frontmatter, the step-4 self-check) with no principle behind it. Now
  explicit: single writer, read-only-in-practice, nothing "done" on intent alone, model tiering.
- Prompt layer gains a done-condition rule: every delegation carries its verification command
  and expected output, so nothing is handed off unverifiable.
- Layer names deliberately kept as headers rather than taught as vocabulary — the block is read
  every turn, and explaining a taxonomy there costs tokens without changing behavior.

## 2.0.0 — policy-rev 2

Upgrade pass across five layers: prompt, context, harness, loop, and graph. The
`<!-- stackwich:v1 -->` marker is unchanged, so v1 installs upgrade in place.

### Context
- Moved `advisor`/`executor`/`verifier` definitions out of `SKILL.md` into `assets/`. They're
  read only when the user accepts scaffolding — roughly a 55% smaller body on every trigger,
  and nothing loaded at all when the scaffolding is declined.
- Dropped the per-task model-tiering restatement from the policy block; tiers are already
  declared in each agent's frontmatter.

### Loop
- Defined routing for `GATE: FAIL` and `REVISE:` — both return to `executor` with the original
  plan attached, capped at 2 cycles, then escalate to the human. Previously both verdicts were
  produced but had no defined destination, leaving revise cycles unbounded.
- `verifier` now separates infrastructure failures (missing dependency, unavailable service)
  from failed changes, so cycles aren't burned on environment problems.
- Added `evals/evals.json` covering five install paths: fresh install, v1 upgrade, name
  collision, policy-only (agents declined), corrupt install.

### Harness
- Added step 4: the skill verifies its own install (marker pair count, `policy-rev` match,
  agent frontmatter validity, rename propagation) and reports observed results. A skill that
  mandates verify-before-done now applies that to itself.
- Scoped `Bash` explicitly to inspection/verification in `advisor` and `verifier`, since
  read-only can't be enforced by the tool list once `Bash` is granted.
- Step 1 now handles a corrupt install (opening marker without closing marker) by asking for
  boundary confirmation instead of guessing.

### Graph
- Added an explicit orchestrator-forwarding contract: each agent's required inputs are named in
  the policy block and restated in the agent file, with instructions to stop rather than
  reconstruct a missing input.
- Named the single-writer rule (`executor` only) as policy rather than leaving it implicit.
- Added fan-out/fan-in guidance: shard large *independent* batches across parallel executors
  into one verifier pass; keep shared-file or order-dependent work serial.

### Prompt
- Added a worked terse-vs-meta-prompt contrast, plus a concrete plan template in `advisor`. The
  central habit was previously described but never demonstrated.
- Moved concrete "hard to reverse" examples (schema migrations, prod config, published APIs,
  auth, history rewrites, CI/CD, data deletion) into the policy block, where the orchestrator
  making the consult-advisor decision actually reads them.
- Broadened the skill description to catch indirect requests ("set up planner/reviewer
  subagents", "add a review gate", "my agents make sloppy edits").
- Fixed a stale instruction referring to "the three bracketed subagent names" — nothing in the
  block was bracketed.
- Made `REVISE:` items required to be independently actionable, since each vague item costs one
  of two capped cycles.

## 1.0.0

Initial release: policy block, marker-based idempotent install, three companion subagents,
two-strike rule.
