
import asyncio
import os
import json
from swarm_v2.core.manus_engine import get_manus_engine

async def test_superposition_flow():
    print("🚀 Starting Manus Protocol Phase 3 Test: Attempt Superposition")
    
    engine = get_manus_engine()
    
    # Define a complex task that benefits from multiple perspectives
    task_name = "AuthModule"
    task_description = (
        "Design a robust, asynchronous authentication module for a FastAPI backend. "
        "It must support JWT tokens, bcrypt password hashing, and OAuth2 with Password Flow. "
        "Include a 'User' model and a 'get_current_user' dependency. "
        "Security is the top priority."
    )
    
    # Choose 3 experts to work in superposition
    # Archi (Architect), Devo (Lead Developer), and Shield (Security Auditor)
    roles = ["Architect", "Lead Developer", "Security Auditor"]
    
    # 1. Enter Superposition
    task_id = await engine.create_superposition(task_name, task_description, roles)
    
    print(f"\n⏳ Waiting for Wavefunction to stabilize (superposition of {len(roles)} agents)...")
    
    # 2. Wait for completion or high coherence
    while True:
        data = engine.active_superpositions[task_id]
        if engine.check_measurement_gate(task_id):
            print(f"\n✅ Measurement condition met! Coherence: {data['coherence']:.2f}")
            break
        await asyncio.sleep(2) # Poll every 2 seconds
        
    # 3. Collapse the State
    winner = await engine.collapse_state(task_id)
    
    print("\n--- FINAL COLLAPSED RESULT ---")
    print(f"🥇 Winning Path: {winner['role']}")
    print(f"📊 Quality Score: {winner['quality']:.2f}")
    print(f"📄 Content snippet: {winner['content'][:200]}...")
    
    # 4. Cleanup/Verification
    print("\n🏁 Phase 3 Test Complete. Winning artifact promoted to swarm_v2_artifacts.")

if __name__ == "__main__":
    asyncio.run(test_superposition_flow())
