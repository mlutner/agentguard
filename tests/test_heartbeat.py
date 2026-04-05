"""Heartbeat stall detection tests."""

import time
import pytest
from agentguard.state import StepContext
from agentguard.checks.heartbeat import Heartbeat


@pytest.fixture
def ctx():
    return StepContext({"max_cost": 5.0, "stall_timeout": 0.5})


def test_no_stall(ctx):
    hb = Heartbeat(ctx)
    hb.last_activity = time.time()
    assert hb.validate() == "ok"


def test_stall_detected(ctx):
    hb = Heartbeat(ctx)
    hb.last_activity = time.time() - 2.0
    assert hb.validate() == "stall"


def test_resolve_force_stops(ctx):
    hb = Heartbeat(ctx)
    hb.last_activity = time.time() - 2.0
    resolution = hb.resolve("stall", {})
    assert resolution["type"] == "interrupt"
    assert ctx.stopped
