#!/usr/bin/env python3
"""
Test which endpoints actually exist.
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an endpoint and return results."""
    try:
        if method == "GET":
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        elif method == "POST":
            resp = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        else:
            return {"error": f"Unknown method {method}"}
        
        return {
            "status": resp.status_code,
            "success": resp.status_code == 200,
            "response": resp.json() if resp.status_code == 200 and resp.text else resp.text[:500]
        }
    except Exception as e:
        return {"error": str(e), "success": False}

def main():
    print("Testing endpoints...")
    
    endpoints = [
        "/health",
        "/memory/stats",
        "/swarm/experts",
        "/artifacts/stats",
        "/agents",  # Might not exist
        "/artifacts",
        "/mesh/topology",
        "/mesh/stats",
        "/swarm/telemetry",
        "/swarm/soul",
        "/learning/skills",
        "/synthesize/tools",
        "/federation/stats",
        "/system/resources",
        "/verification/stats",
        "/infra/health",
        "/changelog/status",
        "/evolver/status",
        "/insights/status",
        "/swarm/orchestrator/stats"
    ]
    
    results = {}
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}...")
        result = test_endpoint(endpoint)
        results[endpoint] = result
        if result.get("success"):
            print(f"  ✅ {result['status']}")
            if endpoint == "/health":
                health_data = result.get("response", {})
                print(f"    Status: {health_data.get('status', 'N/A')}")
                print(f"    Phase: {health_data.get('phase', 'N/A')}")
        else:
            print(f"  ❌ {result.get('status', 'Error')} - {result.get('error', 'No error details')}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    successful = [e for e in endpoints if results[e].get("success")]
    failed = [e for e in endpoints if not results[e].get("success")]
    
    print(f"Successful endpoints ({len(successful)}):")
    for e in successful:
        print(f"  {e}")
    
    print(f"\nFailed endpoints ({len(failed)}):")
    for e in failed:
        status = results[e].get("status", "N/A")
        error = results[e].get("error", "Unknown")
        print(f"  {e} - Status: {status}, Error: {error}")

if __name__ == "__main__":
    main()