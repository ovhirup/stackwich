# 🥪 Stackwich (Grok Edition)

**Delivery discipline for Grok.**  
Plan → Execute → Verify → Review — as standing policy.

This is the Grok-native version of [Stackwich](https://github.com/ovhirup/stackwich).

Most people run coding agents like slot machines: prompt → hope → fix later.  
Stackwich makes Grok behave like a disciplined engineer instead.

---

## What it does

Stackwich installs five layers into Grok coding sessions:

1. **Prompt** — meta-prompt every non-trivial sub-task; never hand off understanding
2. **Context** — keep research and raw tool output out of the main reasoning thread
3. **Harness** — one writer, and nothing is "done" without observed output
4. **Loop** — deliberate iteration, capped at two cycles before you're brought in
5. **Graph** — PLAN → EXECUTE → VERIFY → REVIEW for anything risky

It also enforces:
- A hard verification gate (`GATE: PASS` / `GATE: FAIL`)
- Two-strike rule (same failure twice → stop and escalate)
- No suffixed file copies as a debugging strategy
- Concrete plans with verification commands before non-trivial edits

---

## Claude vs Grok version

| Aspect              | Claude Code version              | Grok edition                          |
|---------------------|----------------------------------|---------------------------------------|
| Layer model         | Prompt · Context · Harness · Loop · Graph | Same five layers; Loop is a written standing task, not a `/loop` command |
| Policy location     | `CLAUDE.md`                      | `GROK.md`                             |
| Architecture        | 3 companion agents (advisor / executor / verifier) | Explicit phases inside one agent     |
| Verification        | Dedicated verifier agent         | Grok runs real project commands itself |
| Installation        | Plugin marketplace + agent scaffolding | Skill + policy block in `GROK.md` |

Both versions share the same philosophy. The implementation is adapted to each platform’s strengths.

---

## Install

### As a Grok skill

Get the files, then copy the skill and its license into your Grok skills directory:

```bash
git clone https://github.com/ovhirup/stackwich
cd stackwich/grok
mkdir -p ~/.grok/skills/stackwich-grok
cp SKILL.md LICENSE ~/.grok/skills/stackwich-grok/
```

> **Port status:** at parity with the Claude Code parent's five-layer policy, as
> `stackwich-grok-rev 1`. The port tracks the parent's layer structure, not its revision
> number — a parent bump does not automatically oblige a port bump. The Graph layer is
> expressed as explicit phases inside one agent rather than three subagents: a deliberate
> design choice for this runtime, not a shortfall.

---

Built by **Abhirup Banerjee** ([@ovhirup](https://github.com/ovhirup)).
Part of [Stackwich](https://github.com/ovhirup/stackwich) — MIT, see [LICENSE](../LICENSE).
