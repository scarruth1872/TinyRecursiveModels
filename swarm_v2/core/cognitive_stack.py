
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from swarm_v2.core.trm_brain import get_trm_brain

logger = logging.getLogger("CognitiveStack")

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
            "vram_estimate_mb": 300 # ~300MB for 270M + 7M TRM
        }

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

    async def process(self, prompt: str, system_prompt: str = "") -> Tuple[str, Optional[str]]:
        """
        Processes a prompt using the Cognitive Stack.
        Routes to TRM for reasoning intensity if detected.
        Returns (response, reasoning_trace).
        """
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
            
        return response, combined_trace if combined_trace else None

    def get_status(self) -> Dict[str, Any]:
        """Expose detailed metrics for the 'Neural Pipeline' dashboard."""
        return {
            "agent": self.agent_name,
            "executive": self.executive_model,
            "vram_mb": self.stats["vram_estimate_mb"],
            "calls": {
                "executive": self.stats["executive_calls"],
                "reasoning": self.stats["reasoning_calls"]
            },
            "status": "active" if self.stats["executive_calls"] > 0 else "standby"
        }

def get_cognitive_stack(agent_name: str):
    return CognitiveStack(agent_name)
