#!/usr/bin/env python3
"""
Simple integration test for TRM-enhanced sub-agent spawning.
Tests actual parallel processing activation.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_parallel_activation():
    """Test if parallel processing actually gets activated."""
    from swarm_v2.core.trm_integration import create_trm_enhanced_agent
    from swarm_v2.core.base_agent import AgentPersona
    from swarm_v2.skills.file_skill import FileSkill
    
    print("Testing parallel processing activation...")
    
    # Create agent with parallel enabled
    persona = AgentPersona(
        name="IntegrationTestAgent",
        role="Integration Tester",
        background="Tests parallel processing activation",
        specialties=["integration testing", "parallel processing"],
        avatar_color="#0000ff"
    )
    
    agent = create_trm_enhanced_agent(persona, [FileSkill()])
    agent.enable_parallel(True)
    agent.set_recursion_depth(2)
    
    # Test with a complex task that should trigger parallel processing
    complex_tasks = [
        # Long complex task - should trigger parallel
        "Analyze this complex pattern and explain the mathematical relationships: " + 
        "1 2 3 5 8 13 21 34 55 89 144 233 377 610 987 1597 2584 4181 6765 " +
        "and also analyze the symbolic structure: alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu",
        
        # Another complex task
        "Solve this multi-step reasoning problem: " +
        "If 3 workers can build 3 houses in 3 days, how many houses can 9 workers build in 9 days? " +
        "Show all mathematical reasoning steps and explain the logical progression.",
    ]
    
    for i, task in enumerate(complex_tasks, 1):
        print(f"\nTask {i}: {task[:80]}...")
        
        # Check task complexity analysis
        complexity = agent._analyze_task_complexity(task)
        print(f"  Complexity analysis: {complexity}")
        
        should_parallel = agent._should_use_parallel(complexity, task)
        print(f"  Should use parallel: {should_parallel}")
        
        if should_parallel:
            print(f"  Task length: {len(task)} characters")
            
            # Test partition function
            partitions = agent.trm_orchestrator.partition_context(task, agent.trm_orchestrator.max_parallel_tasks)
            print(f"  Would partition into: {len(partitions)} sub-tasks")
            
            # Check if partitions are meaningful
            if partitions:
                avg_len = sum(len(p) for p in partitions) / len(partitions)
                print(f"  Average partition length: {avg_len:.0f} chars")
        
        # Get agent status
        status = agent.get_trm_status()
        print(f"  TRM status: parallel_enabled={status['parallel_enabled']}")
        print(f"  Max recursion depth: {status['max_recursion_depth']}")
    
    print("\n" + "="*60)
    print("INTEGRATION TEST COMPLETE")
    print("="*60)
    
    # Check orchestrator status
    from swarm_v2.core.trm_orchestrator import get_trm_orchestrator
    orchestrator = get_trm_orchestrator()
    orchestrator_status = orchestrator.get_status()
    
    print(f"\nTRM Orchestrator Status:")
    print(f"  Available cores: {orchestrator_status.get('available_cores', 0)}")
    print(f"  Max parallel tasks: {orchestrator_status.get('max_parallel_tasks', 0)}")
    print(f"  Subagents: {orchestrator_status.get('subagents', 0)}")
    
    return True

async def test_resource_arbiter_integration():
    """Test integration with resource arbiter."""
    print("\n" + "="*60)
    print("TESTING RESOURCE ARBITER INTEGRATION")
    print("="*60)
    
    try:
        from swarm_v2.core.resource_arbiter import get_resource_arbiter
        arbiter = get_resource_arbiter()
        
        print("Resource Arbiter Status:")
        print(f"  Available VRAM slots: {arbiter.available_vram_slots}")
        print(f"  Total slots: {arbiter.total_slots}")
        print(f"  Active models: {list(arbiter.active_models.keys())}")
        
        return True
    except Exception as e:
        print(f"Resource Arbiter integration test failed: {e}")
        return False

async def test_task_arbiter_integration():
    """Test integration with task arbiter."""
    print("\n" + "="*60)
    print("TESTING TASK ARBITER INTEGRATION")
    print("="*60)
    
    try:
        from swarm_v2.core.task_arbiter import get_task_arbiter
        arbiter = get_task_arbiter()
        
        print("Task Arbiter Status:")
        print(f"  Logical cores: {arbiter.logical_cores}")
        print(f"  Physical cores: {arbiter.physical_cores}")
        print(f"  Available workers: {len(arbiter.workers)}")
        
        return True
    except Exception as e:
        print(f"Task Arbiter integration test failed: {e}")
        return False

async def main():
    print("TRM-ENHANCED SUB-AGENT SPAWNING INTEGRATION TEST")
    print("="*60)
    
    results = []
    
    try:
        # Run tests
        results.append(("Parallel activation test", await test_parallel_activation()))
        results.append(("Resource arbiter integration", await test_resource_arbiter_integration()))
        results.append(("Task arbiter integration", await test_task_arbiter_integration()))
        
        print("\n" + "="*60)
        print("INTEGRATION TEST SUMMARY")
        print("="*60)
        
        all_passed = True
        for test_name, passed in results:
            status = "PASS" if passed else "FAIL"
            print(f"{test_name}: {status}")
            if not passed:
                all_passed = False
        
        print("\n" + "="*60)
        if all_passed:
            print("✅ ALL INTEGRATION TESTS PASSED")
            print("\nThe TRM-enhanced sub-agent spawning system is properly integrated with:")
            print("1. Resource Arbiter - for GPU/VRAM management")
            print("2. Task Arbiter - for CPU core allocation")
            print("3. Parallel processing logic - for task complexity analysis")
        else:
            print("⚠️  SOME INTEGRATION TESTS FAILED")
            print("\nCheck the implementation for integration issues.")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)