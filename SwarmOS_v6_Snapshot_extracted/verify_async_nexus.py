
import httpx
import time
import threading
import uvicorn
from swarm_v2_integrated.nexus_main import app as gateway_app, run_agent_service
from swarm_v2_integrated.nexus_worker import NexusWorker

def test_async_nexus():
    print("--- Verifying Async Nexus Integration (Single Process Threaded) ---")
    
    # 1. Start Agent Service (Sidecar)
    t1 = threading.Thread(target=run_agent_service, daemon=True)
    t1.start()
    
    # 2. Start Gateway
    def run_gateway():
        uvicorn.run(gateway_app, host="127.0.0.1", port=8002)
    t2 = threading.Thread(target=run_gateway, daemon=True)
    t2.start()
    
    # 3. Start Worker
    # Note: Because they are in the same process, they will share the same 'fakeredis' singleton if imported correctly
    # But since we use redis.Redis() which fails and then creates a NEW fakeredis instance in each __init__, 
    # we need to inject the same client.
    
    from swarm_v2_integrated.nexus_main import redis_client as shared_redis
    worker = NexusWorker()
    worker.redis_client = shared_redis # Share the mock memory
    
    t3 = threading.Thread(target=worker.run, daemon=True)
    t3.start()
    
    time.sleep(5)  # Let things initialize
    client = httpx.Client(base_url="http://127.0.0.1:8002", timeout=10)
    
    try:
        # 1. Dispatch Task (Async)
        task_id = "ASYNC-VERIFY-01"
        print(f"\n[1/3] Dispatching Async Task: {task_id}")
        task = {
            "id": task_id,
            "description": "Cross-Thread Integration Test",
            "required_skills": ["python", "redis"]
        }
        r = client.post("/dispatch", json=task)
        print(f"Gateway Response: {r.json()}")
        assert r.json()["status"] == "queued"
        
        # 2. Poll Status
        print("\n[2/3] Polling Task Status...")
        for i in range(10):
            status_r = client.get(f"/status/{task_id}")
            current_status = status_r.json().get("status")
            print(f"Attempt {i+1}: Status is '{current_status}'")
            
            if current_status == "completed":
                print("✨ Integration Verified: Worker processed the task successfully!")
                break
            time.sleep(1)
        else:
            print("❌ Timeout: Worker failed to process task.")
            return

        print("\n✅ NEXUS ASYNC SYSTEM FULLY OPERATIONAL")
        
    except Exception as e:
        print(f"\n❌ Integration Failed: {e}")

if __name__ == "__main__":
    test_async_nexus()
