#!/usr/bin/env python3
"""
Test the /artifacts/stats endpoint to understand why it returns 404.
"""

import requests
import json

def test_endpoint():
    url = "http://localhost:8001/artifacts/stats"
    print(f"Testing {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 404:
            print("\n=== Investigating 404 ===")
            # Try to get all routes from the API
            print("\nTrying /health to verify API is up...")
            health_resp = requests.get("http://localhost:8001/health", timeout=5)
            print(f"Health status: {health_resp.status_code}")
            if health_resp.status_code == 200:
                print("API is accessible")
            
            # Try other artifact endpoints
            print("\nTrying /artifacts endpoint...")
            artifacts_resp = requests.get("http://localhost:8001/artifacts", timeout=5)
            print(f"/artifacts status: {artifacts_resp.status_code}")
            
            # Check if there's a trailing slash issue
            print("\nTrying with trailing slash...")
            url_with_slash = "http://localhost:8001/artifacts/stats/"
            slash_resp = requests.get(url_with_slash, timeout=5)
            print(f"With slash status: {slash_resp.status_code}")
            
            # Check if there's a different path pattern
            print("\nChecking for similar paths...")
            similar_paths = [
                "/artifacts",
                "/artifacts/",
                "/artifacts/stats/",
                "/artifact/stats",
                "/artifact/stats/",
                "/artifacts-stats",
                "/artifacts_stats"
            ]
            for path in similar_paths:
                try:
                    resp = requests.get(f"http://localhost:8001{path}", timeout=3)
                    print(f"  {path}: {resp.status_code}")
                except Exception as e:
                    print(f"  {path}: Error - {e}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint()