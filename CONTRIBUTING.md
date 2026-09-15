# Contributing

Issues and pull requests are welcome. This file exists because the repo has five rules that
aren't obvious from reading the code, and each one has already caused a real bug.

`.github/workflows/validate.yml` enforces all of them. If CI fails on your PR, it is probably
one of these.

## 1. Markers are never renamed

`<!-- stackwich:v1 -->` is a permanent search key, not a version number. A release that
searched for a different string could not find existing installs to upgrade — it would append
a second policy block beside the old one instead of replacing it.

The `v1` is frozen forever. The actual revision lives on a `policy-rev` comment **inside** the
block.

## 2. Each port keeps the marker it shipped with

`grok/` reuses `stackwich:v1`. `codex/` uses `stackwich-codex:v1`. They differ because Codex
shipped first with its own marker, and rule 1 applies to it too.

Ports also carry their own counters — `stackwich-grok-rev`, `stackwich-codex-rev` — starting at
1. A port tracks the parent's **layer structure**, not its revision number. Bumping the parent
does not oblige a port bump.

## 3. The plugin never ships an `agents/` directory

Plugin-supplied agents install namespaced, as `stackwich:advisor`. The policy block refers to
`advisor`, `executor` and `verifier` by bare name, so shipping them in the plugin would break
every reference, remove the user's ability to decline scaffolding, and make rename-on-collision
impossible — a file in the plugin cache is overwritten on update.

The skill scaffolds them from `assets/` instead. CI fails if `plugins/stackwich/agents/` appears.

## 4. Marker checks in CI match whole lines on purpose

These files **document their own syntax**. `SKILL.md` contains the sentence "search for the
opening marker `<!-- stackwich:v1 -->`" as prose, next to the real marker.

A substring check is satisfied by the documentation instead of the thing it documents. That is
not hypothetical: a release once shipped with its opening marker destroyed, and CI passed,
because the grep matched the prose. Every marker and revision assertion is an exact whole-line
count. Do not relax them to `grep -q`.

## 5. `SKILL.md` and `assets/` move together

`SKILL.md` resolves the agent definitions relative to its own directory. Separating them
silently breaks scaffolding for every user, and nothing outside the assets check would notice.

## Running the checks locally

```bash
python3 -m pip install pyyaml
```

Then run the steps in `.github/workflows/validate.yml`. There is no separate test command — the
workflow is the test suite.

## Versioning

One version for the repo, declared in `plugins/stackwich/.claude-plugin/plugin.json` and the
skill's frontmatter. CI asserts they agree and that `CHANGELOG.md` has a matching heading.

`policy-rev` is separate and only moves when the policy block's content changes.
