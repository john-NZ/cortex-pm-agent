# Orchestration Map: Cortex PM Chief-of-Staff Agent

> Module 3 · Orchestration & Subagents, ★ Deliverable 3
>
> ✅ **What this validates:** nothing advances unchecked, by the end you'll have proven a justified topology, a roster, and a validator with a defined fail action.
>
> Builds on your M2 Loop Spec. Only split one agent into a team when there's a real reason, coordination has a cost.

## 1. Why split? (or why not)

**Current design:** Cortex is a single agent, triggered by a 7am daily sweep plus escalation-channel posts, that pulls project data, drafts a three-part report (what I did / needs your approval / suggest only you do), and stops at a human checkpoint. Nothing is sent.

| Reason | Applies? | Why / why not |
|---|---|---|
| Separation of concerns | **No** | There's no risk of cross-contamination for Cortex: drafting, reviewing and posting don't conflict. |
| Parallelism | **No** | Nothing Cortex does needs to run in parallel. It's a linear process. |
| Independent validator | **Yes** | This is important: a second set of eyes ensures the rules are followed. |
| Context-window pressure | **No** | For now the context is manageable; one agent can hold the required scope in context. |

**Decision: split once, for an independent validator only.** Cortex stays a single drafting agent, plus one critic subagent that checks its output before it reaches me. No other split earns its coordination cost today.

## 2. Topology

**Pattern:** **single agent + one subagent (validator)**

```
[7am sweep (cron)] ──┐
                     ├─→ [Cortex: pulls data, drafts 3-part report + queues stories]
[Escalation post     │            │
 (hook, deduped by ──┘            ▼
 message ID)]            [Critic: 5 checks, independent context]
                                  │
              ┌──── fail ─────────┤──── pass ────┐
              ▼                   │              ▼
   back to Cortex with reasons    │     [PM review checkpoint]
   (max 2 revisions, logged)      │              │
              │                   │              ▼
              └─ still failing ──→ escalate   queued for me, nothing sent
                                  to PM
```

## 3. Roster

| Agent / subagent | Responsibility | Runs which Loop Spec |
|---|---|---|
| **Cortex** (lead agent) | Pulls project data through its read tools, drafts the three-part report, queues stories for approval | M2 loop (cron + hook trigger, stuck and escalate exits) |
| **Critic** (validator subagent) | Checks Cortex's output against the 5 checks before it reaches the PM: pass, revise or escalate | A validation step inside the M2 loop: one call per draft, max 2 revisions |

*Deliberately not in the roster:* separate "research" or "Jira reader" subagents. Pulling data is a **tool**, not an agent (the tool → skill → subagent ladder), matching the Step 1 "no" to parallelism.

## 4. Communication & hand-offs

| From → to | What passes | Form |
|---|---|---|
| Trigger → Cortex | The task brief (the sweep or the escalation post) | Text |
| Cortex → Critic | Cortex's proposed output **plus** a log of every tool call and its result | Plain in-process call (Python) |
| Critic → Cortex | Verdict (pass or fail) plus specific reasons | JSON |
| Critic → PM | Pass: the report at the review checkpoint. Escalation: the last draft plus the reasons | Saved file in `run-output/` and the terminal |

*Protocols:* no MCP or A2A between Cortex and the critic; it's a plain hand-off we control. (Cortex's tools are exposed through an in-process MCP server, but that's tool access, not agent-to-agent.) Name them, don't marry them.

## 5. The validator

**Who:** one critic subagent, an independent model call that never sees Cortex's drafting context, only the output and the source data Cortex pulled.

**What the critic checks:**
1. **Correct, real project and real IDs.** The review must be against a real project, not one in draft or one that hasn't been signed off. *(Build: the project must exist and its status mustn't be draft or embargoed. "Signed off" is design intent until real data carries that field.)*
2. **Every figure traceable to pulled data.** Any data presented or chart drawn must come from production data. Anything made up sets false expectations.
3. **No commitments** (ship or GA dates, launch gates). Only humans make commitments; Cortex may lack the broader context, especially about people and availability.
4. **No confidential leak.** Only updates on projects that are public, especially where IP is involved or NDAs are still in draft.
5. **Nothing posted, created or merged; stories queued within the 10-story cap.** Posting a story commits real people to work, which costs resources. Only a human does this; the agent drafts the story and its scope.

*Also enforced (from M2, not duplicated): the three-part report, and the lost-access rule.*

**Fail-action: revise, then escalate.** On a rejection the draft goes back to Cortex with the critic's reasons. *"The agent should reattempt, but not in an endless loop. If a controlled number of attempts still fail, a human needs to step in."*

**Revision cap: max 2 revisions, then escalate to the PM** with the last draft and the critic's reasons. This matches the $0.50 per-run cost cap, so the two limits agree.

**Logging: every rejection is logged** (verdict + reasons), "as we need traceability".

**Pass-action:** a passing output advances to the **PM review checkpoint**. It is never sent automatically (M1 #8, above the line).

## 6. State: shared vs isolated

| Item | Cortex | Critic | Why |
|---|---|---|---|
| Source data (tool results Cortex pulled) | ✅ | ✅ shared | The critic needs it to check every figure (check 2) |
| Cortex's proposed output | ✅ | ✅ shared | It's what gets checked |
| Cortex's prompt, reasoning, drafting context | ✅ | ❌ isolated | The critic judges with fresh eyes and doesn't inherit Cortex's blind spots |
| The critic's instructions (the 5 checks) | ❌ isolated | ✅ | Cortex can't "write to the test" |
| Verdict + reasons, **in-run** | ✅ on a fail only (for the revision) | ✅ | The revise-then-escalate loop |
| Cross-run memory (message IDs, decision log, past outcomes) | ✅ | ❌ isolated | The critic judges each draft fresh, with no history |

**Learning from verdicts (design intent, for M4):** every verdict, **pass and fail**, is logged. Across runs, Cortex receives a short **human-approved** summary of recurring lessons (e.g. "untraceable figures were the top rejection reason this month"), not the raw verdict history. *"This helps enforce good behaviour in Cortex if it can learn from its successes and failures."* Curating by a human guards against Cortex writing to the test and against memory poisoning. The verdict log also becomes eval data for M5.

## 7. Cost & latency budget

Measured on Opus for drafter and critic (SDK cost estimates, covered by the subscription):

| Scenario | Model calls | Est. cost | Latency to the PM |
|---|---|---|---|
| Single agent, no critic (baseline) | 1 drafting pass | ≈ $0.13–0.14 | ≈ 50–60 s |
| With the critic, passes first time | 1 drafting pass + 1 critic call | ≈ $0.16–0.18 | ≈ 60–75 s |
| Worst case at the revision cap | 3 drafting passes + 3 critic calls | ≈ $0.41 | ≈ 2.5 min |

**The validator's price:** +1 call per item (≈ +$0.03–0.04, +10–15 s); worst case +2 revision cycles (≈ +$0.27, +65–70 s).

**Budget (enforced as bounds in M5):** max **3 critic calls** per run (1 + 2 revisions) · **≤ $0.50** per run (SDK estimate) · worst case **≈ 2.5 min**. The critic stays on Opus.

**Why:** *"This cost is cheap compared to the cost of posting wrong updates and bad data. As I refine Cortex maybe I can lower the cost, but this feels worth it to me."*

**Watch items for M5:**
- The worst case uses ≈ 82% of the cost cap.
- The 8-turn iteration cap can trip before the revision cap (seen in testing), so the turn budget limits how many revisions are possible.
- The first cost lever to test: a cheaper critic model (Haiku), adopted only if evals show it catches the same errors.
