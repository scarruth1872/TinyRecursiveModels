"""
Ultrawork Loop — Autonomous Plan → Act → Verify Cycle
The QIAE's core execution pattern: every mission goes through explicit
planning, execution, and verification phases with retry on failure.
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("UltraworkLoop")


class MissionPhase(Enum):
    PLANNING = "planning"
    ACTING = "acting"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MissionStep:
    """A single step in a mission plan."""
    description: str
    acceptance_criteria: str = ""
    status: str = "pending"  # pending, running, completed, failed
    result: str = ""
    attempts: int = 0


@dataclass
class MissionState:
    """Serializable mission state for persistence and resume."""
    mission_id: str
    objective: str
    phase: str = "planning"
    steps: List[Dict[str, Any]] = field(default_factory=list)
    plan_text: str = ""
    progress_log: List[str] = field(default_factory=list)
    verification_result: str = ""
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""


MISSIONS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "swarm_v2_artifacts", "missions"
)


class UltraworkLoop:
    """
    Autonomous Plan → Act → Verify execution cycle.

    Each mission goes through:
    1. PLAN: Agent generates a plan with steps and acceptance criteria
    2. ACT: Agent executes each step, recording progress
    3. VERIFY: Validator agent reviews output against criteria

    Supports mission persistence (resume interrupted missions) and
    integrates with ComplianceMode for gate enforcement.
    """

    def __init__(self):
        os.makedirs(MISSIONS_DIR, exist_ok=True)
        self._active_missions: Dict[str, MissionState] = {}
        self._completed_missions: List[str] = []

    def create_mission(self, objective: str, mission_id: str = None,
                       max_retries: int = 3) -> MissionState:
        """Create a new mission."""
        mid = mission_id or f"mission-{int(time.time())}"
        state = MissionState(
            mission_id=mid,
            objective=objective,
            max_retries=max_retries,
        )
        self._active_missions[mid] = state
        self._persist(state)
        logger.info(f"[Ultrawork] Created mission: {mid} — {objective[:60]}")
        return state

    async def execute_mission(self, mission_id: str,
                              planner: Callable = None,
                              executor: Callable = None,
                              verifier: Callable = None) -> MissionState:
        """
        Execute the full Plan → Act → Verify cycle.

        Args:
            mission_id: ID of the mission to execute
            planner: async fn(objective) -> plan_text
            executor: async fn(step_description) -> result
            verifier: async fn(objective, results) -> "PASS" or "FAIL: reason"
        """
        state = self._active_missions.get(mission_id)
        if not state:
            raise ValueError(f"Mission {mission_id} not found")

        for attempt in range(state.max_retries):
            state.retry_count = attempt

            # --- PLAN ---
            state.phase = MissionPhase.PLANNING.value
            self._log(state, f"Phase: PLANNING (attempt {attempt + 1})")

            if planner:
                plan_text = await planner(state.objective)
                state.plan_text = plan_text
                state.steps = self._parse_plan(plan_text)
            elif not state.steps:
                # Default: single-step plan
                state.steps = [{
                    "description": state.objective,
                    "acceptance_criteria": "Task completed successfully",
                    "status": "pending",
                    "result": "",
                    "attempts": 0,
                }]

            self._persist(state)

            # --- ACT ---
            state.phase = MissionPhase.ACTING.value
            self._log(state, f"Phase: ACTING — {len(state.steps)} steps")

            all_passed = True
            for i, step in enumerate(state.steps):
                step["status"] = "running"
                step["attempts"] += 1
                self._log(state, f"Step {i+1}: {step['description'][:60]}")

                if executor:
                    try:
                        result = await executor(step["description"])
                        step["result"] = str(result)[:500]
                        step["status"] = "completed"
                    except Exception as e:
                        step["result"] = f"ERROR: {e}"
                        step["status"] = "failed"
                        all_passed = False
                else:
                    step["status"] = "completed"
                    step["result"] = "[No executor — auto-pass]"

                self._persist(state)

            # --- VERIFY ---
            state.phase = MissionPhase.VERIFYING.value
            results_summary = "\n".join(
                f"Step {i+1} [{s['status']}]: {s['result'][:100]}"
                for i, s in enumerate(state.steps)
            )
            self._log(state, f"Phase: VERIFYING")

            # Check compliance mode
            skip_verify = False
            try:
                from swarm_v2.core.swarm_engine import ComplianceMode
                # Solo-Ninja skips verification
                skip_verify = False  # Let caller decide
            except ImportError:
                pass

            if verifier and not skip_verify:
                verification = await verifier(state.objective, results_summary)
                state.verification_result = str(verification)[:500]

                if "PASS" in str(verification).upper():
                    state.phase = MissionPhase.COMPLETED.value
                    state.completed_at = datetime.now().isoformat()
                    self._log(state, "VERIFIED: Mission PASSED")
                    self._persist(state)
                    self._completed_missions.append(mission_id)
                    return state
                else:
                    self._log(state, f"VERIFY FAILED: {verification[:100]}. Retrying...")
                    # Reset steps for retry
                    for step in state.steps:
                        step["status"] = "pending"
                        step["result"] = ""
            else:
                # No verifier or skip — auto-pass if all steps completed
                if all_passed:
                    state.phase = MissionPhase.COMPLETED.value
                    state.completed_at = datetime.now().isoformat()
                    self._log(state, "Mission COMPLETED (auto-verified)")
                    self._persist(state)
                    self._completed_missions.append(mission_id)
                    return state

        # Exhausted retries
        state.phase = MissionPhase.FAILED.value
        self._log(state, f"Mission FAILED after {state.max_retries} attempts")
        self._persist(state)
        return state

    def resume_mission(self, mission_id: str) -> Optional[MissionState]:
        """Resume a persisted mission from disk."""
        path = os.path.join(MISSIONS_DIR, f"{mission_id}.json")
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        state = MissionState(**data)
        self._active_missions[mission_id] = state
        logger.info(f"[Ultrawork] Resumed mission: {mission_id} at phase={state.phase}")
        return state

    def _parse_plan(self, plan_text: str) -> List[Dict[str, Any]]:
        """Parse a plan text into structured steps."""
        steps = []
        lines = plan_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                desc = line.lstrip("0123456789.-*) ").strip()
                if desc:
                    steps.append({
                        "description": desc,
                        "acceptance_criteria": "",
                        "status": "pending",
                        "result": "",
                        "attempts": 0,
                    })
        return steps if steps else [{"description": plan_text[:200], "acceptance_criteria": "",
                                     "status": "pending", "result": "", "attempts": 0}]

    def _log(self, state: MissionState, message: str):
        """Append to mission progress log."""
        entry = f"[{datetime.now().isoformat()}] {message}"
        state.progress_log.append(entry)
        logger.info(f"[Ultrawork:{state.mission_id}] {message}")

    def _persist(self, state: MissionState):
        """Save mission state to disk."""
        path = os.path.join(MISSIONS_DIR, f"{state.mission_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(vars(state), f, indent=2, default=str)

    def list_missions(self) -> List[Dict[str, Any]]:
        """List all missions."""
        return [{
            "mission_id": s.mission_id,
            "objective": s.objective[:60],
            "phase": s.phase,
            "steps": len(s.steps),
            "retry_count": s.retry_count,
        } for s in self._active_missions.values()]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "active": len(self._active_missions),
            "completed": len(self._completed_missions),
            "missions_dir": MISSIONS_DIR,
        }


# Singleton
_loop: Optional[UltraworkLoop] = None

def get_ultrawork_loop() -> UltraworkLoop:
    global _loop
    if _loop is None:
        _loop = UltraworkLoop()
    return _loop
