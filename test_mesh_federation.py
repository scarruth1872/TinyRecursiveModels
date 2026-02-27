#!/usr/bin/env python3
"""
Test mesh federation endpoints under load.
"""

import requests
import time
import concurrent.futures
import statistics
import json

BASE_URL = "http://localhost:8001"

def test_endpoint(endpoint, method="GET", data=None, timeout=10):
    """Test an endpoint and return timing."""
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

def test_federation_stats():
    """Test /federation/stats endpoint."""
    print("\n=== Testing /federation/stats ===")
    result = test_endpoint("/federation/stats")
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        stats = result.get("response", {})
        print(f"  Node ID: {stats.get('node_id', 'N/A')}")
        print(f"  Status: {stats.get('status', 'N/A')}")
        print(f"  Total nodes: {stats.get('total_nodes', 'N/A')}")
        print(f"  Online nodes: {stats.get('online_nodes', 'N/A')}")
        return True, result['time']
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False, result.get('time', 0)

def test_learning_skills():
    """Test /learning/skills endpoint."""
    print("\n=== Testing /learning/skills ===")
    result = test_endpoint("/learning/skills")
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        data = result.get("response", {})
        skills = data.get("skills", [])
        print(f"  Skills count: {len(skills)}")
        if skills:
            print(f"  Sample skills: {', '.join([s[:20] + '...' for s in skills[:3]])}")
        return True, result['time']
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False, result.get('time', 0)

def test_mesh_topology():
    """Test /mesh/topology endpoint."""
    print("\n=== Testing /mesh/topology ===")
    result = test_endpoint("/mesh/topology")
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        topology = result.get("response", {})
        nodes = topology.get("nodes", [])
        print(f"  Nodes: {len(nodes)}")
        if nodes:
            print(f"  Node roles: {', '.join([n.get('role', 'unknown') for n in nodes[:3]])}")
        return True, result['time']
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False, result.get('time', 0)

def test_synthesize_tools():
    """Test /synthesize/tools endpoint."""
    print("\n=== Testing /synthesize/tools ===")
    result = test_endpoint("/synthesize/tools")
    if result.get("success"):
        print(f"✅ Success: {result['time']:.3f}s")
        data = result.get("response", {})
        tools = data.get("tools", [])
        print(f"  Tools count: {len(tools)}")
        stats = data.get("stats", {})
        print(f"  Stats: {stats}")
        return True, result['time']
    else:
        print(f"❌ Failed: {result.get('error', result.get('status', 'Unknown'))}")
        return False, result.get('time', 0)

def concurrent_test(test_func, name, num_threads=5, num_requests=20):
    """Run concurrent tests on a specific endpoint."""
    print(f"\n=== Concurrent Test: {name} ===")
    print(f"  Threads: {num_threads}, Total requests: {num_requests}")
    
    results = []
    times = []
    start_time = time.time()
    
    def worker():
        success, elapsed = test_func()
        results.append(success)
        if success:
            times.append(elapsed)
        return success
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker) for _ in range(num_requests)]
        for future in concurrent.futures.as_completed(futures):
            pass
    
    elapsed = time.time() - start_time
    success_count = sum(1 for r in results if r)
    
    print(f"  Results: {success_count}/{num_requests} successful")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Requests/sec: {num_requests/elapsed:.2f}")
    
    if times:
        print(f"  Avg latency: {statistics.mean(times):.3f}s")
        print(f"  Min latency: {min(times):.3f}s")
        print(f"  Max latency: {max(times):.3f}s")
        print(f"  P95 latency: {statistics.quantiles(times, n=20)[18] if len(times) > 1 else times[0]:.3f}s")
    
    return success_count == num_requests

def stress_test_federation():
    """Run comprehensive stress test on federation and learning endpoints."""
    print("="*60)
    print("MESH FEDERATION & LEARNING ENGINE STRESS TEST")
    print("="*60)
    
    # Test individual endpoints
    test_federation_stats()
    test_learning_skills()
    test_mesh_topology()
    test_synthesize_tools()
    
    print("\n" + "="*60)
    print("CONCURRENT STRESS TESTS")
    print("="*60)
    
    success = True
    
    # Test 1: Concurrent federation stats
    success &= concurrent_test(
        lambda: test_endpoint("/federation/stats"),
        "Concurrent /federation/stats requests",
        num_threads=3,
        num_requests=15
    )
    
    # Test 2: Concurrent learning skills
    success &= concurrent_test(
        lambda: test_endpoint("/learning/skills"),
        "Concurrent /learning/skills requests",
        num_threads=3,
        num_requests=15
    )
    
    # Test 3: Concurrent mesh topology
    success &= concurrent_test(
        lambda: test_endpoint("/mesh/topology"),
        "Concurrent /mesh/topology requests",
        num_threads=3,
        num_requests=15
    )
    
    # Test 4: Mixed workload
    print("\n=== Mixed Workload Test ===")
    print("  Threads: 5, Total requests: 20")
    
    endpoints = ["/federation/stats", "/learning/skills", "/mesh/topology"]
    
    def mixed_worker():
        import random
        endpoint = random.choice(endpoints)
        result = test_endpoint(endpoint)
        return result.get("success", False), result.get("time", 0)
    
    results = []
    times = []
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(lambda: mixed_worker()[0]) for _ in range(20)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    elapsed = time.time() - start_time
    success_count = sum(1 for r in results if r)
    
    print(f"  Results: {success_count}/20 successful")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Requests/sec: {20/elapsed:.2f}")
    
    success &= (success_count == 20)
    
    # Final verification
    print("\n" + "="*60)
    print("POST-STRESS VERIFICATION")
    print("="*60)
    
    final_tests = [
        ("/federation/stats", test_federation_stats),
        ("/learning/skills", test_learning_skills),
        ("/mesh/topology", test_mesh_topology),
    ]
    
    for endpoint_name, test_func in final_tests:
        print(f"\nFinal check for {endpoint_name}:")
        final_success, final_time = test_func()
        if not final_success:
            success = False
    
    print("\n" + "="*60)
    if success:
        print("✅ FEDERATION & LEARNING STRESS TEST PASSED")
    else:
        print("⚠️ FEDERATION & LEARNING STRESS TEST PARTIALLY FAILED")
    print("="*60)
    
    return success

def main():
    """Main test function."""
    print("🔍 Checking server availability...")
    
    # Check if server is running
    health_result = test_endpoint("/health")
    if not health_result.get("success"):
        print("❌ Server not available. Please start the Swarm V2 API server first.")
        print(f"   Error: {health_result.get('error', 'Unknown')}")
        return False
    
    print(f"✅ Server is running (Phase: {health_result.get('response', {}).get('phase', 'N/A')})")
    
    # Run the stress test
    return stress_test_federation()

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)