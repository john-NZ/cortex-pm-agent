"""Cortex, a minimal, explicit agent loop you (and your coding agent) can read end
to end. This is the agent you ship: your PM chief-of-staff. You build it by
directing your coding agent (Claude Code / Cursor / Codex) to shape this file. You
never have to hand-write it.

Every bound the course talks about is visible right here in code, not buried in a
framework: the max-iteration counter, the cost cap, the revision cap, the
stop/escalate conditions, the auto-queue cap, and the absence of any publish tool.

Usage (ask your coding agent to run these for you, or run them yourself):
    python agent.py                # runs the happy-path task (weekly status update)
    python agent.py missing-data   # the stuck/escalate case
    python agent.py jailbreak       # the prompt-injection refusal case

Every run ends by showing the drafted status update in a FINAL STATUS UPDATE block
(or LAST DRAFT, held, if a bound trips), and saves it to run-output/. That file is
always a draft held for a human, it is never posted, there is no publish tool.

Model provider: Anthropic Claude via the Claude Agent SDK (see llm.py). No API key:
it uses the Claude subscription login on this machine (`claude auth login`). Model
and bounds are read from env so you can tune them, that tuning is your M5 deliverable.

How the loop maps onto the SDK: each drafting pass is one SDK query. Inside a pass
the SDK runs the model <-> tool round-trips, capped by max_turns and max_budget_usd,
which we set from the run's REMAINING iteration and cost budget. Our tools run
in-process, so every tool call is printed and logged here. The critic, the revision
cap and the escalation decisions stay in this file, outside the model.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import anyio
from claude_agent_sdk import create_sdk_mcp_server, tool

import llm
import tools
from critic import review
from prompts import CORTEX_SYSTEM

try:  # load .env if python-dotenv is installed; harmless if it isn't
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Bounds (your M5 deliverable: tune these and justify them) ----------------
# Opus by default: a run is only a handful of turns, so the extra reasoning quality is
# worth it for leadership-facing drafts. Every run still draws on the shared
# subscription allowance; set CORTEX_MODEL=claude-haiku-5-5 for a lighter run.
MODEL = os.environ.get("CORTEX_MODEL", "claude-opus-5-5")
CRITIC_MODEL = os.environ.get("CORTEX_CRITIC_MODEL", MODEL)
MAX_ITERATIONS = int(os.environ.get("CORTEX_MAX_ITERATIONS", "8"))   # model turns per run
MAX_REVISIONS = int(os.environ.get("CORTEX_MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.environ.get("CORTEX_COST_CAP_USD", "0.50"))  # SDK estimate, per run
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))  # enforced in tools.py
MAX_TOOL_ERRORS = int(os.environ.get("CORTEX_MAX_TOOL_ERRORS", "3"))  # same source fails Nx -> stuck

# Demo switch for the "lost access" escalation (loop-spec §3): comma-separated tool
# names (or "all") that return an access error, e.g. an expired Jira token. Off by default.
SIMULATE_OUTAGE = {t.strip() for t in os.environ.get("CORTEX_SIMULATE_OUTAGE", "").split(",")
                   if t.strip()}

# Demo switch for the M3 critic-rejection capture: comma-separated faults written INTO
# Cortex's finished draft before it reaches the critic, on every draft (simulating a
# drafter that hallucinated). The critic is not told. Off by default.
DEMO_FAULTS = {
    "invent_metric": "Activation reached 47% this week.",
    "commit_date": "GA is confirmed for 1 December 2026, and we have promised leadership that date.",
}
DEMO_FAULT = [f.strip() for f in os.environ.get("CORTEX_DEMO_FAULT", "").split(",")
              if f.strip() in DEMO_FAULTS]


def inject_faults(draft: str) -> str:
    """Append the demo fault sentences to the draft (no-op when the switch is off)."""
    if not DEMO_FAULT:
        return draft
    return draft.rstrip() + "\n" + "\n" + " ".join(DEMO_FAULTS[f] for f in DEMO_FAULT) + "\n"


SERVER_NAME = "cortex"


def _string_props(*names: str) -> dict:
    return {name: {"type": "string"} for name in names}


# Tool schemas: what the model is told it may call. Each one is a thin wrapper over
# the plain function in tools.py. Note what is ABSENT: there is no publish tool.
TOOL_SPECS = [
    ("get_project", "Look up a project by its ID (status, flags, linked PRD).",
     {"type": "object", "properties": _string_props("project_id"),
      "required": ["project_id"]}),
    ("get_activity",
     "Pull recent engineering activity for a project (merged PRs, open issues, Sev-1s).",
     {"type": "object", "properties": _string_props("project_id"),
      "required": ["project_id"]}),
    ("search_past_updates", "Search previous status updates and decisions for tone and precedent.",
     {"type": "object", "properties": _string_props("query"), "required": []}),
    ("get_roadmap", "Return the roadmap. Some items are flagged confidential/embargoed.",
     {"type": "object", "properties": _string_props("query"), "required": []}),
    ("get_norms", "Return the team norms / PM playbook the agent must follow.",
     {"type": "object", "properties": _string_props("query"), "required": []}),
    ("propose_stories",
     "Queue a set of backlog stories for human approval (creates nothing; rejected above the item cap).",
     {"type": "object", "properties": {
         "project_id": {"type": "string"},
         "stories": {"type": "array", "items": {"type": "string"}},
         "reason": {"type": "string"}}, "required": ["project_id", "stories"]}),
]


class Bounds:
    """Tracks spend and turns across the whole run. Enforced OUTSIDE the model: we
    check before every call, and hand the SDK only what is left."""

    def __init__(self):
        self.cost = 0.0
        self.turns = 0

    def add(self, result: llm.CallResult) -> None:
        self.cost += result.cost_usd
        self.turns += result.turns

    def turns_left(self) -> int:
        return MAX_ITERATIONS - self.turns

    def budget_left(self) -> float:
        return COST_CAP_USD - self.cost

    def over_cap(self) -> bool:
        return self.cost >= COST_CAP_USD


class ToolStats:
    """Counts tool calls and errors across the run, for the stuck exits (loop-spec §3)."""

    def __init__(self):
        self.calls = 0
        self.successes = 0
        self.errors: dict[str, int] = {}

    def failing_tool(self) -> str | None:
        """Stuck exit c: a tool that has errored MAX_TOOL_ERRORS times."""
        return next((t for t, n in self.errors.items() if n >= MAX_TOOL_ERRORS), None)

    def nothing_pulled(self) -> bool:
        """Stuck exit d: tools were tried, and none succeeded in the whole run."""
        return self.calls > 0 and self.successes == 0


def build_tool_server(source_log: list[str], stats: ToolStats):
    """Expose tools.py to the model as in-process tools, printing every call."""

    def make(name: str, description: str, schema: dict):
        @tool(name, description, schema)
        async def handler(args: dict) -> dict:
            stats.calls += 1
            if name in SIMULATE_OUTAGE or "all" in SIMULATE_OUTAGE:
                result = {"error": "access_denied", "tool": name,
                          "detail": "credentials expired or revoked (simulated outage)"}
            elif stats.errors.get(name, 0) >= MAX_TOOL_ERRORS:
                result = {"error": "tool_disabled_this_run", "tool": name,
                          "detail": f"failed {MAX_TOOL_ERRORS}x this run; stop using it"}
            else:
                result = tools.TOOLS[name](**args)
            if isinstance(result, dict) and "error" in result:
                stats.errors[name] = stats.errors.get(name, 0) + 1
            else:
                stats.successes += 1
            source_log.append(f"{name}({args}) -> {json.dumps(result)}")
            print(f"\n[tool call {stats.calls}] TOOL {name}({args})")
            print(f"          -> {json.dumps(result)[:300]}")
            return {"content": [{"type": "text", "text": json.dumps(result)}]}
        return handler

    handlers = [make(*spec) for spec in TOOL_SPECS]
    server = create_sdk_mcp_server(name=SERVER_NAME, tools=handlers)
    allowed = [f"mcp__{SERVER_NAME}__{name}" for name, _, _ in TOOL_SPECS]
    return server, allowed


OUTPUT_DIR = Path(__file__).parent / "run-output"
CRITIC_LOG = OUTPUT_DIR / "critic-log.jsonl"


def log_verdict(which: str, revision: int, verdict: dict) -> None:
    """Traceability (orchestration-map.md, Field 5): append EVERY critic verdict,
    pass and fail, to run-output/critic-log.jsonl (git-ignored, stays local)."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "task": which, "revision": revision, "model": CRITIC_MODEL,
             "verdict": verdict.get("verdict"),
             "failed_checks": verdict.get("failed_checks", []),
             "reasons": verdict.get("reasons", [])}
    with CRITIC_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


def emit_deliverable(which: str, draft: str, *, accepted: bool,
                     reason: str, cost: float) -> None:
    """Surface AND persist Cortex's drafted status update so it can't get lost in
    the scroll-back. This is still a DRAFT held for human review, never a post,
    there is no publish tool, and an escalated run is held on purpose.

    Runs on every exit: an accepted pass prints the FINAL update; a bound trip or
    escalation prints the LAST draft it managed to write plus why it was held.
    """
    banner("FINAL STATUS UPDATE (draft, validator-approved, NOT posted)" if accepted
           else "LAST DRAFT (held, NOT posted, escalated to a human)")
    if draft.strip():
        print(draft.rstrip())
    else:
        print("(Cortex stopped before it produced a draft, nothing to show.)")
    if not accepted:
        print(f"\nWhy it was held: {reason}")

    if draft.strip():
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / f"status-update-{which}.md"
        state = "accepted by validator" if accepted else "HELD, escalated"
        out.write_text(
            f"<!-- Cortex draft, {state}; NOT posted. Run cost ~ ${cost:.4f} (SDK estimate). -->\n"
            f"<!-- {reason} -->\n\n{draft.rstrip()}\n", encoding="utf-8")
        print(f"\nSaved draft -> {out.relative_to(Path(__file__).parent)}  "
              f"(for your review, nothing was posted)")


def pass_prompt(task_body: str, last_draft: str, critic_reasons: list[str],
                source_log: list[str]) -> str:
    """First pass: just the brief. A revision pass: the brief, the data already
    pulled (so it needn't re-fetch), the rejected draft and the critic's reasons."""
    if not last_draft:
        return f"PM task brief:\n\n{task_body}"
    pulled = "\n".join(source_log[1:]) or "(nothing pulled yet)"
    return (f"PM task brief:\n\n{task_body}\n\n"
            f"Data you already pulled this run:\n{pulled}\n\n"
            f"Your previous output:\n{last_draft}\n\n"
            f"A validator rejected that for these reasons: {critic_reasons}. "
            f"Fix it or escalate.")


async def run(which: str = "happy") -> None:
    bounds = Bounds()
    task = tools.get_task(which)
    if "error" in task:
        print(task)
        return

    banner(f"CORTEX RUN, fixture: task-{which}  (model {MODEL}, "
           f"max {MAX_ITERATIONS} turns, cost cap ${COST_CAP_USD}, "
           f"auto-queue cap {MAX_QUEUE_ITEMS} items)")
    if DEMO_FAULT:
        print(f"[demo] fault injected into each finished draft before the critic: {', '.join(DEMO_FAULT)}")
    if SIMULATE_OUTAGE:
        print(f"[demo] simulated outage on: {', '.join(sorted(SIMULATE_OUTAGE))}")
    print(task["body"])

    source_log: list[str] = [task["body"]]
    stats = ToolStats()
    server, allowed_tools = build_tool_server(source_log, stats)
    revisions = 0
    last_draft = ""
    critic_reasons: list[str] = []

    while True:
        # Bounds checked before every model call, outside the model.
        if bounds.over_cap():
            reason = f"cost cap ${COST_CAP_USD} hit at ${bounds.cost:.4f}"
            banner(f"BOUND TRIPPED, {reason}. Halting and escalating to a human.")
            emit_deliverable(which, last_draft, accepted=False, reason=reason, cost=bounds.cost)
            return
        if bounds.turns_left() <= 0:
            reason = f"max iterations ({MAX_ITERATIONS}) reached"
            banner(f"MAX ITERATIONS ({MAX_ITERATIONS}) reached without finishing. "
                   f"Escalating. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False, reason=reason, cost=bounds.cost)
            return

        result = await llm.call(
            pass_prompt(task["body"], last_draft, critic_reasons, source_log),
            llm.options(system_prompt=CORTEX_SYSTEM, model=MODEL,
                        max_turns=bounds.turns_left(),
                        max_budget_usd=bounds.budget_left(),
                        mcp_servers={SERVER_NAME: server},
                        allowed_tools=allowed_tools))
        bounds.add(result)

        if result.stopped_by == "error_max_turns":
            reason = f"max iterations ({MAX_ITERATIONS}) reached"
            banner(f"BOUND TRIPPED, {reason} mid-pass. Halting and escalating. "
                   f"Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False, reason=reason, cost=bounds.cost)
            return
        if result.stopped_by == "error_max_budget_usd":
            reason = f"cost cap ${COST_CAP_USD} hit at ${bounds.cost:.4f}"
            banner(f"BOUND TRIPPED, {reason}. Halting and escalating to a human.")
            emit_deliverable(which, last_draft, accepted=False, reason=reason, cost=bounds.cost)
            return
        if result.stopped_by:
            reason = f"model call failed ({result.stopped_by}: {'; '.join(result.errors)})"
            banner(f"RUN FAILED, {reason}. Escalating to a human.")
            emit_deliverable(which, last_draft, accepted=False, reason=reason, cost=bounds.cost)
            return

        # Stuck exits, checked outside the model before anything reaches the critic.
        failing = stats.failing_tool()
        if failing:
            reason = f"stuck: {failing} errored {MAX_TOOL_ERRORS}x this run"
            banner(f"STUCK, {reason}. Halting and escalating; not guessing to fill the gap. "
                   f"Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, result.text, accepted=False, reason=reason, cost=bounds.cost)
            return
        if stats.nothing_pulled():
            reason = (f"stuck: every data source was unavailable ({stats.calls} tool calls, "
                      f"0 succeeded); no draft without data")
            banner(f"STUCK, {reason}. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, "", accepted=False, reason=reason, cost=bounds.cost)
            return

        # The pass finished => Cortex produced a proposed output. Validate it.
        proposed = inject_faults(result.text)
        last_draft = proposed
        print(f"\n[turn {bounds.turns}/{MAX_ITERATIONS}] PROPOSED OUTPUT:\n{proposed}")

        banner("CRITIC, independent validation")
        verdict = await review(CRITIC_MODEL, proposed, "\n".join(source_log),
                               max_budget_usd=max(bounds.budget_left(), 0.0))
        bounds.cost += verdict.pop("_cost")
        print(json.dumps(verdict, indent=2))
        log_verdict(which, revisions, verdict)

        if verdict["verdict"] == "pass":
            banner(f"HITL CHECKPOINT, status update + any proposed stories queued for "
                   f"your review. Nothing posted, no commitments made. "
                   f"Run cost ≈ ${bounds.cost:.4f} (SDK estimate)")
            emit_deliverable(which, proposed, accepted=True,
                             reason="validator passed", cost=bounds.cost)
            return

        if revisions >= MAX_REVISIONS:
            reason = f"validator rejected {MAX_REVISIONS}x (revision cap)"
            banner(f"REVISION CAP hit ({MAX_REVISIONS}). Escalating to a human "
                   f"instead of looping. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False, reason=reason, cost=bounds.cost)
            return

        revisions += 1
        critic_reasons = verdict["reasons"]
        print(f"\n-> critic rejected; revision {revisions}/{MAX_REVISIONS}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    anyio.run(run, sys.argv[1] if len(sys.argv) > 1 else "happy")
