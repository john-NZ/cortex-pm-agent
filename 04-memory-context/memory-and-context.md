# Context Engineering & Memory: Cortex PM Chief-of-Staff Agent

> Module 4 · Context Engineering & Memory
>
> ✅ **What this validates:** the agent reasons on the right, safe inputs, by the end you'll have proven a context budget, per-source retrieve-vs-long-context decisions, and a memory map with risk mitigations.
>
> 🗂️ **How the lab maps to this file:** In **Part A** (before the lecture) you don't edit this file, you rough-draft on scratch, focused on the per-source calls in **section 2** plus a quick remember/forget + "how it rots" sketch. In **Part B** (after the lecture) you complete **all five sections**; the Lab Guide's guided builder writes this file for you to copy in and commit.

## 1. Context budget

What each loop iteration puts on the "desk", in priority order:

| Priority | Context | How | Why this rank |
|---|---|---|---|
| 1 | **Task brief** | Whole (long-context) | It defines the job; without it nothing else matters |
| 2 | **Team norms** | Whole while small (long-context), retrieved later | The rules every claim is judged against (the critic's checks) |
| 3 | **Activity: the current window** (since the last update) | Whole (long-context) | The facts the update reports, and the most volatile |
| 4 | **Project record** (status, flags, PRD scope) | Retrieved, for this project only | Status, holds and scope for stories |
| 5 | **Roadmap: this project's slice plus the confidential flags** | Retrieve | What's shareable and what must stay out |
| 6 | **Past updates: the top 1–2 matches** | Retrieve | Format and precedent only |
| 7 | **Activity history** (older than the window) | Retrieve, *only if needed* | For trends; the first thing to cut |

**Cut order when the desk is full:** history (7) first, then past updates (6) down to one example. Items 1–3 are **never cut**; if they can't fit, Cortex escalates rather than drafting with half the facts.

## 2. Retrieve vs. long-context: per source

For each data source, decide: **retrieve** (narrow a large/changing corpus to the relevant slice) or **long-context** (just include a bounded set you can reason over).

| Source | Size / volatility | Decision | Why |
|---|---|---|---|
| **Activity** (`get_activity`: PRs, issues, metrics; later Jira / GitHub / monitoring) | Large, grows; "where everybody posts their progress… changes most frequently" | **Split by time:** the current window (since the last update) is **long-context**; older history is **retrieve** | Deciding factor: **volatility + size**. "If this is only current activity I would choose long-context, but if this data source includes a lot of history then retrieve", "especially because it is always changing." |
| **Past updates + decisions** (`search_past_updates`) | Unbounded history | **Retrieve** | Deciding factor: **size**. Only the 1–2 most relevant precedents are needed for format and tone. |
| **Roadmap** (`get_roadmap`) | Medium; carries CONFIDENTIAL / EMBARGOED flags | **Retrieve** | Deciding factor: **citation / audit**. Cortex must point at this project's slice and the exact confidential flags. |
| **Team norms / playbook** (`get_norms`) | Medium; must stay current | **Long-context now, retrieve later** | Deciding factor: **size**. "Dependent on the size, maybe in the beginning of the project it is long-context, then later in the project retrieve." |
| **This run's task brief** (`get_task`) | One static document | **Long-context** | Deciding factor: **size**. "It is bounded and should not grow." |

*Build today:* `get_activity` (per-project slice) and `search_past_updates` (keyword match) already retrieve; `get_roadmap`, `get_norms` and the task brief return whole files. The activity time-split and roadmap slicing are design intent for when real data arrives.

## 3. Retrieval quality plan

| Retrieved source | Routing | Grading | Reranking | Self-verify | Caching | Failure it prevents |
|---|---|---|---|---|---|---|
| Activity history (older than the current window) | ✅ | ✅ | | ✅ | | Grading drops other projects' PRs and stale items; routing means history is queried only when a trend is needed |
| Past updates + decisions | | ✅ | ✅ | ✅ | | Keyword search returns loosely related updates (a Northstar query returned Orbit items in testing). Grading drops them; reranking puts the most recent precedent first |
| Roadmap (this project's slice) | | ✅ | | ✅ | ✅ | Grading keeps the confidential flags even when slicing (Pulsar and Orbit can't be hidden by a slice); caching, because it changes slowly |
| Norms (once retrieved, later) | ✅ | | | ✅ | ✅ | Routing sends a question to the right norm section; caching, because norms rarely change within a day |

**Self-verification already exists in the build:** the critic's check 2 ("every figure traceable") verifies every claim against the pulled data, for every source. No retrieved source is naive retrieval.

**Most important move (John): self-verification**, checking the answer actually used the evidence. *"Any claim must be traced to real data and evidence."*

## 4. Memory map (your PM brain)

| Memory type | What Cortex stores | Scope / TTL |
|---|---|---|
| **Working** (in-loop) | The task brief, the pulled data, the drafts, the critic's verdicts within the run | **This run only**, discarded at the end |
| **Episodic** (past runs) | Handled escalation **message IDs** (M2 idempotency) · **outcomes of past runs**: accepted / rejected / "I will do it" / "I won't do it" · the **critic verdict log** (M3) | **Per project.** Message IDs: **7 days** (only needed to stop a duplicate run) · run outcomes and the verdict log: **90 days**, then summarised and deleted |
| **Semantic** (durable facts/prefs) | **Team norms** · **roadmap facts and confidential flags** · **human-approved lessons** distilled from the verdict log (M3 option B) · the **stakeholder map** | **Long-lived but never auto-written**: only the PM adds or changes them. Norms and roadmap reviewed quarterly; lessons reviewed monthly |
| **Shared** (across agents) | Cortex ↔ critic: the output and source data one way, the verdict and reasons back (M3 Field 6) | **This run only.** The critic's reasoning never persists into Cortex's memory |

**Design choices:** semantic memory is **human-write-only** (Cortex can propose a lesson but never store one), the main defence against poisoning. 90 days of episodic memory is long enough to spot trends across a quarter but short enough that old outcomes don't steer today's drafts. *"90 days seems like a good number of days."* *Build today:* only working and shared memory exist; episodic and semantic stores are design intent.

## 5. Memory risks & mitigations

| Risk | Where it bites Cortex | Mitigation |
|---|---|---|
| **Drift** | A stored lesson or norm summary goes out of date while Cortex keeps applying it confidently. *Seen in testing:* the activity feed is ~16 weeks old yet the project still says "on track" | Semantic memory is **human-write-only** with a **quarterly review**; Cortex always **cites the source** of a rule (norms come back whole, not paraphrased); the stale-data warning already fires when the newest activity is old |
| **Poisoning** | A jailbreak line in a pasted brief, or a wrong figure in a past update, gets stored as "precedent" and copied into every future update | **Cortex can't write semantic memory** (it proposes, the PM approves; M3 option B) · task-brief content is treated as **data, not instructions** · critic **check 2** rejects any figure not in the pulled data, even if a past update contains it |
| **Staleness** | Old outcomes or a reversed decision steer today's draft; message IDs pile up | **TTLs**: message IDs 7 days, outcomes 90 days · **reranking puts the most recent precedent first** (§3) · the decision log records reversals explicitly |
| **Confidential / PII / retention** | Embargoed items (**Orbit, Pulsar**) leak into a stored summary and then into a company-wide update; customer data from the read-only database lands in memory | **Scoping:** confidential flags travel with roadmap facts and are never dropped by a slice (§3) · critic **check 4** blocks leaks in every draft · **store the minimum**: no customer records in episodic or semantic memory, only IDs · **retention** follows the TTLs; read/write scope ties to the M1 agent line, and scope and TTLs become **enforced bounds in M5** |

**The risk that worries me most: confidential / PII / retention.** *"I do worry that because Cortex needs leadership plans, they could leak."* It's the core tension: Cortex has to **read** the most sensitive material to do the job, yet must never **repeat** it in the wrong place. I'm happy with the mitigations above.
