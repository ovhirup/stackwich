# 🥪 Stackwich (Codex Edition)

**Delivery discipline for ChatGPT/Codex.**  
Plan → Execute → Verify → Review — as standing policy.

This is the Codex-native version of [Stackwich](https://github.com/ovhirup/stackwich).

---

## What it does

Stackwich installs five layers into Codex sessions:

1. **Prompt** — meta-prompt every delegation; never hand off understanding
2. **Context** — keep noisy research in subagent threads
3. **Harness** — one writer, and nothing is "done" without observed output
4. **Loop** — schedule recurring work; failure cycles are capped, never silent
5. **Graph** — PLAN → EXECUTE → VERIFY → REVIEW for anything risky

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

> **Moving from an older install?** Codex discovers skills under `.agents/skills` — at the
> repo root, at `$HOME`, or system-wide in `/etc/codex/skills`. Earlier versions used
> `$CODEX_HOME/skills`, usually `~/.codex/skills`; that location is no longer in OpenAI's
> documented discovery list, so move any copy living there to the path above.

Then ask Codex to install Stackwich. The skill asks for scope (user or project), writes the
policy block to `AGENTS.md` between `<!-- stackwich-codex:v1 -->` markers, and offers to
scaffold `advisor`, `executor`, and `verifier` as TOML agents.

> **Why a different marker?** The Codex port writes to `AGENTS.md` and shipped with
> `<!-- stackwich-codex:v1 -->`. A marker is never renamed after release — a new version that
> searched for a different string could not find existing installs to upgrade, and would
> insert a duplicate block.

> **Port status:** at parity with the Claude Code parent's five-layer policy, as
> `stackwich-codex-rev 1`. The port tracks the parent's layer structure, not its revision
> number — a parent bump does not automatically oblige a port bump.

---

Built by **Abhirup Banerjee** ([@ovhirup](https://github.com/ovhirup)).
Part of [Stackwich](https://github.com/ovhirup/stackwich) — MIT, see [LICENSE](LICENSE).
