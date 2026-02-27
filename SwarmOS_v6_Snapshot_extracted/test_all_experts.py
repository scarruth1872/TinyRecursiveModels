
import httpx
import time
import json

def test_all_experts():
    print("--- 🛡️ Verifying Full Swarm Intelligence (12 Experts) ---")
    
    agents = [
        "Architect", "Lead Developer", "Researcher", "Reasoning Engine",
        "Security Auditor", "DevOps Engineer", "UI/UX Designer", "QA Engineer",
        "Swarm Manager", "Technical Writer", "Integration Specialist", "Data Analyst"
    ]
    
    results = {}
    client = httpx.Client(base_url="http://localhost:8000", timeout=120)

    for role in agents:
        print(f"\n[Testing] {role}...")
        payload = {
            "role": role,
            "message": f"Identify yourself and state one technical specialty that makes you unique as a {role}."
        }
        
        try:
            start_time = time.time()
            r = client.post("/swarm/chat", json=payload)
            elapsed = time.time() - start_time
            
            if r.status_code == 200:
                response = r.json().get("response", "")
                # Check for signs of real generation (not just a 1-sentence mock)
                is_mock = len(response.strip()) < 50 or "placeholder" in response.lower()
                
                print(f"⏱️ Response Time: {elapsed:.2f}s")
                print(f"📄 Snippet: {response[:150]}...")
                
                results[role] = {
                    "status": "PASS" if not is_mock else "POTENTIAL_MOCK",
                    "length": len(response),
                    "time": elapsed
                }
            else:
                print(f"❌ Error: {r.status_code}")
                results[role] = {"status": "FAILED", "code": r.status_code}
                
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            results[role] = {"status": "ERROR", "error": str(e)}
            
    print("\n" + "="*50)
    print("📊 FINAL SWARM AUDIT REPORT")
    print("="*50)
    
    passed = 0
    for role, data in results.items():
        status = data.get("status")
        print(f"{role:25} | {status}")
        if status == "PASS":
            passed += 1
            
    print("="*50)
    print(f"TOTAL VERIFIED: {passed}/{len(agents)}")
    
    if passed == len(agents):
        print("\n✅ ALL AGENTS CONFIRMED LIVE - NO MOCK RESPONSES DETECTED.")
    else:
        print("\n⚠️ WARNING: Some agents failed or returned suspicious content.")

if __name__ == "__main__":
    test_all_experts()
