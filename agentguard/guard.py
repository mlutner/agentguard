"""@guard decorator — wraps any agent pattern into a guarded pipeline."""

from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, AsyncIterator, Callable, Iterator

from agentguard.state import StepContext

# lazy imports — don't pull heavy deps unless the adapter is used
# Checks
from agentguard.checks.heartbeat import Heartbeat
from agentguard.checks.loop_breaker import LoopBreaker
from agentguard.checks.cost_regulator import CostRegulator


def guard(
    *,
    max_cost: float = 5.0,
    max_steps: int = 100,
    stall_timeout: float = 120.0,
    drift_threshold: float | None = None,   # REQUIRED if drift should be active
    anchor_prompt: str | None = None,
    **kwargs: Any,
):
    """Wrap an agent function with background guard checks.

    Supports three calling patterns transparently:
    1. async generator   (async def agent(): yield step)
    2. sync generator    (def agent(): yield step)
    3. plain callable    (def agent(): return result)

    Parameters
    ----------
    max_cost : float
        Hard-capped USD budget per guarded run.
    max_steps : int
        Maximum number of agent steps before forced stop.
    stall_timeout : float
        Seconds of no-progress before heartbeat triggers.
    drift_threshold : float | None
        Cosine distance threshold (0.0-1.0) for drift detection.
        MUST be supplied if drift detection is desired.
    anchor_prompt : str | None
        The intent / topic anchor for drift detection.
    """

    cfg = dict(
        max_cost=max_cost,
        max_steps=max_steps,
        stall_timeout=stall_timeout,
        drift_threshold=drift_threshold,
        anchor_prompt=anchor_prompt,
        **kwargs,
    )

    def decorator(fn: Callable):

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **fn_kwargs: Any) -> AsyncIterator[dict]:
            ctx = StepContext(cfg)
            checks = _build_checks(ctx, cfg)

            start = time.time()
            from agentguard.checks.heartbeat import _set_start
            _set_start(start)

            agent = fn(*args, **fn_kwargs)

            # Normalise to async iterator
            if hasattr(agent, "__aiter__"):
                it: AsyncIterator[dict] = agent
            elif hasattr(agent, "__iter__"):
                it = _sync_to_async(agent)
            else:
                it = _scalar_to_async(agent)

            async for step in _guarded_iter(it, ctx, checks):
                yield step

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **fn_kwargs: Any) -> Iterator[dict]:
            ctx = StepContext(cfg)
            checks = _build_checks(ctx, cfg)

            start = time.time()
            from agentguard.checks.heartbeat import _set_start
            _set_start(start)

            agent = fn(*args, **fn_kwargs)

            if hasattr(agent, "__iter__") and not hasattr(agent, "__aiter__"):
                it_sync: Iterator[dict] = agent
            elif hasattr(agent, "__aiter__"):
                it_sync = _async_to_sync(agent)
            else:
                it_sync = iter([{**_to_dict(agent)}])

            yield from _guarded_iter_sync(it_sync, ctx, checks)

        # Pick the right wrapper based on original fn type
        import inspect
        if asyncio.iscoroutinefunction(fn) or inspect.isasyncgenfunction(fn):
            return async_wrapper
        return sync_wrapper

    return decorator


# ---------------------------------------------------------------------------
# Adapters — normalise heterogeneous agent outputs into async iteration
# ---------------------------------------------------------------------------

async def _sync_to_async(sync_iter):
    for step in sync_iter:
        yield step


async def _scalar_to_async(scalar):
    yield _to_dict(scalar)


def _async_to_sync(async_iter):
    loop = asyncio.get_event_loop()
    try:
        while True:
            yield loop.run_until_complete(async_iter.__anext__())
    except StopAsyncIteration:
        return


def _to_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    return {"type": "final", "value": value}


# ---------------------------------------------------------------------------
# Guarded iteration — runs checks between every step
# ---------------------------------------------------------------------------

async def _guarded_iter(
    agent_iter: AsyncIterator[dict],
    ctx: StepContext,
    checks: list,
):
    async for step in agent_iter:
        if ctx.stopped:
            yield {"type": "interrupt", "reason": ctx._stop_reason}
            return

        ctx.record(step)

        for check in checks:
            verdict = check.validate()
            if verdict != "ok":
                resolution = check.resolve(verdict, step)
                yield resolution
                if ctx.stopped:
                    return

        # Step limit (built-in, not a separate check)
        if ctx.step_count >= ctx.cfg.get("max_steps", 100):
            ctx.force_stop("max_steps_exceeded")
            yield {"type": "interrupt", "reason": "max_steps_exceeded"}
            return

        yield step


def _guarded_iter_sync(
    agent_iter: Iterator[dict],
    ctx: StepContext,
    checks: list,
):
    for step in agent_iter:
        if ctx.stopped:
            yield {"type": "interrupt", "reason": ctx._stop_reason}
            return

        ctx.record(step)

        for check in checks:
            verdict = check.validate()
            if verdict != "ok":
                resolution = check.resolve(verdict, step)
                yield resolution
                if ctx.stopped:
                    return

        if ctx.step_count >= ctx.cfg.get("max_steps", 100):
            ctx.force_stop("max_steps_exceeded")
            yield {"type": "interrupt", "reason": "max_steps_exceeded"}
            return

        yield step


# ---------------------------------------------------------------------------
# Check factory
# ---------------------------------------------------------------------------

def _build_checks(ctx: StepContext, cfg: dict) -> list:
    checks = []

    # Always active
    checks.append(LoopBreaker(ctx, threshold=cfg.get("loop_threshold", 3)))
    checks.append(CostRegulator(ctx))

    # Optional drift (developer MUST supply drift_threshold to activate)
    if cfg.get("drift_threshold") is not None and cfg.get("anchor_prompt"):
        from agentguard.checks.drift_detector import DriftDetector
        checks.append(DriftDetector(
            ctx,
            threshold=cfg["drift_threshold"],
            interval=cfg.get("drift_interval", 10),
        ))

    return checks
