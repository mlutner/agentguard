"""Central step state shared by all checks."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional, List


@dataclass
class StepContext:
    """Mutable state visible to every check."""

    cfg: dict                         # guard() kwargs
    step_count: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    last_step: Optional[dict] = None
    action_window: List[dict] = field(default_factory=list)
    _stopped: bool = False
    _stop_reason: str = ""

    # sliding window for loop detection (tool call signatures)
    WINDOW_SIZE: int = 8

    def record(self, step: dict) -> None:
        self.step_count += 1
        self.last_step = step
        self.action_window.append(step)
        if len(self.action_window) > self.WINDOW_SIZE:
            self.action_window.pop(0)

    def force_stop(self, reason: str) -> None:
        self._stopped = True
        self._stop_reason = reason

    @property
    def stopped(self) -> bool:
        return self._stopped
