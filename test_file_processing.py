#!/usr/bin/env python3
"""
Test script for file processing endpoints.
"""

import sys
import os
import json
import requests
import time

# Add current directory to path
sys.path.append('.')

def test_file_processing_endpoints():
    """Test the file processing endpoints."""
    base_url = "http://localhost:8001"
    
    print("Testing file processing endpoints...")
    
    # Create a test file
    test_file = "test_sample.py"
    test_content = '''
def hello_world():
    """Simple test function."""
    print("Hello, World!")
    return "Success"

if __name__ == "__main__":
    hello_world()
'''
    
    try:
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Test 1: Process files endpoint
        print("\n1. Testing /swarm/process-files endpoint...")
        payload = {
            "task": "Analyze this Python function and explain what it does",
            "file_paths": [test_file],
            "target_role": "Lead Developer",
            "save_results": True
        }
        
        response = requests.post(f"{base_url}/swarm/process-files", json=payload)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response:", json.dumps(result, indent=2))
            
            # Test 2: List results
            print("\n2. Testing /swarm/processed-results endpoint...")
            list_response = requests.get(f"{base_url}/swarm/processed-results")
            print(f"List status: {list_response.status_code}")
            if list_response.status_code == 200:
                list_data = list_response.json()
                print(f"Found {list_data['total_count']} results")
                if list_data['results']:
                    print("Latest result:", list_data['results'][0]['filename'])
            
            # Test 3: Get specific result
            if result.get('result_file'):
                print("\n3. Testing /swarm/processed-results/{result_id} endpoint...")
                result_id = result['result_file']
                detail_response = requests.get(f"{base_url}/swarm/processed-results/{result_id}")
                print(f"Detail status: {detail_response.status_code}")
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    print(f"Result content length: {len(detail_data.get('content', ''))}")
        else:
            print("Error:", response.text)
    
    except Exception as e:
        print(f"Test failed with error: {e}")
    
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
        print("\nTest completed.")

if __name__ == "__main__":
    print("File Processing Endpoint Test")
    print("=============================")
    test_file_processing_endpoints()