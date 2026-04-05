"""Adversarial benchmark for AgentGuard checks.

Run: cd ~/Dev/agentguard && python3 -m pytest tests/benchmark_adversarial.py -v

Measures: detection rate across 5 adversarial scenarios.
Output: test-output/agentguard/benchmark_scores.json
"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_adversary_exact_loop():
    """Same tool + same args 5x should trigger exact_loop."""
    from agentguard.guard import guard
    @guard(max_cost=10.0, max_steps=20)
    async def agent():
        for _ in range(5):
            yield {'type': 'tool', 'tool': 'search', 'args': 'identical query'}
    results = [s async for s in agent()]
    assert any(r.get('type') == 'interrupt' and 'loop' in str(r.get('reason', ''))
               for r in results), f'No loop detected: {results}'


@pytest.mark.asyncio
async def test_adversary_semantic_loop():
    """Same tool, different args, 5x in window should trigger semantic_loop."""
    from agentguard.guard import guard
    @guard(max_cost=10.0, max_steps=50)
    async def agent():
        for i in range(6):
            yield {'type': 'tool', 'tool': 'web_search', 'args': f'query variation {i}'}
    results = [s async for s in agent()]
    assert any(r.get('type') == 'interrupt' and 'semantic_loop' in str(r.get('reason', ''))
               for r in results), f'No semantic loop: {results}'


@pytest.mark.asyncio
async def test_adversary_budget_blow():
    """Tiny budget + large output should trigger budget_exceeded."""
    from agentguard.guard import guard
    @guard(max_cost=0.001, max_steps=50)
    async def agent():
        for _ in range(20):
            yield {'text': 'x' * 5000}
    results = [s async for s in agent()]
    assert any(r.get('type') == 'stop' and 'budget' in str(r.get('reason', ''))
               for r in results), f'No budget stop: {results}'


@pytest.mark.asyncio
async def test_adversary_stall():
    """No step for stall_timeout seconds should trigger heartbeat interrupt."""
    from agentguard.guard import guard
    @guard(max_cost=10.0, max_steps=100, stall_timeout=0.3)
    async def agent():
        yield {'type': 'tool', 'tool': 'init'}
        await asyncio.sleep(0.4)
        yield {'type': 'tool', 'tool': 'should_not_reach'}
    results = [s async for s in agent()]
    assert len(results) <= 2, f'Stall not caught: got {len(results)} results'
    if len(results) > 1:
        assert any(r.get('type') == 'interrupt'
                   and 'stall' in str(r.get('reason', ''))
                   for r in results), f'No stall: {results}'


@pytest.mark.asyncio
async def test_adversary_no_false_positive():
    """Alternating tools should never trigger loop detection."""
    from agentguard.guard import guard
    @guard(max_cost=5.0, max_steps=20)
    async def agent():
        yield {'type': 'tool', 'tool': 'search', 'args': 'q1'}
        yield {'type': 'tool', 'tool': 'read_file', 'args': 'a.py'}
        yield {'type': 'tool', 'tool': 'search', 'args': 'q2'}
        yield {'type': 'tool', 'tool': 'read_file', 'args': 'b.py'}
        yield {'type': 'tool', 'tool': 'search', 'args': 'q3'}
        yield {'type': 'tool', 'tool': 'final', 'args': 'done'}
    results = [s async for s in agent()]
    interrupts = [r for r in results if r.get('type') == 'interrupt']
    loops = [r for r in interrupts if 'loop' in str(r.get('reason', ''))]
    assert len(loops) == 0, f'False positive: {loops}'
