"""Adversarial loop detection tests."""

import pytest
from agentguard.state import StepContext
from agentguard.checks.loop_breaker import LoopBreaker


@pytest.fixture
def ctx():
    return StepContext({"max_cost": 5.0, "max_steps": 100})


def test_no_loop(ctx):
    """Different tools → no loop."""
    lb = LoopBreaker(ctx)
    ctx.record({"tool": "search", "args": "query_1"})
    ctx.record({"tool": "read_file", "args": "f1.py"})
    ctx.record({"tool": "search", "args": "query_2"})
    assert lb.validate() == "ok"


def test_exact_duplicate(ctx):
    """Same tool + same args 3x → exact_loop."""
    lb = LoopBreaker(ctx, threshold=3)
    for _ in range(4):
        ctx.record({"tool": "search", "args": "identical query"})
    assert lb.validate() == "exact_loop"


def test_exact_duplicate_below_threshold(ctx):
    """2x duplicate with threshold=3 → still ok."""
    lb = LoopBreaker(ctx, threshold=3)
    ctx.record({"tool": "search", "args": "query_a"})
    ctx.record({"tool": "search", "args": "query_a"})
    assert lb.validate() == "ok"


def test_semantic_loop_same_tool(ctx):
    """Same tool, different args, 5 times in window → semantic_loop."""
    lb = LoopBreaker(ctx, same_tool_limit=5)
    for i in range(6):
        ctx.record({"tool": "web_search", "args": f"query variation {i}"})
    result = lb.validate()
    assert result == "semantic_loop:web_search"


def test_semantic_loop_below_limit(ctx):
    """Same tool 4 times with limit=5 → ok."""
    lb = LoopBreaker(ctx, same_tool_limit=5)
    for i in range(4):
        ctx.record({"tool": "web_search", "args": f"rephrased query {i}"})
    assert lb.validate() == "ok"


def test_resolve_returns_interrupt(ctx):
    """resolve() returns a structured interrupt."""
    lb = LoopBreaker(ctx, threshold=2)
    ctx.record({"tool": "search", "args": "x"})
    ctx.record({"tool": "search", "args": "x"})
    ctx.record({"tool": "search", "args": "x"})
    verdict = lb.validate()
    resolution = lb.resolve(verdict, {})
    assert resolution["type"] == "interrupt"
    assert "exact_loop" in resolution["reason"]
    assert ctx.stopped
