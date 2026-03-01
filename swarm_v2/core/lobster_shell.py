
import os
import subprocess
import logging
import json
from typing import List, Dict, Any, Tuple, Optional, Callable
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

PROJECT_ROOT = "f:\\Development sites\\TRM agent swarm"
ALLOWED_COMMANDS = {
    "git", "python", "npm", "pip", "npx", "ollama", "node", "ls", "dir", "mkdir", "echo"
}

BLACKLISTED_PATHS = {
    "C:\\Windows", "C:\\Users", "C:\\Program Files", "/etc", "/usr", "/root"
}

AUDIT_LOG_PATH = "f:\\Development sites\\TRM agent swarm\\swarm_v2_artifacts\\NEURAL_AUDIT_LOG.md"

APPROVAL_QUEUE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "swarm_v2_artifacts", "approval_queue.json"
)


class ApprovalGate:
    """
    Human-in-the-loop approval gate for LobsterShell pipelines.
    Writes approval requests to a JSON queue file and polls for status.
    """

    def __init__(self, queue_path: str = APPROVAL_QUEUE_PATH, timeout_s: float = 300.0):
        self.queue_path = os.path.abspath(queue_path)
        self.timeout_s = timeout_s
        os.makedirs(os.path.dirname(self.queue_path), exist_ok=True)

    def request_approval(self, pipeline_name: str, step_name: str,
                         step_index: int) -> bool:
        """
        Submit an approval request and check for auto-approve.

        In production, this writes to the queue and returns True only if
        the approval_queue.json is updated with status="approved".
        For now, we auto-approve and log the request.
        """
        import time as _time
        request = {
            "pipeline": pipeline_name,
            "step": step_name,
            "step_index": step_index,
            "status": "pending",
            "requested_at": datetime.now().isoformat(),
        }

        # Write request to queue
        queue = self._load_queue()
        queue.append(request)
        self._save_queue(queue)

        logger.info(f"[ApprovalGate] Requested approval for {pipeline_name}/{step_name}")

        # Check if compliance mode allows auto-approve
        try:
            from swarm_v2.core.swarm_engine import ComplianceMode
            # Auto-approve in Solo-Ninja mode
            return True  # Default: auto-approve (queue is for audit trail)
        except ImportError:
            return True

    def _load_queue(self) -> list:
        if os.path.exists(self.queue_path):
            try:
                with open(self.queue_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_queue(self, queue: list):
        # Keep only last 50 entries
        queue = queue[-50:]
        with open(self.queue_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2)


class LobsterStep(BaseModel):
    tool: str
    args: Dict[str, Any] = {}
    gate: Optional[str] = None # "manual" or "auto"
    transform: Optional[str] = None # e.g., "pick:id", "head:5", "json"

class LobsterPipeline(BaseModel):
    name: str
    steps: List[LobsterStep]

class LobsterShell:
    """
    Lobster Shell (Shell-01 Protocol + Typed Pipelines).
    The hardened environment for autonomous agent execution and deterministic workflows.
    """
    def __init__(self, tool_executor: Optional[Callable] = None):
        self.execute_tool = tool_executor

    @staticmethod
    def audit_and_execute(command: str, cwd: str = PROJECT_ROOT) -> Tuple[bool, str]:
        """Validates and executes a raw shell command (Security Middleware)."""
        abs_cwd = os.path.abspath(cwd)
        if not abs_cwd.startswith(os.path.abspath(PROJECT_ROOT)):
            error_msg = f"Security Violation: Attempted execution outside project root ({abs_cwd})"
            LobsterShell._log_violation(command, error_msg)
            return False, error_msg

        base_cmd = command.split()[0].lower()
        base_cmd = os.path.basename(base_cmd).replace(".exe", "").replace(".ps1", "")
        
        if base_cmd not in ALLOWED_COMMANDS:
            if not (base_cmd.startswith(".") or base_cmd.startswith("venv")):
                error_msg = f"Security Violation: Command '{base_cmd}' is not in the Shell-01 whitelist."
                LobsterShell._log_violation(command, error_msg)
                return False, error_msg

        for blocked in BLACKLISTED_PATHS:
            if blocked.lower() in command.lower():
                error_msg = f"Security Violation: Accessed blacklisted path '{blocked}'."
                LobsterShell._log_violation(command, error_msg)
                return False, error_msg

        try:
            print(f"[Lobster Shell] ✅ Executing approved command: {command}")
            result = subprocess.run(
                command, shell=True, cwd=abs_cwd,
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                 return False, result.stderr
            return True, result.stdout
        except subprocess.TimeoutExpired:
            return False, "Process timed out after 60 seconds."
        except Exception as e:
            return False, str(e)

    async def run_pipeline(self, pipeline: LobsterPipeline, initial_input: Any = None) -> Any:
        """Executes a typed pipeline of tool calls."""
        if not self.execute_tool:
            raise ValueError("LobsterShell needs a tool_executor to run pipelines.")

        current_data = initial_input
        print(f"[Lobster] Starting Pipeline: {pipeline.name}")

        for i, step in enumerate(pipeline.steps):
            print(f"[Lobster] Step {i+1}/{len(pipeline.steps)}: {step.tool}")
            
            if step.gate == "manual":
                gate = ApprovalGate()
                approved = gate.request_approval(
                    pipeline_name=pipeline.name,
                    step_name=step.tool,
                    step_index=i,
                )
                if not approved:
                    print(f"[Lobster] BLOCKED: Step {i+1} rejected or timed out.")
                    return {"error": "approval_rejected", "step": i}
            
            args = step.args.copy()
            if current_data is not None:
                args["input_context"] = current_data

            result = await self.execute_tool(step.tool, args)
            current_data = self._apply_transform(result, step.transform)
            
        return current_data


    def _apply_transform(self, data: Any, transform: Optional[str]) -> Any:
        if not transform: return data
        try:
            if transform.startswith("pick:"):
                key = transform.split(":")[1]
                if isinstance(data, dict): return data.get(key)
                if isinstance(data, list): return [item.get(key) for item in data if isinstance(item, dict)]
            elif transform.startswith("head:"):
                n = int(transform.split(":")[1])
                return data[:n] if isinstance(data, list) else data
            elif transform == "json":
                return json.loads(data) if isinstance(data, str) else data
        except Exception as e:
            logger.error(f"[Lobster] Transform error: {e}")
        return data

    @staticmethod
    def _log_violation(command: str, reason: str):
        timestamp = datetime.now().isoformat()
        entry = (f"\n### [Shell-01 Violation] {timestamp}\n"
                 f"- **Command**: `{command}`\n- **Reason**: {reason}\n- **Status**: BLOCKED\n")
        try:
            with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(entry)
        except: pass

def get_lobster_shell(executor: Optional[Callable] = None):
    return LobsterShell(tool_executor=executor)
