"""
Coherence Threshold Framework
Defines the stability thresholds for the Swarm's autonomous self-healing capabilities.
Part of Phase 4: Shell-01 (Recursive Self-Healing).
"""

from typing import Dict, Any

class CoherenceThresholds:
    # System Stability Thresholds
    CPU_LOAD_WARNING = 80.0     # Percentage
    MEMORY_USAGE_WARNING = 85.0 # Percentage
    DISK_SPACE_WARNING = 90.0   # Percentage

    # Agent Health Thresholds
    MAX_RESPONSE_LATENCY = 5.0  # Seconds
    HEARTBEAT_TIMEOUT = 300     # Seconds (5 minutes)
    ERROR_RATE_LIMIT = 0.1      # 10% failure rate over a window

    # Mesh Integrity Thresholds
    MIN_ACTIVE_AGENTS = 3       # Minimum agents required for a functional mesh
    MAX_ORPHANED_TASKS = 5      # Tasks routed but not picked up

    # Remediation Action Levels
    LEVEL_1_WARNING = "LOG_WARNING"
    LEVEL_2_RESTART = "RESTART_SERVICE"
    LEVEL_3_ROLLBACK = "ROLLBACK_DEPLOYMENT"
    LEVEL_4_EMERGENCY = "FULL_SYSTEM_RESET"

    @classmethod
    def get_thresholds(cls) -> Dict[str, Any]:
        """Return all defined thresholds as a dictionary."""
        return {k: v for k, v in cls.__dict__.items() if not k.startswith("__") and not callable(v)}

    @classmethod
    def check_stability(cls, metrics: Dict[str, float]) -> str:
        """Evaluate current system metrics against thresholds."""
        if metrics.get("cpu_load", 0) > cls.CPU_LOAD_WARNING:
            return cls.LEVEL_1_WARNING
        if metrics.get("memory_usage", 0) > cls.MEMORY_USAGE_WARNING:
            return cls.LEVEL_1_WARNING
        if metrics.get("error_rate", 0) > cls.ERROR_RATE_LIMIT:
            return cls.LEVEL_2_RESTART
        return "STABLE"
