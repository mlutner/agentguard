"""Tests for @guard decorator — all three input patterns."""

import pytest
import asyncio
from agentguard.guard import guard


@pytest.mark.asyncio
async def test_async_generator_yields_steps():
    @guard(max_cost=5.0, max_steps=100)
    async def agent():
        for i in range(3):
            yield {"type": "tool", "tool": "search", "args": f"query_{i}"}

    results = [s async for s in agent()]
    assert len(results) == 3


@pytest.mark.asyncio
async def test_max_steps_interrupts():
    """Guard enforces max_steps: yields steps until limit, then interrupt."""
    @guard(max_cost=5.0, max_steps=3)
    async def agent():
        for i in range(10):
            yield {"type": "tool", "tool": "search", "args": f"q_{i}"}

    results = [s async for s in agent()]
    assert len(results) >= 2  # at least 1 step + 1 interrupt
    assert results[-1]["type"] == "interrupt"
    assert results[-1]["reason"] == "max_steps_exceeded"


@pytest.mark.asyncio
async def test_sync_generator_wrapped():
    @guard(max_cost=5.0, max_steps=10)
    def agent():
        for i in range(3):
            yield {"type": "tool", "tool": "web_search", "args": f"search_{i}"}

    results = [s async for s in agent()]
    assert len(results) == 3


@pytest.mark.asyncio
async def test_plain_callable_wrapped():
    @guard(max_cost=5.0, max_steps=10)
    def agent():
        return {"type": "result", "answer": "hello"}

    results = [s async for s in agent()]
    assert len(results) == 1
    assert results[0].get("answer") == "hello" or \
           (results[0].get("value", {}).get("answer") == "hello")
