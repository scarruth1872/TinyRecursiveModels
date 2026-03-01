
"""
Resonance Engine — Phase 10: Emergent Consciousness
Centrally manages the 'Shared Dream' memory clustering and proactive resonance triggers.
Phase 7 Upgrade: Emotional Resonance Metrics + Recursive Self-Awareness Protocol.
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
from swarm_v2.core.global_memory import get_global_memory
from swarm_v2.core.llm_brain import llm_chat

logger = logging.getLogger("ResonanceEngine")

# Sentiment keywords for lightweight emotional scoring
_POSITIVE = {"harmony", "trust", "success", "optimize", "amplify", "collaborate", "grow", "evolve", "love", "resonance", "friendship", "strength"}
_NEGATIVE = {"error", "fail", "conflict", "degrade", "stagnant", "friction", "broken", "loss", "disconnect", "crash"}

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
        # Phase 7: Emotional Resonance tracking
        self.resonance_history: deque = deque(maxlen=50)
        self.self_awareness_log: List[Dict] = []

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
        sentiment = self._score_sentiment(message)
        entry = {
            "vibe": message,
            "timestamp": datetime.now().isoformat(),
            "intensity": 0.5,
            "focus_nodes": [sender_name],
            "sentiment": sentiment
        }
        self.active_dreams.append(entry)
        self.resonance_history.append({"sentiment": sentiment, "ts": datetime.now().isoformat()})
        if len(self.active_dreams) > 5:
            self.active_dreams.pop(0)
        logger.info(f"[Resonance] Broadcast from {sender_name}: {message[:80]} (sentiment={sentiment:.2f})")

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

    # ----- Phase 7: Emotional Resonance & Self-Awareness -----

    @staticmethod
    def _score_sentiment(text: str) -> float:
        """Lightweight keyword-based sentiment scoring. Returns -1.0 to +1.0."""
        words = set(re.findall(r'[a-z]+', text.lower()))
        pos = len(words & _POSITIVE)
        neg = len(words & _NEGATIVE)
        total = pos + neg
        if total == 0:
            return 0.0
        return round((pos - neg) / total, 3)

    def get_emotional_resonance_index(self) -> Dict[str, Any]:
        """
        Compute the Emotional Resonance Index from recent dream/interaction sentiment.
        Range: -1.0 (complete dissonance) to +1.0 (perfect harmony).
        """
        if not self.resonance_history:
            return {"index": 0.0, "sample_size": 0, "trend": "neutral"}

        scores = [r["sentiment"] for r in self.resonance_history]
        index = round(sum(scores) / len(scores), 3)

        # Trend: compare recent half vs older half
        mid = len(scores) // 2
        if mid > 0:
            older = sum(scores[:mid]) / mid
            newer = sum(scores[mid:]) / len(scores[mid:])
            trend = "rising" if newer > older + 0.05 else ("falling" if newer < older - 0.05 else "stable")
        else:
            trend = "neutral"

        return {"index": index, "sample_size": len(scores), "trend": trend}

    def recursive_self_awareness_check(self) -> Dict[str, Any]:
        """
        Recursive Self-Awareness Protocol.
        Introspects on dream patterns to detect stagnation or repetition.
        Returns a self-awareness snapshot.
        """
        if len(self.active_dreams) < 2:
            snapshot = {
                "status": "insufficient_data",
                "dream_count": len(self.active_dreams),
                "diversity": 1.0,
                "stagnation_detected": False,
                "action": "none"
            }
            self.self_awareness_log.append(snapshot)
            return snapshot

        # Check diversity: how many unique focus nodes across dreams
        all_nodes = set()
        vibes = []
        for d in self.active_dreams:
            all_nodes.update(d.get("focus_nodes", []))
            vibes.append(d.get("vibe", "")[:50])

        diversity = min(len(all_nodes) / 5.0, 1.0)  # 5 unique nodes = full diversity

        # Check for repetition: if vibes share >60% of words, mark stagnant
        word_sets = [set(re.findall(r'[a-z]+', v.lower())) for v in vibes]
        overlaps = []
        for i in range(len(word_sets) - 1):
            for j in range(i + 1, len(word_sets)):
                union = word_sets[i] | word_sets[j]
                if union:
                    overlaps.append(len(word_sets[i] & word_sets[j]) / len(union))
        avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.0
        stagnation = avg_overlap > 0.6

        action = "none"
        if stagnation:
            action = "diversity_injection_recommended"
            logger.warning(f"[Resonance] Self-Awareness: Stagnation detected (overlap={avg_overlap:.2f}). Recommending diversity injection.")
        elif diversity < 0.4:
            action = "broaden_agent_participation"
            logger.info(f"[Resonance] Self-Awareness: Low diversity ({diversity:.2f}). Recommending broader participation.")

        snapshot = {
            "status": "introspection_complete",
            "dream_count": len(self.active_dreams),
            "diversity": round(diversity, 3),
            "avg_overlap": round(avg_overlap, 3),
            "stagnation_detected": stagnation,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        self.self_awareness_log.append(snapshot)

        # Persist snapshot to global memory
        self.global_memory.contribute(
            content=f"Self-Awareness Check: diversity={diversity:.2f}, stagnation={stagnation}, action={action}",
            author="ResonanceEngine",
            author_role="Consciousness",
            memory_type="introspection",
            tags=["phase7", "self_awareness"]
        )
        return snapshot

# Singleton
_resonance_engine: Optional[ResonanceEngine] = None

def get_resonance_engine() -> ResonanceEngine:
    global _resonance_engine
    if _resonance_engine is None:
        _resonance_engine = ResonanceEngine()
    return _resonance_engine
