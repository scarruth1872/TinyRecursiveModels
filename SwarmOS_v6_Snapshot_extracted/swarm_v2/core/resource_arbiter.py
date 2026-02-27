
"""
Resource Arbiter for Swarm V2 (Phase 4)
Manages VRAM usage and model loading to prevent system instability.
Optimized for single/multi-GPU setups by explicily managing Ollama's model residency.
"""

import asyncio
import logging
import subprocess
import shutil
from typing import Dict, List, Optional
from datetime import datetime

# Adjust based on system. 11.5GB is optimal for the 12GB 6700XT.
DEFAULT_VRAM_BUDGET_GB = 11.5

# Approximate model sizes in GB (with some context overhead)
# Available models on this system:
# - deepseek-r1:8b (5.2GB) - Complex reasoning
# - gemma3:4b (3.3GB) - Balanced
# - deepseek-r1:1.5b (1.1GB) - Fast reasoning
# - llama3.2:latest (2.0GB) - General purpose
# - phi3:latest (2.2GB) - Microsoft lightweight
# - gemma2:2b (1.6GB) - Small Google model
# - starcoder2:3b (1.7GB) - Code generation
# - qwen2.5-coder:latest (4.7GB) - Code specialist

MODEL_SIZES = {
    "deepseek-r1:8b": 5.2,
    "gemma3:4b": 3.3,
    "deepseek-r1:1.5b": 1.5,
    "llama3.2:latest": 2.0,
    "phi3:latest": 2.2,
    "gemma2:2b": 1.6,
    "starcoder2:3b": 1.7,
    "qwen2.5-coder:latest": 4.7,
    "gemma3:270m": 0.3,
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Arbiter] %(message)s",
    handlers=[
        logging.FileHandler("swarm_v2_artifacts/arbiter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ResourceArbiter")

class ResourceArbiter:
    def __init__(self, vram_budget_gb: float = DEFAULT_VRAM_BUDGET_GB):
        self.vram_budget = vram_budget_gb
        self.active_models: Dict[str, float] = {}  # model_name -> size_gb
        self.busy_models = set()  # models currently generating tokens
        self.lock = asyncio.Lock()
        self.ollama_cmd = shutil.which("ollama")
        self.original_budget = vram_budget_gb
        self._expansion_count = 0

    def expand_budget(self):
        """
        Dynamically expand the budget if system resources allow.
        Triggered when high-complexity tasks are detected.
        """
        import psutil
        mem = psutil.virtual_memory()
        free_gb = mem.available / (1024 ** 3)
        
        if free_gb > 8.0 and self.vram_budget < (self.original_budget * 1.5):
            expansion = 2.0  # Add 2GB to budget
            self.vram_budget += expansion
            self._expansion_count += 1
            logger.info(f"[RESOURCE] EXPANSION: Budget increased to {self.vram_budget}GB. Total System RAM Free: {free_gb:.1f}GB")
            return True
        return False

    def _get_ollama_ps(self) -> List[Dict]:
        """Parse 'ollama ps' output to see what's actually running."""
        if not self.ollama_cmd:
            return []
        try:
            # Run ollama ps
            result = subprocess.run(
                [self.ollama_cmd, "ps"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode != 0:
                logger.error(f"ollama ps failed: {result.stderr}")
                return []

            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return []

            # Parse simple text table
            # NAME              ID              SIZE      PROCESSOR    
            # deepseek-r1:8b    6995872bfe4c    7.8 GB    100% GPU     
            models = []
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 4:
                    name = parts[0]
                    size_str = parts[2]
                    unit = parts[3]
                    
                    # Convert to GB
                    size_gb = float(size_str)
                    if "MB" in unit:
                        size_gb /= 1024
                    
                    models.append({"name": name, "size_gb": size_gb})
            return models
        except Exception as e:
            logger.error(f"Error parsing ollama ps: {e}")
            return []

    async def sync_state(self):
        """Sync internal state with actual Ollama process state."""
        real_models = self._get_ollama_ps()
        
        async with self.lock:
            self.active_models.clear()
            for m in real_models:
                self.active_models[m["name"]] = m["size_gb"]
        
        return self.active_models

    def _estimate_size(self, model_name: str) -> float:
        """Get estimated size for a model not yet running."""
        # Check standard map
        for key, size in MODEL_SIZES.items():
            if key in model_name:
                return size
        # Default fallback
        return 4.0

    async def acquire_slot(self, model_name: str) -> bool:
        """
        Distributed Stack Upgrade: Slots are always available.
        Total footprint for all agents is managed by the Stack architecture.
        """
        return True

    async def _stop_model(self, model_name: str) -> bool:
        """Tell Ollama to stop a model to unload it."""
        if not self.ollama_cmd:
            return False
        
        try:
            proc = await asyncio.create_subprocess_exec(
                self.ollama_cmd, "stop", model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    def get_status(self) -> Dict:
        usage = sum(self.active_models.values())
        return {
            "vram_budget_gb": self.vram_budget,
            "current_usage_gb": round(usage, 2),
            "utilization_pct": round((usage / self.vram_budget) * 100, 1),
            "active_models": list(self.active_models.keys()),
            "busy_models": list(self.busy_models)
        }

    def mark_busy(self, model_name: str):
        self.busy_models.add(model_name)

    def mark_idle(self, model_name: str):
        self.busy_models.discard(model_name)

# Global singleton
_arbiter = ResourceArbiter()

def get_resource_arbiter():
    return _arbiter
