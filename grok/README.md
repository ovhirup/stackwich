# 🥪 Stackwich (Grok Edition)

**Delivery discipline for Grok.**  
Plan → Execute → Verify → Review — as standing policy.

This is the Grok-native version of [Stackwich](https://github.com/ovhirup/stackwich).

Most people run coding agents like slot machines: prompt → hope → fix later.  
Stackwich makes Grok behave like a disciplined engineer instead.

---

## What it does

Stackwich installs four habits into Grok coding sessions:

1. **Meta-prompt every non-trivial sub-task** — never hand off understanding
2. **Sandwich risky work** — PLAN → EXECUTE → VERIFY → REVIEW
3. **Loop by default** for recurring work
4. **Context engineering** — keep research and raw tool output out of the main thread

It also enforces:
- A hard verification gate (`GATE: PASS` / `GATE: FAIL`)
- Two-strike rule (same failure twice → stop and escalate)
- No suffixed file copies as a debugging strategy
- Concrete plans with verification commands before non-trivial edits

---

## Claude vs Grok version

| Aspect              | Claude Code version              | Grok edition                          |
|---------------------|----------------------------------|---------------------------------------|
| Policy location     | `CLAUDE.md`                      | `GROK.md`                             |
| Architecture        | 3 companion agents (advisor / executor / verifier) | Explicit phases inside one agent     |
| Verification        | Dedicated verifier agent         | Grok runs real project commands itself |
| Installation        | Skill + agent scaffolding        | Skill + policy block in `GROK.md`     |

Both versions share the same philosophy. The implementation is adapted to each platform’s strengths.

---

## Install

### As a Grok skill

Copy the `SKILL.md` into your Grok skills directory:

```bash
mkdir -p ~/.grok/skills/stackwich-grok
cp SKILL.md ~/.grok/skills/stackwich-grok/
```

> **Port status:** this port tracks the original four-habit framing. The Claude Code
> parent is at v2.1.0 (five layers: Prompt / Context / Harness / Loop / Graph).
> A parity pass is tracked separately.

---

Built by **Abhirup Banerjee** ([@ovhirup](https://github.com/ovhirup)).
Part of [Stackwich](https://github.com/ovhirup/stackwich) — MIT, see [LICENSE](../LICENSE).
