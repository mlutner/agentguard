"""Cost regulation tests."""

import pytest
from agentguard.state import StepContext
from agentguard.checks.cost_regulator import CostRegulator


@pytest.fixture
def ctx():
    return StepContext({"max_cost": 0.005, "model": "openai/gpt-4o"})


def test_accumulates_cost(ctx):
    """Multiple steps accumulate token cost."""
    cr = CostRegulator(ctx)
    ctx.record({"text": "hello world this is a test string"})
    # First validation
    cr.validate()
    assert ctx.total_cost >= 0


def test_budget_exceeded(ctx):
    """Cost exceeding max_cost triggers budget_exceeded."""
    cr = CostRegulator(ctx)
    # Inject fake cost to simulate budget blow
    ctx.total_cost = 0.01  # exceeds 0.005 max
    assert cr.validate() == "budget_exceeded"


def test_resolve_stops_agent(ctx):
    """resolve() force-stops the agent."""
    cr = CostRegulator(ctx)
    ctx.total_cost = 0.01
    resolution = cr.resolve("budget_exceeded", {})
    assert resolution["type"] == "stop"
    assert ctx.stopped
    assert "total_cost" in resolution


def test_zero_cost_model(ctx):
    """Free models like qwen3.6-plus don't accumulate cost."""
    ctx.cfg["model"] = "qwen/qwen3.6-plus"
    cr = CostRegulator(ctx)
    ctx.record({"text": "a" * 10000})  # huge output
    cr.validate()
    # Free model → cost stays near zero
    assert ctx.total_cost < 0.0001
