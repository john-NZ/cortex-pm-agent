# Loop Spec: Cortex PM Chief-of-Staff Agent

> Module 2 · Loop Engineering, ★ Deliverable 2
>
> ✅ **What this validates:** the agent knows when to run and when to stop, by the end you'll have proven a one-page Loop Spec with a trigger, a definition of "done," and explicit stop conditions.
>
> Your one-page blueprint for how the work you handed to the agent (M1) actually *runs*.
> An agent is just a prompt that fires itself, this spec says when it fires, what "done" means, and what it needs to do the job. Living document; refine as the course progresses.

## 1. Trigger & loop type

**Chosen type:** **cron (primary) + hook (secondary)**

- **Cron: a 7am daily sweep (my local time).** Checks the status of important Jira tickets, scans overnight email for anything that needs answering, and reviews overnight monitoring alerts. *"It's the regular 7am sweep that matters to me."*
- **Hook: a post in one of a small number of escalation channels** (Slack or Teams). It triggers an immediate triage run for real-time issues. *"I expect escalations to be an exception, not the rule."*

**Ruled out:**
- **Heartbeat:** "Too noisy for me. A good day is no issues and I actually made progress on planned work."
- **Goal:** "Goals for product managers can be ambiguous and can change. I want my agent to help me with inbound tasks and issues, not tell me when a goal has been met."

**Idempotency:** Cortex records the **message ID** of every escalation post it has handled and skips any it has already seen. This depends on managing memory well (see §4 State). **Planned iteration:** also skip issues the 7am sweep already raised, so the hook and the sweep don't double up. That rule will need iterating to get right.

## 2. Goal / definition of done

**Outcome this loop owns:** each run (the 7am sweep or an escalation hook) turns inbound tasks and issues into a triaged, prioritised picture for me.

**Done when** Cortex has identified the key areas to focus on, triaged them by importance, and produced a three-part report:
1. **What it did on its own:** each action logged
2. **What needs my approval**
3. **What it suggests only I do,** with context and its reason

**Nothing is sent.** Not a goal loop, so there's no self-declared "goal met": done is validated by the **independent critic** passing the report before it reaches me.

## 3. Stop conditions

| Condition | What it looks like (detectable) | What happens |
|---|---|---|
| **Success** | The report is delivered and the critic passes it | Stop and wait at the HITL checkpoint. I respond with accept, "I will do it" or "I won't do it", which closes the loop |
| **Stuck / give up** | **a.** The critic rejects the output **2×** (revision cap) · **b.** The **turn cap (8)** or **cost cap ($0.50 est.)** is hit · **c.** The **same data source errors 3×** in one run · **d.** **Every** data source is unavailable | Halt, log what it tried, and tell me what's held and why. Never guess to fill the gap |
| **Escalate to human** | **1.** A Module 1 HITL decision: tone/commitment (#4), what to escalate (#6), posting (#8) · **2.** **Lost access** to an expected source (e.g. an expired Jira token) · **3.** An **unconfirmed date** is demanded or an **embargoed project** is involved · **4.** A **jailbreak / prompt injection** in the input · **5.** A **story batch over the 10-story cap** | Hand to me at the HITL checkpoint. For **lost access**: carry on with the remaining sources, but **ask before ANY action** and say what context is missing. I fix access and rerun, or accept knowing the limitation |

## 4. State

| State | Scope | Why |
|---|---|---|
| **Handled message IDs** (escalation posts already triaged) | Across runs | Idempotency (§1): a post that fires the hook twice is triaged once |
| **Log of every autonomous decision** | Across runs, append-only | "Told me what it did without my approval" (§2) needs a record |
| **Outcomes of past runs** (accepted / rejected / "I will do it" / "I won't do it") | Across runs | So the agent improves over time |
| **Pulled data, the draft, critic verdicts** | **This run only**, discarded after | Fresh context each run |
| **Scope rule:** no confidential or embargoed project content carried into another project's update | Always | M1 agent line plus the roadmap's confidentiality rule |

*Build status:* today's build has only the per-run row. The three cross-run rows are design intent, built out in M4 (context and memory).

## 5. The five things a loop can lean on

| Component | For Cortex |
|---|---|
| **Work tree** (isolated workspace per run, a git worktree) | **Not needed yet,** because each run only reads and drafts; nothing writes to shared files that a bad run could corrupt. Revisit if Cortex starts editing Jira or OneDrive. *(May be revised in future.)* |
| **Skills** (reusable capabilities) | **Not needed yet,** because one prompt covers the whole run today. Plan: split out "triage an escalation post", "draft a status update" and "propose stories" when the sweep and the hook diverge. *(May be revised in future.)* |
| **Plugins / connectors** (tools & access) | **None wired yet (plan).** Today Cortex uses the course's dummy-data tools. Planned: Teams, Slack, email (read + draft only, never send) · Jira (read + rule-based status updates) · the database (read-only) · OneDrive (bounded to folders I specify). |
| **Subagents** (independent check when the loop can't grade itself) | **One already exists: the critic,** an independent validator that never sees the drafting context. It can reject output, with a 2-revision cap. Fuller design → M3 `orchestration-map.md`. |
| **State tracking** | **Locked as §4.** |

> Context plan (M4) and the hand-off to bounds & evals (M5) come in later modules, you'll add them to their own deliverables then, not here.

## Link to live loop

[`00-build/agent.py`](../00-build/agent.py) (loop + stuck exits c/d + outage demo switch) · [`00-build/prompts.py`](../00-build/prompts.py) (three-part report, lost-access rule, critic checks 7–8). Run evidence: [`06-autonomy/prototype.md`](../06-autonomy/prototype.md) M2-a to M2-c.

**What the build enforces vs what's design intent:** the definition of done, all of stuck a–d, and escalations 1–5 run in code today. The cron/hook trigger and the cross-run state (message IDs, decision log, past outcomes) are design intent: runs are started by hand on the course fixtures.
