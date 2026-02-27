"""
Swarm V2 Monitor Daemon
Phase 4: Shell-01 (Recursive Self-Healing)

This background daemon continuously monitors the health of the Agent Mesh
and individual agents against the thresholds defined in `coherence_thresholds.py`.

It acts as the "Sensory System" for the self-healing loop.
"""

import asyncio
import logging
import time
from typing import Dict, List
from datetime import datetime

# Import core components (assuming they are in the pythonpath)
try:
    from swarm_v2.core.agent_mesh import get_agent_mesh
    from swarm_v2_artifacts.coherence_thresholds import CoherenceThresholds
except ImportError:
    # Fallback for standalone testing or initial setup
    class CoherenceThresholds:
        HEARTBEAT_TIMEOUT = 300
        MIN_ACTIVE_AGENTS = 3
        
    def get_agent_mesh():
        return None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Monitor] %(message)s",
    handlers=[
        logging.FileHandler("swarm_v2_artifacts/monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MonitorDaemon")

class MonitorDaemon:
    def __init__(self, remediation_engine=None, interval: int = 10):
        self.interval = interval
        self.mesh = get_agent_mesh()
        self.remediation_engine = remediation_engine
        self.running = False
        self.remediation_queue = []

    async def start(self):
        """Start the monitoring loop."""
        self.running = True
        logger.info("[Monitor] Monitor Daemon started. Watching Agent Mesh...")
        
        while self.running:
            try:
                if not self.mesh:
                    self.mesh = get_agent_mesh()
                
                if self.mesh:
                    await self._check_mesh_health()
                else:
                    logger.warning("Agent Mesh not initialized yet.")
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            await asyncio.sleep(self.interval)

    async def stop(self):
        """Stop the monitoring loop."""
        self.running = False
        logger.info("Monitor Daemon stopped.")

    async def _check_mesh_health(self):
        """Inspect all agents in the mesh."""
        stats = self.mesh.get_stats()
        alive_count = stats.get("alive_nodes", 0)
        
        # 1. Check Mesh Integrity
        if alive_count < CoherenceThresholds.MIN_ACTIVE_AGENTS:
            logger.critical(
                f"[CRITICAL] Mesh integrity compromised! "
                f"Alive agents: {alive_count} (Min: {CoherenceThresholds.MIN_ACTIVE_AGENTS})"
            )
            await self._queue_remediation("MESH_INTEGRITY", f"Alive count {alive_count} too low")

        # 2. Check Individual Agents
        topology = self.mesh.get_topology()
        current_time = time.time()
        
        for node in topology.get("nodes", []):
            node_id = node.get("node_id")
            name = node.get("name")
            role = node.get("role")
            last_beat = node.get("last_heartbeat", 0)
            
            # Check Heartbeat
            time_since_beat = current_time - last_beat
            if time_since_beat > CoherenceThresholds.HEARTBEAT_TIMEOUT:
                logger.warning(f"[WARNING] Agent {name} ({node_id}) is unresponsive. Last beat: {int(time_since_beat)}s ago")
                # Pass the role as the target for restarting
                await self._queue_remediation("AGENT_TIMEOUT", role or name)

    async def _queue_remediation(self, issue_type: str, details: str):
        """Send an issue to the Remediation Engine."""
        issue = {
            "type": issue_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.remediation_queue.append(issue)
        logger.info(f"Queued remediation for: {issue_type} - {details}")
        
        if self.remediation_engine:
            await self.remediation_engine.handle_issue(issue_type, details)

if __name__ == "__main__":
    # Standalone run
    daemon = MonitorDaemon()
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        asyncio.run(daemon.stop())
