"""LangGraph/LangChain adapter — hooks into RunnableConfig callbacks."""

from __future__ import annotations
import asyncio
from typing import Any, AsyncIterator

from agentguard.adapters.base import BaseAdapter


class LangGraphAdapter(BaseAdapter):
    """Normalises LangGraph agent runs into step dicts.

    Uses LangGraph callbacks:
    - on_chat_model_start / on_chat_model_end → capture input/output
    - on_tool_start / on_tool_end → capture tool calls
    """

    def wrap(self, agent_fn, *args, **kwargs) -> AsyncIterator[dict]:
        """Returns an async generator that yields steps as LangGraph executes."""
        from langchain_core.callbacks import BaseCallbackHandler

        class GuardCallback(BaseCallbackHandler):
            def __init__(self):
                self.steps = asyncio.Queue(maxsize=0)  # unbounded

            def on_chain_start(self, serialized, inputs, **kw):
                pass  # not used for step tracking

            def on_tool_start(self, serialized, input_str, **kw):
                tool_name = serialized.get("name", "unknown") if serialized else "unknown"
                self.steps.put_nowait({
                    "type": "tool_start",
                    "tool": tool_name,
                    "args": input_str,
                })

            def on_chat_model_end(self, response, **kw):
                content = response.generations[0][0].text if response.generations else ""
                self.steps.put_nowait({
                    "type": "model_output",
                    "text": content,
                })

        callback = GuardCallback()

        # Run agent with guard callback
        async def run_and_yield():
            # Inject callback into kwargs
            run_kwargs = dict(*args, **kwargs)
            run_kwargs["config"] = {"callbacks": [callback]}

            # Start the agent in a task
            task = asyncio.create_task(agent_fn(**run_kwargs))

            # Yield steps as they arrive
            while not task.done() or not callback.steps.empty():
                try:
                    step = await asyncio.wait_for(callback.steps.get(), timeout=0.5)
                    yield step
                except asyncio.TimeoutError:
                    if task.done():
                        break

            # Wait for completion
            try:
                final = await task
                yield {"type": "final", "value": final}
            except Exception as e:
                yield {"type": "error", "message": str(e)}

        return run_and_yield()
