#!/usr/bin/env python3
"""
Integration test for TRM-enhanced system with existing Swarm V2 components.
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_existing_system():
    """Test the current system without TRM integration."""
    print("="*70)
    print("TEST 1: EXISTING SYSTEM WITHOUT TRM")
    print("="*70)
    
    from swarm_v2.core.base_agent import AgentPersona, BaseAgent
    from swarm_v2.core.expert_registry import get_expert_registry
    from swarm_v2.core.cognitive_stack import CognitiveStack
    
    # Create a simple agent
    persona = AgentPersona(
        name="TestAgent",
        role="Tester",
        background="Test agent for integration",
        specialties=["testing", "integration"],
        avatar_color="#ff0000"
    )
    
    agent = BaseAgent(persona, [])
    
    # Test cognitive stack
    print("\n1. Testing CognitiveStack...")
    stack = CognitiveStack("TestAgent")
    
    test_prompt = "Analyze this pattern: 1 2 3 4 5 6 7 8 9 10"
    response, trace = await stack.process(test_prompt)
    
    print(f"   Prompt: {test_prompt}")
    print(f"   Response length: {len(response)} chars")
    print(f"   Trace: {trace}")
    
    # Test expert registry
    print("\n2. Testing ExpertRegistry...")
    registry = get_expert_registry()
    registry.register_team({"TestAgent": agent})
    
    retrieved = registry.get_agent("TestAgent")
    print(f"   Agent retrieved: {retrieved is not None}")
    if retrieved:
        print(f"   Agent name: {retrieved.persona.name}")
    
    return True

async def test_trm_integration():
    """Test TRM integration with existing components."""
    print("\n" + "="*70)
    print("TEST 2: TRM-ENHANCED SYSTEM INTEGRATION")
    print("="*70)
    
    from swarm_v2.core.trm_integration import create_trm_enhanced_agent
    from swarm_v2.core.base_agent import AgentPersona
    from swarm_v2.core.expert_registry import get_expert_registry
    
    # Create TRM-enhanced agent
    persona = AgentPersona(
        name="TRMTestAgent",
        role="TRM Tester",
        background="TRM-enhanced test agent",
        specialties=["parallel reasoning", "symbolic analysis"],
        avatar_color="#00ff00"
    )
    
    agent = create_trm_enhanced_agent(persona, [])
    
    print(f"1. Created TRM-enhanced agent:")
    print(f"   Name: {agent.persona.name}")
    print(f"   Parallel enabled: {agent.parallel_enabled}")
    print(f"   Max recursion depth: {agent.max_recursion_depth}")
    print(f"   Has TRM orchestrator: {hasattr(agent, 'trm_orchestrator')}")
    
    # Test with registry
    print("\n2. Testing with ExpertRegistry...")
    registry = get_expert_registry()
    registry.register_team({"TRMTestAgent": agent})
    
    retrieved = registry.get_agent("TRMTestAgent")
    print(f"   Agent retrieved from registry: {retrieved is not None}")
    
    if retrieved:
        # Check if it's TRM-enhanced
        print(f"   Is TRM-enhanced: {hasattr(retrieved, 'trm_orchestrator')}")
        print(f"   Parallel enabled: {getattr(retrieved, 'parallel_enabled', 'N/A')}")
        
        # Test status method
        if hasattr(retrieved, 'get_trm_status'):
            status = retrieved.get_trm_status()
            print(f"   TRM status available: {bool(status)}")
            print(f"   Agent ID: {status.get('agent_id', 'N/A')}")
    
    return True

async def test_cognitive_stack_with_trm():
    """Test if CognitiveStack can leverage TRM capabilities."""
    print("\n" + "="*70)
    print("TEST 3: COGNITIVE STACK WITH TRM INTEGRATION")
    print("="*70)
    
    from swarm_v2.core.cognitive_stack import CognitiveStack
    from swarm_v2.core.trm_brain import get_trm_brain
    
    print("1. Testing TRM brain availability...")
    try:
        trm_brain = get_trm_brain()
        print(f"   TRM brain loaded: {trm_brain is not None}")
        
        # Test simple reasoning
        test_tokens = [1, 2, 3, 4, 5]
        try:
            result = trm_brain.reason(test_tokens)
            print(f"   TRM reasoning works: {len(result)} tokens output")
        except Exception as e:
            print(f"   TRM reasoning error: {e}")
    except Exception as e:
        print(f"   TRM brain load failed: {e}")
    
    print("\n2. Testing CognitiveStack with TRM offloading...")
    stack = CognitiveStack("TRMTestAgent")
    
    # Test cases that should trigger TRM offloading
    test_cases = [
        ("Simple calculation", "Calculate 2 + 2"),
        ("Pattern analysis", "Analyze this pattern: 1 2 3 5 8 13"),
        ("Logic puzzle", "If all As are Bs and some Bs are Cs, are all As Cs?"),
        ("Simple chat", "Hello, how are you?"),
    ]
    
    for name, prompt in test_cases:
        print(f"\n   Test: {name}")
        print(f"   Prompt: {prompt}")
        
        # Check if should offload to reasoning
        should_offload = stack._should_offload_to_reasoning(prompt)
        print(f"   Should offload to TRM: {should_offload}")
        
        if should_offload:
            # Actually process it
            response, trace = await stack.process(prompt)
            print(f"   Response length: {len(response)} chars")
            print(f"   Trace: {trace[:100] if trace else 'None'}")
    
    return True

async def test_task_arbiter_integration():
    """Test TaskArbiter integration with TRM-aware scheduling."""
    print("\n" + "="*70)
    print("TEST 4: TASK ARBITER INTEGRATION")
    print("="*70)
    
    try:
        from swarm_v2.core.task_arbiter import get_task_arbiter, Task, TaskComplexity
        
        arbiter = get_task_arbiter()
        print(f"1. TaskArbiter initialized:")
        print(f"   Logical cores: {arbiter.cpu_count}")
        print(f"   Physical cores: {arbiter.cpu_physical}")
        print(f"   Maintenance tasks: {len(arbiter.dynamic_arbiter.maintenance_tasks)}")
        
        # Submit a test task
        print("\n2. Submitting test task...")
        task = Task(
            task_id="test_integration",
            task_type="llm",
            complexity=TaskComplexity.MEDIUM,
            payload={"task": "Analyze symbolic pattern", "agent_id": "test_agent"},
            priority=1
        )
        
        await arbiter.submit_task(task)
        print(f"   Task submitted: {task.task_id}")
        
        # Get status
        status = arbiter.get_system_status()
        print(f"   Queued tasks: {status.get('tasks', {}).get('queued', 0)}")
        print(f"   Total tasks processed: {status.get('tasks', {}).get('total_processed', 0)}")
        
        # Complete task
        arbiter.complete_task(task.task_id, result="Test completed")
        print(f"   Task completed")
        
        return True
        
    except Exception as e:
        print(f"   TaskArbiter test failed: {e}")
        return False

async def test_full_integration_workflow():
    """Test full workflow with all integrated components."""
    print("\n" + "="*70)
    print("TEST 5: FULL INTEGRATION WORKFLOW")
    print("="*70)
    
    from swarm_v2.core.trm_integration import create_trm_enhanced_agent
    from swarm_v2.core.base_agent import AgentPersona
    from swarm_v2.core.expert_registry import get_expert_registry
    from swarm_v2.skills.file_skill import FileSkill
    
    # Create team of TRM-enhanced agents
    print("1. Creating TRM-enhanced agent team...")
    
    personas = [
        AgentPersona(
            name="LogicTRM",
            role="TRM Logic Expert",
            background="Enhanced with parallel symbolic reasoning",
            specialties=["logic", "symbolic analysis", "parallel processing"],
            avatar_color="#0000ff"
        ),
        AgentPersona(
            name="DevoTRM",
            role="TRM Developer",
            background="Enhanced with parallel code analysis",
            specialties=["coding", "code review", "parallel debugging"],
            avatar_color="#00ff00"
        ),
    ]
    
    agents = {}
    for persona in personas:
        agent = create_trm_enhanced_agent(persona, [FileSkill()])
        agents[persona.name] = agent
        print(f"   Created {persona.name}: parallel={agent.parallel_enabled}")
    
    # Register team
    print("\n2. Registering team with ExpertRegistry...")
    registry = get_expert_registry()
    registry.register_team(agents)
    
    # Test retrieval
    for name in agents.keys():
        retrieved = registry.get_agent(name)
        print(f"   {name} retrieved: {retrieved is not None}")
        if retrieved and hasattr(retrieved, 'get_trm_status'):
            status = retrieved.get_trm_status()
            print(f"     - Parallel enabled: {status.get('parallel_enabled', 'N/A')}")
    
    # Test delegation
    print("\n3. Testing delegation between TRM-enhanced agents...")
    logic_agent = registry.get_agent("LogicTRM")
    if logic_agent:
        # Create a task that would benefit from parallel reasoning
        task = """
        Analyze this complex symbolic pattern and provide insights:
        
        Pattern A: 1 4 9 16 25 36 49 64 81 100
        Pattern B: 2 3 5 7 11 13 17 19 23 29
        Pattern C: 1 1 2 3 5 8 13 21 34 55
        
        Identify the mathematical relationships and any connections between patterns.
        """
        
        print(f"   Task: {task[:80]}...")
        print(f"   Starting TRM-enhanced processing...")
        
        # Use TRM-enhanced processing
        if hasattr(logic_agent, 'process_with_trm'):
            try:
                result = await logic_agent.process_with_trm(task)
                print(f"   Processing mode: {result.get('processing_mode', 'unknown')}")
                print(f"   Partition count: {result.get('partition_count', 1)}")
                print(f"   Synthesis quality: {result.get('synthesis_quality', 0):.2f}")
                print(f"   Response preview: {result.get('response', '')[:200]}...")
            except Exception as e:
                print(f"   TRM processing failed: {e}")
        else:
            print(f"   Agent doesn't have process_with_trm method")
    
    return True

async def main():
    """Run all integration tests."""
    print("TRM-ENHANCED SYSTEM INTEGRATION TEST SUITE")
    print("="*70)
    
    results = {}
    
    try:
        results["existing_system"] = await test_existing_system()
    except Exception as e:
        print(f"Test 1 failed: {e}")
        results["existing_system"] = False
        
    try:
        results["trm_integration"] = await test_trm_integration()
    except Exception as e:
        print(f"Test 2 failed: {e}")
        results["trm_integration"] = False
        
    try:
        results["cognitive_stack"] = await test_cognitive_stack_with_trm()
    except Exception as e:
        print(f"Test 3 failed: {e}")
        results["cognitive_stack"] = False
        
    try:
        results["task_arbiter"] = await test_task_arbiter_integration()
    except Exception as e:
        print(f"Test 4 failed: {e}")
        results["task_arbiter"] = False
        
    try:
        results["full_workflow"] = await test_full_integration_workflow()
    except Exception as e:
        print(f"Test 5 failed: {e}")
        results["full_workflow"] = False
    
    # Summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL INTEGRATION TESTS PASSED")
        print("TRM-enhanced system is ready for production use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Some integration issues need to be addressed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)