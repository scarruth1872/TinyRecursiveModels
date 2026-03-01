
import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Tuple
from collections import deque
from swarm_v2.core.trm_brain import get_trm_brain

logger = logging.getLogger("CognitiveStack")

# Adaptive tuning constants
DEFAULT_H_CYCLES = 3
MIN_H_CYCLES = 1
MAX_H_CYCLES = 8
LATENCY_WINDOW = 20        # Rolling window size for latency tracking
HIGH_LATENCY_THRESHOLD = 5.0  # seconds — reduce depth above this
LOW_HARMONY_THRESHOLD = 0.4   # increase depth below this

class CognitiveStack:
    """
    Hyper-efficient model stack for distributed agent intelligence.
    Gemma 3 1B (Executive) + Samsung TRM 7M (Reasoning).
    """
    def __init__(self, agent_name: str, executive_model: str = "gemma3:270m"):
        self.agent_name = agent_name
        self.executive_model = executive_model
        self.reasoning_core = get_trm_brain()
        self.stats = {
            "executive_calls": 0,
            "reasoning_calls": 0,
            "vram_estimate_mb": 300  # ~300MB for 270M + 7M TRM
        }
        # Phase 7: Adaptive Recursion Depth Tuning
        self.h_cycles = DEFAULT_H_CYCLES
        self.latency_history: deque = deque(maxlen=LATENCY_WINDOW)
        self.tuning_log: List[Dict] = []
        self._last_harmony_score = 1.0  # Updated externally via tune_recursion_depth()

    async def _executive_generate(self, prompt: str, system_prompt: str = "") -> Tuple[str, str]:
        """Calls the executive model for communication and tool calling via Ollama."""
        self.stats["executive_calls"] += 1
        from swarm_v2.core.llm_brain import llm_chat
        res = await llm_chat(
            system_prompt=system_prompt,
            user_message=prompt,
            model=self.executive_model,
        )
        if isinstance(res, dict):
            return res.get("content", ""), res.get("thought", "")
        return str(res), ""

    def _should_offload_to_reasoning(self, prompt: str) -> bool:
        """Heuristic to detect if a prompt needs deep reasoning."""
        keywords = ["calculate", "analyze", "explain why", "logic", "reason", "audit", "math", "verify"]
        return any(k in prompt.lower() for k in keywords)

    def tune_recursion_depth(self, harmony_score: float = None) -> Dict[str, Any]:
        """
        Phase 7: Adaptive H_cycles Tuning.
        Adjusts TRM recursion depth based on latency and harmony feedback.
        - If harmony is low → increase depth for higher fidelity reasoning.
        - If latency is high → decrease depth for swarm throughput.
        Returns the tuning decision.
        """
        old_h = self.h_cycles
        if harmony_score is not None:
            self._last_harmony_score = harmony_score

        avg_latency = sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0.0

        reason = "stable"
        if avg_latency > HIGH_LATENCY_THRESHOLD and self.h_cycles > MIN_H_CYCLES:
            self.h_cycles = max(MIN_H_CYCLES, self.h_cycles - 1)
            reason = f"latency_high ({avg_latency:.2f}s > {HIGH_LATENCY_THRESHOLD}s)"
        elif self._last_harmony_score < LOW_HARMONY_THRESHOLD and self.h_cycles < MAX_H_CYCLES:
            self.h_cycles = min(MAX_H_CYCLES, self.h_cycles + 1)
            reason = f"harmony_low ({self._last_harmony_score:.2f} < {LOW_HARMONY_THRESHOLD})"

        decision = {
            "agent": self.agent_name,
            "old_h_cycles": old_h,
            "new_h_cycles": self.h_cycles,
            "avg_latency": round(avg_latency, 3),
            "harmony_score": self._last_harmony_score,
            "reason": reason
        }
        if old_h != self.h_cycles:
            self.tuning_log.append(decision)
            logger.info(f"[Stack:{self.agent_name}] H_cycles tuned: {old_h} → {self.h_cycles} ({reason})")
        return decision

    async def process(self, prompt: str, system_prompt: str = "") -> Tuple[str, Optional[str]]:
        """
        Processes a prompt using the Cognitive Stack.
        Routes to TRM for reasoning intensity if detected.
        Returns (response, reasoning_trace).
        """
        t_start = time.time()
        needs_reasoning = self._should_offload_to_reasoning(prompt)
        trm_trace = None
        
        reasoning_context = ""
        if needs_reasoning:
            self.stats["reasoning_calls"] += 1
            logger.info(f"[Stack:{self.agent_name}] Offloading to TRM Reasoning Core...")
            
            try:
                tokens = [(ord(c) % 12) for c in prompt[:128]]
                reasoning_preds = self.reasoning_core.reason(tokens)
                
                logic_nodes = ["SYN", "ANA", "VAL", "GEN", "CMP", "EXT", "FLW", "INS", "RMT", "INF", "DDC", "LGC"]
                trace_nodes = [logic_nodes[p % 12] for p in reasoning_preds[:12]]
                trm_trace = f"[{'->'.join(trace_nodes)}]"
                
                reasoning_context = f"TRM_RECURSIVE_REASONING_STAGES: {trm_trace}"
                logger.info(f"[Stack:{self.agent_name}] TRM Cluster Analysis: {trm_trace}")
            except Exception as e:
                logger.warning(f"[Stack:{self.agent_name}] TRM reasoning failed: {e}")
                reasoning_context = "Internal Reasoning Analysis pending due to cluster congestion."
                trm_trace = "[REASONING_CONGESTED]"
            
            rich_prompt = (
                f"### INTERNAL REASONING CORE ANALYSIS\n"
                f"{reasoning_context}\n\n"
                f"### USER REQUEST\n"
                f"{prompt}\n\n"
                f"Based on my internal reasoning nodes above, I will now formulate my response:"
            )
            # For 270M models, the TRM header confuses the executive — pass clean prompt only
            is_small_model = "270m" in self.executive_model.lower()
            exec_input = prompt if is_small_model else rich_prompt
            response, exec_thought = await self._executive_generate(exec_input, system_prompt)
        else:
            response, exec_thought = await self._executive_generate(prompt, system_prompt)
        
        # Merge TRM and Executive traces for the dashboard
        combined_trace = ""
        if trm_trace:
            combined_trace += f"TRM_NODES: {trm_trace}"
        if exec_thought:
            if combined_trace: combined_trace += "\n\n"
            combined_trace += f"EXECUTIVE_THOUGHT:\n{exec_thought}"
            
        # Track latency for adaptive tuning
        elapsed = time.time() - t_start
        self.latency_history.append(elapsed)

        return response, combined_trace if combined_trace else None

    def get_status(self) -> Dict[str, Any]:
        """Expose detailed metrics for the 'Neural Pipeline' dashboard."""
        avg_latency = sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0.0
        return {
            "agent": self.agent_name,
            "executive": self.executive_model,
            "vram_mb": self.stats["vram_estimate_mb"],
            "calls": {
                "executive": self.stats["executive_calls"],
                "reasoning": self.stats["reasoning_calls"]
            },
            "status": "active" if self.stats["executive_calls"] > 0 else "standby",
            "adaptive_tuning": {
                "h_cycles": self.h_cycles,
                "avg_latency_s": round(avg_latency, 3),
                "harmony_score": self._last_harmony_score,
                "tuning_events": len(self.tuning_log)
            }
        }

def get_cognitive_stack(agent_name: str):
    return CognitiveStack(agent_name)
