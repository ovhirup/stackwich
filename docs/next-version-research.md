# Stackwich: research and next-version enhancement brief

Research date: 30 October 2026 (UTC)
Status: research and proposed backlog; no product changes implemented
Baseline: `ovhirup/stackwich` main, v3.2.0, commit `60543eeec74b9aa842f2aadd35f90f3a86c00241` (15 October 2026)

## Start here

Stackwich's strongest opportunity is to make disciplined AI delivery easy to adopt and demonstrably reliable. Prioritize executable verification, evidence of better outcomes, and a simpler first experience. Preserve the lightweight policy, explicit handoffs, bounded retries, and model tiering.

Suggested positioning:

> Stackwich helps AI coding agents finish with verified results, bounded retries, and reviewable evidence—inside your existing workflow.

The five-layer taxonomy remains useful architecture documentation. Lead onboarding and promotion with user outcomes.

The priority ratings below are research judgments, not measured adoption forecasts. Assign the next version number only after its scope is agreed; this brief does not assume that every recommendation belongs in one release.

## Scope and limitations

Reviewed the public repository's README, changelog, policy, agent assets, Codex documentation, measured-layer code, schema and tests, CI, eval scenarios, recent commits, branches, releases, and issue/PR history. Also reviewed the older `abhirup-artizent/stackwich` copy, the public Dynamic LLM Router verification documentation, competitor repositories, and the archived Stackwich showcase source and factual notes in connected Google Drive.

Broader web search repeatedly returned errors. This is a primary-source comparison, not an exhaustive survey of community sentiment. Competitor capability descriptions come from their documentation, not comparative execution tests. Unpublished local changes were unavailable. The website assessment uses an October 19 source archive, not a verified current live deployment.

Research inspected the latest public main at the time. Recheck main, tags, Releases, documentation, and competitor capabilities before implementation. Findings may have changed since the research date.

## Comparative assessment

| Project | Documented strengths | Implication for Stackwich |
|---|---|---|
| Superpowers | Composable development skills, design clarification, TDD, review, broad coding-tool support, behavioral eval infrastructure | Plan–execute–verify–review alone is insufficient differentiation. Emphasize bounded overhead and traceable evidence. |
| GSD Core | Fresh-context execution, durable state artifacts, guided onboarding, discuss-to-ship workflow across tools | Improve recovery across sessions and the first successful task. Avoid competing on breadth immediately. |
| BMAD Method | Product, architecture, development, and testing perspectives; process depth adapted to the task | Serve users who want delivery controls without adopting a comprehensive methodology. |
| Spec Kit | Structured specifications, reusable processes, verification artifacts, integrations, customization | Accept existing plans and specifications rather than requiring a separate planning system. |
| Dynamic LLM Router (your project) | Optional Stackwich report validation, scope and retry checks, independent configured tests before commits | Reuse and demonstrate an existing integration. Do not treat it as an unbuilt feature. |

GSD discovery note: `gsd-build/get-shit-done` redirected readers to `open-gsd/gsd-core` during this research; use the current project when refreshing the comparison.

## Most significant enhancements

| ID | Enhancement | Concrete scope | User value | Traction potential |
|---|---|---|---|---|
| H1 | Executable verification | Optional runner or supported runtime integration validating transitions, scope, retry ceilings, and evidence; bind results to the tested revision/diff; reuse Router protocol where practical | Very high | High |
| H2 | Reproducible outcome comparisons | Compare plain agent, policy-only Stackwich, and executable-gated Stackwich on identical tasks; publish failures and overhead | Very high | Very high |
| H3 | First successful task in minutes | Guided installation diagnostics, small demo repository, visible fail/correct/pass sequence, safe uninstall and recovery | High | Very high |
| H4 | User-visible acceptance checks | Optional browser-flow, responsive-layout, accessibility, API, and authentication recipes; clearly state coverage and unchecked areas | Very high for vibe coders | High |
| H5 | Runnable behavior evals | Execute installation fixtures and agent scenarios; test skipped verification, scope violations, missing contracts, and retry exhaustion | Very high | High through credibility |
| H6 | Discovery and release consistency | Link existing showcase, publish current release notes, establish canonical repository and flag older installation instructions | High | High; relatively low effort |

### H1: distinguish policy from enforced boundaries

The Claude advisor and verifier both have Bash. Their restrictions are expressed in instructions; the agent files do not themselves impose a filesystem boundary. Tests and builds can legitimately write generated artifacts. Specify what is protected: product source, external state, credentials, or all filesystem writes. Document each runtime's actual guarantees.

Router already validates reports, planned/changed/actual product paths, attempts, configured test results, and evidence stability around tests. Its documentation correctly says in-session stages are not independent model review. Preserve that distinction in product claims.

Proposed acceptance criteria:

- Each supported execution mode documents which checks are mechanical and which depend on model compliance.
- Verification evidence identifies the exact product revision or diff tested.
- Product changes after verification invalidate the prior verdict.
- Scope violations, missing evidence, and exhausted retries cannot produce a successful completion status.
- Test/build output directories can be permitted without granting arbitrary product-source edits.
- Unsupported runtimes are explicitly identified rather than silently claiming equivalent enforcement.

### H2: measure outcomes rather than architecture

The archived showcase describes Scrum Master usage and explicitly says Stackwich was not used in developers' code generation. That experience is valuable but does not establish coding-task improvements. Validate coding-community claims separately.

Benchmark task families: bug fixes, UI changes, migrations, and unfamiliar repositories. Hold task inputs and evaluation criteria constant; record model/runtime versions and configuration; repeat runs where practical and disclose sample sizes.

Report accepted-task completion, regressions, human intervention, review time, elapsed time, retries, and observed cost where available. Include overhead for simple tasks. Do not infer cost savings from cheaper executor tiers alone.

### H3 and H6: use the showcase you already have

The archived website already includes an interactive workflow, a model picker, build status, and Router explanation. Improve discoverability and consistency before building a replacement. At research time, public GitHub Releases stopped at v3.0.0 while main contained v3.2.0. The older `abhirup-artizent` copy still documented clone-based installation.

Proposed acceptance criteria:

- README points to the showcase and one canonical installation guide.
- Current release notes explain changes, upgrade requirements, and policy/port revisions.
- Older copies clearly identify their status and link to current instructions.
- A new user can install, confirm the active policy and agents, complete one verified task, and uninstall using documented steps.

### H5: test behavior, not just package structure

The seven cases in `evals/evals.json` are scenario specifications. Reviewed CI checks package structure, manifests, YAML, markers, and revision agreement; it does not execute those seven agent-behavior scenarios or the measured-layer test suite.

Convert the installation cases into fixtures with observable filesystem assertions. Add runtime behavior checks separately; model-dependent evals should publish their environment and avoid claiming universal guarantees from a single passing run.

## Medium significance enhancements

| ID | Enhancement | Recommended scope and rationale |
|---|---|---|
| M1 | Adaptive model selection | Start with configurable role mappings and escalation based on observed failures. Optimize total cost per accepted task, including retries and planning. Savings remain unproven until measured. |
| M2 | Durable session recovery | Save plan, tested revision, stage, failure count, and unresolved decisions. Check repository changes before resuming. |
| M3 | Workflow interoperability | Accept existing Markdown plans/specifications; document instruction precedence and conflicts beside other tools. |
| M4 | Correct and automate measurement | Capture supported runtime events; distinguish event history from current state, and estimates from observations. |
| M5 | Separate solo and team profiles | Keep individual use lightweight. Make four-person approval optional; strengthen identity and evidence before enterprise assurance claims. |
| M6 | Selective platform expansion | Prioritize adapters requested by active users. Publish a capability matrix and run a conformance suite per runtime. |

The small M4 defects below warrant an early maintenance fix even though broader analytics investment ranks medium.

## Reproduced findings in the measured layer

### R1: resolved human gate remains pending in aggregate

Input: two `gate.human` events with the same `work_id` and `gate`, first `pending`, then `approve`.

Observed summary:

```json
{"approve":1,"reject":0,"pending":1}
```

`report.py` counts events, not the latest gate state. If the report describes current state, use a stable gate identity and select its latest decision. If it describes history, label attempt/event counts separately.

Proposed acceptance: a gate transitioning pending → approve contributes one currently approved gate and zero currently pending gates; event history remains available separately.

### R2: updated iteration item counts as two commitments

Input: two `iteration.item` events with the same `work_id` and `item_id`, both committed; first `done=false`, then `done=true`.

Observed summary:

```json
{"committed":2,"done":1,"carryover":1}
```

Proposed acceptance: current-state reporting counts one committed item, one done item, and zero carryover items. Define the reporting period and update semantics before implementation.

### R3: approval is a local workflow check, not authenticated separation of duties

`approve.py` compares caller-supplied planner/writer/verifier/approver strings, stores a local ledger, and writes `applied.txt` on execute. It does not authenticate distinct people, bind approval to an immutable patch, or apply the actual product diff.

Action: document this boundary clearly. If stronger team assurance is required, add authenticated identity, approval bound to an exact change, and protected execution. Do not describe the current local mechanism as independent proof of four distinct human participants.

### Verification performed

Using temporary local copies of the reviewed files:

```bash
python3 measured/test_measured.py
python3 measured/approve.py --self-check
python3 measured/report.py --log measured/examples/sprint.jsonl
```

Results: five tests passed; self-check printed `SOD: PASS`; example report rendered successfully. The demo's 3.5 estimated hours returned and 50% verification rate are example data, not evidence of production benefit. R1 and R2 were reproduced separately with small in-memory event sequences. No benchmark of live coding agents was run.

## Low significance: defer unless demand changes

| ID | Enhancement | Why defer |
|---|---|---|
| L1 | Hosted analytics dashboard | Reliable capture and metric definitions should come first. |
| L2 | Large agent-role catalog | Coordination overhead precedes demonstrated benefit. |
| L3 | Full Jira/Azure DevOps synchronization | Potential team value, but substantial maintenance and limited immediate benefit for individuals. |
| L4 | Major visual redesign or more taxonomy | An interactive showcase already exists. Improve examples, evidence, and links first. |
| L5 | Ports without active demand | More reach helps only when installation and verification remain dependable. |

## Suggested release sequence

1. Maintenance and clarity: fix R1/R2, document R3 and enforcement boundaries, publish current release notes, and connect the existing showcase.
2. Activation and assurance: demo repository, install diagnostics, runnable installation fixtures, behavioral eval harness, and meaningful CI coverage.
3. Verified execution and evidence: reuse the Router contract, bind results to exact changes, publish outcome comparisons, and add browser acceptance recipes.
4. Expand from usage: adaptive routing, session recovery, integrations, and additional platforms based on observed user needs.

Treat this as sequencing, not a commitment to a particular version number or calendar. Keep changes reviewable and separately releasable.

## Success measures

- Installation-to-first-verified-task conversion.
- Repeat usage over a stated period.
- Accepted-task completion and regressions.
- Human intervention and review time.
- Verification overhead and total cost per accepted task where cost is observable.
- Installation failures and abandonment reasons.

Stars and agent counts are secondary discovery/activity signals, not evidence of delivery value. If collecting usage data, make its scope explicit and preserve the project's local-first expectations.

## Source index

Baseline sources are pinned where possible; comparator links are live and should be refreshed.

- [Stackwich baseline tree](https://github.com/ovhirup/stackwich/tree/60543eeec74b9aa842f2aadd35f90f3a86c00241)
- [README](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/README.md)
- [Changelog](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/CHANGELOG.md)
- [Installed-policy source and installer instructions](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/plugins/stackwich/skills/stackwich/SKILL.md)
- [Advisor](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/plugins/stackwich/skills/stackwich/assets/advisor.md)
- [Executor](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/plugins/stackwich/skills/stackwich/assets/executor.md)
- [Verifier](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/plugins/stackwich/skills/stackwich/assets/verifier.md)
- [Behavior scenarios](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/evals/evals.json)
- [CI workflow](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/.github/workflows/validate.yml)
- [Measured reports](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/measured/report.py)
- [Approval tool](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/measured/approve.py)
- [Measured-layer design note](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/docs/teams-layer.md)
- [Codex documentation](https://github.com/ovhirup/stackwich/blob/60543eeec74b9aa842f2aadd35f90f3a86c00241/codex/README.md)
- [GitHub Releases](https://github.com/ovhirup/stackwich/releases)
- [Older repository copy](https://github.com/abhirup-artizent/stackwich)
- [Dynamic LLM Router verification contract](https://github.com/ovhirup/dynamic-llm-router#optional-stackwich-verification)
- [Superpowers](https://github.com/obra/superpowers)
- [GSD Core](https://github.com/open-gsd/gsd-core)
- [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD)
- [Spec Kit](https://github.com/github/spec-kit)

## Handoff prompt for an implementation session

> Read `docs/next-version-research.md`, then inspect the current Stackwich repository and its contribution instructions. Revalidate the baseline and the reproduced findings before editing. Start with R1/R2 reporting semantics and the maintenance items in release sequence step 1. Preserve unrelated behavior, agree on current-state versus event-history metrics, and add focused regression coverage. Reuse existing Router functionality where appropriate. Do not claim model-independent enforcement or production benefits without supporting evidence. Keep the proposed changes small and reviewable; report what changed and what was verified.
