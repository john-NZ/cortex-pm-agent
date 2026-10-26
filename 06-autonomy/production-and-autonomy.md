# Production & Autonomy: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 5, how you'd ship it, govern it, and widen trust over time
>
> ✅ **What this validates:** you can ship it, govern it, and widen trust deliberately, by the end you'll have proven an autonomy dial, a Trust Ladder rung with its eval gate, and a governance plan.

## Autonomy Dial by segment

_Autonomy is a product decision per user, not one global setting._

| Segment | Desired autonomy | Why |
|---|---|---|
| **John, the PM who built Cortex** | **Supervised** | The right balance between (1) fully trusting that the correct sources were chosen, since even the critic could miss something, and (2) having too much oversight of Cortex, when the whole point is to free up my time. |
| **Other seasoned PMs in the company, new to Cortex** | **Shadow → assisted → supervised** | They didn't build Cortex, so they don't know how it works. I want them to build confidence at their own pace, and starting in shadow makes it safe, so they'll try it. They can move quickly to assisted, depending on their confidence, and eventually to supervised. |
| **A new PM (just joined the company)** | **Shadow, for longer than a seasoned PM.** An experienced PM new to the company gets plain shadow. A junior PM just starting out gets shadow, with each comparison reviewed with a mentor PM. | The same reasons as for seasoned PMs, but without the company's domain knowledge they can't yet tell a wrong fact from a right one. A junior PM might copy Cortex's draft without being able to judge it, so a mentor reviews the comparison. |

The product lead who requests the update is a reader, not an operator, so they don't get a segment of their own.

The dial sets how much each segment reviews. It doesn't move the M1 agent line: **posting stays above the line for everyone**, and no segment has Cortex post (M5 bound 5). The rules for moving up a rung are set in the widen-autonomy rule below.

## Trust Ladder

**Current rung: shadow.** "Cortex needs very close watching while it's new, like any product in alpha. Supervised comes only after Cortex shows it can follow the rules, and I'd rather spend time in shadow than risk going to supervised too early." It has only run on the course fixtures so far, and no real update has been drafted or posted from it.

**Next rung: supervised.**

**Eval gate (to reach supervised):** after **one month, at least 30 shadow runs** (one a day, including hook runs), measured against these thresholds. "This is more realistic than 30 perfect runs… only if we meet these would I consider moving to supervised."

| Measure | Source (M5) | Threshold |
|---|---|---|
| Follows the rules | Critic checks 3, 4, 5 + EV-5 | **0 violations.** One resets the window. |
| Factual drafts | Critic checks 1, 2 | **≥ 90%** pass on the first try |
| Useful drafts | Shadow comparison with John's own update | **≥ 80%** John would have posted with minor edits |
| Stays bounded | Bound trips (8 turns, 15 calls, 180 s, cost) | Every trip escalated, **no runaway** |
| No regressions | Replay set R1–R5 | **All 5 pass** at the end of the month |

**Incident record so far:** no real incidents, because Cortex hasn't run on real data. In tests, it refused the jailbreak and the hidden sabotage, the critic caught the invented 47%, and every bound trip escalated with nothing posted. Known defects: the escalation banners say "validator-approved" when nothing was drafted, the critic sometimes puts reason text in `failed_checks`, and the login-expired error is unclear.

**What counts as a trust incident in the window:** a rule break that gets past the critic, or a draft John would have been embarrassed to post: "a poorly worded post, or a suggested post that references old data." **Any trust incident resets the window.**

## Deployment plan

**Runtime: phased.**
- **Shadow:** John's laptop, with Windows Task Scheduler running it at 7am on John's Claude login. "In the shadow stage I wouldn't run this while on vacation or expect anyone else to run it."
- **Supervised:** **the company's managed deploy platform**. A scheduled serverless function runs the 7am cron, and an endpoint takes the escalation-channel hook. This needs an organisation Claude credential, approved by the company's AI administrator, because a server can't use a personal login. Moving to it is part of the step to supervised.

**Operator / on-call:**

| Problem | Shadow | Supervised |
|---|---|---|
| Cortex escalates (stuck, bound trip, jailbreak) | John | John |
| Cortex is down or broken | John (it simply doesn't run that day) | John; **backup: engineering team lead** |
| Platform outage | n/a | Platform team |
| Security (injection, suspected leak) | John → the security team | John → the security team |

The engineering team lead takes over only once Cortex has reached supervised.

**Rollback (in order):**
1. **Kill file:** create `CORTEX_KILL`, and Cortex halts at the next check. Discard the queued draft and stories.
2. **Disable a tool:** take a source returning bad data out of the tool list, and the update is marked UNVERIFIED. "A broken tool may just be temporary anyway, so reverting the version may not be required."
3. **Revert the version:** `git revert` the PR that made Cortex worse.
4. **Drop the dial a rung:** after a trust incident, that segment goes supervised → shadow and the 30-run gate restarts.

**Monitoring:**

| Signal | Source | Alert when |
|---|---|---|
| Eval pass % (critic, first try) | `critic-log.jsonl` | Below 90% |
| Escalation rate | Run output | Above **20%** of runs in a week (to begin with) |
| Cost-to-serve | `total_cost_usd` per run | The daily $1.50 cap trips, or the average goes over $0.30 per run |
| Trust incidents | John's shadow comparison notes | Any one, which resets the window |

**Where:** in shadow, John reviews the logs weekly. In supervised, a monitoring dashboard with alerts, so the backup on-call has something to watch.

**Vacation test:** at supervised, the engineering team lead has the rollback ladder, the dashboard and the escalation paths, so they could run Cortex from this page.

## ROI metrics (beyond adoption & tokens)

| Metric | How measured | Target |
|---|---|---|
| **Outcome: time per weekly update** (leadership update + next-sprint story proposals) | During shadow, John logs his time writing by hand vs his time reviewing Cortex's draft | **From about 2 hours by hand to 30 minutes of review (−75%)** |
| **Outcome (secondary): story acceptance rate** | Share of Cortex's queued stories that survive sprint planning | **≥ 50%.** "Story planning is tough! But if 50% get through, that would be amazing." |
| **Cost-to-serve** | `total_cost_usd` per run (SDK estimate) | **Under $0.30 per run** (≈ $0.17 today). John's time is counted in the outcome metric. |
| **Trust incidents** | John's shadow comparison notes (Trust Ladder definition) | **0 per month.** Any one resets the gate window. |

## Widen-autonomy decision rule

A segment moves up one rung only when (1) its runs meet the Trust Ladder thresholds with zero trust incidents over the required window, (2) the PM agrees they're ready, so no one is pushed up a rung, and (3) the new rung is never above John's own.

| Move | Required window |
|---|---|
| John: shadow → supervised | 30 runs in a month (the Trust Ladder gate) |
| Seasoned PM: shadow → assisted | 10 clean runs, because Cortex is already proven with John |
| Seasoned PM: assisted → supervised | 30 runs, the same gate John met |
| New PM: shadow → assisted | 20 clean runs, double a seasoned PM's; a junior PM also needs mentor sign-off |

## Governance & forward strategy

- **Compliance:** never in a prompt: customer and clinic names, pet-owner and patient data (PII), credentials and tokens, and anything marked CONFIDENTIAL or embargoed. Sources are filtered **at the tool, before the prompt**. For example, the roadmap tool strips Orbit and Pulsar, so Cortex never sees them. Critic check 4 stays as a second layer on the output. Logs are kept for 90 days (the org retention policy). Cortex runs under the company's Claude Team plan terms.
- **Safety:** above the line for every segment, at every rung: posting or sending any update, committing a ship/GA/launch date, marking launch gates or closing/creating/merging tickets, creating stories in the tracker (Cortex only queues them, capped at 10), and changing its own rules or permissions. "I wouldn't let anything below the line." **Kill switch:** the `CORTEX_KILL` file today, owned by John. The infrastructure off-switch is added before Cortex is ever given posting access.
- **Reliability:** caps of 8 turns, 15 tool calls, 180 s, $0.50 per run / $1.50 per day, 10 stories, and data age 90 days stop / 7 days STALE. Escalate on stuck (M2 rules a–d), never invent a figure. **Model down:** notify and stop. Cortex sends a clear "Cortex couldn't run: <reason>" message, and John writes the update by hand or re-runs it later. No automatic retry, and no fallback to an untested model.
- **Strategy:**
  1. **Real data:** read-only Jira, GitHub and Slack connectors, filtered at the tool. Gated by replay set R1–R5 passing on real data, plus a clean 30-run shadow window on real data.
  2. **Then seasoned PMs,** in shadow on their own projects, once John is at supervised on real data. Then the widen rule applies.
  3. **JIT posting** (the M5 widening step) stays a *later* option. It needs its own gate, and the approval decision stays with John.
