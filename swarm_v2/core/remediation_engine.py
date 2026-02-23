"""
Swarm V2 Remediation Engine
Phase 4: Shell-01 (Recursive Self-Healing)

This engine responds to issues reported by the `monitor_daemon.py`.
It autonomously applies corrective actions based on the issue type
and defined policy levels in `coherence_thresholds.py`.

It can restart specific agents, rollback deployments, or escalate to human intervention.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from swarm_v2.core.coherence_thresholds import CoherenceThresholds
from swarm_v2.experts.registry import EXPERTS_CONFIG
from swarm_v2.core.base_agent import BaseAgent, AgentPersona
# Import Skill Classes for reconstruction
from swarm_v2.skills.file_skill import FileSkill, ShellSkill, WebSearchSkill, CodeAnalysisSkill, DataSkill, DocSkill
from swarm_v2.skills.doc_ingestion_skill import DocIngestionSkill

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Remediation] %(message)s",
    handlers=[
        logging.FileHandler("swarm_v2_artifacts/remediation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RemediationEngine")

class RemediationEngine:
    def __init__(self, team_ref: Dict[str, Any]):
        self.team = team_ref  # Reference to the live agent dictionary
        self.active_issues: Dict[str, Any] = {}
        self.action_history: list = []

    async def handle_issue(self, issue_type: str, details: str):
        """
        Main entry point for remediation logic.
        Decides on the action level based on the issue type.
        """
        logger.info(f"Received Issue: {issue_type} - {details}")
        
        # Determine Severity Level
        level = self._determine_level(issue_type)
        action = self._determine_action(level)
        
        # Execute Action
        result = await self._execute_action(level, action, details)
        
        # Log resolution attempt (Phase 4 requirement: autonomous logging)
        self.action_history.append({
            "type": issue_type,
            "level": level,
            "action": action,
            "result": result,
            "timestamp": "now" # In real system datetime.now()
        })
        return result

    def _determine_level(self, issue_type: str) -> str:
        """Map issue types to remediation levels."""
        if issue_type == "AGENT_TIMEOUT":
            return CoherenceThresholds.LEVEL_2_RESTART
        elif issue_type == "MESH_INTEGRITY":
            return CoherenceThresholds.LEVEL_3_ROLLBACK
        elif issue_type == "HIGH_CPU":
            return CoherenceThresholds.LEVEL_1_WARNING
        elif issue_type == "CRITICAL_FAIL":
            return CoherenceThresholds.LEVEL_4_EMERGENCY
        return CoherenceThresholds.LEVEL_1_WARNING

    def _determine_action(self, level: str) -> str:
        """Map levels to specific action functions."""
        if level == CoherenceThresholds.LEVEL_2_RESTART:
            return "Restart Agent"
        if level == CoherenceThresholds.LEVEL_3_ROLLBACK:
            return "Rollback Deployment"
        if level == CoherenceThresholds.LEVEL_4_EMERGENCY:
            return "Full System Reset"
        return "Log Only"

    async def _execute_action(self, level: str, action: str, target: str) -> str:
        """Perform the automated remediation action."""
        if level == CoherenceThresholds.LEVEL_1_WARNING:
            logger.warning(f"⚠️ [Monitor Alert] Issue detected: {target}. Logging only.")
            return "Logged"

        if level == CoherenceThresholds.LEVEL_2_RESTART:
            logger.info(f"🔄 Attempting restart of agent: {target}")
            success = await self._restart_agent(target)
            if success:
                logger.info(f"✅ Successfully restarted agent: {target}")
                return "Configured Restart Successful"
            else:
                logger.error(f"❌ Restart failed for agent: {target}")
                return "Restart Failed"

        if level == CoherenceThresholds.LEVEL_3_ROLLBACK:
            logger.critical(f"🛑 Initiating Rollback due to integrity failure: {target}")
            # Simulate rollback logic
            return "Rollback Triggered"

        if level == CoherenceThresholds.LEVEL_4_EMERGENCY:
            logger.critical(f"🔥🔥🔥 EMERGENCY RESET TRIGGERED! Reason: {target}")
            # Simulate hard reset
            return "Reset Triggered"

        return "Unknown Action"

    async def _restart_agent(self, role: str) -> bool:
        """Re-initialize an agent from config and replace it in the team dict."""
        print(f"[Remediation] Restarting {role}...")
        
        # Find config
        cfg = next((c for c in EXPERTS_CONFIG if c["role"] == role), None)
        if not cfg:
            logger.error(f"No config found for role: {role}")
            return False

        try:
            # Reconstruct Persona
            persona = AgentPersona(
                name=cfg["name"],
                role=cfg["role"],
                background=cfg["background"],
                specialties=cfg["specialties"],
                avatar_color=cfg.get("avatar_color", "#00ff41"),
                model=cfg.get("model"),
            )
            # Reconstruct Skills
            skills = [SkillClass() for SkillClass in cfg.get("skills", [])]
            
            # Create new Agent instance
            new_agent = BaseAgent(persona, skills=skills)
            
            # Replace in live dictionary
            self.team[role] = new_agent
            
            # Re-register with Mesh (since it's a new agent ID)
            # We need to import get_agent_mesh here to avoid circular imports at top level if possible,
            # or rely on app_v2 to handle mesh registration. 
            # Ideally, the agent should register itself, but BaseAgent doesn't do that automatically in __init__.
            # Let's do it manually here.
            from swarm_v2.core.agent_mesh import get_agent_mesh
            mesh = get_agent_mesh()
            mesh.register_node(
                name=persona.name,
                role=role,
                specialties=persona.specialties,
                skills=new_agent.get_skill_names(),
                host="127.0.0.1",
                port=8000
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to restart agent {role}: {e}")
            return False

if __name__ == "__main__":
    # Test harness
    engine = RemediationEngine({})
    # asyncio.run(engine.handle_issue("AGENT_TIMEOUT", "Archi"))
