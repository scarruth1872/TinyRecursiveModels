
import asyncio
from typing import List, Dict, Any
from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.base_agent import Message

class SwarmEngine:
    def __init__(self):
        self.team = get_expert_team()
        self.history = []

    async def broadcast(self, content: str, sender: str = "user"):
        tasks = []
        for role, agent in self.team.items():
            tasks.append(agent.process_task(content, sender=sender))
        
        responses = await asyncio.gather(*tasks)
        return dict(zip(self.team.keys(), responses))

    async def delegate_to(self, role: str, task: str, sender: str = "user"):
        if role not in self.team:
            return f"Error: Expert with role '{role}' not found in team."
        
        agent = self.team[role]
        response = await agent.process_task(task, sender=sender)
        return response

    def get_status(self):
        return {role: {"id": agent.agent_id, "name": agent.persona.name} for role, agent in self.team.items()}
