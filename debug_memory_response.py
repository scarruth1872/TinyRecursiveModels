#!/usr/bin/env python3
"""
Debug the memory query response format.
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_query():
    data = {
        "query": "quantum computing",
        "top_k": 3
    }
    resp = requests.post(f"{BASE_URL}/memory/query", json=data, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        response = resp.json()
        print(f"Full response keys: {list(response.keys())}")
        print(f"Results type: {type(response.get('results'))}")
        if response.get('results'):
            print(f"First result: {response['results'][0]}")
            print(f"Type of first result: {type(response['results'][0])}")
            if isinstance(response['results'][0], list):
                print(f"First result is list of length: {len(response['results'][0])}")
                for i, item in enumerate(response['results'][0]):
                    print(f"  Item {i}: {type(item)} = {item}")
            elif isinstance(response['results'][0], tuple):
                print(f"First result is tuple of length: {len(response['results'][0])}")
                for i, item in enumerate(response['results'][0]):
                    print(f"  Item {i}: {type(item)} = {item}")
            elif isinstance(response['results'][0], dict):
                print(f"First result dict keys: {list(response['results'][0].keys())}")
        else:
            print("No results in response")

if __name__ == "__main__":
    test_query()