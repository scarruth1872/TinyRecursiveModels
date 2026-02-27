#!/usr/bin/env python3
"""
Quick stress test for working endpoints.
"""

import requests
import time
import threading
import concurrent.futures
import random

BASE_URL = "http://localhost:8001"
NUM_CONCURRENT = 5
NUM_REQUESTS = 20

def test_endpoint(endpoint, method="GET", data=None, timeout=30):
    """Test endpoint with timeout."""
    start = time.time()
    try:
        if method == "GET":
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=timeout)
        elif method == "POST":
            resp = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=timeout)
        else:
            return {"error": f"Unknown method {method}", "time": time.time()-start, "success": False}
        
        elapsed = time.time() - start
        return {
            "status": resp.status_code,
            "time": elapsed,
            "success": resp.status_code == 200,
            "response": resp.json() if resp.status_code == 200 and resp.text else resp.text[:200]
        }
    except Exception as e:
        return {
            "error": str(e),
            "time": time.time() - start,
            "success": False
        }

def test_health():
    """Test /health endpoint."""
    print("\n=== Testing /health ===")
    result = test_endpoint("/health")
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        print(f"  Status: {result.get('response', {}).get('status', 'N/A')}")
        print(f"  Phase: {result.get('response', {}).get('phase', 'N/A')}")
        print(f"  Agents: {result.get('response', {}).get('agents', 'N/A')}")
        return True
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False

def test_memory_stats():
    """Test /memory/stats endpoint."""
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

def test_agents():
    """Test /agents endpoint."""
    print("\n=== Testing /agents ===")
    result = test_endpoint("/agents")
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        agents = result.get("response", {})
        if isinstance(agents, dict) and 'agents' in agents:
            print(f"  Found {len(agents['agents'])} agents")
        return True
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False

def test_artifacts_stats():
    """Test /artifacts/stats endpoint."""
    print("\n=== Testing /artifacts/stats ===")
    result = test_endpoint("/artifacts/stats")
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        stats = result.get("response", {})
        print(f"  Total: {stats.get('total', 'N/A')}")
        print(f"  Approved: {stats.get('approved', 'N/A')}")
        return True
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False

def concurrent_test(test_func, name):
    """Run concurrent tests."""
    print(f"\n=== Concurrent Test: {name} ===")
    print(f"  Threads: {NUM_CONCURRENT}, Total requests: {NUM_REQUESTS}")
    
    results = []
    start_time = time.time()
    
    def worker():
        try:
            result = test_func()
            results.append(result)
            return result
        except Exception as e:
            return {"error": str(e), "success": False}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CONCURRENT) as executor:
        futures = [executor.submit(worker) for _ in range(NUM_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            pass
    
    elapsed = time.time() - start_time
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    
    print(f"  Results: {success_count}/{NUM_REQUESTS} successful")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Requests/sec: {NUM_REQUESTS/elapsed:.2f}")
    print(f"  Avg latency: {elapsed/NUM_REQUESTS*1000:.1f}ms")
    
    return success_count == NUM_REQUESTS

def stress_test():
    """Main stress test."""
    print("="*60)
    print("QUICK STRESS TEST")
    print("="*60)
    
    # Test individual endpoints
    test_health()
    test_memory_stats()
    test_agents()
    test_artifacts_stats()
    
    print("\n" + "="*60)
    print("RUNNING CONCURRENT TESTS")
    print("="*60)
    
    # Concurrent tests
    success = True
    
    # Test 1: Concurrent health checks
    def health_worker():
        return test_endpoint("/health").get("success", False)
    
    success &= concurrent_test(health_worker, "Concurrent /health requests")
    
    # Test 2: Concurrent memory stats
    def stats_worker():
        return test_endpoint("/memory/stats").get("success", False)
    
    success &= concurrent_test(stats_worker, "Concurrent /memory/stats requests")
    
    # Test 3: Concurrent agents list
    def agents_worker():
        return test_endpoint("/agents").get("success", False)
    
    success &= concurrent_test(agents_worker, "Concurrent /agents requests")
    
    # Test 4: Mixed workload
    print("\n=== Mixed Workload Test ===")
    print(f"  Threads: {NUM_CONCURRENT}, Total requests: {NUM_REQUESTS}")
    
    def mixed_worker():
        endpoints = ["/health", "/memory/stats", "/agents"]
        endpoint = random.choice(endpoints)
        return test_endpoint(endpoint).get("success", False)
    
    results = []
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CONCURRENT) as executor:
        futures = [executor.submit(mixed_worker) for _ in range(NUM_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            pass
    
    elapsed = time.time() - start_time
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    
    print(f"  Results: {success_count}/{NUM_REQUESTS} successful")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Requests/sec: {NUM_REQUESTS/elapsed:.2f}")
    print(f"  Avg latency: {elapsed/NUM_REQUESTS*1000:.1f}ms")
    
    success &= (success_count == NUM_REQUESTS)
    
    # Final verification
    print("\n" + "="*60)
    print("POST-STRESS VERIFICATION")
    print("="*60)
    
    final_health = test_endpoint("/health")
    if final_health.get("success"):
        print(f"✅ Final health check: {final_health['time']:.3f}s")
        print(f"   Status: {final_health.get('response', {}).get('status', 'N/A')}")
    else:
        print(f"❌ Final health check failed")
        success = False
    
    print("\n" + "="*60)
    if success:
        print("✅ STRESS TEST PASSED")
    else:
        print("⚠️ STRESS TEST PARTIALLY FAILED (some endpoints may have issues)")
    print("="*60)
    
    return success

if __name__ == "__main__":
    try:
        success = stress_test()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)