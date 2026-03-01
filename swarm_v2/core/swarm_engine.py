
import asyncio
import logging
from typing import List, Dict, Any
from enum import Enum
from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.base_agent import Message

logger = logging.getLogger("SwarmEngine")


class ComplianceMode(Enum):
    """Adaptive compliance modes from the QIAE framework."""
    SOLO_NINJA = "solo_ninja"        # Minimal gates, single fast-track, skip security audit
    AGILE_SQUAD = "agile_squad"      # Standard team, plan verification, moderate security
    SOFTWARE_FACTORY = "software_factory"  # Mandatory security audit, full pipeline gates


# Mode configuration presets
MODE_CONFIG = {
    ComplianceMode.SOLO_NINJA: {
        "security_audit": False,
        "approval_gates": False,
        "team_size": "minimal",        # Use only the required specialist
        "pipeline_gates": False,
        "description": "Optimized for speed; hybrid agents with cross-domain capabilities.",
    },
    ComplianceMode.AGILE_SQUAD: {
        "security_audit": True,
        "approval_gates": False,       # Auto-approve in agile mode
        "team_size": "standard",       # Full team with plan verification
        "pipeline_gates": True,
        "description": "Coordinated workflow with plan verification; focused specialist agents.",
    },
    ComplianceMode.SOFTWARE_FACTORY: {
        "security_audit": True,
        "approval_gates": True,        # Manual approval required
        "team_size": "full",           # Maximum standardization
        "pipeline_gates": True,
        "description": "Mandatory security audits and quality gates; maximum standardization.",
    },
}


class SwarmEngine:
    def __init__(self):
        self.team = get_expert_team()
        self.history = []
        self.compliance_mode = ComplianceMode.AGILE_SQUAD
        self._mode_config = MODE_CONFIG[self.compliance_mode]
        logger.info(f"SwarmEngine initialized in {self.compliance_mode.value} mode")

    def set_compliance_mode(self, mode: ComplianceMode):
        """Switch operational compliance mode."""
        self.compliance_mode = mode
        self._mode_config = MODE_CONFIG[mode]
        logger.info(f"[SwarmEngine] Compliance mode set to: {mode.value} — "
                    f"{self._mode_config['description']}")
        return self._mode_config

    def get_mode_config(self) -> Dict[str, Any]:
        """Get the current compliance mode configuration."""
        return {
            "mode": self.compliance_mode.value,
            **self._mode_config,
        }

    def requires_security_audit(self) -> bool:
        """Check if the current mode requires security auditing."""
        return self._mode_config["security_audit"]

    def requires_approval_gates(self) -> bool:
        """Check if the current mode requires manual approval gates."""
        return self._mode_config["approval_gates"]

    async def broadcast(self, content: str, sender: str = "user"):
        # In Solo-Ninja, only broadcast to the most relevant agent
        if self.compliance_mode == ComplianceMode.SOLO_NINJA:
            # Fast-track: delegate to Architect only for routing
            if "Architect" in self.team:
                return {"Architect": await self.team["Architect"].process_task(content, sender=sender)}

        tasks = []
        for role, agent in self.team.items():
            tasks.append(agent.process_task(content, sender=sender))
        
        responses = await asyncio.gather(*tasks)
        return dict(zip(self.team.keys(), responses))

    async def delegate_to(self, role: str, task: str, sender: str = "user"):
        if role not in self.team:
            return f"Error: Expert with role '{role}' not found in team."

        # Software-Factory: run security audit before delegation
        if self.requires_security_audit():
            try:
                from swarm_v2.core.neural_wall import get_neural_wall
                wall = get_neural_wall()
                detection = wall.analyze(task)
                if detection.is_malicious:
                    logger.warning(f"[SwarmEngine] Task blocked by NeuralWall: {detection.description}")
                    return f"BLOCKED: Security audit flagged this task — {detection.description}"
            except Exception as e:
                logger.warning(f"[SwarmEngine] Security audit unavailable: {e}")
        
        agent = self.team[role]
        response = await agent.process_task(task, sender=sender)
        return response

    def get_status(self):
        return {
            "compliance_mode": self.compliance_mode.value,
            "mode_config": self._mode_config,
            "agents": {role: {"id": agent.agent_id, "name": agent.persona.name}
                       for role, agent in self.team.items()},
        }
