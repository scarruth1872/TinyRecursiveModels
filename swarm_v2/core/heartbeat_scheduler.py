import os
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class HeartbeatScheduler:
    """
    Poller for HEARTBEAT.md to trigger proactive agent actions.
    """
    def __init__(self, heartbeat_file: str, engine_team: Dict[str, Any], interval: int = 60):
        self.heartbeat_file = heartbeat_file
        self.engine_team = engine_team
        self.interval = interval
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info(f"HeartbeatScheduler started (Interval: {self.interval}s)")
        while self.is_running:
            try:
                await self.pulse()
            except Exception as e:
                logger.error(f"Heartbeat pulse failed: {e}")
            await asyncio.sleep(self.interval)

    def stop(self):
        self.is_running = False

    async def pulse(self):
        """Perform one pulse cycle: read, dispatch, update."""
        if not os.path.exists(self.heartbeat_file):
            return

        with open(self.heartbeat_file, "r") as f:
            content = f.read()

        # Find uncompleted tasks: - [ ] Task
        uncompleted = re.findall(r'-\s\[\s\]\s*(.*)', content)
        
        if not uncompleted:
            return

        logger.info(f"Heartbeat detected {len(uncompleted)} active goals/tasks.")
        
        # Dispatch the first uncompleted task to the Architect for coordination
        task = uncompleted[0].split('\n')[0].strip()
        architect = self.engine_team.get("Architect")
        
        if architect:
            logger.info(f"Dispatching proactive task: {task}")
            # We use 'self' sender to indicate internal proactive motivation
            await architect.process_task(f"PROACTIVE_HEARTBEAT: {task}", sender="self")
            
            # Mark as completed in file (primitive update)
            new_content = content.replace(f"- [ ] {task}", f"- [x] {task}")
            
            # Update last heartbeat
            ts = datetime.now().isoformat()
            new_content = re.sub(r'Last Heartbeat: .*', f'Last Heartbeat: {ts}', new_content)
            
            with open(self.heartbeat_file, "w") as f:
                f.write(new_content)

_scheduler: Optional[HeartbeatScheduler] = None

def get_heartbeat_scheduler(heartbeat_file: str = None, engine_team: Dict[str, Any] = None) -> HeartbeatScheduler:
    global _scheduler
    if _scheduler is None:
        if not heartbeat_file:
            heartbeat_file = os.path.join(os.getcwd(), "HEARTBEAT.md")
        _scheduler = HeartbeatScheduler(heartbeat_file, engine_team)
    return _scheduler
