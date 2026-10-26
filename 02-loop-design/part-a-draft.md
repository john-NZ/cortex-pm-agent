# Loop Spec, Part A draft (by instinct, pre-lecture)

> Module 2 · Loop Engineering, Part A. Written from gut feel before the lecture, in John's words. Parked as the starting point for Part B (`loop-spec.md`). "The diff between the Part A guess and the final version *is* the learning."

## 1. What should make Cortex start?

1. **A regular timed run, around 7am my time.** It checks the status of important Jira tickets, scans overnight email for anything that needs answering, and reviews overnight alerts from monitoring tools.
2. **An event: a post in an escalation channel (Slack or Teams; we have both).** Issues sometimes come up in real time and need acting on. Only a very small number of escalation channels need monitoring. An agent can quickly read and triage a post, and the loop runs.

## 2. What does "done" mean for one run?

> "I call it done when the agent has identified the key areas to focus on, correctly triaged them by importance, told me what it did without my approval, asked me for approval for things that need it, and made suggestions for things only a human should do."

## 3. When should it stop or hand off to a human?

- **It stops to ask permission** to do something. Even if I just click accept, it still waits.
- **It stops when it suggests I do something myself.** It gives the context and its reasoning, but I have to do it. I click "I will do it" or "I won't do it", and that closes the loop.
- **It loses access it expected** (e.g. the Jira access token has expired). It skips that part and moves on (e.g. reads Slack), but it's now missing context, so any decision is risky. It should carry on, but ask me before **any** action it wants to take and tell me what context is missing. I can fix the issue and rerun the loop, or accept its suggestions knowing the limitation.

## 4. What does Cortex need?

**Connectors**
- **MS Teams, Slack, email:** read, plus draft a post if the service allows it, but never post. This holds for email; I'm not sure yet whether Teams and Slack support drafts. *Any outbound communication on any channel can be drafted by the agent but only sent by me.*
- **Jira:** read, plus update a ticket if the rules are clear (e.g. moving a ticket's status).
- **Our database:** read-only, to check customer data.

**Information:** roadmap, product documentation, stakeholder map.

**A place to put things:** OneDrive, bounded to folders I specify.

**Memory and oversight**
- **Outcomes of past runs**, so the agent improves over time.
- **A log of all its autonomous decisions.**
- **A critic** that pushes back on any decision before it reaches me.

## Observed on rerun (today's build vs this draft)

`task-happy`: 6 tool calls, 7 stories queued, critic pass, stopped at the HITL checkpoint (~$0.14). `missing-data`: P-HALO not found, so it escalated and drafted nothing (~$0.09).

| This draft | Today's build | Gap |
|---|---|---|
| 7am sweep + escalation-channel trigger | Started by hand only | No trigger yet |
| Done = did on its own / needs approval / suggestions for me | One draft and a queue, all for approval | No three-way split |
| Stops to ask permission and waits | Everything waits at the HITL checkpoint | Matches |
| Missing access → continue, ask before any action, say what's missing | Missing data → stops and escalates | Different behaviour; missing *access* isn't tested by the fixtures |
| Teams / Slack / email / Jira / DB / OneDrive | Course dummy-data tools only | Planned connectors |
| Log of autonomous decisions + memory of past runs | Neither | Gap |
| Critic that pushes back | Critic in place | Matches |

## Parked: least sure about

- Is the 7am timed run plus escalation-channel posts the right trigger pairing?
- Jira status changes made by the agent on its own aren't in my M1 agent-line map, where Cortex only proposes. Should they be?
