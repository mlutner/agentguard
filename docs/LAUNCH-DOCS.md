# AgentGuard — End-to-End Documentation

> The background nervous system that lets you stop watching your agents.

---

## OUTCOME THIS DELIVERS

**Before:** You set up an agent → it loops → it burns $40 → it saves results nowhere → you spend 2 hours debugging.

**After:** You add `@guard(max_cost=5.0, max_steps=100)` → the agent self-regulates → when it finishes or hits a boundary, you get a clean report. Nobody watched it.

---

## CURRENT METRICS (v0.1.0, April 4 2026)

```
Unit Tests:          17/17 passing (0.19s)
  - 4 cost regulator  (budget tracking, zero-cost models)
  - 4 guard decorator (async/sync/callable patterns, max_steps)
  - 3 heartbeat       (stall detection, force stop)
  - 6 loop breaker    (exact hash dedup, semantic frequency)
  - skip: drift (needs ollama, not installed in this env)

Adversarial:          5/5  passing (0.55s)
  - Exact loop detection
  - Semantic loop (same tool, different args)
  - Budget blow protection
  - Stall detection
  - No false positives (alternating tools)

Code:                12 Python files (~2500 lines)
  - 4 checks (loop_breaker, cost_regulator, drift_detector, heartbeat)
  - 3 adapters (langgraph, crewai, async/sync/callable)
  - 1 guard decorator (@guard entry point)
```

---

## HOW IT WORKS (ARCHITECTURE)

```
         @guard(max_cost=5.0, max_steps=100)
                            │
                            ▼
              ┌─────────────────────────┐
              │   Guarded Iteration     │
              │                         │
              │  1. Run loop checker    │ ← Detects: exact loops, semantic loops
              │  2. Run cost checker    │ ← Tracks: token usage, USD budget, hard cap
              │  3. Run heartbeat       │ ← Detects: stall timeout → force stop
              │  4. Run drift checker   │ ← Detects: intent drift (optional)
              │  5. Run agent step      │ ← Your agent proceeds
              └─────────────────────────┘
                     │          │
                     ▼          ▼
                 Keep/Stop  Interrupt
```

**The magic:** All checks run BEFORE each step. The agent cannot execute a step that would violate any boundary. No cleanup needed, no post-mortem, no dashboard to watch.

---

## LAUNCH ROADMAP

### Phase 1 ✅ (DONE — TODAY)
- Core SDK with 4 checks
- 17 unit tests + 5 adversarial benchmarks
- Framework adapters (LangGraph, CrewAI, async/sync/callable)
- MIT license

### Phase 2 (Week 1-2)
- pip install agentguard (PyPI)
- GitHub repo: public, with clear README
- 10 developers testing (free)
- Auto-research pipeline: adversarial → patch → commit loop

### Phase 3 (Month 2)
- Cloud layer: real-time dashboard, Slack/webhook alerts
- Pricing: $49-$199/mo for team features
- 1000+ GitHub stars

### Phase 4 (Month 3-6)
- Enterprise features: team policies, cost analytics, audit logs
- Integration marketplace: Claude Agents, LangChain, AutoGen
- Funding pitch

---

## WHAT TO BUILD NEXT (IN ORDER)

1. **PyPI upload** — `pip install agentguard` is the single best validation signal
2. **Auto-iteration cron** — Every 6h: adversarial generation → test → patch → re-test → commit if +5% improvement
3. **Stitch MCP integration** — Use Stitch API to generate demo agent behaviors → test them against AgentGuard
4. **Cloudflare Pages site** — https://agentguard.localpixel.ca with:
   - 30-second demo
   - Code examples
   - Benchmark results (live)
5. **Email campaign** — 50 engineering leads who've complained about agent babysitting on Twitter/HN

---

## RISK ASSESSMENT

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| Drift detection unreliable (without LLM judge) | HIGH | MEDIUM | Use local embeddings first; LLM judge as paid tier |
| Framework adapter breakage (LangChain/crewAI updates) | HIGH | HIGH | Pin versions; add version-aware adapter selection |
| LangGraph adds native guard features | MEDIUM | HIGH | Double down on framework-agnostic advantage |
| No adoption (too niche) | MEDIUM | CRITICAL | Target exact pain point: cost explosions, silent loops |
| Performance overhead >200ms/step | LOW | HIGH | Keep all checks rule-based; async-only; no blocking |
| Token pricing model goes stale | HIGH | LOW | Weekly cron updates from OpenRouter API |

---

## COMPETITIVE LANDSCAPE

| Product | What They Do | What They Don't Do | How AgentGuard Wins |
|---------|-------------|-------------------|--------------------|
| LangSmith | Observability dashboard | No enforcement, just reporting | We STOP agents before they break |
| PydanticAI | Output validation | No cost/budget limits, no drift detection | We validate the agent, not just the output |
| DSPy | Programmatic prompts | No runtime guard layer | We wrap their programs without modification |
| LangGraph | State machines + retries | Developers still write guard code | We drop in as a one-line decorator |

---

## AUTO-ITERATION PIPELINE (COMING SOON)

```
Cron (every 6h)
  │
  ├── 1. Qwen3-coder generates 20 adversarial agent behaviors
  ├── 2. Run against current AgentGuard
  ├── 3. Measure detection rate (current: 100% on 5 scenarios)
  ├── 4. If new attack pattern found:
  │   ├── Nemotron analyzes why guard missed it
  │   ├── Qwen3-coder generates fix
  │   ├── Run full test suite (17 tests)
  │   └── If pass + detection rate +5% → commit
  └── 5. Log scores to test-output/agentguard/benchmark_scores.json
```

---

## QUICK START (CURRENT)

```python
# Install (local only for now)
cd ~/Dev/agentguard && pip install -e .

# Use it
from agentguard import guard

@guard(max_cost=5.0, max_steps=100, anchor_prompt="Research competitors")
async def my_agent(query):
    for result in agent.run(query):
        yield {"type": "tool", "tool": "search", "args": result}

async for step in my_agent("Find top AI startups"):
    print(step)
```
