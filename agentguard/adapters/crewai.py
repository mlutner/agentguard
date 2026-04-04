"""CrewAI adapter — hooks into agent execution callbacks."""

from __future__ import annotations
import asyncio
from typing import Any, AsyncIterator

from agentguard.adapters.base import BaseAdapter


class CrewAIAdapter(BaseAdapter):
    """Normalises CrewAI agent execution into step dicts.

    Uses CrewAI events/callbacks to capture:
    - tool usage
    - LLM responses
    - task completion
    """

    def wrap(self, agent_fn, *args, **kwargs) -> AsyncIterator[dict]:
        steps_queue = asyncio.Queue(maxsize=0)

        async def run_and_yield():
            # TODO: inject CrewAI callback to capture tool calls
            # For now, run the agent and yield a single final step
            task = asyncio.create_task(agent_fn(*args, **kwargs))

            while not task.done():
                await asyncio.sleep(0.1)
                yield {"type": "heartbeat", "alive": True}

            try:
                result = await task
                yield {"type": "final", "value": str(result)}
            except Exception as e:
                yield {"type": "error", "message": str(e)}

        return run_and_yield()
