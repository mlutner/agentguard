"""Stall detection — if no step in stall_timeout seconds, force stop."""

from __future__ import annotations
import time
from typing import Any


class Heartbeat:
    """Raises an interrupt if the agent has made no progress for stall_timeout."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.start_time = time.time()  # per-instance timestamp
        self.last_activity = self.start_time
        self.timeout = ctx.cfg.get("stall_timeout", 120.0)

    def validate(self) -> str:
        if time.time() - self.last_activity > self.timeout:
            return "stall"
        return "ok"

    def resolve(self, verdict: str, step: dict) -> dict:
        self.ctx.force_stop("Heartbeat stall timeout")
        return {"type": "interrupt", "reason": "heartbeat_stall"}
