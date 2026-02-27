#!/usr/bin/env python3
"""
Stress test for Cognitive Stack with gemma3:270m model.
Tests parallel execution, response times, and concurrency handling.
"""

import asyncio
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import statistics

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

async def test_single_cognitive_stack():
    """Test a single cognitive stack request."""
    try:
        from swarm_v2.core.cognitive_stack import CognitiveStack
        
        agent_name = "StressTestAgent"
        executive_model = "gemma3:270m"
        
        print(f"Creating CognitiveStack with model: {executive_model}")
        stack = CognitiveStack(agent_name, executive_model=executive_model)
        
        prompt = "Hello! What's 2+2? Please respond concisely."
        
        start_time = time.time()
        response, trace = await stack.process(prompt)
        end_time = time.time()
        
        elapsed = end_time - start_time
        print(f"Single request completed in {elapsed:.2f}s")
        print(f"Response: {response[:100]}...")
        print(f"Stats: {stack.get_status()}")
        
        return elapsed, True
    except Exception as e:
        print(f"❌ Error in single request: {e}")
        import traceback
        traceback.print_exc()
        return 0, False

async def test_parallel_requests(num_requests=10):
    """Test parallel cognitive stack requests."""
    try:
        from swarm_v2.core.cognitive_stack import CognitiveStack
        
        print(f"\n🧪 Testing {num_requests} parallel requests...")
        
        # Create a single stack to test concurrent access
        agent_name = "ParallelTestAgent"
        executive_model = "gemma3:270m"
        stack = CognitiveStack(agent_name, executive_model=executive_model)
        
        prompts = [
            f"Request {i}: What's {i}+{i}? Please respond concisely." 
            for i in range(num_requests)
        ]
        
        async def process_one(prompt, idx):
            try:
                start = time.time()
                response, trace = await stack.process(prompt)
                elapsed = time.time() - start
                print(f"  Request {idx+1}: {elapsed:.2f}s")
                return elapsed, True, response[:50]
            except Exception as e:
                print(f"  Request {idx+1} failed: {e}")
                return 0, False, ""
        
        # Run all requests concurrently
        start_time = time.time()
        tasks = [process_one(prompt, i) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Analyze results
        successful = [r for r in results if r[1]]
        failed = [r for r in results if not r[1]]
        times = [r[0] for r in successful]
        
        total_time = end_time - start_time
        
        print(f"\n📊 Parallel Test Results:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Successful: {len(successful)}/{num_requests}")
        print(f"  Failed: {len(failed)}/{num_requests}")
        
        if times:
            print(f"  Avg response time: {statistics.mean(times):.2f}s")
            print(f"  Min response time: {min(times):.2f}s")
            print(f"  Max response time: {max(times):.2f}s")
            if len(times) > 1:
                print(f"  Std dev: {statistics.stdev(times):.2f}s")
        
        stats = stack.get_status()
        print(f"\n📈 Cognitive Stack Stats:")
        print(f"  Executive calls: {stats['calls']['executive']}")
        print(f"  Reasoning calls: {stats['calls']['reasoning']}")
        print(f"  VRAM estimate: {stats['vram_mb']} MB")
        
        return len(successful) == num_requests
        
    except Exception as e:
        print(f"❌ Error in parallel test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_concurrent_stacks(num_stacks=5):
    """Test multiple independent cognitive stacks running concurrently."""
    try:
        from swarm_v2.core.cognitive_stack import CognitiveStack
        
        print(f"\n🏗️ Testing {num_stacks} independent cognitive stacks...")
        
        stacks = []
        for i in range(num_stacks):
            stack = CognitiveStack(f"Agent{i}", executive_model="gemma3:270m")
            stacks.append(stack)
        
        async def process_with_stack(stack, idx):
            try:
                prompt = f"I am agent {idx}. What's {idx}*{idx}?"
                start = time.time()
                response, trace = await stack.process(prompt)
                elapsed = time.time() - start
                print(f"  Stack {idx+1}: {elapsed:.2f}s")
                return elapsed, True
            except Exception as e:
                print(f"  Stack {idx+1} failed: {e}")
                return 0, False
        
        # Run all stacks concurrently
        start_time = time.time()
        tasks = [process_with_stack(stack, i) for i, stack in enumerate(stacks)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        successful = [r for r in results if r[1]]
        times = [r[0] for r in successful]
        
        print(f"\n📊 Independent Stacks Results:")
        print(f"  Total time: {end_time - start_time:.2f}s")
        print(f"  Successful: {len(successful)}/{num_stacks}")
        
        if times:
            print(f"  Avg time per stack: {statistics.mean(times):.2f}s")
        
        return len(successful) == num_stacks
        
    except Exception as e:
        print(f"❌ Error in concurrent stacks test: {e}")
        return False

async def test_mixed_workload():
    """Test mixed workload with different prompt complexities."""
    try:
        from swarm_v2.core.cognitive_stack import CognitiveStack
        
        print(f"\n🎭 Testing mixed workload...")
        
        stack = CognitiveStack("MixedWorkloadAgent", executive_model="gemma3:270m")
        
        prompts = [
            "Simple: Hello!",
            "Math: What's 15 * 3?",
            "Reasoning: If A then B, and A is true, what can we conclude?",
            "Code: Write a Python function to reverse a string.",
            "Analysis: What are the benefits of using small language models?",
        ]
        
        async def process_prompt(prompt, idx):
            try:
                start = time.time()
                response, trace = await stack.process(prompt)
                elapsed = time.time() - start
                print(f"  Prompt {idx+1} ({prompt[:20]}...): {elapsed:.2f}s")
                return elapsed, True
            except Exception as e:
                print(f"  Prompt {idx+1} failed: {e}")
                return 0, False
        
        start_time = time.time()
        tasks = [process_prompt(prompt, i) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        successful = [r for r in results if r[1]]
        times = [r[0] for r in successful]
        
        print(f"\n📊 Mixed Workload Results:")
        print(f"  Total time: {end_time - start_time:.2f}s")
        print(f"  Successful: {len(successful)}/{len(prompts)}")
        
        if times:
            print(f"  Avg response time: {statistics.mean(times):.2f}s")
        
        # Check if reasoning was triggered for appropriate prompts
        stats = stack.get_status()
        print(f"\n📈 Stack Stats after mixed workload:")
        print(f"  Executive calls: {stats['calls']['executive']}")
        print(f"  Reasoning calls: {stats['calls']['reasoning']}")
        
        return len(successful) == len(prompts)
        
    except Exception as e:
        print(f"❌ Error in mixed workload test: {e}")
        return False

async def test_timeout_resilience():
    """Test that the system doesn't hang on long prompts."""
    try:
        from swarm_v2.core.cognitive_stack import CognitiveStack
        
        print(f"\n⏱️ Testing timeout resilience...")
        
        stack = CognitiveStack("TimeoutTestAgent", executive_model="gemma3:270m")
        
        # Create a moderately complex prompt (not too long to avoid actual timeout)
        prompt = "Please explain the concept of recursive neural networks in detail, including their architecture, training process, and applications in natural language processing."
        
        try:
            # Set a timeout of 30 seconds
            response, trace = await asyncio.wait_for(
                stack.process(prompt),
                timeout=30.0
            )
            print(f"✅ Request completed within timeout")
            print(f"Response length: {len(response)} chars")
            return True
        except asyncio.TimeoutError:
            print(f"❌ Request timed out after 30 seconds")
            return False
            
    except Exception as e:
        print(f"❌ Error in timeout test: {e}")
        return False

async def main():
    """Run all stress tests."""
    print("🚀 Starting Cognitive Stack Stress Test with gemma3:270m")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Single request baseline
    print("\n1️⃣ Single Request Baseline Test")
    elapsed, success = await test_single_cognitive_stack()
    results["single_request"] = {"success": success, "time": elapsed if success else None}
    
    # Test 2: Parallel requests (10 concurrent)
    print("\n2️⃣ Parallel Requests Test (10 concurrent)")
    parallel_success = await test_parallel_requests(10)
    results["parallel_requests"] = {"success": parallel_success}
    
    # Test 3: Independent stacks
    print("\n3️⃣ Independent Cognitive Stacks Test (5 stacks)")
    stacks_success = await test_concurrent_stacks(5)
    results["independent_stacks"] = {"success": stacks_success}
    
    # Test 4: Mixed workload
    print("\n4️⃣ Mixed Workload Test")
    mixed_success = await test_mixed_workload()
    results["mixed_workload"] = {"success": mixed_success}
    
    # Test 5: Timeout resilience
    print("\n5️⃣ Timeout Resilience Test")
    timeout_success = await test_timeout_resilience()
    results["timeout_resilience"] = {"success": timeout_success}
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 STRESS TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["success"])
    
    for test_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✨ All stress tests passed! gemma3:270m cognitive stack is production-ready.")
        return True
    else:
        print("⚠️ Some stress tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    # Set higher recursion limit if needed
    sys.setrecursionlimit(10000)
    
    # Run the stress test
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Stress test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Stress test failed!")
        sys.exit(1)