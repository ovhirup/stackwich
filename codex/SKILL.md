---
name: stackwich-codex
description: "Install the Stackwich Codex delegation architecture: context-rich delegation, a plan-execute-verify-review sandwich for risky work, scheduled automation for recurring work, and subagent-based context engineering. Write durable policy to AGENTS.md and optionally scaffold advisor, executor, and verifier custom agents. Use when the user asks to adopt, install, convert, or bootstrap Stackwich or Stackwich Codex for a ChatGPT/Codex user account, repository, or team setup."
author: Abhirup Banerjee (@ovhirup)
---

# Stackwich Codex

Install five layers of delivery discipline: **Prompt** (meta-prompt every delegation),
**Context** (move noisy independent research into subagent threads), **Harness** (one writer,
and nothing done on the strength of intent), **Loop** (schedule recurring work, and cap failure
cycles), and **Graph** (plan, execute, verify, review for anything risky).

Created by **Abhirup Banerjee** ([@ovhirup](https://github.com/ovhirup)). Adapted for
ChatGPT/Codex from `ovhirup/stackwich` under the MIT License. Preserve this credit and the
bundled `LICENSE` when copying or distributing the skill.

## 1. Choose the scope

Ask only when the user has not made the scope clear:

- **User scope**: write policy to `$CODEX_HOME/AGENTS.md` and agents to
  `$CODEX_HOME/agents/`. Treat `~/.codex` as `CODEX_HOME` when it is unset.
- **Project scope**: write policy to the applicable repository-root `AGENTS.md` and agents
  to `<repo>/.codex/agents/`.

Suggest user scope for a standing personal habit and project scope for a shared repository
workflow. Resolve the repository root and `CODEX_HOME` before writing. Request approval for
writes outside the permitted workspace when the current environment requires it.

## 2. Load the exact templates

Read [references/templates.md](references/templates.md) completely before editing. Use its
policy block and agent definitions as the source of truth.

## 3. Inspect the existing setup

Search the target `AGENTS.md` for `<!-- stackwich-codex:v1 -->` and
`<!-- /stackwich-codex:v1 -->`.

- If both markers exist, show the installed block and ask whether to replace that block or
  leave it. Never duplicate it.
- If only one marker exists, stop and ask how to repair the malformed section.
- If neither exists, insert the block without altering unrelated instructions.
- If the file does not exist, create it with only the Stackwich block.

Keep more specific existing `AGENTS.md` instructions intact. Do not weaken permission,
sandbox, approval, security, or repository rules.

## 4. Offer the companion agents

Ask whether to scaffold `advisor`, `executor`, and `verifier`. Skip scaffolding when the user
already has equivalent agents and prefers to wire those roles into the policy.

Before writing, check the chosen agents directory and the other scope's agents directory for
matching `name` values. If a name belongs to an unrelated agent, ask for a replacement and
substitute it consistently in the policy block, filenames, TOML `name` values, descriptions,
and in-body references. Never overwrite an unrelated agent.

Write standalone TOML files from the templates to the chosen agents directory. Do not pin
model names: the templates use reasoning and sandbox settings so they remain portable across
accounts and future model catalogs.

## 5. Verify the installation

- Confirm there is exactly one opening marker and one closing marker in the target file.
- Parse every created agent TOML with Python's `tomllib` when Python 3.11+ is available.
- Inspect the resulting diff or changed paths and run `git diff --check` for project scope
  when the target is in a Git repository.
- Verify behavior or structure rather than re-reading a just-written file solely to confirm
  that the write occurred.

Fix validation failures before reporting success. Apply the two-strike rule to repeated
verification failures: after the same failure occurs twice, stop blind retries and report the
evidence.

## 6. Report the result

List every created or modified path. Explain that Stackwich Codex changes future working behavior;
it does not retroactively audit completed work. If custom agents were added, suggest opening
the app's Subagents view or using `/agent` in the CLI after starting a new task to confirm the
roles are available.
