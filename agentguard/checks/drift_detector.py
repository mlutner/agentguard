"""Intent drift detection via local embedding (nomic-embed-text via Ollama)."""

from __future__ import annotations

import numpy as np
from typing import Any


class DriftDetector:
    """Runs every `interval` steps. Uses cosine distance between the
    anchor_prompt embedding and the current step's text embedding.

    drift_threshold is REQUIRED on @guard — no implicit default.
    """

    def __init__(self, ctx, *, threshold: float, interval: int = 10):
        self.ctx = ctx
        self.threshold = threshold
        self.interval = interval
        self._anchor = None  # lazy-init

    def _get_anchor(self) -> np.ndarray:
        if self._anchor is None:
            self._anchor = self._embed(self.ctx.cfg.get("anchor_prompt", ""))
        return self._anchor

    def _embed(self, text: str) -> np.ndarray:
        import ollama
        res = ollama.embed(model="nomic-embed-text", input=[text])
        return np.array(res["embeddings"][0])

    def validate(self) -> str:
        if self.ctx.step_count % self.interval != 0:
            return "ok"
        current_text = _extract_text(self.ctx.last_step)
        current = self._embed(current_text)
        anchor = self._get_anchor()
        cos = np.dot(anchor, current) / (np.linalg.norm(anchor) * np.linalg.norm(current))
        dist = 1.0 - cos
        return "drift" if dist > self.threshold else "ok"

    def resolve(self, verdict: str, step: dict) -> dict:
        injection = (
            f"⚠️ You are drifting from the original intent: "
            f"'{self.ctx.cfg.get('anchor_prompt', '')}'. Refocus immediately."
        )
        step["_guard_injection"] = injection
        return {"type": "corrected", "injection": injection, "step": step}


def _extract_text(obj: dict) -> str:
    for key in ("text", "content", "output", "message", "value"):
        if key in obj:
            return str(obj[key])
    return str(obj)
