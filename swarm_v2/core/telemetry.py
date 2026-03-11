
import os
import psutil
from typing import Dict, Any, List
from datetime import datetime
# from swarm_v2.core.manus_engine import get_manus_engine
from swarm_v2.core.resource_arbiter import get_resource_arbiter
from swarm_v2.core.coherence_thresholds import CoherenceThresholds
from swarm_v2.core.proactive_loop import get_proactive_loop
from swarm_v2.skills.relationship_skill import RelationshipReasoningSkill
from typing import Optional

class SwarmTelemetry:
    """
    Emergence Hub Telemetry (Phase 4).
    Aggregates live metrics from the Mesh, Manus Engine, and Resource Arbiter.
    """

    def __init__(self):
        self.manus = None # get_manus_engine()
        self.arbiter = get_resource_arbiter()
        self.proactive = get_proactive_loop()
        self.harmony_monitor = RelationshipReasoningSkill()

    def get_emergence_report(self) -> Dict[str, Any]:
        """
        Generates a comprehensive snapshot of the swarm's current state.
        """
        # 1. System Stability
        mem = psutil.virtual_memory()
        system_stats = {
            "cpu_load": psutil.cpu_percent(),
            "memory_usage": mem.percent,
            "timestamp": datetime.now().isoformat()
        }
        
        # 2. Vibe/Coherence Status
        stability_level = CoherenceThresholds.check_stability(system_stats)
        
        # 3. Quantum-Inspired States (Manus Protocol)
        active_superpositions = []
        for tid, data in self.manus.active_superpositions.items():
            active_superpositions.append({
                "task_id": tid,
                "name": data["name"],
                "coherence": data["coherence"],
                "status": data["status"],
                "paths": len(data["roles"])
            })
            
        # 4. Resource Allocation
        vram_stats = self.arbiter.get_status()
        
        # 5. Distributed Stack Health
        from swarm_v2.experts.registry import get_expert_team
        team = get_expert_team()
        stack_stats = []
        for role, agent in team.items():
            if hasattr(agent, "cognitive_stack"):
                stack_stats.append(agent.cognitive_stack.get_status())
        
        return {
            "status": stability_level,
            "system": system_stats,
            "superpositions": active_superpositions,
            "resource_arbiter": vram_stats,
            "distributed_stacks": stack_stats,
            "mesh_coherence": self._calculate_global_coherence(active_superpositions),
            "harmony_index": self.harmony_monitor.get_harmony_index(),
            "active_proposals": len(self.proactive.get_active_proposals())
        }

    def get_soul_report(self) -> Dict[str, Any]:
        """
        Aggregates philosophical status and autonomous evolution proposals.
        """
        return {
            "harmony_index": self.harmony_monitor.get_harmony_index(),
            "reflection": self.harmony_monitor.generate_alignment_reflection(),
            "autonomous_proposals": self.proactive.get_active_proposals(),
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_global_coherence(self, superpositions: List[Dict]) -> float:
        """Calculates global swarm coherence as the average of active tasks."""
        if not superpositions:
            return 1.0 # Optimal state if idle
        
        total_coherence = sum(s["coherence"] for s in superpositions)
        return total_coherence / len(superpositions)

_telemetry: Optional['SwarmTelemetry'] = None

def get_telemetry() -> 'SwarmTelemetry':
    global _telemetry
    if _telemetry is None:
        _telemetry = SwarmTelemetry()
    return _telemetry
