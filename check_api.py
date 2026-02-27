#!/usr/bin/env python3
"""Check if the TRM Swarm V2 API is running."""
import requests
import sys
import time

def check_api():
    """Check if API is accessible."""
    url = "http://localhost:8001/health"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ API is running. Status: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {data}")
        except:
            print(f"Response text: {response.text[:200]}")
            
        return True
    except requests.ConnectionError:
        print("❌ API is not running (connection refused)")
        return False
    except requests.Timeout:
        print("❌ API request timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking if TRM Swarm V2 API is running...")
    if check_api():
        sys.exit(0)
    else:
        sys.exit(1)