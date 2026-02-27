#!/usr/bin/env python3
"""
Test TRM Parallel Sub-Agent Spawning System

Demonstrates:
1. Recursive reasoning with sub-agent spawning
2. Parallel processing across CPU cores
3. Stateful superposition and consensus
4. Performance comparison with sequential processing
"""

import asyncio
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from swarm_v2.core.trm_integration import create_trm_enhanced_agent
from swarm_v2.core.base_agent import AgentPersona
from swarm_v2.skills.file_skill import FileSkill

async def test_sequential_processing():
    """Test sequential processing as baseline."""
    print("\n" + "="*60)
    print("BASELINE: SEQUENTIAL PROCESSING")
    print("="*60)
    
    persona = AgentPersona(
        name="TestAgent",
        role="Tester",
        background="Test agent for performance comparison",
        specialties=["testing", "benchmarking"],
        avatar_color="#ff0000"
    )
    
    agent = create_trm_enhanced_agent(persona, [FileSkill()])
    agent.enable_parallel(False)  # Disable parallel for baseline
    
    test_tasks = [
        "Analyze this pattern: 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15",
        "Explain the relationship between these numbers: 2, 4, 8, 16, 32",
        "What comes next in this sequence: A, B, C, D, E, F, G, H",
        "Solve this puzzle: If 3 cats catch 3 mice in 3 minutes, how long for 100 cats to catch 100 mice?",
        "Analyze the symbolic structure: alpha beta gamma delta epsilon"
    ]
    
    results = []
    total_start = time.time()
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n[{i}/{len(test_tasks)}] Sequential task: {task[:40]}...")
        start = time.time()
        result = await agent.process_with_trm(task)
        elapsed = time.time() - start
        
        results.append({
            "task": task,
            "time": elapsed,
            "mode": result.get("processing_mode", "unknown"),
            "quality": result.get("synthesis_quality", 0)
        })
        
        print(f"  Time: {elapsed:.2f}s | Mode: {result.get('processing_mode', 'unknown')}")
        
    total_time = time.time() - total_start
    avg_time = total_time / len(test_tasks)
    
    print(f"\nSequential Results:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average per task: {avg_time:.2f}s")
    print(f"  Total tasks: {len(test_tasks)}")
    
    return results, total_time

async def test_parallel_processing():
    """Test parallel processing with TRM enhancement."""
    print("\n" + "="*60)
    print("ENHANCED: PARALLEL PROCESSING WITH TRM")
    print("="*60)
    
    persona = AgentPersona(
        name="ParallelAgent",
        role="Parallel Tester",
        background="Test agent for parallel performance",
        specialties=["parallel processing", "optimization"],
        avatar_color="#00ff00"
    )
    
    agent = create_trm_enhanced_agent(persona, [FileSkill()])
    agent.enable_parallel(True)  # Enable parallel processing
    agent.set_recursion_depth(2)  # Set moderate recursion depth
    
    test_tasks = [
        "Analyze this pattern: 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15",
        "Explain the relationship between these numbers: 2, 4, 8, 16, 32",
        "What comes next in this sequence: A, B, C, D, E, F, G, H",
        "Solve this puzzle: If 3 cats catch 3 mice in 3 minutes, how long for 100 cats to catch 100 mice?",
        "Analyze the symbolic structure: alpha beta gamma delta epsilon"
    ]
    
    results = []
    total_start = time.time()
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n[{i}/{len(test_tasks)}] Parallel task: {task[:40]}...")
        start = time.time()
        result = await agent.process_with_trm(task)
        elapsed = time.time() - start
        
        results.append({
            "task": task,
            "time": elapsed,
            "mode": result.get("processing_mode", "unknown"),
            "quality": result.get("synthesis_quality", 0),
            "partitions": result.get("partition_count", 1),
            "speedup": result.get("trm_metrics", {}).get("avg_speedup", 1.0)
        })
        
        print(f"  Time: {elapsed:.2f}s | Partitions: {result.get('partition_count', 1)}")
        print(f"  Mode: {result.get('processing_mode', 'unknown')}")
        
    total_time = time.time() - total_start
    avg_time = total_time / len(test_tasks)
    
    # Get TRM metrics
    trm_status = agent.get_trm_status()
    metrics = trm_status.get("trm_metrics", {})
    
    print(f"\nParallel Results:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average per task: {avg_time:.2f}s")
    print(f"  Average speedup: {metrics.get('avg_speedup', 1.0):.2f}x")
    print(f"  Parallel executions: {metrics.get('parallel_executions', 0)}")
    print(f"  Error reduction: {metrics.get('error_reduction', 0.0):.2%}")
    
    return results, total_time, metrics

async def test_complex_symbolic_reasoning():
    """Test complex symbolic reasoning with recursion."""
    print("\n" + "="*60)
    print("COMPLEX SYMBOLIC REASONING WITH RECURSION")
    print("="*60)
    
    persona = AgentPersona(
        name="SymbolicMaster",
        role="Symbolic Reasoning Expert",
        background="Expert in symbolic pattern analysis",
        specialties=["symbolic reasoning", "pattern recognition"],
        avatar_color="#0000ff"
    )
    
    agent = create_trm_enhanced_agent(persona, [FileSkill()])
    agent.enable_parallel(True)
    agent.set_recursion_depth(3)  # Deeper recursion for complex patterns
    
    # Complex symbolic patterns
    complex_patterns = [
        # Long numeric pattern
        "1 2 3 5 8 13 21 34 55 89 144 233 377 610 987 1597 2584 4181 6765",
        
        # Mixed symbolic pattern
        "A1 B2 C3 D4 E5 F6 G7 H8 I9 J10 K11 L12 M13 N14 O15 P16 Q17 R18 S19 T20",
        
        # Mathematical sequence
        "2 4 16 256 65536 4294967296 18446744073709551616",
        
        # Puzzle pattern
        "3 1 4 1 5 9 2 6 5 3 5 8 9 7 9 3 2 3 8 4 6 2 6 4 3 3 8 3 2 7 9 5",
    ]
    
    for i, pattern in enumerate(complex_patterns, 1):
        print(f"\n[{i}/{len(complex_patterns)}] Complex pattern analysis:")
        print(f"  Pattern: {pattern[:50]}...")
        
        start = time.time()
        result = await agent.process_with_trm(f"Analyze this pattern: {pattern}")
        elapsed = time.time() - start
        
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Partitions: {result.get('partition_count', 1)}")
        print(f"  Recursion depth used: {result.get('processing_mode', 'unknown')}")
        
        if result.get("symbolic_processing", False):
            print(f"  Symbolic processing: YES")
            
        # Show snippet of response
        response = result.get("response", "")
        if isinstance(response, dict):
            response = str(response)[:100]
        print(f"  Response snippet: {response[:100]}...")
        
    # Get final metrics
    trm_status = agent.get_trm_status()
    print(f"\nFinal TRM Status:")
    for key, value in trm_status.get("trm_metrics", {}).items():
        print(f"  {key}: {value}")

async def test_resource_utilization():
    """Test resource utilization during parallel processing."""
    print("\n" + "="*60)
    print("RESOURCE UTILIZATION MONITORING")
    print("="*60)
    
    import psutil
    import threading
    
    resource_data = {
        "cpu_percent": [],
        "memory_percent": [],
        "parallel_tasks": []
    }
    
    def monitor_resources(interval=0.5, duration=10):
        """Monitor system resources in background thread."""
        end_time = time.time() + duration
        while time.time() < end_time:
            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory().percent
            
            resource_data["cpu_percent"].append(cpu)
            resource_data["memory_percent"].append(memory)
            time.sleep(interval)
    
    # Start monitoring
    monitor_thread = threading.Thread(target=monitor_resources, args=(0.5, 10))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Run parallel tasks
    persona = AgentPersona(
        name="ResourceMonitor",
        role="Resource Analyst",
        background="Monitors system resource utilization",
        specialties=["performance monitoring", "resource optimization"],
        avatar_color="#ff00ff"
    )
    
    agent = create_trm_enhanced_agent(persona, [FileSkill()])
    agent.enable_parallel(True)
    
    # Create workload
    workload = []
    for i in range(20):
        workload.append(f"Task {i}: Analyze pattern {i} {i*2} {i*3} {i*4} {i*5}")
    
    print(f"Running {len(workload)} parallel tasks...")
    start = time.time()
    
    # Execute in batches
    batch_size = 4
    for batch_start in range(0, len(workload), batch_size):
        batch = workload[batch_start:batch_start + batch_size]
        print(f"  Batch {batch_start//batch_size + 1}: {len(batch)} tasks")
        
        tasks = [agent.process_with_trm(task) for task in batch]
        results = await asyncio.gather(*tasks)
        
        # Track parallel tasks
        for result in results:
            partitions = result.get("partition_count", 1)
            resource_data["parallel_tasks"].append(partitions)
    
    elapsed = time.time() - start
    
    # Wait for monitor to finish
    monitor_thread.join(timeout=1)
    
    # Analyze resource data
    if resource_data["cpu_percent"]:
        avg_cpu = sum(resource_data["cpu_percent"]) / len(resource_data["cpu_percent"])
        max_cpu = max(resource_data["cpu_percent"])
    else:
        avg_cpu = max_cpu = 0
        
    if resource_data["memory_percent"]:
        avg_memory = sum(resource_data["memory_percent"]) / len(resource_data["memory_percent"])
        max_memory = max(resource_data["memory_percent"])
    else:
        avg_memory = max_memory = 0
    
    avg_parallel = sum(resource_data["parallel_tasks"]) / len(resource_data["parallel_tasks"]) if resource_data["parallel_tasks"] else 0
    
    print(f"\nResource Utilization Results:")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Tasks completed: {len(workload)}")
    print(f"  Average CPU usage: {avg_cpu:.1f}%")
    print(f"  Peak CPU usage: {max_cpu:.1f}%")
    print(f"  Average memory usage: {avg_memory:.1f}%")
    print(f"  Peak memory usage: {max_memory:.1f}%")
    print(f"  Average parallel tasks: {avg_parallel:.1f}")
    
    return resource_data

async def main():
    """Run all tests."""
    print("TRM PARALLEL SUB-AGENT SPAWNING SYSTEM TEST")
    print("="*60)
    
    try:
        # Test 1: Baseline sequential
        seq_results, seq_time = await test_sequential_processing()
        
        # Test 2: Enhanced parallel
        par_results, par_time, metrics = await test_parallel_processing()
        
        # Test 3: Complex symbolic reasoning
        await test_complex_symbolic_reasoning()
        
        # Test 4: Resource utilization
        resource_data = await test_resource_utilization()
        
        # Performance comparison
        print("\n" + "="*60)
        print("PERFORMANCE COMPARISON SUMMARY")
        print("="*60)
        
        if seq_time > 0 and par_time > 0:
            speedup = seq_time / par_time
            efficiency = (speedup / metrics.get('avg_speedup', 1.0)) * 100
            
            print(f"Sequential total time: {seq_time:.2f}s")
            print(f"Parallel total time: {par_time:.2f}s")
            print(f"Overall speedup: {speedup:.2f}x")
            print(f"System efficiency: {efficiency:.1f}%")
            
            # Calculate quality comparison
            seq_quality = sum(r['quality'] for r in seq_results) / len(seq_results) if seq_results else 0
            par_quality = sum(r['quality'] for r in par_results) / len(par_results) if par_results else 0
            
            print(f"Sequential quality score: {seq_quality:.3f}")
            print(f"Parallel quality score: {par_quality:.3f}")
            print(f"Quality improvement: {(par_quality - seq_quality)/seq_quality*100 if seq_quality > 0 else 0:+.1f}%")
        
        print("\n" + "="*60)
        print("SYSTEM VALIDATION")
        print("="*60)
        
        # Validate system components
        from swarm_v2.core.trm_orchestrator import get_trm_orchestrator
        orchestrator = get_trm_orchestrator()
        status = orchestrator.get_status()
        
        print(f"TRM Orchestrator Status:")
        print(f"  Active tasks: {status.get('active_tasks', 0)}")
        print(f"  Subagents: {status.get('subagents', 0)}")
        print(f"  Available cores: {status.get('available_cores', 0)}")
        print(f"  Max parallel tasks: {status.get('max_parallel_tasks', 0)}")
        
        metrics = status.get('metrics', {})
        print(f"  Total tasks processed: {metrics.get('total_tasks', 0)}")
        print(f"  Average response time: {metrics.get('avg_response_time', 0):.2f}s")
        print(f"  Error rate: {metrics.get('error_rate', 0):.2%}")
        
        print("\n" + "="*60)
        print("TEST COMPLETE - SYSTEM OPERATIONAL")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)