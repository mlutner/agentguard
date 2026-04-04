# AgentGuard

Background nervous system for AI agents. Cost caps, loop breaking, drift detection, and memory management — without the agent knowing or caring.

**The pitch:** The thing that lets you stop watching your agents.

## Quick Start

```bash
pip install agentguard
```

```python
from agentguard import guard

@guard(max_cost=5.0, max_steps=100, anchor_prompt="Research competitors in AI")
async def research_agent(query):
    # Your agent code here — yields step dicts
    for result in agent.run(query):
        yield {"type": "tool", "tool": "search", "args": result}
```

## Guard Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `max_cost` | float | No | Hard USD budget cap (default: 5.0) |
| `max_steps` | int | No | Maximum agent steps (default: 100) |
| `stall_timeout` | float | No | Seconds of no-progress before heartbeat kill |
| `drift_threshold` | float | **Required for drift** | Cosine distance threshold (0.0-1.0) |
| `anchor_prompt` | str | Required with drift | Intent/topic anchor for drift detection |

## Four Checks

### 1. Loop Breaker
Detects:
- **Exact loops**: Same tool + same args repeated N times
- **Semantic loops**: Same tool called 5+ times in last 8 steps (catches rephrased search loops)

### 2. Cost Regulator
Tracks token consumption per step. Shuts down agent when `max_cost` is reached.
Uses tiktoken for estimation, pricing from `pricing/models.json`.

### 3. Drift Detector
Embeds anchor_prompt + current step text via local ollama (nomic-embed-text).
If cosine distance > `drift_threshold`, injects a "refocus" correction into the step.

### 4. Heartbeat
If no agent step in `stall_timeout` seconds, force-stops with interrupt.

## Framework Adapters

| Framework | Status |
|-----------|--------|
| Async generators | ✅ Native support |
| Sync generators | ✅ Auto-wrapped |
| Plain callables | ✅ Single-step wrapper |
| LangGraph | ✅ Callback-based adapter |
| CrewAI | ✅ (basic — extends as needed) |

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

## License

MIT
