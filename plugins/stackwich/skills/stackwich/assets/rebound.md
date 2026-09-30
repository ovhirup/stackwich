# Rebound check

Read this when the user asks about agent cost, token budgets, loops that run too long, how many
parallel agents to run, or whether more automation will actually save effort. It is reference
material for that conversation, not policy: nothing here is written into CLAUDE.md.

## The pattern
Making a unit of work cheaper tends to increase how many units get used. When demand is elastic
enough, total consumption rises even though each unit costs less — Jevons' observation about
coal in 1865, later formalized as the Khazzoom–Brookes postulate. The literature's consistent
remedy is to pair each efficiency with something that caps volume. Stackwich's policy does this
with run ceilings on loops, a stated shard count, and delegations sized to what can be reviewed.

## Four rebound types, in agent terms
| Type | Economics meaning | Agent example |
|---|---|---|
| Direct | More use of the thing that got cheaper | A cheap executor tier leads to more delegations; a loop that costs nothing to start gets started for everything |
| Indirect | Savings spent on other resource-using things | Time saved by fast generation goes into refactors nobody asked for; faster diffs land on a reviewer who did not get faster |
| Economy-wide | Efficiency raises output, which raises aggregate demand | A user-level install makes agent work frictionless on every project, so total spend rises while per-task spend falls |
| Backfire | Rebound over 100%: absolute use goes up | Parallel fan-out — Anthropic measured multi-agent systems at roughly 15x the tokens of chat — and continuous heavy Claude Code use that led to weekly rate limits |

## Four questions
Ask these of any change that makes something cheaper, faster, or automatic — a cache, loop,
cron, parallelism, a cheaper model, code generation, autoscaling:
1. **What gets cheaper?** Name the unit: a run, a delegation, a token, a request, a diff.
2. **Who uses more of it?** The agent itself, the user, downstream callers, the reviewer.
3. **What's the cap?** A run ceiling, a shard count, a batch size, a rate limit, a budget someone
   actually enforces. With no cap, the efficiency is open-ended.
4. **What metric shows it?** Something observable: run count, delegation count, review queue
   length, token or cost figures where the environment exposes them. Never report a figure you
   did not see.

## For teams: capacity against demand
When AI raises throughput, check whether three things rose with it:
- **Intake.** Did the backlog grow because more now looks cheap to attempt?
- **Review and QA.** Generation got cheaper; verification did not. If review is the constraint,
  more generation only lengthens the queue. In METR's 2025 trial, experienced developers were
  19% slower with AI tools while believing they were faster.
- **Spend.** Token, compute, or cloud spend in total, not per task.

If any of them rose faster than delivered value, the efficiency is being spent as volume.

## Sources
- W. S. Jevons, *The Coal Question* (1865). Overview: https://en.wikipedia.org/wiki/Jevons_paradox
- H. Saunders, "The Khazzoom-Brookes Postulate and Neoclassical Growth," *The Energy Journal* 13(4), 1992.
- L. Greening, D. Greene, C. Difiglio, "Energy efficiency and consumption — the rebound effect — a survey," *Energy Policy* 28, 2000.
- S. Sorrell, "Jevons' Paradox revisited: The evidence for backfire from improved energy efficiency," *Energy Policy* 37(4), 2009. https://ideas.repec.org/a/eee/enepol/v37y2009i4p1456-1469.html
- UKERC, *The Rebound Effect* (Sorrell, 2007). https://ukerc.ac.uk/project/the-rebound-effect-report/
- K. Gillingham, M. Kotchen, D. Rapson, G. Wagner, "The rebound effect is overplayed," *Nature* 493, 2013.
- Anthropic, "How we built our multi-agent research system" (June 2025). https://www.anthropic.com/engineering/multi-agent-research-system
- TechCrunch, "Anthropic unveils new rate limits to curb Claude Code power users" (28 Jul 2025). https://techcrunch.com/2025/07/28/anthropic-unveils-new-rate-limits-to-curb-claude-code-power-users/
- METR, early-2025 experienced open-source developer study (July 2025). https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ — the Feb 2026 follow-up was inconclusive: https://metr.org/blog/2026-02-24-uplift-update/
