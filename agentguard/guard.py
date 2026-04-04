"""@guard decorator — wraps any agent pattern into a guarded pipeline."""

from __future__ import annotations

import asyncio
import functools
from typing import Any, AsyncIterator, Callable, Iterator

from agentguard.state import StepContext
from agentguard.checks.heartbeat import Heartbeat, _set_start
from agentguard.checks.loop_breaker import LoopBreaker
from agentguard.checks.cost_regulator import CostRegulator

import time


def guard(
    *,
    max_cost: float = 5.0,
    max_steps: int = 100,
    stall_timeout: float = 120.0,
    drift_threshold: float | None = None,
    anchor_prompt: str | None = None,
    **kwargs: Any,
):
    """Wrap an agent function with background guard checks."""
    cfg = dict(
        max_cost=max_cost, max_steps=max_steps, stall_timeout=stall_timeout,
        drift_threshold=drift_threshold, anchor_prompt=anchor_prompt, **kwargs,
    )

    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **fn_kwargs: Any) -> AsyncIterator[dict]:
            ctx = StepContext(cfg)
            checks = _build_checks(ctx, cfg)
            _set_start(time.time())
            agent = fn(*args, **fn_kwargs)

            if hasattr(agent, "__aiter__"):
                it: AsyncIterator[dict] = agent
            elif hasattr(agent, "__iter__") and not isinstance(agent, dict):
                it = _sync_to_async(agent)
            else:
                it = _scalar_to_async(agent)

            async for step in _guarded_iter(it, ctx, checks):
                yield step

        return async_wrapper

    return decorator


async def _sync_to_async(sync_iter):
    for step in sync_iter:
        yield step


async def _scalar_to_async(scalar):
    yield _to_dict(scalar)


def _to_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    return {"type": "final", "value": value}


async def _guarded_iter(
    agent_iter: AsyncIterator[dict],
    ctx: StepContext,
    checks: list,
):
    async for step in agent_iter:
        if ctx.stopped:
            yield {"type": "interrupt", "reason": ctx._stop_reason}
            return

        # Run checks before recording this step
        for check in checks:
            verdict = check.validate()
            if verdict != "ok":
                resolution = check.resolve(verdict, step)
                yield resolution
                return

        # Record and then check step limit
        ctx.record(step)
        max_steps = ctx.cfg.get("max_steps", 100)
        if ctx.step_count >= max_steps:
            ctx.force_stop("max_steps_exceeded")
            yield {"type": "interrupt", "reason": "max_steps_exceeded"}
            return

        yield step


def _build_checks(ctx: StepContext, cfg: dict) -> list:
    checks = []
    checks.append(LoopBreaker(ctx, threshold=cfg.get("loop_threshold", 3)))
    checks.append(CostRegulator(ctx))
    if cfg.get("drift_threshold") is not None and cfg.get("anchor_prompt"):
        from agentguard.checks.drift_detector import DriftDetector
        checks.append(DriftDetector(
            ctx, threshold=cfg["drift_threshold"],
            interval=cfg.get("drift_interval", 10),
        ))
    return checks
