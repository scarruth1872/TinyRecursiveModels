#!/usr/bin/env python3
"""
Detailed test to understand why /artifacts/stats returns 404.
"""

import requests
import json
import sys

def test_with_debug():
    base_url = "http://localhost:8001"
    
    # First, test that the server is up
    print("=== Testing server connectivity ===")
    try:
        health_resp = requests.get(f"{base_url}/health", timeout=5)
        print(f"/health: {health_resp.status_code}")
        if health_resp.status_code == 200:
            health_data = health_resp.json()
            print(f"  Status: {health_data.get('status', 'N/A')}")
            print(f"  Phase: {health_data.get('phase', 'N/A')}")
            print(f"  Agents: {health_data.get('agents', 'N/A')}")
    except Exception as e:
        print(f"  Error: {e}")
        return
    
    # Test /artifacts endpoint
    print("\n=== Testing /artifacts endpoint ===")
    try:
        artifacts_resp = requests.get(f"{base_url}/artifacts", timeout=5)
        print(f"/artifacts: {artifacts_resp.status_code}")
        if artifacts_resp.status_code == 200:
            artifacts_data = artifacts_resp.json()
            stats = artifacts_data.get('stats', {})
            print(f"  Total artifacts: {stats.get('total', 'N/A')}")
            print(f"  Pending: {stats.get('pending', 'N/A')}")
            print(f"  Approved: {stats.get('approved', 'N/A')}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test /artifacts/stats endpoint
    print("\n=== Testing /artifacts/stats endpoint ===")
    try:
        stats_resp = requests.get(f"{base_url}/artifacts/stats", timeout=5)
        print(f"/artifacts/stats: {stats_resp.status_code}")
        print(f"  Headers: {dict(stats_resp.headers)}")
        if stats_resp.status_code == 200:
            stats_data = stats_resp.json()
            print(f"  Response: {json.dumps(stats_data, indent=2)}")
        else:
            print(f"  Response body: {stats_resp.text}")
            
            # Try with different variations
            print("\n=== Trying variations ===")
            variations = [
                "/artifacts/stats/",
                "/artifacts/stats?debug=1",
                "/artifacts/stats?",
                "/artifacts/stats?format=json",
            ]
            for variation in variations:
                try:
                    var_resp = requests.get(f"{base_url}{variation}", timeout=3)
                    print(f"  {variation}: {var_resp.status_code}")
                except Exception as e:
                    print(f"  {variation}: Error - {e}")
                    
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test if there's a duplicate route with same path but different method
    print("\n=== Testing different HTTP methods ===")
    methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']
    for method in methods:
        try:
            resp = requests.request(method, f"{base_url}/artifacts/stats", timeout=3)
            print(f"  {method}: {resp.status_code}")
            if method == 'OPTIONS' and resp.status_code == 200:
                print(f"    Allowed methods: {resp.headers.get('allow', 'N/A')}")
        except Exception as e:
            print(f"  {method}: Error - {e}")
    
    # Try to get all routes from the API (if there's an openapi.json or docs)
    print("\n=== Checking for OpenAPI/Swagger docs ===")
    for doc_path in ['/openapi.json', '/docs', '/redoc', '/swagger.json']:
        try:
            doc_resp = requests.get(f"{base_url}{doc_path}", timeout=3)
            print(f"  {doc_path}: {doc_resp.status_code}")
            if doc_resp.status_code == 200 and doc_path == '/openapi.json':
                # Try to parse and find the /artifacts/stats route
                try:
                    openapi_data = doc_resp.json()
                    paths = openapi_data.get('paths', {})
                    if '/artifacts/stats' in paths:
                        print(f"    Found /artifacts/stats in OpenAPI!")
                        print(f"    Methods: {list(paths['/artifacts/stats'].keys())}")
                except:
                    pass
        except Exception as e:
            print(f"  {doc_path}: Error - {e}")
    
    # Try to get error logs by making a request with trace header
    print("\n=== Testing with trace headers ===")
    headers = {'X-Trace-Id': 'debug-test-123'}
    try:
        trace_resp = requests.get(f"{base_url}/artifacts/stats", headers=headers, timeout=5)
        print(f"  With trace header: {trace_resp.status_code}")
    except Exception as e:
        print(f"  Error with trace: {e}")

if __name__ == "__main__":
    test_with_debug()