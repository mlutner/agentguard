"""Base adapter — all framework adapters normalise output into:
  async yield -> dict with at least {"type": ..., "tool": ..., "args": ...}

Implementations must provide:
  wrap(agent_fn) -> async generator yielding step dicts
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class BaseAdapter(ABC):
    @abstractmethod
    def wrap(self, agent_fn, *args: Any, **kwargs: Any) -> AsyncIterator[dict]:
        ...
