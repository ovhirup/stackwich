# Changelog

Headings are `## <repo version> — <what moved>`. Ports are named in the body with their own rev
counters: a port tracks the parent's layer structure, not its revision number.

## 3.0.0 — installs as a plugin

Stackwich is now a Claude Code plugin marketplace rather than a repo you clone into your skills
directory. **Your policy and your agents are unchanged.** `policy-rev` stays at 3, the
`CLAUDE.md` block is identical, the scaffolded `advisor` / `executor` / `verifier` keep their
names and contents, and there is nothing to re-run — only the delivery mechanism moved.

### Upgrading

```
/plugin marketplace add ovhirup/stackwich
/plugin install stackwich@stackwich
```

Then remove the old clone with `rm -rf ~/.claude/skills/stackwich`. Leaving it in place gives
you two skills both named `stackwich`.

### Why the layout moved
- Claude Code discovers skills only by scanning a plugin's `skills/` directory, and no manifest
  field can point at a root-level `SKILL.md`. The skill therefore moved to
  `plugins/stackwich/skills/stackwich/`.
- `assets/` moved with it. `SKILL.md` resolves the agent definitions relative to its own
  directory, so the two are only correct together — which also makes the skill directory
  self-contained and copyable on its own.

### What the plugin deliberately does not ship
- **No `agents/` directory.** Plugin-supplied agents install namespaced, as `stackwich:advisor`,
  on both Claude Code and Grok. That would break the policy block's bare references, remove the
  choice to decline scaffolding, and make rename-on-collision impossible, since a file in the
  plugin cache is overwritten on update. The skill keeps scaffolding them from `assets/`.
- **No stub `SKILL.md` at the repo root.** A stub would itself be a skill named `stackwich`, and
  would collide with the installed plugin — the very duplicate this release tells you to avoid.

### Repo
- CI validates both manifests, checks the marketplace entry and `plugin.json` agree on name,
  checks `plugin.json`'s version matches the skill's frontmatter, and fails if a root
  `SKILL.md`, a root `assets/`, or a `plugins/stackwich/agents/` ever reappears.
- The `grok/` and `codex/` ports are untouched and stay at the repo root — nothing there sits on
  a Claude Code discovery path.

## 2.2.0 — ports reach five-layer parity

The `grok/` and `codex/` ports now install the same Prompt / Context / Harness / Loop / Graph
structure as the Claude parent. **The parent policy block is unchanged and `policy-rev` stays at
3** — diff an existing Claude install against this release and you will find nothing, and no
re-install is needed.

### Grok — stackwich-grok-rev 1
- The installed `GROK.md` block grows from seven flat bullets to the five layers, carrying
  single-writer, nothing-done-on-intent, capped failure routing, and per-phase input contracts.
- Graph is expressed as explicit phases inside one agent rather than three subagents — the
  port's deliberate design. The fan-out rule becomes the reason behind it: batch independent
  work, never interleave edits to one file across passes.
- The install step gained a marker-search procedure. It previously said only "or update it if it
  already exists", which would have appended a second block to every existing install now that
  the block is six times longer.
- Fixed literal backslash-escaped backticks that left the copy-verbatim policy block with no
  code-fence boundary.

### Codex — stackwich-codex-rev 1
- The `AGENTS.md` block keeps its twelve bullets, redistributed under the five layers, and gains
  read-only-in-practice, capped `GATE: FAIL` / `REVISE:` routing with an infrastructure-versus-
  change split, and orchestrator hand-off contracts.
- The three agent TOMLs gained explicit input contracts: `advisor` no longer reviews a diff
  without the plan that produced it, `executor` says when it could not verify rather than
  inventing a command, and `verifier` separates an environment failure from a failed change so
  one cannot burn a capped cycle.
- The `stackwich-codex:v1` marker is unchanged.

### Repo
- CI asserts every marker and rev comment as an exact whole-line match, plus all five layer
  headings in each port, so a port cannot silently drift — the failure this release corrects.
  Whole-line matching is the point: these files document their own marker syntax in prose, so a
  substring check is satisfied by the documentation instead of the thing it documents. That bit
  us during this release, in the parent's own check as well as both ports'.
- `evals/evals.json` expected `policy-rev 2`; corrected to 3.

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
