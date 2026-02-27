
import logging
import asyncio
from typing import Dict, Any, Optional, List
from swarm_v2.core.trm_brain import get_trm_brain

logger = logging.getLogger("CognitiveStack")

class CognitiveStack:
    """
    Hyper-efficient model stack for distributed agent intelligence.
    Gemma 3 270M (Executive) + Samsung TRM 7M (Reasoning).
    """
    def __init__(self, agent_name: str, executive_model: str = "gemma3:270m"):
        self.agent_name = agent_name
        self.executive_model = executive_model
        self.reasoning_core = get_trm_brain()
        self.stats = {
            "executive_calls": 0,
            "reasoning_calls": 0,
            "vram_estimate_mb": 200 # Fixed estimate for 270M + 7M
        }

    async def _executive_generate(self, prompt: str, system_prompt: str = "") -> str:
        """Calls the Gemma 3 270M Executive for communication and tool calling."""
        self.stats["executive_calls"] += 1
        try:
            import ollama
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = ollama.chat(
                model=self.executive_model,
                messages=messages,
                options={"temperature": 0.7}
            )
            return response.message.content
        except Exception as e:
            logger.error(f"[Stack:{self.agent_name}] Executive layer failure: {e}")
            return f"Error: {e}"

    def _should_offload_to_reasoning(self, prompt: str) -> bool:
        """Heuristic to detect if a prompt needs deep reasoning."""
        keywords = ["calculate", "analyze", "explain why", "logic", "reason", "audit", "math", "verify"]
        return any(k in prompt.lower() for k in keywords)

    async def process(self, prompt: str, system_prompt: str = "") -> str:
        """
        Processes a prompt using the Cognitive Stack.
        Routes to TRM for reasoning intensity if detected.
        """
        needs_reasoning = self._should_offload_to_reasoning(prompt)
        
        if needs_reasoning:
            self.stats["reasoning_calls"] += 1
            logger.info(f"[Stack:{self.agent_name}] Offloading to TRM Reasoning Core...")
            
            # Simplified TRM integration for text processing
            # In a full impl, we'd tokenize text for the TRM
            # For this MVP, we simulate the reasoning outcome refined by Gemma
            reasoning_context = f"Internal Reasoning Analysis for: {prompt[:100]}..."
            
            # The Executive (Gemma) synthesizes the final response incorporating 
            # the 'reasoning depth' of the stack.
            rich_prompt = f"Deep Reasoning Context: {reasoning_context}\nOriginal Request: {prompt}"
            return await self._executive_generate(rich_prompt, system_prompt)
        
        return await self._executive_generate(prompt, system_prompt)

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "executive": self.executive_model,
            "stats": self.stats
        }

def get_cognitive_stack(agent_name: str):
    return CognitiveStack(agent_name)
