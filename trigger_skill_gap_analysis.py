import httpx
import json

def trigger_skill_scan():
    api_base = "http://127.0.0.1:8001"
    
    # 1. Ask Archi to review research findings and identify missing skills
    archi_prompt = (
        "Archi, as the Architect of the TRM Swarm, please review our recent research findings (Seeker Reconnaissance) "
        "and compare them against our current 35 learned skills. "
        "Identify the top 3 high-impact skills that we currently LACK but are documented in our research (e.g., REAP prompting, Agent Q reasoning, or specific model pruning techniques). "
        "Draft a directive for Devo to synthesize these skills into the Learning Engine."
    )
    
    print("Triggering Archi for Skill Gap Analysis...")
    try:
        response = httpx.post(f"{api_base}/swarm/chat", json={
            "role": "Architect",
            "message": archi_prompt,
            "sender": "user_system_check"
        }, timeout=300.0)
        
        print(f"Archi Response Status: {response.status_code}")
        archi_data = response.json()
        with open("swarm_v2_artifacts/skill_gap_analysis.md", "w", encoding="utf-8") as f:
            f.write(archi_data["response"])
        print("Skill gap analysis saved to swarm_v2_artifacts/skill_gap_analysis.md")
        
    except Exception as e:
        print(f"Error triggering Archi: {e}")

if __name__ == "__main__":
    trigger_skill_scan()
