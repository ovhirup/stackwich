# 🥪 stackwich

[![validate](https://github.com/ovhirup/stackwich/actions/workflows/validate.yml/badge.svg)](https://github.com/ovhirup/stackwich/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skill-D97757.svg)](https://docs.claude.com/en/docs/claude-code/skills)

**Delivery discipline for AI agents. Four habits, one command.**

Most people run AI coding agents like slot machines: prompt → pull the lever → hope. The agent writes code 10× faster than you review it, declares itself done, and you find out later. We would never accept that from a junior engineer — we accept it from our tools every day.

Stackwich is 15 years of delivery coaching — plan → build → test → review, the oldest idea in software — compressed into standing policy for [Claude Code](https://docs.claude.com/en/docs/claude-code). Install it once and every future session works this way.

![The Stackwich sandwich: plan (advisor·opus) → execute (executor·haiku) → verify (the gate·sonnet) → review (advisor·opus)](docs/sandwich.jpg)

## The four habits

1. **Meta-prompt every delegation.** Subagents get context — the why, what's been ruled out, exact files and lines — never terse commands. You don't delegate understanding.
2. **Sandwich risky work.** Anything hard to reverse, production-touching, or cross-repo goes plan → execute → verify → review. Mandatory, not vibes.
3. **Loop by default.** Recurring work runs on `/loop`, not a re-run-it-by-hand habit.
4. **Engineer your context.** Research and read-heavy scans fork off the main thread so raw output never pollutes it; memory, plans, and tasks each do their own job.

Cost discipline isn't a fifth habit — it's built into the other four: cheap models grind, expensive models only plan and review, and nothing already established gets re-derived.

## The sandwich

| Stage | Agent | Model | Contract |
|---|---|---|---|
| 🍞 **Plan** | `advisor` | opus | Read-only. Exact files, exact edits, a verification command per step. Flags anything irreversible. |
| 🥩 **Execute** | `executor` | haiku | Mechanical and exact. No redesigns, no improvising, no suffixed file copies. |
| 🧪 **Verify** | `verifier` | sonnet | Runs the project's real tests/lint/build. `GATE: PASS` or `GATE: FAIL` — never repairs. |
| 🍞 **Review** | `advisor` | opus | Diff vs. plan, conventions, blast radius. `APPROVE` or `REVISE: <list>`. |

Small, reversible changes skip the ceremony — the verifier alone closes the loop. If the same verification fails twice, iteration stops and escalates to the advisor. Speed without a gate is just faster mistakes.

## Install

```bash
mkdir -p ~/.claude/skills/stackwich && \
curl -fsSL https://raw.githubusercontent.com/ovhirup/stackwich/main/SKILL.md \
  -o ~/.claude/skills/stackwich/SKILL.md
```

Then, inside any Claude Code session:

```
/stackwich
```

The skill does the rest interactively: asks for scope, writes the policy, offers the three agents. Run `/agents` afterwards to confirm `advisor`, `executor`, and `verifier` are picked up.

## What it writes

| Path | What |
|---|---|
| `<scope>/CLAUDE.md` | The operating policy, fenced between `<!-- stackwich:v1 -->` markers — updates in place, never duplicates |
| `<scope>/agents/advisor.md` | Read-only planner/reviewer (opus) |
| `<scope>/agents/executor.md` | Cheap mechanical executor (haiku) |
| `<scope>/agents/verifier.md` | PASS/FAIL verification gate (sonnet) |

`<scope>` is `~/.claude` (user level — every project, the recommended default) or `./.claude` (this project only). Already have your own plan/execute/verify agents? Keep them — Stackwich is the policy; the three files are just a default implementation, and the installer handles name collisions.

## Uninstall

```bash
rm -rf ~/.claude/skills/stackwich
rm -f ~/.claude/agents/{advisor,executor,verifier}.md
```

…and delete the `<!-- stackwich:v1 -->` … `<!-- /stackwich:v1 -->` block from your `CLAUDE.md`.

## FAQ

**Does it audit my existing code?** No. It's forward-looking policy — it changes how future work gets done, nothing retroactive.

**Will it slow me down?** Only where slow is the point. Small, reversible edits run exactly as before; the full sandwich fires only when a change is hard to reverse, touches shared systems, or spans repos.

**Why these three models?** Tiering is the cost control: opus judgment where it pays (plan/review), haiku hands where it doesn't (mechanical edits), sonnet in between as the gate. Swap models in the agent frontmatter if your stack differs.

## Author

Built by **Abhirup Banerjee** ([@ovhirup](https://github.com/ovhirup)) — AI-native Agile coach; SAFe, PI Planning, and large BFSI delivery programs. Stackwich is that delivery discipline, ported to agents.

MIT — see [LICENSE](LICENSE). If it saves you a bad merge, a ⭐ is appreciated.
