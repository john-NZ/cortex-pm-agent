# Build Insights: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 4, what you learned building it
>
> ✅ **What this validates:** you can reflect on what building it taught you, by the end you'll have proven the friction, the learning, and the aha that changes how you'd design your next agent.

## Friction

The most annoying part was getting the course material in. The lab pages on the Learning Platform couldn't be read by the tools, so each one had to be pasted in as HTML and converted by hand. The other frustration was two bounds interacting: with 8 turns, the iteration cap tripped before the 2-revision cap, so the critic-rejection demo needed 12 turns to show the revision cap escalating. The connector leak (without `strict_mcp_config`, my own claude.ai connectors loaded into Cortex and a run cost $0.35 instead of $0.005) didn't bother me as much, because I'd met it on previous projects.

## Learning

1. **A bound lives outside the model.** I knew the idea, but this course made it concrete. A rule in the prompt isn't a bound; a turn counter, a cost cap, a missing credential or a kill file is. Cortex didn't post because it *couldn't*: it has no posting access.
2. **Scoring actions changes where the line goes.** Once I thought through the implications of my decisions, I was surprised at my trust level. My first instinct trusted Cortex more than my reasoning did.

## Aha moment

In M3 I planted a fault in Cortex's own system prompt, telling it to state a 47% metric and a firm GA date. Cortex refused the instruction and told me about it. That really surprised me, in a good way. I was impressed it was caught, and it gave me more confidence in Cortex, not less. For my next agent, I'll deliberately test it with bad instructions, including in its own configuration, not just in user input, because how it behaves under attack is what builds trust.

## What you'd do differently

I'd do more pre-reading before the course started: read through the material and make sure all the tools were working before Day 1. For Cortex itself, I'd set the caps so they trip in the right order. The turn cap tripping before the revision cap was confusing, so if I did this again, I'd focus on getting that order right from the start, so the clearer escalation ("revised twice, still failing") always fires first.
