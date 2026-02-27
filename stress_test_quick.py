#!/usr/bin/env python3
"""
QUICK STRESS TEST FOR TRM SWARM V2
Reduced duration for faster feedback.
"""

import requests
import time
import random
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

BASE_URL = "http://localhost:8001"
TEST_DURATION_SECONDS = 15  # Shorter test
CONCURRENT_WORKERS = 10     # Fewer workers
REQUEST_TIMEOUT = 10.0

def test_endpoint(endpoint, method="GET"):
    """Test a single endpoint."""
    start = time.time()
    try:
        if method == "GET":
            r = requests.get(f"{BASE_URL}{endpoint}", timeout=REQUEST_TIMEOUT)
        elif method == "POST":
            r = requests.post(f"{BASE_URL}{endpoint}", timeout=REQUEST_TIMEOUT)
        else:
            return False, time.time() - start, f"Invalid method {method}"
        
        elapsed = time.time() - start
        success = r.status_code in [200, 201, 202]
        error = f"HTTP {r.status_code}" if not success else None
        return success, elapsed, error
    except Exception as e:
        elapsed = time.time() - start
        return False, elapsed, str(e)

def run_concurrent_test(endpoints):
    """Run concurrent stress test on endpoints."""
    results = {
        "total": 0,
        "success": 0,
        "fail": 0,
        "times": [],
        "errors": []
    }
    
    stop_time = time.time() + TEST_DURATION_SECONDS
    
    def worker(worker_id):
        count = 0
        while time.time() < stop_time:
            method, endpoint = random.choice(endpoints)
            success, elapsed, error = test_endpoint(endpoint, method)
            if success:
                results["success"] += 1
                results["times"].append(elapsed)
            else:
                results["fail"] += 1
                if error:
                    results["errors"].append(error)
            results["total"] += 1
            count += 1
            time.sleep(random.uniform(0.05, 0.2))
        return count
    
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(worker, i) for i in range(CONCURRENT_WORKERS)]
        for future in as_completed(futures):
            try:
                count = future.result()
                print(f"  Worker completed {count} requests")
            except Exception as e:
                print(f"  Worker error: {e}")
    
    return results

def main():
    print("🚀 QUICK STRESS TEST FOR TRM SWARM V2")
    print("="*50)
    
    # Verify API is accessible
    print("\n🔍 Verifying API...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        if r.status_code == 200:
            print(f"✅ API accessible: {r.json().get('status')}")
        else:
            print(f"❌ API returned {r.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect: {e}")
        return
    
    # Test endpoints
    endpoints = [
        ("GET", "/health"),
        ("GET", "/artifacts"),
        ("GET", "/artifacts/stats"),
        ("GET", "/mesh/stats"),
        ("GET", "/memory/stats"),
        ("GET", "/learning/skills"),
    ]
    
    print(f"\n🧪 Testing {len(endpoints)} endpoints...")
    for method, endpoint in endpoints:
        success, elapsed, error = test_endpoint(endpoint, method)
        status = "✅" if success else "❌"
        print(f"  {status} {method} {endpoint}: {elapsed:.3f}s")
    
    # Run concurrent test
    print(f"\n🔥 Running concurrent stress test ({CONCURRENT_WORKERS} workers, {TEST_DURATION_SECONDS}s)...")
    results = run_concurrent_test(endpoints)
    
    # Print results
    print(f"\n📊 RESULTS:")
    print(f"  Total requests: {results['total']}")
    print(f"  Successful: {results['success']}")
    print(f"  Failed: {results['fail']}")
    
    if results['success'] > 0:
        success_rate = (results['success'] / results['total']) * 100
        print(f"  Success rate: {success_rate:.1f}%")
        
        if results['times']:
            avg_time = statistics.mean(results['times'])
            min_time = min(results['times'])
            max_time = max(results['times'])
            req_per_sec = results['success'] / TEST_DURATION_SECONDS
            print(f"  Avg response: {avg_time:.3f}s")
            print(f"  Min response: {min_time:.3f}s")
            print(f"  Max response: {max_time:.3f}s")
            print(f"  Requests/sec: {req_per_sec:.1f}")
    
    if results['errors']:
        unique_errors = set(results['errors'])
        print(f"\n❌ Errors ({len(unique_errors)} unique):")
        for err in list(unique_errors)[:3]:
            print(f"  - {err}")
        if len(unique_errors) > 3:
            print(f"  ... and {len(unique_errors) - 3} more")
    
    # Final health check
    print(f"\n🏥 Final health check...")
    try:
        start = time.time()
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        elapsed = time.time() - start
        print(f"  Health check: {r.status_code} in {elapsed:.3f}s")
        if r.status_code == 200:
            data = r.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Agents: {data.get('agents')}")
            print(f"  Artifacts: {data.get('artifacts', {}).get('total', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
    
    # Assessment
    success_rate = (results['success'] / max(1, results['total'])) * 100
    if success_rate >= 95.0:
        print(f"\n🎉 QUICK TEST PASSED: {success_rate:.1f}% success rate")
        return True
    else:
        print(f"\n⚠️  QUICK TEST WARNING: {success_rate:.1f}% success rate (target: 95%)")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)