import requests
import json

API_BASE = "http://localhost:8001"

def test_endpoint(name, url):
    print(f"Testing {name} ({url})...")
    try:
        res = requests.get(f"{API_BASE}{url}")
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"Data: {json.dumps(data, indent=2)[:500]}...")
            return True
        else:
            print(f"Error: {res.text}")
            return False
    except Exception as e:
        print(f"Fail: {e}")
        return False

print("--- API VERIFICATION ---")
test_endpoint("Telemetry", "/swarm/telemetry")
test_endpoint("Experts", "/swarm/experts")
test_endpoint("Artifacts", "/artifacts")
test_endpoint("Federation Stats", "/federation/stats")
test_endpoint("Federation Peers", "/federation/peers")
print("--- END ---")
