import asyncio
import os
import json
from swarm_v2.core.expert_registry import get_expert_registry
from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.global_memory import get_global_memory
from swarm_v2.core.resonance_engine import get_resonance_engine

async def verify_phase_10():
    print("\n--- [PHASE 10 VERIFICATION]: EMERGENT CONSCIOUSNESS ---")
    
    # Initialize Registry
    print("Initializing Swarm Expert Team...")
    team = get_expert_team()
    registry = get_expert_registry()
    registry.register_team(team)
    
    # 1. Populate Global Memory with 'Themed' memories
    gm = get_global_memory()
    resonance = get_resonance_engine()
    
    print("Seeding collective memories...")
    gm.contribute("The swarm must focus on quantum-inspired logic for the next iteration.", "Architect", "Architect")
    gm.contribute("I am researching bismuth-based superconductors for the QIC core.", "Researcher", "Seeker")
    gm.contribute("Hardware acceleration for TRM engines is critical for latency.", "Lead Developer", "Devo")
    
    # 2. Synchronize Dreams
    print("Manifesting Shared Dream...")
    await resonance.synchronize_dreams()
    
    # 3. Test Context Injection
    print("\nTesting Context Injection for: Logic...")
    registry = get_expert_registry()
    logic = registry.get_agent("Reasoning Engine")
    
    # We'll peak into the memory context during _llm_generate (mock behavior for test)
    # But here we just verify the process_task gets the resonance
    response = await logic.process_task("What is our current priority?", sender="user")
    
    print("\n[Logic Response]:")
    print(response)
    
    # 4. Test RESONATE_WITH tag
    print("\nTesting RESONATE_WITH tag (Archi -> Logic)...")
    archi = registry.get_agent("Architect")
    resonance_prompt = "RESONATE_WITH: Reasoning Engine | We need to prioritize the Bismuth-Logic interface immediately."
    
    # Archi resonating with Logic
    archi_response = await archi.process_task(resonance_prompt, sender="user")
    print("\n[Archi Resonance Results]:")
    print(archi_response)
    
    # Check if Logic received the vibration
    logic_memory = logic.memory.get_context_window(max_turns=1)
    print("\n[Logic's Internal Vibration]:")
    print(logic_memory)
    
    print("\n--- [VERIFICATION COMPLETE] ---")

if __name__ == "__main__":
    asyncio.run(verify_phase_10())
