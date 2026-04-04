"""Loop detection — exact tool-call hash AND semantic frequency check."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


class LoopBreaker:
    """Two-layer loop detection:

    1. Exact-duplicate hash: flags the same tool + args repeated N+1 times
       (threshold=3 → flags on 4th identical call)
    2. Semantic frequency: flags the same tool called 5+ times in the last 8 steps
       *regardless* of argument variation (catches rephrased search loops)
    """

    def __init__(self, ctx, *, threshold: int = 3, same_tool_limit: int = 5):
        self.ctx = ctx
        self.hash_threshold = threshold
        self.same_tool_limit = same_tool_limit

    def validate(self) -> str:
        window = self.ctx.action_window
        if len(window) < 2:
            return "ok"

        # Layer 1: exact tool-call hash
        hashes = []
        for a in window:
            if isinstance(a, dict):
                tool = a.get("tool", a.get("type", ""))
                args = str(a.get("args", ""))
                h = hashlib.md5(f"{tool}::{args}".encode()).hexdigest()
            else:
                h = hashlib.md5(str(a).encode()).hexdigest()
            hashes.append(h)

        counts = Counter(hashes)
        if any(c > self.hash_threshold for c in counts.values()):
            return "exact_loop"

        # Layer 2: same tool, any args — 5+ in window of 8
        if len(window) >= self.same_tool_limit:
            tools = []
            for a in window[-self.ctx.WINDOW_SIZE:]:
                if isinstance(a, dict):
                    tools.append(a.get("tool", a.get("type", "")))
                else:
                    tools.append(str(a))
            tool_counts = Counter(tools)
            if any(c >= self.same_tool_limit for c in tool_counts.values()):
                dominant = max(tool_counts, key=tool_counts.get)
                return f"semantic_loop:{dominant}"

        return "ok"

    def resolve(self, verdict: str, step: dict) -> dict:
        self.ctx.force_stop(f"Loop breaker: {verdict}")
        return {"type": "interrupt", "reason": verdict}
