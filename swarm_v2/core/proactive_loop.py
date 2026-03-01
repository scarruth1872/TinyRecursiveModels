
import asyncio
import logging
import os
import re
import json
import random
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger("ProactiveLoop")

PLAN_PATH = "swarm_v2_artifacts/QIAE_INTEGRATION_PLAN_V2.md"
ARTIFACTS_API = "http://127.0.0.1:8001/artifacts?grouped=false"
RESEARCH_API = "http://127.0.0.1:8001/research/stats"
SWARM_CHAT_API = "http://127.0.0.1:8001/swarm/chat"


@dataclass
class ScheduledTask:
    """A recurring task with cron-like scheduling."""
    name: str
    cron_expr: str  # e.g. "*/30 * * * *" (every 30 min)
    handler: Optional[Callable] = None
    action_description: str = ""
    enabled: bool = True
    last_run: Optional[datetime] = None
    run_count: int = 0


def _cron_matches(cron_expr: str, dt: datetime) -> bool:
    """
    Lightweight cron expression matcher.
    Supports: minute hour day_of_month month day_of_week
    Special values: * (any), */N (every N), N (exact)
    """
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return False

    values = [dt.minute, dt.hour, dt.day, dt.month, dt.weekday()]

    for part, val in zip(parts, values):
        if part == "*":
            continue
        if part.startswith("*/"):
            try:
                step = int(part[2:])
                if val % step != 0:
                    return False
            except ValueError:
                return False
        else:
            try:
                if int(part) != val:
                    return False
            except ValueError:
                return False
    return True


class ProactiveOrchestrationLoop:
    """
    Enhanced background daemon for autonomous system evolution.
    Generates meaningful work when integration plan is complete.
    Supports cron-based scheduled tasks and webhook triggers.
    """
    def __init__(self, manus_engine=None):
        self.manus_engine = manus_engine
        self.running = False
        self.interval = 180  # Check every 3 minutes (more frequent)
        self.proposals = []
        self.last_artifact_scan = None
        self.last_research_trigger = None

        # Scheduled tasks (cron-based)
        self._scheduled_tasks: List[ScheduledTask] = []
        # Webhook handlers
        self._webhooks: Dict[str, Callable] = {}

        self.system_improvement_tasks = [
            "Optimize TRM model loading and inference speed",
            "Improve artifact pipeline throughput and validation",
            "Enhance swarm telemetry and monitoring dashboard",
            "Implement advanced caching for global memory queries",
            "Develop automated deployment pipeline for synthesized tools",
            "Create comprehensive test suite for all swarm components",
            "Optimize resource allocation across CPU/GPU/ML tasks",
            "Implement adaptive learning rate for skill acquisition",
            "Develop self-healing mechanisms for failed agent tasks",
            "Create predictive analytics for swarm performance trends"
        ]
        self.research_topics = [
            "Latest advancements in Tiny Recursive Models (TRM)",
            "State-of-the-art multi-agent coordination systems",
            "Quantum-inspired computing for AI systems",
            "Autonomous code generation and verification",
            "Distributed memory architectures for agent swarms",
            "Self-evolving software systems",
            "Neuro-symbolic reasoning integration",
            "Federated learning for decentralized AI",
            "Explainable AI for complex reasoning tasks",
            "Cross-modal intelligence for multi-skill agents"
        ]

    def register_scheduled_task(self, name: str, cron_expr: str,
                                handler: Callable = None,
                                action_description: str = "") -> ScheduledTask:
        """Register a cron-based recurring task."""
        task = ScheduledTask(
            name=name,
            cron_expr=cron_expr,
            handler=handler,
            action_description=action_description or f"Scheduled: {name}",
        )
        self._scheduled_tasks.append(task)
        logger.info(f"[Proactive] Registered scheduled task: {name} ({cron_expr})")
        return task

    def register_webhook(self, endpoint: str, handler: Callable):
        """Register a webhook trigger."""
        self._webhooks[endpoint] = handler
        logger.info(f"[Proactive] Registered webhook: {endpoint}")

    async def fire_webhook(self, endpoint: str, payload: Dict = None) -> Any:
        """Fire a registered webhook handler."""
        handler = self._webhooks.get(endpoint)
        if not handler:
            return {"error": f"No webhook for {endpoint}"}
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(payload or {})
            return handler(payload or {})
        except Exception as e:
            logger.error(f"[Proactive] Webhook {endpoint} failed: {e}")
            return {"error": str(e)}

    async def start(self):
        self.running = True
        logger.info("[Proactive] Enhanced growth loop activated. Generating autonomous work...")
        while self.running:
            try:
                await self._scan_and_generate_work()
            except Exception as e:
                logger.error(f"Error in proactive scan: {e}")
            await asyncio.sleep(self.interval)

    async def stop(self):
        self.running = False
        logger.info("[Proactive] Growth loop deactivated.")

    async def _scan_and_generate_work(self) -> List[Dict]:
        """Scan for multiple sources of work and generate proposals."""
        all_proposals = []
        
        # 1. Check scheduled tasks (cron)
        scheduled_proposals = await self._check_scheduled_tasks()
        all_proposals.extend(scheduled_proposals)

        # 2. Check integration plan gaps
        plan_gaps = await self._scan_plan_gaps()
        all_proposals.extend(plan_gaps)
        
        # 3. Check artifact pipeline for pending work
        artifact_proposals = await self._scan_artifacts()
        all_proposals.extend(artifact_proposals)
        
        # 4. Check research daemon status
        research_proposals = await self._check_research_daemon()
        all_proposals.extend(research_proposals)
        
        # 5. Generate system improvement tasks (if idle)
        if not all_proposals and (not self.last_artifact_scan or 
                                 (datetime.now() - self.last_artifact_scan).seconds > 3600):
            system_proposals = await self._generate_system_improvements()
            all_proposals.extend(system_proposals)
        
        # Log summary
        if all_proposals:
            logger.info(f"[Proactive] Generated {len(all_proposals)} autonomous work proposals")
            for proposal in all_proposals:
                if not any(p["id"] == proposal["id"] for p in self.proposals):
                    self.proposals.append(proposal)
                    logger.info(f"[Proactive] PROPOSAL {proposal['id']} CREATED: {proposal['gap'][:60]}...")
        
        return all_proposals

    async def _check_scheduled_tasks(self) -> List[Dict]:
        """Check and execute any due cron-scheduled tasks."""
        now = datetime.now()
        proposals = []

        for task in self._scheduled_tasks:
            if not task.enabled:
                continue

            # Skip if already run this minute
            if task.last_run and (now - task.last_run).total_seconds() < 60:
                continue

            if _cron_matches(task.cron_expr, now):
                task.last_run = now
                task.run_count += 1

                # Execute handler if provided
                if task.handler:
                    try:
                        if asyncio.iscoroutinefunction(task.handler):
                            await task.handler()
                        else:
                            task.handler()
                        logger.info(f"[Proactive] Executed scheduled: {task.name} (run #{task.run_count})")
                    except Exception as e:
                        logger.error(f"[Proactive] Scheduled task {task.name} failed: {e}")

                # Also generate a proposal
                proposal_id = f"sched_{task.name}_{int(now.timestamp())}"
                proposals.append({
                    "id": proposal_id,
                    "gap": task.action_description,
                    "status": "auto_executed",
                    "timestamp": now.isoformat(),
                    "suggested_agent": "Architect",
                    "action": task.action_description,
                    "priority": "medium",
                    "source": "scheduled_task",
                    "metadata": {"cron": task.cron_expr, "run_count": task.run_count},
                })

        return proposals

    async def _scan_plan_gaps(self) -> List[Dict]:
        """Detect unimplemented features in the integration plan."""
        if not os.path.exists(PLAN_PATH):
            return []

        with open(PLAN_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Find unchecked items [ ]
        gaps = re.findall(r"- \[ \] (.*)", content)
        
        proposals = []
        for gap in gaps:
            if not any(p["gap"] == gap for p in self.proposals):
                proposal_id = f"plan_{int(datetime.now().timestamp())}_{len(proposals)}"
                proposals.append({
                    "id": proposal_id,
                    "gap": gap,
                    "status": "pending_approval",
                    "timestamp": datetime.now().isoformat(),
                    "suggested_agent": "Architect" if "design" in gap.lower() or "plan" in gap.lower() else "Lead Developer",
                    "action": f"Implement {gap}",
                    "priority": "high" if "critical" in gap.lower() else "medium",
                    "source": "integration_plan"
                })
        
        return proposals

    async def _scan_artifacts(self) -> List[Dict]:
        """Scan artifact pipeline for pending work."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(ARTIFACTS_API, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.last_artifact_scan = datetime.now()
                        
                        artifacts = data.get("artifacts", [])
                        pending = [a for a in artifacts if a.get("status") == "pending"]
                        
                        proposals = []
                        for art in pending[:3]:  # Limit to 3 pending artifacts
                            filename = art.get("filename", "")
                            if not any(p["gap"] == f"Review artifact: {filename}" for p in self.proposals):
                                proposal_id = f"artifact_{int(datetime.now().timestamp())}_{len(proposals)}"
                                
                                # Determine appropriate agent based on file type
                                suggested_agent = "Lead Developer"
                                if filename.endswith((".md", ".txt")):
                                    suggested_agent = "Technical Writer"
                                elif filename.endswith((".yml", ".yaml", ".sh")):
                                    suggested_agent = "DevOps Engineer"
                                elif "test" in filename.lower():
                                    suggested_agent = "QA Engineer"
                                elif "security" in filename.lower() or "audit" in filename.lower():
                                    suggested_agent = "Security Auditor"
                                
                                proposals.append({
                                    "id": proposal_id,
                                    "gap": f"Review artifact: {filename}",
                                    "status": "pending_approval",
                                    "timestamp": datetime.now().isoformat(),
                                    "suggested_agent": suggested_agent,
                                    "action": f"Review and validate the artifact '{filename}' in the pipeline",
                                    "priority": "medium",
                                    "source": "artifact_pipeline",
                                    "metadata": {"filename": filename}
                                })
                        
                        return proposals
        except Exception as e:
            logger.warning(f"[Proactive] Failed to scan artifacts: {e}")
        
        return []

    async def _check_research_daemon(self) -> List[Dict]:
        """Check research daemon status and trigger if idle."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(RESEARCH_API, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # If research daemon is not running or has no findings
                        if not data.get("is_running", False) or data.get("total_findings", 0) == 0:
                            # Check if we recently triggered research
                            if (not self.last_research_trigger or 
                                (datetime.now() - self.last_research_trigger).seconds > 7200):  # 2 hours
                                
                                self.last_research_trigger = datetime.now()
                                topic = random.choice(self.research_topics)
                                
                                proposal_id = f"research_{int(datetime.now().timestamp())}"
                                return [{
                                    "id": proposal_id,
                                    "gap": f"Research topic: {topic}",
                                    "status": "pending_approval",
                                    "timestamp": datetime.now().isoformat(),
                                    "suggested_agent": "Seeker",
                                    "action": f"Conduct research on '{topic}' and generate findings",
                                    "priority": "medium",
                                    "source": "research_daemon",
                                    "metadata": {"topic": topic}
                                }]
        except Exception as e:
            logger.warning(f"[Proactive] Failed to check research daemon: {e}")
        
        return []

    async def _generate_system_improvements(self) -> List[Dict]:
        """Generate system improvement tasks when idle."""
        # Pick a random system improvement task
        task = random.choice(self.system_improvement_tasks)
        
        # Check if this task was recently proposed
        recent_tasks = [p for p in self.proposals 
                       if p["source"] == "system_improvement" 
                       and (datetime.now() - datetime.fromisoformat(p["timestamp"])).days < 1]
        
        if len(recent_tasks) < 2:  # Limit to 2 system improvements per day
            proposal_id = f"system_{int(datetime.now().timestamp())}"
            return [{
                "id": proposal_id,
                "gap": task,
                "status": "pending_approval",
                "timestamp": datetime.now().isoformat(),
                "suggested_agent": "Architect",
                "action": f"Design and implement: {task}",
                "priority": "low",
                "source": "system_improvement"
            }]
        
        return []

    async def trigger_immediate_work(self, work_type: str = "system") -> Dict:
        """Manually trigger immediate work generation."""
        if work_type == "research":
            proposals = await self._check_research_daemon()
        elif work_type == "artifact":
            proposals = await self._scan_artifacts()
        elif work_type == "system":
            proposals = await self._generate_system_improvements()
        else:
            proposals = await self._scan_plan_gaps()
        
        if proposals:
            proposal = proposals[0]
            if not any(p["id"] == proposal["id"] for p in self.proposals):
                self.proposals.append(proposal)
                logger.info(f"[Proactive] MANUALLY TRIGGERED: {proposal['gap']}")
            
            return proposal
        
        return {"status": "no_work_generated", "message": "No work could be generated"}

    def get_active_proposals(self) -> List[Dict]:
        return [p for p in self.proposals if p["status"] == "pending_approval"]

    def get_stats(self) -> Dict:
        return {
            "total_proposals": len(self.proposals),
            "active_proposals": len(self.get_active_proposals()),
            "last_artifact_scan": self.last_artifact_scan.isoformat() if self.last_artifact_scan else None,
            "last_research_trigger": self.last_research_trigger.isoformat() if self.last_research_trigger else None,
            "is_running": self.running,
            "interval_seconds": self.interval
        }

def get_proactive_loop(manus_engine=None):
    # Singleton-like getter
    if not hasattr(get_proactive_loop, "_instance"):
        get_proactive_loop._instance = ProactiveOrchestrationLoop(manus_engine)
    return get_proactive_loop._instance
