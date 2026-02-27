#!/usr/bin/env python3
"""
Debug the parallel processing logic in TRM-enhanced agents.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_parallel_decision():
    """Debug why parallel processing isn't being triggered."""
    from swarm_v2.core.trm_integration import create_trm_enhanced_agent
    from swarm_v2.core.base_agent import AgentPersona
    
    persona = AgentPersona(
        name="DebugAgent",
        role="Debugger",
        background="Debug parallel processing",
        specialties=["debugging"],
        avatar_color="#ff0000"
    )
    
    agent = create_trm_enhanced_agent(persona, [])
    agent.enable_parallel(True)
    
    # Test tasks
    test_tasks = [
        ("Short symbolic", "Analyze pattern: 1 2 3 4 5"),
        ("Medium symbolic", "Analyze pattern: " + "1 " * 50),
        ("Long symbolic", "Analyze pattern: " + "1 " * 150),
        ("Complex symbolic", "Analyze this pattern and explain: " + "1 2 3 5 8 13 21 34 55 89 144 233 377 610 " * 3),
        ("Text task", "Explain the relationship between these numbers: " + "word " * 200),
    ]
    
    print("Debugging parallel processing decisions:")
    print("="*60)
    
    for task_name, task in test_tasks:
        print(f"\nTask: {task_name}")
        print(f"  Length: {len(task)} characters")
        
        complexity = agent._analyze_task_complexity(task)
        print(f"  Complexity: {complexity}")
        
        should_parallel = agent._should_use_parallel(complexity, task)
        print(f"  Should parallel: {should_parallel}")
        
        # Check the logic step by step
        print(f"  Parallel enabled: {agent.parallel_enabled}")
        
        if agent.parallel_enabled:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            print(f"  CPU percent: {cpu_percent:.1f}%")
            print(f"  Memory percent: {memory.percent:.1f}%")
            
            # Check complexity-based logic
            if complexity in ["symbolic_high", "text_high"]:
                print(f"  High complexity check: len(task) > 100 = {len(task) > 100}")
            elif complexity == "text_medium":
                print(f"  Medium complexity check: len(task) > 300 = {len(task) > 300}")
        
        # Test partition function
        if should_parallel:
            partitions = agent.trm_orchestrator.partition_context(task, agent.trm_orchestrator.max_parallel_tasks)
            print(f"  Would partition into: {len(partitions)} sub-tasks")
    
    print("\n" + "="*60)
    print("Checking system resources for parallel decisions...")
    
    import psutil
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    
    print(f"CPU usage: {cpu_percent:.1f}%")
    print(f"Memory usage: {memory.percent:.1f}%")
    print(f"CPU > 80%: {cpu_percent > 80}")
    print(f"Memory > 85%: {memory.percent > 85}")
    
    print("\n" + "="*60)
    print("Testing partition logic...")
    
    # Test the partition function directly
    long_task = "x " * 500
    partitions = agent.trm_orchestrator.partition_context(long_task, 4)
    print(f"500-char task partitioned into {len(partitions)} parts")
    for i, part in enumerate(partitions[:3]):  # Show first 3
        print(f"  Part {i+1}: {len(part)} chars: {part[:50]}...")
    
    return True

def check_torch_issue():
    """Check the torch 'Buffer' attribute issue."""
    print("\n" + "="*60)
    print("Checking torch compatibility issue...")
    
    try:
        import torch
        print(f"Torch version: {torch.__version__}")
        print(f"Has nn.Buffer: {hasattr(torch.nn, 'Buffer')}")
        print(f"nn module attributes: {[x for x in dir(torch.nn) if not x.startswith('_')][:10]}...")
    except ImportError as e:
        print(f"Torch import error: {e}")
    
    return True

def main():
    print("DEBUG PARALLEL PROCESSING LOGIC")
    print("="*60)
    
    try:
        debug_parallel_decision()
        check_torch_issue()
        
        print("\n" + "="*60)
        print("DEBUG COMPLETE")
        
        return 0
    except Exception as e:
        print(f"\nError during debug: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())