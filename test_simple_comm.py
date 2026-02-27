
import requests
import json
import time

API_BASE = "http://127.0.0.1:8001"

def test_chat():
    print("--- Testing Chat Endpoint ---")
    payload = {
        "role": "Lead Developer",
        "message": "Hello, world!",
        "sender": "test_script"
    }
    try:
        print(f"Attempting to connect to {API_BASE}/swarm/chat")
        start_time = time.time()
        response = requests.post(f"{API_BASE}/swarm/chat", json=payload, timeout=60) # Added timeout
        end_time = time.time()
        print("Request sent, processing response...")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2))
            print(f"\nRequest completed in {end_time - start_time:.2f} seconds.")
        else:
            print("Error Response:")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_chat()
