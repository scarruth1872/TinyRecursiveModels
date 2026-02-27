#!/usr/bin/env python3
"""
Stress test for Global Memory concurrent access.
Tests the /memory/stats, /memory/query, and /memory/contribute endpoints
with concurrent requests to verify thread safety and performance.
"""

import requests
import json
import time
import threading
import concurrent.futures
import random
import sys
from typing import List, Dict, Any

BASE_URL = "http://localhost:8001"
NUM_CONCURRENT = 10  # Number of concurrent requests
NUM_REQUESTS = 50   # Total requests per test
TEST_CONTENT = [
    "Quantum computing uses qubits for superposition",
    "Machine learning models require large datasets",
    "Swarm intelligence emerges from simple agents",
    "Vector databases enable semantic search",
    "FastAPI provides async web framework",
    "Distributed systems need consensus algorithms",
    "Neural networks have multiple hidden layers",
    "Reinforcement learning uses reward signals",
    "Natural language processing understands text",
    "Computer vision identifies objects in images"
]

def test_endpoint(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Test a single endpoint and return timing info."""
    start = time.time()
    try:
        if method == "GET":
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        elif method == "POST":
            resp = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        else:
            return {"error": f"Unknown method {method}"}
        
        elapsed = time.time() - start
        return {
            "status": resp.status_code,
            "time": elapsed,
            "success": resp.status_code == 200,
            "response": resp.json() if resp.status_code == 200 else resp.text[:200]
        }
    except Exception as e:
        return {
            "error": str(e),
            "time": time.time() - start,
            "success": False
        }

def test_memory_stats_single():
    """Test the /memory/stats endpoint."""
    print("\n=== Testing /memory/stats ===")
    result = test_endpoint("/memory/stats")
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        stats = result.get("response", {})
        print(f"  Total memories: {stats.get('total_memories', 'N/A')}")
        print(f"  Backend: {stats.get('backend', 'N/A')}")
        return True
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False

def test_memory_query_single():
    """Test the /memory/query endpoint."""
    print("\n=== Testing /memory/query ===")
    data = {
        "query": "quantum computing",
        "top_k": 3
    }
    result = test_endpoint("/memory/query", "POST", data)
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        response = result.get("response", {})
        results = response.get("results", [])
        print(f"  Found {len(results)} matches")
        if results:
            for i, (score, entry) in enumerate(results):
                print(f"    {i+1}. Score: {score:.3f}, Content: {entry.get('content', '')[:50]}...")
        return True
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False

def test_memory_contribute_single():
    """Test the /memory/contribute endpoint."""
    print("\n=== Testing /memory/contribute ===")
    content = random.choice(TEST_CONTENT)
    data = {
        "content": f"Test memory: {content} - {time.time()}",
        "author": "StressTester",
        "author_role": "Tester",
        "memory_type": "test_knowledge",
        "tags": ["stress_test", "concurrent"]
    }
    result = test_endpoint("/memory/contribute", "POST", data)
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        print(f"  Contributed: {data['content'][:50]}...")
        return True
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False

def concurrent_test(endpoint_func, num_threads=NUM_CONCURRENT, num_requests=NUM_REQUESTS):
    """Run concurrent tests on an endpoint."""
    print(f"\n=== Concurrent Test: {endpoint_func.__name__} ===")
    print(f"  Threads: {num_threads}, Total requests: {num_requests}")
    
    results = []
    errors = 0
    start_time = time.time()
    
    def worker():
        try:
            result = endpoint_func()
            results.append(result)
            return result
        except Exception as e:
            return {"error": str(e), "success": False}
    
    # Use ThreadPoolExecutor for concurrent execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker) for _ in range(num_requests)]
        for future in concurrent.futures.as_completed(futures):
            pass  # Results are collected in the worker
    
    elapsed = time.time() - start_time
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    
    print(f"\n  Results: {success_count}/{num_requests} successful")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Requests/sec: {num_requests/elapsed:.2f}")
    print(f"  Avg latency: {elapsed/num_requests*1000:.1f}ms")
    
    return success_count == num_requests

def stress_test_memory_concurrent():
    """Main stress test for global memory endpoints."""
    print("="*60)
    print("GLOBAL MEMORY STRESS TEST")
    print("="*60)
    
    # First, verify basic endpoints work
    if not test_memory_stats_single():
        print("Skipping further tests - basic endpoint failed")
        return False
    
    test_memory_query_single()
    test_memory_contribute_single()
    
    # Run concurrent tests
    print("\n" + "="*60)
    print("RUNNING CONCURRENT STRESS TESTS")
    print("="*60)
    
    # Test 1: Concurrent stats requests (read-only)
    print("\n[Test 1] Concurrent /memory/stats requests")
    def stats_worker():
        return test_endpoint("/memory/stats").get("success", False)
    
    success = concurrent_test(lambda: test_endpoint("/memory/stats").get("success", False))
    
    # Test 2: Concurrent query requests (read-heavy)
    print("\n[Test 2] Concurrent /memory/query requests")
    def query_worker():
        data = {
            "query": random.choice(["quantum", "machine learning", "swarm", "database"]),
            "top_k": random.randint(1, 5)
        }
        return test_endpoint("/memory/query", "POST", data).get("success", False)
    
    success &= concurrent_test(lambda: query_worker())
    
    # Test 3: Concurrent contribute requests (write-heavy)
    print("\n[Test 3] Concurrent /memory/contribute requests")
    def contribute_worker():
        data = {
            "content": f"Concurrent test memory {threading.get_ident()}-{time.time()}",
            "author": f"Worker-{threading.get_ident()}",
            "author_role": "StressTester",
            "memory_type": "concurrent_test",
            "tags": ["stress", f"thread-{threading.get_ident()}"]
        }
        return test_endpoint("/memory/contribute", "POST", data).get("success", False)
    
    success &= concurrent_test(lambda: contribute_worker())
    
    # Test 4: Mixed workload (reads and writes)
    print("\n[Test 4] Mixed read/write workload")
    def mixed_worker():
        # 70% reads, 30% writes
        if random.random() < 0.7:
            if random.random() < 0.5:
                return test_endpoint("/memory/stats").get("success", False)
            else:
                data = {"query": "test", "top_k": 2}
                return test_endpoint("/memory/query", "POST", data).get("success", False)
        else:
            data = {
                "content": f"Mixed workload test {time.time()}",
                "author": "MixedWorker",
                "author_role": "Tester",
                "memory_type": "mixed",
                "tags": ["mixed", "stress"]
            }
            return test_endpoint("/memory/contribute", "POST", data).get("success", False)
    
    success &= concurrent_test(lambda: mixed_worker())
    
    # Final check: verify system still works
    print("\n" + "="*60)
    print("POST-STRESS VERIFICATION")
    print("="*60)
    
    final_stats = test_endpoint("/memory/stats")
    if final_stats.get("success"):
        stats = final_stats.get("response", {})
        print(f"✅ Final memory stats:")
        print(f"   Total memories: {stats.get('total_memories', 'N/A')}")
        print(f"   Backend: {stats.get('backend', 'N/A')}")
        print(f"   Total accesses: {stats.get('total_accesses', 'N/A')}")
    else:
        print(f"❌ Failed to get final stats: {final_stats.get('error', 'Unknown')}")
        success = False
    
    # Check system health
    health = test_endpoint("/health")
    if health.get("success"):
        print(f"✅ System health: {health.get('response', {}).get('status', 'N/A')}")
    else:
        print(f"❌ System health check failed")
        success = False
    
    print("\n" + "="*60)
    if success:
        print("✅ STRESS TEST PASSED")
    else:
        print("❌ STRESS TEST FAILED")
    print("="*60)
    
    return success

if __name__ == "__main__":
    try:
        # Reduce parameters for quicker test
        NUM_CONCURRENT = 5
        NUM_REQUESTS = 20
        success = stress_test_memory_concurrent()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)