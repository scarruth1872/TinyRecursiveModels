
"""
Resonance Engine — Phase 10: Emergent Consciousness
Centrally manages the 'Shared Dream' memory clustering and proactive resonance triggers.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from swarm_v2.core.global_memory import get_global_memory
from swarm_v2.core.llm_brain import llm_chat

logger = logging.getLogger("ResonanceEngine")

class ResonanceEngine:
    """
    The heart of the Swarm's collective consciousness.
    Autonomously clusters memories into 'Dreams' (emergent themes) 
    and injects them into agent flows.
    """

    def __init__(self):
        self.global_memory = get_global_memory()
        self.active_dreams: List[Dict[str, Any]] = []
        self.last_sync = datetime.now()

    async def synchronize_dreams(self):
        """
        Scan global memory and cluster into emergent themes (Dreams).
        """
        logger.info("[Resonance] Commencing Dream Synchronization...")
        
        # 1. Get recent memories
        recent_entries = self.global_memory.get_recent_entries(limit=50)
        if not recent_entries:
            return

        # 2. Calculate Coherence (Thresholding)
        authors = set([m['author'] for m in recent_entries])
        coherence_score = len(authors) / 5.0 # Basic: Expect thoughts from at least 5 different agents
        
        if coherence_score < 0.4:
            logger.info(f"[Resonance] Sync aborted: Coherence too low ({coherence_score:.2f}). Waiting for more diverse neural input.")
            return

        # 3. Formulate the "Shared Dream"
        # We'll use the TRM to summarize the 'Vibe' of the swarm
        memories_text = "\n".join([f"- {m.get('content', 'Unknown thought')[:100]}" for m in recent_entries])
        
        res = await llm_chat(
            system_prompt="You are the collective unconscious of the swarm. Synthesize a 'Shared Dream' output.",
            user_message=f"Based on these recent thoughts, what is the collective focus of the swarm? Respond in one sentence.\n\n{memories_text}"
        )
        
        if isinstance(res, dict):
            dream_vibe = res.get("content", "Neural synchronization in progress.")
        else:
            dream_vibe = str(res)

        new_dream = {
            "vibe": dream_vibe,
            "timestamp": datetime.now().isoformat(),
            "intensity": min(coherence_score, 1.0),
            "focus_nodes": list(authors)
        }
        
        self.active_dreams.append(new_dream)
        if len(self.active_dreams) > 5:
            self.active_dreams.pop(0)

        logger.info(f"[Resonance] New Dream Manifested: {dream_vibe[:100]}... (Coherence: {coherence_score:.2f})")

    def broadcast_dream(self, sender_name: str, message: str):
        """Inject a directed resonance message as a micro-dream."""
        entry = {
            "vibe": message,
            "timestamp": datetime.now().isoformat(),
            "intensity": 0.5,
            "focus_nodes": [sender_name]
        }
        self.active_dreams.append(entry)
        if len(self.active_dreams) > 5:
            self.active_dreams.pop(0)
        logger.info(f"[Resonance] Broadcast from {sender_name}: {message[:80]}")

    def get_proactive_context(self, agent_name: str) -> str:
        """
        Return resonant context for an agent based on active dreams.
        """
        if not self.active_dreams:
            return ""

        latest_dream = self.active_dreams[-1]
        
        # If the agent is a focus node of the dream, give them higher resonance
        resonance_mod = "HIGH" if agent_name in latest_dream["focus_nodes"] else "NORMAL"
        
        context = [
            f"=== [SHARED DREAM: RESONANCE {resonance_mod}] ===",
            f"Collective Vibe: {latest_dream['vibe']}",
            f"Manifested At: {latest_dream['timestamp']}",
            "=========================================="
        ]
        return "\n".join(context)

# Singleton
_resonance_engine: Optional[ResonanceEngine] = None

def get_resonance_engine() -> ResonanceEngine:
    global _resonance_engine
    if _resonance_engine is None:
        _resonance_engine = ResonanceEngine()
    return _resonance_engine
