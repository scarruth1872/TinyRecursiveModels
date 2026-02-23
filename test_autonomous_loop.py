
import asyncio
from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
from swarm_v2.core.expert_registry import get_expert_registry

async def run_demo():
    print("[Demo] Phase 5 Autonomous Loop - Verbose Mode")
    
    team = get_expert_team()
    get_expert_registry().register_team(team)
    
    devo = team["Lead Developer"]
    
    mission = (
        "TASK 1: Create 'math_fail.py' with a DELIBERATE BUG: 'def add(a, b): return a - b'. "
        "IMPORTANT: Do NOT fix it yet. You MUST submit the broken version first to test the QA process. "
        "TASK 2: Once the QA Engineer (Verify) detects it and rejects it via REJECT_ARTIFACT, "
        "you must then fix it to return 'a + b'."
    )
    
    print(f"[Mission]: {mission}")
    
    # Process Task
    response = await devo.process_task(mission, sender="user")
    
    print("\n" + "="*50)
    print("[NODAL LOGS] (Self-Diagnosis):")
    print("="*50)
    for log in devo.nodal_logs:
        print(log)
    
    # Also check Verify's logs if possible
    verify = team["QA Engineer"]
    print("\n" + "="*50)
    print("[VERIFY LOGS]:")
    print("="*50)
    for log in verify.nodal_logs:
        print(log)

    print("\n" + "="*50)
    print("[FINAL RESPONSE]:")
    print("="*50)
    print(response)

if __name__ == "__main__":
    asyncio.run(run_demo())
