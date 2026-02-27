#!/usr/bin/env python3
"""
Comprehensive API stress test for TRM Swarm V2.
Tests all major endpoints with concurrent requests, measures response times,
and validates system stability under load.
"""

import asyncio
import aiohttp
import time
import statistics
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
import random

# Configuration
BASE_URL = "http://localhost:8001"
CONCURRENT_REQUESTS = 10
TEST_DURATION_SECONDS = 30  # Run stress test for 30 seconds
REQUEST_TIMEOUT = 30.0

# Test endpoints and their payloads
ENDPOINTS = [
    {
        "path": "/health",
        "method": "GET",
        "payload": None,
        "weight": 0.3  # Higher weight = more frequent requests
    },
    {
        "path": "/swarm/experts",
        "method": "GET", 
        "payload": None,
        "weight": 0.2
    },
    {
        "path": "/artifacts",
        "method": "GET",
        "payload": None,
        "weight": 0.2
    },
    {
        "path": "/swarm/chat",
        "method": "POST",
        "payload": {
            "role": "Lead Developer",
            "message": "Hello! What's 2+2? Please respond concisely.",
            "sender": "stress_test"
        },
        "weight": 0.15
    },
    {
        "path": "/swarm/chat",
        "method": "POST",
        "payload": {
            "role": "Architect", 
            "message": "Explain the concept of recursive neural networks in one sentence.",
            "sender": "stress_test"
        },
        "weight": 0.1
    },
    {
        "path": "/swarm/chat",
        "method": "POST",
        "payload": {
            "role": "QA Engineer",
            "message": "Write a simple test for a Python function that adds two numbers.",
            "sender": "stress_test"
        },
        "weight": 0.05
    }
]

class StressTestResults:
    """Collect and analyze stress test results."""
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.errors_by_endpoint = {}
        self.status_codes = {}
        
    def add_result(self, endpoint: str, success: bool, response_time: float, 
                   status_code: int = None, error: str = None):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            self.response_times.append(response_time)
        else:
            self.failed_requests += 1
            
        if status_code:
            self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
            
        if error:
            key = f"{endpoint}: {error}"
            self.errors_by_endpoint[key] = self.errors_by_endpoint.get(key, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        summary = {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "status_codes": self.status_codes,
            "errors_by_endpoint": self.errors_by_endpoint
        }
        
        if self.response_times:
            summary.update({
                "avg_response_time": statistics.mean(self.response_times),
                "min_response_time": min(self.response_times),
                "max_response_time": max(self.response_times),
                "median_response_time": statistics.median(self.response_times),
                "p95_response_time": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 1 else self.response_times[0],
                "requests_per_second": self.successful_requests / (TEST_DURATION_SECONDS if TEST_DURATION_SECONDS > 0 else 1)
            })
            
        return summary
    
    def print_summary(self):
        """Print formatted summary."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 STRESS TEST SUMMARY")
        print("="*60)
        
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Successful: {summary['successful_requests']}")
        print(f"Failed: {summary['failed_requests']}")
        print(f"Success Rate: {summary['success_rate']:.2f}%")
        
        if 'avg_response_time' in summary:
            print(f"\n⏱️ Response Times:")
            print(f"  Average: {summary['avg_response_time']:.3f}s")
            print(f"  Minimum: {summary['min_response_time']:.3f}s")
            print(f"  Maximum: {summary['max_response_time']:.3f}s")
            print(f"  Median: {summary['median_response_time']:.3f}s")
            print(f"  P95: {summary['p95_response_time']:.3f}s")
            print(f"  Requests/sec: {summary['requests_per_second']:.2f}")
        
        if summary['status_codes']:
            print(f"\n📋 Status Codes:")
            for code, count in sorted(summary['status_codes'].items()):
                print(f"  {code}: {count}")
        
        if summary['errors_by_endpoint']:
            print(f"\n❌ Errors by Endpoint:")
            for error, count in summary['errors_by_endpoint'].items():
                print(f"  {error}: {count}")

async def make_request(session: aiohttp.ClientSession, endpoint_config: Dict[str, Any], 
                       results: StressTestResults, request_id: int):
    """Make a single HTTP request and record results."""
    start_time = time.time()
    endpoint = endpoint_config["path"]
    method = endpoint_config["method"]
    payload = endpoint_config["payload"]
    
    try:
        if method == "GET":
            async with session.get(f"{BASE_URL}{endpoint}", timeout=REQUEST_TIMEOUT) as response:
                response_time = time.time() - start_time
                success = response.status == 200
                results.add_result(
                    endpoint=endpoint,
                    success=success,
                    response_time=response_time,
                    status_code=response.status,
                    error=None if success else f"HTTP {response.status}"
                )
                
        elif method == "POST":
            async with session.post(f"{BASE_URL}{endpoint}", 
                                   json=payload, 
                                   timeout=REQUEST_TIMEOUT) as response:
                response_time = time.time() - start_time
                success = response.status in [200, 201]
                results.add_result(
                    endpoint=endpoint,
                    success=success,
                    response_time=response_time,
                    status_code=response.status,
                    error=None if success else f"HTTP {response.status}"
                )
                
    except asyncio.TimeoutError:
        response_time = time.time() - start_time
        results.add_result(
            endpoint=endpoint,
            success=False,
            response_time=response_time,
            status_code=0,
            error="Timeout"
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        results.add_result(
            endpoint=endpoint,
            success=False,
            response_time=response_time,
            status_code=0,
            error=str(e)[:100]
        )

def select_endpoint() -> Dict[str, Any]:
    """Select an endpoint based on weights."""
    weights = [ep["weight"] for ep in ENDPOINTS]
    return random.choices(ENDPOINTS, weights=weights)[0]

async def stress_test_worker(session: aiohttp.ClientSession, results: StressTestResults, 
                             worker_id: int, stop_event: asyncio.Event):
    """Worker that continuously makes requests until stopped."""
    request_count = 0
    
    while not stop_event.is_set():
        endpoint_config = select_endpoint()
        await make_request(session, endpoint_config, results, worker_id * 1000 + request_count)
        request_count += 1
        
        # Small random delay between requests to simulate real usage
        await asyncio.sleep(random.uniform(0.01, 0.1))

async def run_stress_test():
    """Run the main stress test."""
    print("🚀 Starting Comprehensive API Stress Test")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Concurrent Workers: {CONCURRENT_REQUESTS}")
    print(f"Test Duration: {TEST_DURATION_SECONDS} seconds")
    print(f"Request Timeout: {REQUEST_TIMEOUT} seconds")
    print("="*60)
    
    results = StressTestResults()
    stop_event = asyncio.Event()
    
    # Create connector with higher limits
    connector = aiohttp.TCPConnector(
        limit=CONCURRENT_REQUESTS * 2,
        limit_per_host=CONCURRENT_REQUESTS * 2,
        ttl_dns_cache=300
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # First, verify the API is accessible
        print("🔍 Verifying API accessibility...")
        try:
            async with session.get(f"{BASE_URL}/health", timeout=5.0) as response:
                if response.status == 200:
                    print("✅ API is accessible")
                else:
                    print(f"❌ API returned status {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return False
        
        # Start workers
        print(f"\n👷 Starting {CONCURRENT_REQUESTS} concurrent workers...")
        workers = []
        for i in range(CONCURRENT_REQUESTS):
            worker = asyncio.create_task(
                stress_test_worker(session, results, i, stop_event)
            )
            workers.append(worker)
        
        # Let workers run for the test duration
        print(f"\n⏳ Running stress test for {TEST_DURATION_SECONDS} seconds...")
        start_time = time.time()
        
        # Print progress every 5 seconds
        while time.time() - start_time < TEST_DURATION_SECONDS:
            elapsed = time.time() - start_time
            remaining = TEST_DURATION_SECONDS - elapsed
            
            # Print intermediate stats
            if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                print(f"  [{int(elapsed)}s] Requests: {results.total_requests}, "
                      f"Success: {results.successful_requests}, "
                      f"Rate: {results.successful_requests / elapsed:.1f}/s")
            
            await asyncio.sleep(1)
        
        # Stop workers
        print("\n🛑 Stopping workers...")
        stop_event.set()
        await asyncio.gather(*workers, return_exceptions=True)
        
        # Final stats
        total_time = time.time() - start_time
        print(f"\n✅ Stress test completed in {total_time:.2f} seconds")
        
        return results

async def test_specific_endpoints():
    """Test specific endpoints with detailed metrics."""
    print("\n" + "="*60)
    print("🎯 Detailed Endpoint Testing")
    print("="*60)
    
    connector = aiohttp.TCPConnector(limit=10)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        endpoints_to_test = [
            ("/health", "GET", None),
            ("/swarm/experts", "GET", None),
            ("/artifacts", "GET", None),
            ("/swarm/telemetry", "GET", None),
            ("/swarm/soul", "GET", None),
        ]
        
        for endpoint, method, payload in endpoints_to_test:
            print(f"\n🔍 Testing {endpoint}...")
            
            times = []
            successes = 0
            failures = 0
            
            # Make 5 requests to this endpoint
            for i in range(5):
                try:
                    start_time = time.time()
                    
                    if method == "GET":
                        async with session.get(f"{BASE_URL}{endpoint}", timeout=10.0) as response:
                            elapsed = time.time() - start_time
                            times.append(elapsed)
                            
                            if response.status == 200:
                                successes += 1
                                if i == 0:  # Print first response preview
                                    try:
                                        data = await response.json()
                                        print(f"  Response preview: {str(data)[:150]}...")
                                    except:
                                        text = await response.text()
                                        print(f"  Response: {text[:150]}...")
                            else:
                                failures += 1
                                print(f"  Request {i+1}: HTTP {response.status}")
                    
                except Exception as e:
                    elapsed = time.time() - start_time
                    times.append(elapsed)
                    failures += 1
                    print(f"  Request {i+1}: Error - {str(e)[:50]}")
            
            if times:
                print(f"  Stats: {successes}/5 successful, "
                      f"Avg time: {statistics.mean(times):.3f}s, "
                      f"Min: {min(times):.3f}s, Max: {max(times):.3f}s")

async def test_chat_endpoint_concurrency():
    """Test the chat endpoint with high concurrency."""
    print("\n" + "="*60)
    print("💬 Chat Endpoint Concurrency Test")
    print("="*60)
    
    connector = aiohttp.TCPConnector(limit=20)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Test different roles concurrently
        roles = ["Lead Developer", "Architect", "QA Engineer", "DevOps Engineer", 
                 "Security Auditor", "Technical Writer"]
        
        async def chat_with_role(role):
            payload = {
                "role": role,
                "message": f"Hello from stress test! What's 2+2?",
                "sender": "stress_test"
            }
            
            try:
                start_time = time.time()
                async with session.post(f"{BASE_URL}/swarm/chat", 
                                       json=payload, 
                                       timeout=30.0) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "role": role,
                            "success": True,
                            "time": elapsed,
                            "response_length": len(str(data))
                        }
                    else:
                        return {
                            "role": role,
                            "success": False,
                            "time": elapsed,
                            "error": f"HTTP {response.status}"
                        }
            except Exception as e:
                return {
                    "role": role,
                    "success": False,
                    "time": time.time() - start_time,
                    "error": str(e)[:50]
                }
        
        # Run all roles concurrently
        print(f"Testing {len(roles)} roles concurrently...")
        tasks = [chat_with_role(role) for role in roles]
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print(f"\n📊 Chat Concurrency Results:")
        print(f"  Successful: {len(successful)}/{len(roles)}")
        print(f"  Failed: {len(failed)}/{len(roles)}")
        
        if successful:
            times = [r["time"] for r in successful]
            print(f"  Average time: {statistics.mean(times):.3f}s")
            print(f"  Min time: {min(times):.3f}s")
            print(f"  Max time: {max(times):.3f}s")
            
            # Show individual results
            for result in results:
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {result['role']}: {result['time']:.3f}s")
                if not result["success"] and "error" in result:
                    print(f"    Error: {result['error']}")

async def main():
    """Run all stress tests."""
    try:
        # Run the main stress test
        results = await run_stress_test()
        if not results:
            print("❌ Stress test failed to start")
            return False
        
        # Print main results
        results.print_summary()
        
        # Run detailed endpoint tests
        await test_specific_endpoints()
        
        # Run chat concurrency test
        await test_chat_endpoint_concurrency()
        
        # Final assessment
        print("\n" + "="*60)
        print("🎯 FINAL ASSESSMENT")
        print("="*60)
        
        summary = results.get_summary()
        
        # Criteria for passing
        criteria = {
            "Success Rate > 95%": summary["success_rate"] > 95,
            "Average Response Time < 2s": summary.get("avg_response_time", 999) < 2.0,
            "P95 Response Time < 5s": summary.get("p95_response_time", 999) < 5.0,
            "No Timeouts": summary["errors_by_endpoint"].get("Timeout", 0) == 0,
        }
        
        all_passed = all(criteria.values())
        
        for criterion, passed in criteria.items():
            status = "✅" if passed else "❌"
            print(f"{status} {criterion}")
        
        if all_passed:
            print("\n✨ All stress test criteria met! System is production-ready.")
            return True
        else:
            print("\n⚠️ Some stress test criteria not met. Review logs above.")
            return False
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stress test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check if server is running first
    print("🔍 Checking if Swarm V2 API server is running...")
    print("Note: Make sure to run 'python swarm_v2/app_v2.py' in another terminal first!")
    print("="*60)
    
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Comprehensive stress test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Stress test failed!")
        sys.exit(1)