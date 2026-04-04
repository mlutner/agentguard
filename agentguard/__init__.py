"""AgentGuard — background nervous system for AI agents.

Usage:
    from agentguard import guard

    @guard(max_cost=5.0, max_steps=100, anchor_prompt="Research competitors...")
    async def my_agent(): ...
"""

from agentguard.guard import guard

__version__ = "0.1.0"
__all__ = ["guard"]
