# 🥪 Stackwich (Codex Edition)

**Delivery discipline for ChatGPT/Codex.**  
Plan → Execute → Verify → Review — as standing policy.

This is the Codex-native version of [Stackwich](https://github.com/ovhirup/stackwich).

---

## What it does

Stackwich installs four habits into Codex sessions:

1. **Meta-prompt every delegation** — never hand off understanding
2. **Sandwich risky work** — PLAN → EXECUTE → VERIFY → REVIEW
3. **Schedule recurring work** instead of re-running it by hand
4. **Context engineering** — keep noisy research in subagent threads

It also enforces the two-strike rule (same failure twice → stop and escalate), verification
by behavior rather than re-reading a just-written file, and no suffixed file copies as a
debugging strategy.

---

## Claude vs Codex version

| Aspect | Claude Code version | Codex edition |
|---|---|---|
| Policy location | `CLAUDE.md` | `AGENTS.md` (`$CODEX_HOME` or repo root) |
| Agent format | Markdown in `~/.claude/agents/` | TOML in `$CODEX_HOME/agents/` or `<repo>/.codex/agents/` |
| Model tiering | Named tiers (opus / haiku / sonnet) | No pinned models — reasoning and sandbox settings only, for portability across accounts |
| Block marker | `<!-- stackwich:v1 -->` | `<!-- stackwich-codex:v1 -->` |

Both versions share the same philosophy. The implementation is adapted to each platform.

---

## Install

Copy the whole directory. `SKILL.md` reads `references/templates.md` at install time, so
copying `SKILL.md` alone is not enough:

```bash
mkdir -p ~/.agents/skills/stackwich-codex
cp -R SKILL.md references agents LICENSE ~/.agents/skills/stackwich-codex/
```

> **Check your skills path first.** OpenAI's current docs put skill discovery at
> `~/.agents/skills`. Some setups use `~/.codex/skills`. Confirm against the docs for your
> Codex version and adjust the path above before copying.

Then ask Codex to install Stackwich. The skill asks for scope (user or project), writes the
policy block to `AGENTS.md` between `<!-- stackwich-codex:v1 -->` markers, and offers to
scaffold `advisor`, `executor`, and `verifier` as TOML agents.

> **Why a different marker?** The Codex port writes to `AGENTS.md` and shipped with
> `<!-- stackwich-codex:v1 -->`. A marker is never renamed after release — a new version that
> searched for a different string could not find existing installs to upgrade, and would
> insert a duplicate block.

> **Port status:** this port tracks the original four-habit framing. The Claude Code
> parent is at v2.1.0 (five layers: Prompt / Context / Harness / Loop / Graph).
> A parity pass is tracked separately.

---

Built by **Abhirup Banerjee** ([@ovhirup](https://github.com/ovhirup)).
Part of [Stackwich](https://github.com/ovhirup/stackwich) — MIT, see [LICENSE](LICENSE).
