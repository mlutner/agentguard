"""Tests for @guard decorator and all three input patterns."""

import pytest
import asyncio
from agentguard.guard import guard


# ---- Pattern 1: async generator (native) ----

@pytest.mark.asyncio
async def test_async_generator_yields_steps():
    """Basic async generator with 3 steps passes through cleanly."""
    @guard(max_cost=5.0, max_steps=10)
    async def agent():
        for i in range(3):
            yield {"type": "tool", "tool": "search", "args": f"query_{i}"}

    results = [s async for s in agent()]
    assert len(results) == 3
    assert results[0]["args"] == "query_0"


@pytest.mark.asyncio
async def test_max_steps_interrupts():
    """Agent exceeding max_steps gets cut off."""
    @guard(max_cost=5.0, max_steps=2)
    async def agent():
        for i in range(10):
            yield {"type": "tool", "tool": "search", "args": f"q_{i}"}

    results = [s async for s in agent()]
    assert len(results) == 3  # 2 valid + 1 interrupt
    assert results[-1]["type"] == "interrupt"


# ---- Pattern 2: sync generator ----

@pytest.mark.asyncio
async def test_sync_generator_wrapped():
    """Sync generators are normalised to async."""
    @guard(max_cost=5.0, max_steps=5)
    def agent():
        for i in range(3):
            yield {"type": "tool", "tool": "web_search", "args": f"search_{i}"}

    results = [s async for s in agent()]
    assert len(results) == 3


# ---- Pattern 3: plain callable ----

@pytest.mark.asyncio
async def test_plain_callable_wrapped():
    """Plain return-value callables are wrapped as single step."""
    @guard(max_cost=5.0, max_steps=5)
    def agent():
        return {"type": "result", "answer": "hello"}

    results = [s async for s in agent()]
    assert len(results) == 1
    assert results[0]["value"]["answer"] == "hello"
