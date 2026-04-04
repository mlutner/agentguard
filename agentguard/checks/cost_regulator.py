"""Token cost tracking with hard cap — uses tiktoken for estimation."""

from __future__ import annotations

import tiktoken
from typing import Any


_PRICING = {
    "openai/gpt-4o":             {"input_per_1k": 0.0050, "output_per_1k": 0.0150},
    "anthropic/claude-sonnet-4": {"input_per_1k": 0.0030, "output_per_1k": 0.0150},
    "qwen/qwen3-coder":          {"input_per_1k": 0.00022, "output_per_1k": 0.0100},
    "qwen/qwen3.6-plus":         {"input_per_1k": 0.00000, "output_per_1k": 0.00000},
}


class CostRegulator:
    """Tracks cumulative token cost. Shuts down agent when budget is blown."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.model = ctx.cfg.get("model", "openai/gpt-4o")
        self.pricing = _PRICING.get(self.model, _PRICING["openai/gpt-4o"])
        try:
            self.enc = tiktoken.encoding_for_model("gpt-4o")
        except Exception:
            self.enc = tiktoken.get_encoding("cl100k_base")

    def validate(self) -> str:
        text_out = _extract_text(self.ctx.last_step or {})
        tokens_out = len(self.enc.encode(text_out))
        text_in = ""
        for a in self.ctx.action_window:
            if isinstance(a, dict):
                text_in += str(a.get("text", a.get("message", "")))
            else:
                text_in += str(a)
        tokens_in = len(self.enc.encode(text_in))

        cost_in = tokens_in * self.pricing["input_per_1k"] / 1000
        cost_out = tokens_out * self.pricing["output_per_1k"] / 1000
        self.ctx.total_cost += cost_in + cost_out
        self.ctx.total_tokens += tokens_in + tokens_out

        if self.ctx.total_cost >= self.ctx.cfg.get("max_cost", 5.0):
            return "budget_exceeded"
        return "ok"

    def resolve(self, verdict: str, step: dict) -> dict:
        self.ctx.force_stop(f"Cost cap (${self.ctx.cfg['max_cost']}) reached. "
                            f"Spent: ${self.ctx.total_cost:.4f}")
        return {"type": "stop", "reason": verdict, "total_cost": self.ctx.total_cost}


def _extract_text(obj: dict) -> str:
    for key in ("text", "content", "output", "message", "value"):
        if key in obj:
            return str(obj[key])
    return str(obj)
