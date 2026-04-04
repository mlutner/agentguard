"""Shared fixtures for AgentGuard tests."""

import pytest
from agentguard.state import StepContext


@pytest.fixture
def basic_cfg():
    return {
        "max_cost": 5.0,
        "max_steps": 100,
        "stall_timeout": 120.0,
    }


@pytest.fixture
def ctx(basic_cfg):
    return StepContext(basic_cfg)


@pytest.fixture
def strict_cfg():
    return {"max_cost": 0.01, "max_steps": 10, "stall_timeout": 1.0}
