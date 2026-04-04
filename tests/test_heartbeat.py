"""Heartbeat stall detection tests."""

import pytest
import time
from unittest.mock import patch
from agentguard.state import StepContext
from agentguard.checks.heartbeat import Heartbeat, _set_start


@pytest.fixture
def ctx():
    return StepContext({"max_cost": 5.0, "stall_timeout": 0.5})


def test_no_stall(ctx):
    """validate() returns ok when within timeout."""
    _set_start(time.time())
    hb = Heartbeat(ctx)
    hb.last_activity = time.time()
    assert hb.validate() == "ok"


def test_stall_detected(ctx):
    """validate() returns stall when timeout exceeded."""
    _set_start(time.time() - 2.0)  # 2 seconds ago
    hb = Heartbeat(ctx)           # timeout is 0.5
    assert hb.validate() == "stall"


def test_resolve_force_stops(ctx):
    """resolve() force-stops the context."""
    _set_start(time.time() - 2.0)
    hb = Heartbeat(ctx)
    resolution = hb.resolve("stall", {})
    assert resolution["type"] == "interrupt"
    assert ctx.stopped
