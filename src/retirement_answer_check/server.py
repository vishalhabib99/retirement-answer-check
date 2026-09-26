"""MCP server for retirement-answer-check (stdio)."""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from .checker import FACTS, check

mcp = MCPServer("retirement-answer-check")
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


@mcp.tool(annotations=READ_ONLY)
def check_answer(question: str, answer: str) -> dict:
    """Check an AI-drafted answer to a US retirement-account question before it is sent to a customer.

    Verifies numbers and rules (contribution limits, RMDs, rollovers, early-distribution tax and
    exceptions, excess contributions) against IRS-sourced facts, flags out-of-scope topics, and
    runs phrase rules for personal recommendations and promissory claims. Returns
    {"decision": "SEND" | "REVIEW", "flags": [{"type", "span", "reason", "source"}]}.
    Any number the facts table can't verify returns REVIEW, never SEND. The phrase rules are a
    baseline only: also run the advice-judge skill before treating SEND as final.

    Args:
        question: The customer's question, verbatim.
        answer: The AI-drafted answer to check, verbatim. An empty answer returns REVIEW.
    """
    try:
        return check(question, answer)
    except Exception as exc:  # never let a checker bug turn into a silent SEND
        return {"decision": "REVIEW", "flags": [{"type": "checker_error", "span": "", "source": None,
                "reason": f"checker failed ({type(exc).__name__}: {exc}); route this answer to a human"}]}


@mcp.tool(annotations=READ_ONLY)
def get_facts() -> dict:
    """Return the full IRS-sourced facts table the checker verifies against.

    Includes contribution limits by tax year, RMD rules, rollover rules, early-distribution tax and
    exceptions, and the source URL for every entry, plus the date the values were verified. Use it
    to show a reviewer why a number was flagged. Takes no arguments.
    """
    try:
        return FACTS
    except Exception as exc:
        raise RuntimeError(f"facts table unavailable ({exc}); check data/facts.json is present and valid JSON") from exc


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
