"""Independent validator (M3). A separate model call that never saw the drafting
context, so it can't inherit the draft's blind spots. Returns a pass/fail verdict.
The revision cap that stops a critic<->drafter loop lives in `agent.py`.

Runs on Anthropic Claude via the Agent SDK (see llm.py): one turn, no tools at all.
"""

from __future__ import annotations

import json
import re

import llm
from prompts import CRITIC_SYSTEM


def _parse_verdict(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)  # tolerate ```json fences / prose
    try:
        verdict = json.loads(match.group(0)) if match else None
    except json.JSONDecodeError:
        verdict = None
    if not isinstance(verdict, dict) or verdict.get("verdict") not in ("pass", "fail"):
        return {"verdict": "fail", "reasons": ["critic returned unparseable output"]}
    verdict.setdefault("reasons", [])
    verdict.setdefault("failed_checks", [])
    return verdict


async def review(model: str, proposed_output: str, source_data: str,
                 max_budget_usd: float) -> dict:
    """Return {"verdict": "pass"|"fail", "reasons": [...], "_cost": float}."""
    result = await llm.call(
        f"SOURCE DATA Cortex used:\n{source_data}\n\n"
        f"CORTEX PROPOSED OUTPUT:\n{proposed_output}",
        llm.options(system_prompt=CRITIC_SYSTEM, model=model,
                    max_turns=1, max_budget_usd=max_budget_usd))
    if result.stopped_by:
        verdict = {"verdict": "fail", "failed_checks": ["critic-error"],
                   "reasons": [f"critic call stopped early ({result.stopped_by})"]}
    else:
        verdict = _parse_verdict(result.text)
    verdict["_cost"] = result.cost_usd
    return verdict
