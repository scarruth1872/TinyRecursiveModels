
from typing import Dict, Any, Optional

class ExpertRegistry:
    """A global registry to connect live agent instances across the swarm."""
    _instance = None
    _team: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExpertRegistry, cls).__new__(cls)
        return cls._instance

    def register_team(self, team: Dict[str, Any]):
        """Register the live expert team (Role -> Agent Instance)."""
        self._team = team

    def get_agent(self, identifier: str) -> Optional[Any]:
        """Retrieve a live agent instance by their role or name."""
        # 1. Try direct role match (Legacy/Primary)
        if identifier in self._team:
            return self._team[identifier]
            
        # 2. Try name match
        for agent in self._team.values():
            if hasattr(agent, "persona") and agent.persona.name == identifier:
                return agent
        return None

    def get_all_agents(self) -> Dict[str, Any]:
        return self._team

def get_expert_registry() -> ExpertRegistry:
    return ExpertRegistry()
