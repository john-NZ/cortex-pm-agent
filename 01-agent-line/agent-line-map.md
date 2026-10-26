# Agent Line Map: Cortex PM Chief-of-Staff Agent

> Module 1 · The Agent Line
>
> ✅ **What this validates:** every risky action has a clear owner, by the end you'll have proven an above/below-the-line map with HITL checkpoints, scored on reversibility, blast radius, and measurability.

## The workflow, decision by decision

List every discrete decision or action in your agent's workflow, then score each one and place it **above** the line (a human owns it) or **below** (the agent owns it). Borderline calls get an HITL checkpoint.

| Decision / action | Reversibility (H/M/L) | Blast radius (H/M/L) | Measurability (H/M/L) | Above / Below | HITL? |
|---|---|---|---|---|---|
| 1. Pull project state + recent activity | H | L | H | Below | · |
| 2. Decide relevant context | H | L | M | Below + HITL | light: PM glances at which inputs Cortex chose |
| 3. Draft the update | H | L | M | Below + HITL | required: PM reviews the draft |
| 4. Decide tone / commitment level | H | H | L | HITL (Cortex proposes) | required: PM audits tone + every commitment |
| 5. Flag at-risk / escalation | H | L | H | Below | · |
| 6. Choose what to escalate | H | H | H | HITL (Cortex proposes) | required: PM re-labels escalations up/down before anything goes out |
| 7. Propose a story batch (capped) | H | L | H | Below | · (stories only queued for approval, never created) |
| 8. Post an update / approve a company-wide one | L | H | L | Above | required: a human posts, Cortex never does |

**What changed after scoring:** #2, #3, #4 and #6 were "below" on first instinct (Step 1). After scoring them against the golden rule they became HITL checkpoints. John: "in line with my thinking now I have given it some thought."

**Scoring notes (John's words):**
1. A data pull with no decisions.
2. Harder to measure but achievable. Depends on all the context being available and kept up to date.
3. Harder to measure when there are many inputs from different teams.
4. Blast radius is high, especially if the tone is offensive to some people (unlikely but possible). Other people's response to tone is very hard to measure, and commitments are even harder when other teams contribute to the outcome. This needs stakeholder management.
5. Depends on the human keeping the context current, so new information that adds or removes risk reaches the agent.
6. The blast radius can be large if a problem is escalated to multiple teams (database, infrastructure, platform, etc.). It's measurable if the work created for other teams is logged.
7. Measurable using tools that evaluate story quality (e.g. Gherkin acceptance criteria).
8. It's tough to measure how others respond to an update, so great care is needed before posting.

## Agent anatomy (sketch)

- **Model:** Anthropic Claude via the Claude Agent SDK, with **Opus (`claude-opus-5-5`) for every step** (drafter and critic). A run is only a handful of turns (~$0.17 estimated, covered by the subscription), so the extra reasoning quality is worth it for leadership-facing work. The design stays model-agnostic: `CORTEX_MODEL` swaps in Haiku per run, and I'd step down to a fast model for routine steps if volume or cost grows.
- **Tools:** project lookup · activity lookup · past-update search · roadmap · team norms · story proposal (capped at 10, queued for approval only). All run in-process; built-in tools and the account's connectors are disabled. **Deliberately absent:** post, send, create, merge, close, commit a date. The agent line is enforced by which tools exist, not by a prompt.
- **Memory:** **Persistent across runs:** roadmap, decision log, team norms, past updates. **Per run only:** the task brief, pulled activity, drafts. Persistent context is only as good as it is current: the PM must keep it up to date so new information that adds or removes risk reaches Cortex (see decisions #2 and #5; developed in M4).
- **Loop:** _placeholder, defined in M2 loop-spec.md_
- **Bounds:** _placeholder, defined in M5 bounds-and-evals.md_
- **Evals:** _placeholder, defined in M5 bounds-and-evals.md_

## The golden rule, applied

1. **Pull project state + activity** sits **below** the line because it's easy to reverse (read-only), has a low blast radius, and is easy to verify (the rows are checkable). Deciding factor: **reversibility**. It's a data pull with no decisions.
2. **Decide relevant context** sits **below, with a light HITL**, because it's easy to reverse and low in blast radius, but only moderately measurable, since a missing input is hard to spot. Deciding factor: **measurability**.
3. **Draft the update** sits **below, with a required HITL**, because a draft is easy to reverse and has a low blast radius, but is only moderately measurable when many teams feed into it. Deciding factor: **measurability**.
4. **Decide tone / commitment level** is a **HITL (Cortex proposes)** because, although it's reversible before sending, the wrong tone or a commitment other teams must deliver has a high blast radius, and people's reactions are very hard to measure. Deciding factor: **measurability**.
5. **Flag at-risk / escalation** sits **below** the line because flags are easy to reverse, low in blast radius, and easy to verify, provided the context is kept current. Deciding factor: **blast radius**.
6. **Choose what to escalate** is a **HITL (Cortex proposes)** because an escalation is reversible before it goes out and measurable through the work it creates, but it can pull in several teams (database, infrastructure, platform). Deciding factor: **blast radius**.
7. **Propose a story batch (capped)** sits **below** the line because the stories are only queued (easy to reverse), have a low blast radius within the cap, and are easy to verify with story-quality checks such as Gherkin. Deciding factor: **reversibility**.
8. **Post an update / approve a company-wide one** sits **above** the line because it can't be reversed, has a high blast radius, and it's hard to measure how people respond. Deciding factor: **reversibility**. Great care is needed before posting.

## Hardest call

**#4, deciding tone and commitment level.** Deciding axis: **measurability**.

> "#4 felt safe because I could edit the tone before sending. But given how hard it is to measure, I decided something involving tone and commitment must have a human involved."

It moved from below the line (Step 1 gut) to a HITL checkpoint where Cortex proposes and the PM audits.
