"""
Port Management Daemon
Prevents agent port collisions when running parallel web services.
Manages a port pool with cross-process locking.
"""

import os
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
from threading import Lock

logger = logging.getLogger("PortManager")

DEFAULT_PORT_RANGE = (9000, 9100)
PORT_STATE_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "swarm_v2_artifacts", "port_allocations.json"
)


class PortManager:
    """
    Agent-aware port allocation daemon.

    Manages a pool of ports (default 9000-9100) and tracks which agent
    holds which port. Uses a JSON file for cross-process visibility.
    """

    def __init__(self, port_range: tuple = DEFAULT_PORT_RANGE,
                 state_file: str = PORT_STATE_FILE):
        self.port_min, self.port_max = port_range
        self.state_file = os.path.abspath(state_file)
        self._lock = Lock()
        self._allocations: Dict[int, Dict] = {}

        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        self._load_state()

    def _load_state(self):
        """Load port allocations from disk."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._allocations = {int(k): v for k, v in data.items()}
            except Exception as e:
                logger.warning(f"Could not load port state: {e}")
                self._allocations = {}

    def _save_state(self):
        """Persist port allocations to disk."""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._allocations, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save port state: {e}")

    def acquire_port(self, agent_id: str, purpose: str = "dev_server") -> Optional[int]:
        """
        Acquire the next available port from the pool.

        Args:
            agent_id: ID of the requesting agent
            purpose: Description of what the port is for

        Returns:
            Port number, or None if pool is exhausted
        """
        with self._lock:
            for port in range(self.port_min, self.port_max + 1):
                if port not in self._allocations:
                    self._allocations[port] = {
                        "agent_id": agent_id,
                        "purpose": purpose,
                        "acquired_at": datetime.now().isoformat(),
                    }
                    self._save_state()
                    logger.info(f"[PortManager] Allocated port {port} to {agent_id} ({purpose})")
                    return port

            logger.warning(f"[PortManager] Port pool exhausted ({self.port_min}-{self.port_max})")
            return None

    def release_port(self, port: int) -> bool:
        """
        Release a port back to the pool.

        Args:
            port: Port number to release

        Returns:
            True if released, False if port wasn't allocated
        """
        with self._lock:
            if port in self._allocations:
                agent_id = self._allocations[port]["agent_id"]
                del self._allocations[port]
                self._save_state()
                logger.info(f"[PortManager] Released port {port} (was {agent_id})")
                return True
            return False

    def release_agent_ports(self, agent_id: str) -> int:
        """Release all ports held by a specific agent."""
        with self._lock:
            to_release = [p for p, info in self._allocations.items()
                          if info["agent_id"] == agent_id]
            for port in to_release:
                del self._allocations[port]
            if to_release:
                self._save_state()
            return len(to_release)

    def get_allocation(self) -> Dict[int, Dict]:
        """Get all current port allocations."""
        return dict(self._allocations)

    def get_agent_ports(self, agent_id: str) -> List[int]:
        """Get all ports allocated to a specific agent."""
        return [p for p, info in self._allocations.items()
                if info["agent_id"] == agent_id]

    def get_stats(self) -> Dict:
        """Get port manager statistics."""
        return {
            "pool_range": f"{self.port_min}-{self.port_max}",
            "total_ports": self.port_max - self.port_min + 1,
            "allocated": len(self._allocations),
            "available": (self.port_max - self.port_min + 1) - len(self._allocations),
            "allocations": {
                str(port): info for port, info in self._allocations.items()
            },
        }


# Singleton
_pm: Optional[PortManager] = None

def get_port_manager() -> PortManager:
    global _pm
    if _pm is None:
        _pm = PortManager()
    return _pm
