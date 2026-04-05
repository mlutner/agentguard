# AgentGuard

Background nervous system for AI agents. Cost caps, loop breaking, drift detection, and memory management — without the agent knowing or caring.

**The pitch:** The thing that lets you stop watching your agents.

---

## Quick Start

```bash
pip install agentguard
```

```python
from agentguard import guard

@guard(max_cost=5.0, max_steps=100, anchor_prompt="Research competitors in AI")
async def research_agent(query):
    for result in agent.run(query):
        yield {"type": "tool", "tool": "search", "args": result}
```

---

## Four Checks That Run Before Every Agent Step

| Check | What It Catches | How It Works |
|-------|----------------|--------------|
| **Loop Breaker** | Exact duplicates + semantic loops | Hash tool+args, same-tool frequency in sliding window |
| **Cost Regulator** | Budget explosions (silent and loud) | tiktoken estimation, hard USD cap, instant shutdown |
| **Drift Detector** | Agent goes off-topic | Local embeddings (nomic-embed-text) vs. intent anchor |
| **Heartbeat** | Stalled agents (no progress for X seconds) | Per-instance timestamp, timeout enforcement |

---

## Current Metrics (v0.1.0 — April 4, 2026)

```
Unit Tests:          17/17 passing (0.19s)
Adversarial:          5/5  passing (0.55s)
Framework Adapters:  LangGraph, CrewAI, async/sync/callable
Code:               ~2500 lines, 12 Python files
License:            MIT
```

---

## Guard Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `max_cost` | float | 5.0 | Hard USD budget cap per guarded run |
| `max_steps` | int | 100 | Maximum agent steps before forced stop |
| `stall_timeout` | float | 120.0 | Seconds of no-progress before heartbeat kill |
| `drift_threshold` | float | **None** (off) | **Required if drift active**. Cosine distance threshold |
| `anchor_prompt` | str | None | Intent/topic anchor for drift detection |

---

## Launch Roadmap

### Phase 1 ✅ (DONE)
- Core SDK with 4 checks
- 22 test suite (17 unit + 5 adversarial benchmarks)
- Framework adapters (LangGraph, CrewAI, async/sync/callable)
- MIT license, public GitHub repo

### Phase 2 (Week 1-2)
- PyPI upload: `pip install agentguard`
- 10 developers testing (free)
- Auto-iteration pipeline (adversarial → patch → commit loop)

### Phase 3 (Month 2)
- Cloud layer: dashboard, Slack/webhook alerts, cost analytics
- Pricing: $49-$199/mo for team features
- 1000+ GitHub stars

### Phase 4 (Month 3-6)
- Enterprise: team policies, audit logs, integration marketplace
- Funding pitch

---

## Why This Wins

| Competitor | What They Do | How AgentGuard Wins |
|------------|-------------|-------------------|
| LangSmith | Observability dashboard | We STOP agents before they break |
| PydanticAI | Output validation | We protect the agent, not just the output |
| DSPy | Programmatic prompts | We wrap their programs without modification |

**Observability shows you the crash. We prevent it.**

---

## License

MIT
