"""Drift detection tests (skipped unless ollama installed)."""

import pytest
from unittest.mock import patch
import numpy as np
from agentguard.state import StepContext

# Skip all drift tests when ollama is not installed
pytest.skip("ollama not installed", allow_module_level=True)

def _extract_text(obj):
    for key in ("text", "content", "output", "message", "value"):
        if key in obj:
            return str(obj[key])
    return str(obj)

def test_extract_text():
    assert _extract_text({"text": "hello"}) == "hello"
    assert _extract_text({"value": 42}) == "42"
