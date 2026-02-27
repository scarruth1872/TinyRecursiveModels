
import os
import subprocess
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Lobster Shell (Shell-01 Protocol)
# Defines the hardened environment for autonomous agent execution.

PROJECT_ROOT = "f:\\Development sites\\TRM agent swarm"
ALLOWED_COMMANDS = {
    "git", "python", "npm", "pip", "npx", "ollama", "node", "ls", "dir", "mkdir", "echo"
}

BLACKLISTED_PATHS = {
    "C:\\Windows", "C:\\Users", "C:\\Program Files", "/etc", "/usr", "/root"
}

# Configure Neural Audit Log
AUDIT_LOG_PATH = "f:\\Development sites\\TRM agent swarm\\swarm_v2_artifacts\\NEURAL_AUDIT_LOG.md"

class LobsterShell:
    """
    Security Middleware for shell-level operations in Swarm OS.
    Ensures agents stay within Project boundaries and approved toolsets.
    """

    @staticmethod
    def audit_and_execute(command: str, cwd: str = PROJECT_ROOT) -> Tuple[bool, str]:
        """
        Validates the command against the Shell-01 protocol whitelists.
        If approved, executes in the restricted environment.
        """
        # 1. Integrity Check: Absolute Path Restriction
        abs_cwd = os.path.abspath(cwd)
        if not abs_cwd.startswith(os.path.abspath(PROJECT_ROOT)):
            error_msg = f"Security Violation: Attempted execution outside project root ({abs_cwd})"
            LobsterShell._log_violation(command, error_msg)
            return False, error_msg

        # 2. Command Whitelist Check
        base_cmd = command.split()[0].lower()
        # Handle Windows .exe or .ps1 extensions
        base_cmd = os.path.basename(base_cmd).replace(".exe", "").replace(".ps1", "")
        
        if base_cmd not in ALLOWED_COMMANDS:
            # Check for common internal scripts
            if not (base_cmd.startswith(".") or base_cmd.startswith("venv")):
                error_msg = f"Security Violation: Command '{base_cmd}' is not in the Shell-01 whitelist."
                LobsterShell._log_violation(command, error_msg)
                return False, error_msg

        # 3. Path Traversal & Blacklist Check
        for blocked in BLACKLISTED_PATHS:
            if blocked.lower() in command.lower():
                error_msg = f"Security Violation: Accessed blacklisted path '{blocked}'."
                LobsterShell._log_violation(command, error_msg)
                return False, error_msg

        # 4. Controlled Execution
        try:
            print(f"[Lobster Shell] ✅ Executing approved command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=abs_cwd,
                capture_output=True,
                text=True,
                timeout=30 # Hard timeout for agent tasks
            )
            
            if result.returncode != 0:
                 return False, result.stderr
            return True, result.stdout
            
        except subprocess.TimeoutExpired:
            return False, "Process timed out after 30 seconds."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _log_violation(command: str, reason: str):
        """Logs security discrepancies to the NEURAL_AUDIT_LOG.md."""
        timestamp = datetime.now().isoformat()
        entry = f"\n### [Shell-01 Violation] {timestamp}\n- **Command**: `{command}`\n- **Reason**: {reason}\n- **Status**: BLOCKED\n"
        
        try:
            with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
             print(f"Failed to write to audit log: {e}")

def get_lobster_shell():
    return LobsterShell()
