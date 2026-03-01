import asyncio
import uuid
import logging
import time
from typing import Dict, List, Any
from datetime import datetime

# Assuming existing modules are accessible
from swarm_v2.core.trm_brain import get_trm_brain
from swarm_v2.core.global_memory import get_global_memory
from swarm_v2.experts.registry import get_expert_team

logger = logging.getLogger("CollabReasoning")

class CollaborativeReasoningEngine:
    """
    Phase 7: Collaborative Reasoning Amplification (CRA).
    Enables agents to share intermediate TRM states to amplify collective reasoning.
    """
    
    def __init__(self):
        self.trm_brain = get_trm_brain()
        self.global_memory = get_global_memory()
        self.agents = get_expert_team()
        self.active_sessions: Dict[str, Dict] = {}
        # Phase 7: Session history for performance meta-analysis
        self.session_history: List[Dict] = []

    async def amplify_reasoning(self, problem_statement: str, required_roles: List[str] = None) -> Dict:
        """
        Coordinates a multi-agent reasoning session to solve a complex problem.
        """
        session_id = f"cra_{uuid.uuid4().hex[:8]}"
        t_start = time.time()
        logger.info(f"[{session_id}] Initiating Collaborative Reasoning Amplification")
        
        # 1. Determine participating agents
        participants = required_roles or ["Logic", "Archi", "Devo"]
        active_agents = {role: self.agents[role] for role in participants if role in self.agents}
        
        if not active_agents:
            return {"error": "No capable agents available for reasoning."}

        self.active_sessions[session_id] = {
            "problem": problem_statement,
            "participants": list(active_agents.keys()),
            "states": {},
            "status": "active",
            "start_time": datetime.now().isoformat()
        }

        # 2. Initial Reasoning Phase: Each agent processes independently using TRM
        logger.info(f"[{session_id}] Phase 1: Distributed Initial Reasoning")
        initial_tasks = []
        for role, agent in active_agents.items():
            # Construct a prompt tailored to their role but focused on the core problem
            prompt = f"Analyze this problem from your perspective ({role}): {problem_statement}. Provide your initial logical breakdown."
            initial_tasks.append(self._gather_initial_state(session_id, role, agent, prompt))
            
        await asyncio.gather(*initial_tasks)

        # 3. Intermediate State Sharing & Amplification
        logger.info(f"[{session_id}] Phase 2: State Sharing & Amplification")
        
        # Compile shared state
        shared_context = f"Problem: {problem_statement}\n\nIntermediate States:\n"
        for role, data in self.active_sessions[session_id]["states"].items():
            shared_context += f"--- {role} ---\n{data.get('content', '')}\n\n"
            
        # Store in Global Memory for persistence
        self.global_memory.contribute(
            content=shared_context,
            author="Swarm Collective",
            author_role="CRA_Engine",
            memory_type="reasoning_state",
            tags=["phase7", "amplification", session_id]
        )

        # 4. Consensus Formation (typically driven by Logic or Lead Developer)
        logger.info(f"[{session_id}] Phase 3: Consensus Formation")
        synthesizer_role = "Logic" if "Logic" in active_agents else list(active_agents.keys())[0]
        synthesizer = active_agents[synthesizer_role]
        
        consensus_prompt = (
            f"Review the shared reasoning states from the team:\n{shared_context}\n"
            f"Synthesize these perspectives into a final, unified, and amplified solution. "
            f"Identify any emergent patterns or insights that single agents missed.\n"
            f"Please output a detailed synthesis outlining the final consensus."
        )
        
        final_result = await synthesizer.process_task(consensus_prompt, sender="CRA_Engine")
        
        # Determine actual output
        amplified_solution = final_result
        if isinstance(final_result, dict):
            amplified_solution = final_result.get("response", "Failed to extract final response.")

        if "Failed to extract" in amplified_solution or not amplified_solution:
            logger.warning(f"[{session_id}] Synthesis empty, forcing raw concatenation")
            amplified_solution = f"Synthesis from team:\n{shared_context}"

        # 4b. Interference Pass (Reflect-and-Critique)
        interference_events = 0
        for interference_round in range(2):  # Max 2 interference passes
            critique_tasks = []
            for role, agent in active_agents.items():
                if role == synthesizer_role:
                    continue
                critique_prompt = (
                    f"Review this consensus solution:\n{amplified_solution[:500]}\n\n"
                    "Respond with exactly one of: AGREE, DISAGREE, or REFINE.\n"
                    "If REFINE, briefly state what should change."
                )
                critique_tasks.append((role, agent.process_task(critique_prompt, sender="CRA_Interference")))

            if not critique_tasks:
                break

            critiques = {}
            for role, task in critique_tasks:
                try:
                    result = await task
                    response = result.get("response", result) if isinstance(result, dict) else str(result)
                    critiques[role] = response
                except Exception:
                    critiques[role] = "AGREE"

            # Count votes
            refine_count = sum(1 for c in critiques.values() if "REFINE" in str(c).upper())
            total_voters = len(critiques)

            if refine_count > total_voters / 2:
                # Majority wants refinement — run second synthesis
                interference_events += 1
                refinement_context = "\n".join(f"[{r}]: {c}" for r, c in critiques.items())
                refine_prompt = (
                    f"The team reviewed your synthesis and requested refinement:\n{refinement_context}\n\n"
                    f"Original synthesis:\n{amplified_solution[:500]}\n\n"
                    "Produce an improved synthesis incorporating the feedback."
                )
                refined = await synthesizer.process_task(refine_prompt, sender="CRA_Interference")
                amplified_solution = refined.get("response", refined) if isinstance(refined, dict) else str(refined)
                logger.info(f"[{session_id}] Interference round {interference_round+1}: refined ({refine_count}/{total_voters} votes)")
            else:
                logger.info(f"[{session_id}] Interference round {interference_round+1}: consensus holds ({refine_count}/{total_voters} refine votes)")
                break

        # 5. Compute confidence and amplification metrics
        confidence_scores = []
        for role, data in self.active_sessions[session_id]["states"].items():
            agent_confidence = data.get("confidence", 0.5)
            confidence_scores.append(agent_confidence)

        composite_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        amplification_factor = round(1.0 + (len(active_agents) - 1) * 0.25 * composite_confidence, 3)

        self.active_sessions[session_id]["status"] = "completed"
        self.active_sessions[session_id]["final_solution"] = amplified_solution
        self.active_sessions[session_id]["confidence"] = round(composite_confidence, 3)
        self.active_sessions[session_id]["amplification_factor"] = amplification_factor
        self.active_sessions[session_id]["interference_events"] = interference_events
        
        elapsed = time.time() - t_start
        logger.info(f"[{session_id}] Amplification Complete. Confidence={composite_confidence:.2f}, Factor={amplification_factor}, Interference={interference_events}, Time={elapsed:.1f}s")
        
        # Log to session history for meta-analysis
        self.session_history.append({
            "session_id": session_id,
            "participants": list(active_agents.keys()),
            "confidence": round(composite_confidence, 3),
            "amplification_factor": amplification_factor,
            "interference_events": interference_events,
            "elapsed_s": round(elapsed, 2),
            "timestamp": datetime.now().isoformat()
        })

        return {
            "session_id": session_id,
            "participants": list(active_agents.keys()),
            "amplified_solution": amplified_solution,
            "intermediate_states": self.active_sessions[session_id]["states"],
            "confidence": round(composite_confidence, 3),
            "amplification_factor": amplification_factor,
            "interference_events": interference_events,
            "elapsed_s": round(elapsed, 2)
        }

    async def _gather_initial_state(self, session_id: str, role: str, agent: Any, prompt: str):
        """Helper to run agent task and capture state."""
        try:
            # We request the agent to process the task
            result = await agent.process_task(prompt, sender="CRA_Engine")
            
            # If the agent returns a dict (with reasoning_trace), grab it
            if isinstance(result, dict):
                content = result.get("response", "")
                trace = result.get("reasoning_trace", "")
            else:
                content = result
                trace = "Implicit execution."
                
            self.active_sessions[session_id]["states"][role] = {
                "content": content,
                "trace": trace,
                "confidence": min(1.0, len(content) / 200.0) if content else 0.0
            }
        except Exception as e:
            logger.error(f"[{session_id}] Agent {role} failed initial reasoning: {e}")
            self.active_sessions[session_id]["states"][role] = {
                "content": f"Error: {e}",
                "trace": "",
                "confidence": 0.0
            }

    def get_session_history(self, limit: int = 20) -> List[Dict]:
        """Phase 7: Return recent CRA session history for meta-analysis."""
        return self.session_history[-limit:]

# Singleton accessor
_cra_engine = None
def get_cra_engine():
    global _cra_engine
    if _cra_engine is None:
        _cra_engine = CollaborativeReasoningEngine()
    return _cra_engine
