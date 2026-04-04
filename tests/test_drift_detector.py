"""Drift detection tests.

Note: Actual Ollama calls skip if nomic-embed-text not available.
"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from agentguard.state import StepContext
from agentguard.checks.drift_detector import DriftDetector, _extract_text


@pytest.fixture
def ctx():
    return StepContext({
        "max_cost": 5.0,
        "anchor_prompt": "Research top 5 competitors in the AI agent space",
    })


def test_extract_text():
    """_extract_text pulls text from various step shapes."""
    assert _extract_text({"text": "hello"}) == "hello"
    assert _extract_text({"content": "world"}) == "world"
    assert _extract_text({"value": 42}) == "42"
    assert _extract_text({"foo": "bar"}) == "{'foo': 'bar'}"


def test_drift_skips_when_not_interval(ctx):
    """validate() returns ok when step_count doesn't match interval."""
    with patch.object(DriftDetector, '_embed', return_value=np.zeros(768)):
        dd = DriftDetector(ctx, threshold=0.3, interval=10)
        ctx.step_count = 5  # not a multiple of 10
        assert dd.validate() == "ok"


def test_drift_check_at_interval(ctx):
    """validate() runs drift check at the interval."""
    vec = np.ones(768)
    with patch.object(DriftDetector, '_embed', return_value=vec):
        dd = DriftDetector(ctx, threshold=0.3, interval=10)
        dd.anchor = vec
        ctx.step_count = 10  # triggers check
        ctx.last_step = {"text": "same topic content here"}
        # Same vector → cosine 1.0 → distance 0.0 → < 0.3 threshold
        verdict = dd.validate()
        assert verdict == "ok"


def test_drift_detected(ctx):
    """When cosine distance > threshold → drift."""
    vec_anchor = np.ones(768)
    vec_drift = -np.ones(768)  # opposite direction → cosine -1.0 → distance 2.0
    with patch.object(DriftDetector, '_embed', side_effect=[vec_anchor, vec_drift]):
        dd = DriftDetector(ctx, threshold=0.3, interval=5)
        ctx.step_count = 5
        ctx.last_step = {"text": "completely unrelated cooking recipe"}
        verdict = dd.validate()
        assert verdict == "drift"


def test_drift_resolve_injects_correction(ctx):
    """resolve() adds a system injection message."""
    ctx_with_anchor = StepContext({
        "max_cost": 5.0,
        "anchor_prompt": "Research competitors",
    })
    dd = DriftDetector(ctx_with_anchor, threshold=0.2, interval=5)
    step = {"text": "irrelevant"}
    resolution = dd.resolve("drift", step)
    assert "Refocus immediately" in resolution["injection"]
    assert "_guard_injection" in step
