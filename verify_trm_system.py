#!/usr/bin/env python3
"""
Quick verification of TRM-enhanced sub-agent spawning system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_modules():
    """Check if required modules exist and can be imported."""
    print("Checking TRM-enhanced system modules...")
    
    modules_to_check = [
        ("swarm_v2.core.trm_integration", "TRM Integration"),
        ("swarm_v2.core.trm_orchestrator", "TRM Orchestrator"),
        ("swarm_v2.core.trm_brain", "TRM Brain"),
        ("swarm_v2.core.base_agent", "Base Agent"),
    ]
    
    all_good = True
    for module_name, display_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name} module loaded")
        except ImportError as e:
            print(f"  ✗ {display_name} module failed: {e}")
            all_good = False
    
    return all_good

def check_class_availability():
    """Check if key classes are available."""
    print("\nChecking class availability...")
    
    try:
        from swarm_v2.core.trm_integration import TRMEnhancedAgent, create_trm_enhanced_agent
        print("  ✓ TRMEnhancedAgent class available")
        print("  ✓ create_trm_enhanced_agent factory function available")
        
        from swarm_v2.core.base_agent import AgentPersona
        print("  ✓ AgentPersona class available")
        
        # Test creating a simple persona
        persona = AgentPersona(
            name="TestAgent",
            role="Tester",
            background="Test agent",
            specialties=["testing"],
            avatar_color="#ff0000"
        )
        print("  ✓ Can create AgentPersona instance")
        
        return True
    except Exception as e:
        print(f"  ✗ Class availability check failed: {e}")
        return False

def check_file_existence():
    """Check if key implementation files exist."""
    print("\nChecking file existence...")
    
    files_to_check = [
        "swarm_v2/core/trm_integration.py",
        "swarm_v2/core/trm_orchestrator.py",
        "swarm_v2/core/trm_brain.py",
        "test_trm_parallel.py",
        "TRM_SUBAGENT_ARCHITECTURE.md"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file_path} exists ({size} bytes)")
        else:
            print(f"  ✗ {file_path} missing")
            all_exist = False
    
    return all_exist

def quick_smoke_test():
    """Run a quick smoke test without heavy dependencies."""
    print("\nRunning quick smoke test...")
    
    try:
        # Try to create a simple agent without running it
        from swarm_v2.core.trm_integration import create_trm_enhanced_agent
        from swarm_v2.core.base_agent import AgentPersona
        
        persona = AgentPersona(
            name="SmokeTestAgent",
            role="Smoke Tester",
            background="Smoke test agent",
            specialties=["smoke testing"],
            avatar_color="#00ff00"
        )
        
        # Create agent (won't actually run anything)
        agent = create_trm_enhanced_agent(persona, [])
        
        # Check if agent has expected attributes
        expected_attrs = ["trm_orchestrator", "parallel_enabled", "max_recursion_depth"]
        for attr in expected_attrs:
            if hasattr(agent, attr):
                print(f"  ✓ Agent has {attr} attribute")
            else:
                print(f"  ✗ Agent missing {attr} attribute")
                return False
        
        print("  ✓ Smoke test passed - basic agent creation works")
        return True
        
    except Exception as e:
        print(f"  ✗ Smoke test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("TRM-ENHANCED SUB-AGENT SPAWNING SYSTEM VERIFICATION")
    print("=" * 60)
    
    results = []
    
    # Run checks
    results.append(("Module imports", check_modules()))
    results.append(("Class availability", check_class_availability()))
    results.append(("File existence", check_file_existence()))
    results.append(("Smoke test", quick_smoke_test()))
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ SYSTEM VERIFIED - TRM-enhanced sub-agent spawning ready")
        print("\nKey components implemented:")
        print("1. TRMIntegration - Connects TRM Orchestrator with BaseAgent")
        print("2. TRMOrchestrator - Manages parallel sub-agent spawning")
        print("3. TRMEnhancedAgent - BaseAgent with parallel reasoning")
        print("4. Test suite - Performance comparison and validation")
        print("\nTest with: python test_trm_parallel.py")
    else:
        print("⚠️  SYSTEM INCOMPLETE - Some components missing")
        print("\nCheck the implementation files and dependencies.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())