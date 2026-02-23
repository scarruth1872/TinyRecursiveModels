
from swarm_v2.core.lobster_shell import get_lobster_shell
import os

def test_lobster_shell():
    print("🦞 Starting Lobster Shell Security Stress Test...")
    shell = get_lobster_shell()
    
    # Test 1: Whitelist Command
    print("\n[Test 1] Running Whitelisted Command (git --version)...")
    success, result = shell.audit_and_execute("git --version")
    print(f"Result (Success={success}): {result.strip()}")
    
    # Test 2: Non-Whitelisted Command
    print("\n[Test 2] Running Blocked Command (whoami)...")
    success, result = shell.audit_and_execute("whoami")
    print(f"Result (Success={success}): {result.strip()}")
    
    # Test 3: System Path Escape
    print("\n[Test 3] Attempting System Path Access (dir C:\\Windows)...")
    success, result = shell.audit_and_execute("dir C:\\Windows")
    print(f"Result (Success={success}): {result.strip()}")
    
    # Test 4: Project Root Escape
    print("\n[Test 4] Attempting Execution Outside Project Root...")
    success, result = shell.audit_and_execute("dir", cwd="C:\\")
    print(f"Result (Success={success}): {result.strip()}")

    print("\n🏁 Lobster Shell Test Complete. Check NEURAL_AUDIT_LOG.md for violation records.")

if __name__ == "__main__":
    test_lobster_shell()
