import asyncio
import torch
from typing import List, Dict, Any, Optional
from swarm_v2.core.qic._state import QState, QOperator, ManusProtocol
from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.artifact_pipeline import ArtifactPipeline

class ManusEngine:
    """
    The Orchestrator for Phase 3: Quantum Logic & Manus Protocol.
    Manages task superposition, parallel execution, and measurement collapse.
    """
    
    def __init__(self):
        self.protocol = ManusProtocol()
        self.pipeline = ArtifactPipeline()
        self.team = get_expert_team()
        self.active_superpositions: Dict[str, Dict[str, Any]] = {}

    async def create_superposition(self, task_name: str, task_description: str, agent_roles: List[str]) -> str:
        """
        Spins up multiple agents to solve the same task in parallel.
        """
        task_id = f"super-{task_name}-{len(self.active_superpositions)}"
        num_agents = len(agent_roles)
        
        # Initialize the wavefunction
        state = self.protocol.initialize_task_state(task_id, num_outcomes=num_agents)
        
        self.active_superpositions[task_id] = {
            "name": task_name,
            "description": task_description,
            "roles": agent_roles,
            "state": state,
            "attempts": {},
            "coherence": 0.0,
            "status": "SUPERPOSITION"
        }
        
        print(f"🌀 Created Superposition [{task_id}] with {num_agents} potential paths.")
        
        # Dispatch parallel tasks
        for idx, role in enumerate(agent_roles):
            asyncio.create_task(self._run_attempt(task_id, idx, role, task_description))
            
        return task_id

    async def _run_attempt(self, task_id: str, attempt_idx: int, role: str, description: str):
        """Runs a single path integral (agent attempt)."""
        agent = self.team.get(role)
        if not agent:
            print(f"⚠️ Agent {role} not found for attempt {attempt_idx}")
            return

        # Prepare specialized prompt for superposition
        prompt = (
            f"SUPERPOSITION TASK: {description}\n\n"
            "Produce your best implementation/solution. "
            "Focus on high-quality code and clear reasoning. "
            "You are competing in a parallel attempt - your success will increase your priority in the measurement gate."
        )
        
        # Use full process_task to leverage skills/tools
        result = await agent.process_task(prompt)
        
        # Calculate heuristics for "Quality" as evidence strength
        quality = self._calculate_evidence_strength(result)
        
        # Store attempt
        self.active_superpositions[task_id]["attempts"][attempt_idx] = {
            "role": role,
            "content": result,
            "quality": quality
        }
        
        # Apply interference to the task state
        self.protocol.update_state(task_id, attempt_idx, evidence_strength=quality)
        
        # Update coherence
        self._update_coherence(task_id)
        
        print(f"✨ Attempt {attempt_idx} ({role}) completed. Quality: {quality:.2f}. Coherence: {self.active_superpositions[task_id]['coherence']:.2f}")

    def _calculate_evidence_strength(self, result: str) -> float:
        """Heuristic evaluation for evidence strength."""
        strength = 0.5 # Baseline
        
        # Positive indicators
        if "```" in result: strength += 0.1 # Real code
        if "PLAN" in result.upper(): strength += 0.1 # Structured
        if "DEBUG" in result.upper() or "TEST" in result.upper(): strength += 0.1 # Robustness
        if len(result) > 800: strength += 0.1 # Comprehensive
        
        # Check for TRM reasoning markers (if any)
        if "RECURSIVE BRAIN" in result.upper() or "TRM" in result.upper():
            strength += 0.2
            
        return min(strength, 1.0)

    def _update_coherence(self, task_id: str):
        """Calculates coherence based on probability distribution stability."""
        data = self.active_superpositions[task_id]
        if not data["attempts"]:
            data["coherence"] = 0.0
            return
            
        probs = self.protocol.get_probabilities(task_id)
        if probs is None: return
        
        # Coherence = 1.0 - Entropy (normalized)
        # Simply: if one probability is clearly dominating, coherence is high.
        max_prob = torch.max(probs).item()
        
        # Simple coherence metric: progress of completions vs probability spread
        completion_ratio = len(data["attempts"]) / len(data["roles"])
        data["coherence"] = max_prob * completion_ratio

    def check_measurement_gate(self, task_id: str) -> bool:
        """Determines if the state is ready for collapse (>0.85 coherence)."""
        if task_id not in self.active_superpositions: return False
        
        # Allow collapse if all agents finished OR coherence is very high
        data = self.active_superpositions[task_id]
        all_finished = len(data["attempts"]) == len(data["roles"])
        
        if data["coherence"] >= 0.85 or all_finished:
            return True
        return False

    async def collapse_state(self, task_id: str) -> Dict[str, Any]:
        """Measurement Gate: Collapses the wavefunction into a single winning result."""
        if task_id not in self.active_superpositions:
            raise ValueError(f"Task {task_id} not found.")
            
        data = self.active_superpositions[task_id]
        
        # Use probabilistic resolve
        probs = self.protocol.get_probabilities(task_id)
        winner_idx = torch.argmax(probs).item() # Deterministic collapse for production stability
        
        winner = data["attempts"].get(winner_idx)
        if not winner:
            # Fallback to whatever is available
            winner_idx = list(data["attempts"].keys())[0]
            winner = data["attempts"][winner_idx]
            
        data["status"] = "COLLAPSED"
        data["winner_idx"] = winner_idx
        
        print(f"⚖️ Measurement Gate Triggered! Wavefunction collapsed into Path {winner_idx} ({winner['role']})")
        
        # Integrate into real filesystem/pipeline
        filename = f"{data['name']}_FINAL.md"
        from swarm_v2.skills.file_skill import FileSkill
        FileSkill().write_file(filename, winner["content"])
        
        self.pipeline.register_artifact(filename, created_by=winner["role"])
        self.pipeline.approve(filename, reviewer="Manus Measurement Gate", notes=f"Resolved from {len(data['roles'])} parallel attempts.")
        
        return winner

def get_manus_engine():
    return ManusEngine()
