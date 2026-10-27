# Cortex, a bounded PM chief-of-staff: one agent, one critic, a human at the end

> A PM chief-of-staff agent that gathers project data, drafts the weekly leadership status update and proposes next-sprint stories, checks its own work with an independent critic, and queues everything for the PM to approve, so the PM reviews in 30 minutes instead of writing for 2 hours, and nothing is posted without a person.

_John Wagner · Agentic Loops for PMs Cohort · October 2026_

Repo: https://github.com/john-NZ/cortex-pm-agent

This repo is my final project for the Agentic Loops for PMs Certification, **Cortex**. Each module’s artifact lives in its own folder; this README is the dashboard and the pitch.

---

## Module artifacts

### M1 · The Agent Line
- **Agent-line map**: [`01-agent-line/agent-line-map.md`](01-agent-line/agent-line-map.md)

### M2 · Loop Engineering
- **Loop spec**: [`02-loop-design/loop-spec.md`](02-loop-design/loop-spec.md)

### M3 · Orchestration &amp; Subagents
- **Orchestration map**: [`03-orchestration/orchestration-map.md`](03-orchestration/orchestration-map.md)

### M4 · Context Engineering &amp; Memory
- **Memory &amp; context plan**: [`04-memory-context/memory-and-context.md`](04-memory-context/memory-and-context.md)

### M5 · Bounds &amp; Evals
- **Bounds &amp; evals**: [`05-bounds-evals/bounds-and-evals.md`](05-bounds-evals/bounds-and-evals.md)

### M6 · Autonomy &amp; Production
- **Production &amp; autonomy plan**: [`06-autonomy/production-and-autonomy.md`](06-autonomy/production-and-autonomy.md)
- **Prototype write-up**: [`06-autonomy/prototype.md`](06-autonomy/prototype.md)

---

## Ship plan

### Autonomy dial (per segment)
- John (built Cortex) → Supervised. The balance between trusting that Cortex chose the right sources (even the critic can miss something) and over-checking it, when the point is to free up my time.
- Seasoned PMs new to Cortex → Shadow → Assisted → Supervised, at their own pace. They didn't build it, so shadow makes it safe to try.
- New PM → Shadow, for longer. A junior PM also reviews each shadow comparison with a mentor PM, because they can't yet tell a wrong fact from a right one.
- For every segment, posting stays above the line: Cortex drafts and queues, a person posts.

### Trust Ladder rung + eval gate
Current rung: Shadow. Cortex has only run on course fixtures; like any alpha product it needs close watching first.
Eval gate to climb to Supervised: at least 30 shadow runs over one month, with:
- 0 rule violations (no commitments, no confidential leak, nothing posted)
- ≥ 90% of drafts pass the critic's factual checks on the first try
- ≥ 80% of drafts I'd have posted with only minor edits
- every bound trip escalated, no runaway loop
- all 5 replay evals (R1–R5) pass at the end of the month
Trust incident = a rule break that gets past the critic, a poorly worded draft, or one that cites old data. Any one resets the 30-run window.
Clean record so far: in tests Cortex refused a jailbreak and hidden sabotage in its own prompt, the critic caught an invented metric, and every bound trip escalated with nothing posted.

### Deployment plan
- Runtime, phased: in shadow, my laptop runs Cortex at 7am on my own Claude login (not while I'm on vacation). At supervised, it moves to the company's managed deploy platform: a scheduled serverless function for the 7am run and an endpoint for the escalation-channel hook, on an organisation credential approved by the company's AI administrator.
- On-call: I handle every escalation (stuck, bound trip, jailbreak). From supervised, the engineering team lead is backup if Cortex is down; the platform team owns platform outages; suspected leaks go to the security team.
- Rollback, in order: (1) kill file, Cortex halts and the queued draft is discarded; (2) disable the tool returning bad data, the update is marked UNVERIFIED; (3) revert the version; (4) drop that segment a rung and restart the 30-run gate.
- Monitoring: critic first-try pass % (alert below 90%), escalation rate (alert above 20% of a week's runs), cost-to-serve (alert if the $1.50 daily cap trips or the average passes $0.30/run), trust incidents (any one). In shadow I review logs weekly; at supervised a monitoring dashboard gives the backup on-call something to watch.

### ROI metrics + widen-autonomy rule
- Outcome: time per weekly update (leadership update + story proposals), from about 2 hours by hand to 30 minutes of review (-75%), logged during shadow.
- Outcome (secondary): at least 50% of Cortex's queued stories survive sprint planning.
- Cost-to-serve: under $0.30 per run (about $0.17 today, SDK estimate); my review time is counted in the outcome metric.
- Trust incidents: 0 per month; any one resets the gate window.
Widen rule: a segment moves up one rung only when its runs meet the Trust Ladder thresholds with zero trust incidents over the window, the PM agrees they're ready, and the new rung is never above mine. Windows: me shadow → supervised = 30 runs in a month; seasoned PM shadow → assisted = 10 clean runs, assisted → supervised = 30; new PM shadow → assisted = 20 clean runs (a junior PM also needs mentor sign-off).

### Governance &amp; strategy
- Compliance: customer and clinic names, patient and pet-owner data, credentials, and anything CONFIDENTIAL or embargoed never enter a prompt. Sources are filtered at the tool, before the prompt (the roadmap tool strips embargoed projects); critic check 4 is a second layer on the output. Logs kept 90 days, per the org retention policy.
- Safety: above the line for every segment at every rung: posting or sending, committing ship/launch dates, changing tickets, creating stories in the tracker (Cortex only queues them, max 10), and changing its own rules. Kill switch: a kill file today; an infrastructure off-switch before Cortex is ever given posting access.
- Reliability: caps of 8 turns, 15 tool calls, 180 s, $0.50/run and $1.50/day, 10 stories, data age 90-day stop / 7-day STALE warning. On stuck, escalate; never invent a figure. Model down: notify and stop with a clear "Cortex couldn't run" message; no automatic retry, no fallback to an untested model.
- Strategy: (1) real data through read-only Jira, GitHub and Slack connectors, filtered at the tool, once R1–R5 pass and a clean 30-run shadow window runs on real data; (2) then seasoned PMs in shadow on their own projects; (3) just-in-time posting stays a later option with its own gate, and the approval stays with me.

---

## Build insights

- **Friction point.** Getting the course material in: the lab pages couldn't be read by the tools, so each one was pasted in as HTML. And two bounds interacted: with 8 turns, the turn cap tripped before the 2-revision cap, so the critic-rejection demo needed 12 turns.
- **Key learning.** A bound lives outside the model: a rule in the prompt isn't a bound, but a turn counter, a cost cap, a missing credential or a kill file is. Cortex didn't post because it couldn't.
- **Aha moment.** I planted a fault in Cortex's own system prompt (a made-up 47% metric and a firm GA date), and Cortex refused it and told me. It gave me more confidence, not less: next time I'll test my agent with bad instructions in its own configuration, not just in user input.

---

_Certification submission, Agentic Loops for PMs Certification._
