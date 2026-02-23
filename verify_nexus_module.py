
import httpx
import time
import subprocess
import os

def test_nexus():
    print("--- Testing Nexus Platform Module ---")
    
    # Start the Nexus Platform
    # Using python directly from venv
    process = subprocess.Popen(
        [os.path.join("venv", "Scripts", "python.exe"), "-m", "swarm_v2_integrated.nexus_main"],
        env={**os.environ, "PYTHONPATH": "."}
    )
    
    time.sleep(5)  # Wait for services to start
    
    client = httpx.Client(base_url="http://127.0.0.1:8002", timeout=10)
    
    try:
        # 1. Check Root
        print("[Test 1] Checking Gateway Health...")
        r = client.get("/")
        print(f"Response: {r.json()}")
        assert r.status_code == 200
        
        # 2. Test Task Dispatch
        print("[Test 2] Dispatching Task to Agent Manager via Gateway...")
        task = {
            "id": "task-101",
            "description": "Build a secure API",
            "required_skills": ["python", "fastapi"]
        }
        r = client.post("/dispatch", json=task)
        print(f"Response: {r.json()}")
        assert r.json()["status"] == "dispatched"
        assert r.json()["agent"] == "agent-01"
        
        # 3. Check Agent Service directly (port 8001)
        print("[Test 3] Checking Back-end Agent Manager directly...")
        r_agent = httpx.get("http://127.0.0.1:8001/agents")
        print(f"Agent Service Response: {r_agent.status_code}")
        assert r_agent.status_code == 200
        
        print("\n✅ Nexus Platform Module Verification: PASSED")
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
    finally:
        process.terminate()
        process.wait()
        print("Nexus Platform Process Terminated")

if __name__ == "__main__":
    test_nexus()
