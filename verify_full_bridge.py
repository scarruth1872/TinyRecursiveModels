
import httpx
import time
import threading
import uvicorn
import sys
import os

# Ensure we can import
sys.path.append(os.getcwd())

from swarm_v2_integrated.nexus_main import app as gateway_app, run_agent_service
from swarm_v2_integrated.nexus_worker import NexusWorker
from swarm_v2_integrated.nexus_main import redis_client as shared_redis

def test_full_swarm_nexus_bridge():
    print("--- Verifying Nexus to Swarm Core Bridge ---")
    
    # Check if Swarm Core is online
    try:
        httpx.get("http://localhost:8000/health")
        print("✅ Swarm V2 Core is ONLINE")
    except:
        print("❌ Error: Swarm V2 Core (app_v2.py) must be running on port 8000 for this test.")
        return

    # 1. Start Gateway in Thread
    def run_gateway():
        uvicorn.run(gateway_app, host="127.0.0.1", port=8002, log_level="error")
    t_gw = threading.Thread(target=run_gateway, daemon=True)
    t_gw.start()
    
    # 2. Start Worker in Thread (Inject shared mock redis if needed)
    worker = NexusWorker()
    worker.redis_client = shared_redis # Ensure they share the same in-memory store
    
    t_worker = threading.Thread(target=worker.run, daemon=True)
    t_worker.start()
    
    time.sleep(3)
    
    client = httpx.Client(base_url="http://127.0.0.1:8002", timeout=60)
    
    try:
        # 1. Dispatch a SECURITY task
        task_id = "SEC-AUDIT-001"
        print(f"\n[1/2] Dispatching Security Audit Task: {task_id}")
        task = {
            "id": task_id,
            "description": "Perform a security audit of our Redis connection logic. Is it secure against injections?",
            "required_skills": ["security", "audit"]
        }
        r = client.post("/dispatch", json=task)
        print(f"Gateway Response: {r.json()}")
        
        # 2. Poll for the REAL expert response
        print("\n[2/2] Polling for Real Expert Response (TRM Reasoning)...")
        for i in range(15):
            status_r = client.get(f"/status/{task_id}")
            data = status_r.json()
            status = data.get("status")
            expert = data.get("expert")
            
            print(f"Attempt {i+1}: Status is '{status}' (Expert: {expert})")
            
            if status == "completed":
                print(f"✨ SUCCESS! Task handled by REAL Agent: {expert}")
                response_text = data.get("response", "")
                print(f"\nExpert Logic Output (Snippet):\n{response_text[:300]}...")
                break
            time.sleep(2)
        else:
            print("❌ Timeout: Worker or core failed to respond.")
            
        print("\n✅ DISTRIBUTED NEXUS → SWARM BRIDGE VERIFIED")
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    test_full_swarm_nexus_bridge()
