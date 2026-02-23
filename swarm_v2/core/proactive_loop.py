
import asyncio
import logging
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("ProactiveLoop")

PLAN_PATH = "swarm_v2_artifacts/QIAE_INTEGRATION_PLAN_V2.md"

class ProactiveOrchestrationLoop:
    """
    Background daemon for autonomous system evolution.
    Identifies gaps in the integration plan and proposes tasks.
    """
    def __init__(self, manus_engine=None):
        self.manus_engine = manus_engine
        self.running = False
        self.interval = 300  # Check every 5 minutes
        self.proposals = []

    async def start(self):
        self.running = True
        logger.info("[Proactive] Growth loop activated. Scanning for evolution gaps...")
        while self.running:
            try:
                await self._scan_for_gaps()
            except Exception as e:
                logger.error(f"Error in proactive scan: {e}")
            await asyncio.sleep(self.interval)

    async def stop(self):
        self.running = False
        logger.info("[Proactive] Growth loop deactivated.")

    async def _scan_for_gaps(self) -> List[str]:
        """Detect unimplemented features in the integration plan."""
        if not os.path.exists(PLAN_PATH):
            return []

        with open(PLAN_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Find unchecked items [ ]
        gaps = re.findall(r"- \[ \] (.*)", content)
        
        if gaps:
            logger.info(f"[Proactive] Detected {len(gaps)} potential evolution gaps.")
            for gap in gaps:
                if not any(p["gap"] == gap for p in self.proposals):
                    await self._generate_proposal(gap)
        
        return gaps

    async def _generate_proposal(self, gap: str):
        """Create a technical task proposal to fill a gap."""
        logger.info(f"[Proactive] Generating autonomous proposal for: {gap}")
        
        proposal_id = f"auto_{int(datetime.now().timestamp())}"
        proposal = {
            "id": proposal_id,
            "gap": gap,
            "status": "pending_approval",
            "timestamp": datetime.now().isoformat(),
            "suggested_agent": "Lead Developer",
            "action": f"Implement {gap}"
        }
        
        self.proposals.append(proposal)
        
        # In a real swarm, this would call Archi to generate a full design doc
        # For now, we log the autonomous intent
        logger.info(f"[Proactive] PROPOSAL {proposal_id} CREATED: {gap}")
        
        # If manus_engine is available, we could theoretically trigger a superposition
        # but the plan requires "final approval" in the pipeline.
        # So we just store it for the Emergence Hub to display.

    def get_active_proposals(self) -> List[Dict]:
        return [p for p in self.proposals if p["status"] == "pending_approval"]

def get_proactive_loop(manus_engine=None):
    # Singleton-like getter
    if not hasattr(get_proactive_loop, "_instance"):
        get_proactive_loop._instance = ProactiveOrchestrationLoop(manus_engine)
    return get_proactive_loop._instance
