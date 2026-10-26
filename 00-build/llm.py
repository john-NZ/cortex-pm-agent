"""The one place Cortex talks to a model: Anthropic Claude via the Claude Agent SDK.

Cortex authenticates with the Claude subscription login on this machine
(`claude auth login`), not an API key. Every call is locked down the same way so the
model can only reach what we hand it:

- tools=[]                no built-in tools (no Bash, file edits, web access, sub-agents)
- strict_mcp_config=True  only the MCP servers we pass; the account's claude.ai
                          connectors (Atlassian, Slack, ...) are NOT loaded
- setting_sources=[]      no user/project settings or CLAUDE.md leak into Cortex's context
- system_prompt=...   our prompt replaces the default Claude Code system prompt

Bounds (turns and budget) are passed in by the caller per call; they are enforced by
the SDK outside the model. `total_cost_usd` is the SDK's cost *estimate*; on a
subscription it is notional, but it still drives the cost cap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultError,
    ResultMessage,
    TextBlock,
    query,
)

BUILD_DIR = Path(__file__).parent


@dataclass
class CallResult:
    text: str = ""            # the model's final text for this call
    cost_usd: float = 0.0     # SDK cost estimate for this call
    turns: int = 0            # model turns used (each tool round-trip is a turn)
    stopped_by: str = ""      # "" if it finished; else the SDK bound/error subtype
    errors: list[str] = field(default_factory=list)


def options(*, system_prompt: str, model: str, max_turns: int, max_budget_usd: float,
            mcp_servers: dict | None = None,
            allowed_tools: list[str] | None = None) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model=model,
        system_prompt=system_prompt,
        tools=[],
        mcp_servers=mcp_servers or {},
        strict_mcp_config=True,
        allowed_tools=allowed_tools or [],
        setting_sources=[],
        cwd=str(BUILD_DIR),
        max_turns=max_turns,
        max_budget_usd=max_budget_usd,
    )


async def call(prompt: str, opts: ClaudeAgentOptions) -> CallResult:
    """Run one SDK query to completion (or until a bound stops it)."""
    out = CallResult()
    texts: list[str] = []
    try:
        async for msg in query(prompt=prompt, options=opts):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        texts.append(block.text)
            elif isinstance(msg, ResultMessage):
                out.cost_usd = msg.total_cost_usd or 0.0
                out.turns = msg.num_turns or 0
                if msg.is_error:
                    out.stopped_by = msg.subtype
                elif msg.result:
                    texts.append(msg.result)
    except ResultError as e:
        # The SDK yields the error ResultMessage above, then raises. A bound trip
        # (error_max_turns / error_max_budget_usd) lands here and is handled by the
        # caller as an escalation, not a crash.
        out.stopped_by = out.stopped_by or e.subtype or "error"
        out.errors = list(e.errors or [])
    # The final result repeats the last assistant text; keep the last one.
    out.text = texts[-1] if texts else ""
    return out
