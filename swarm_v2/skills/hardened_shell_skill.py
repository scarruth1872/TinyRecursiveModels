
from swarm_v2.core.lobster_shell import get_lobster_shell

class HardenedShellSkill:
    """Safe shell execution using the Lobster Shell security middleware."""
    skill_name = "ShellSkill" # Overriding standard ShellSkill name for registry compatibility
    description = "Execute shell commands within a hardened security context (Shell-01 Protocol)."

    def __init__(self):
        self.shell = get_lobster_shell()

    def run(self, command: str) -> str:
        """
        Runs a command through the Lobster Shell audit.
        """
        success, result = self.shell.audit_and_execute(command)
        
        if not success:
            return f"[SECURITY BLOCK] {result}"
            
        return result or "(no output)"
