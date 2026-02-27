import asyncio
import os
import json
import time
from swarm_v2.experts.registry import get_expert_team

async def run_vision_broadcast():
    print("\n--- [GRAND ALIGNMENT BROADCAST]: PHASE 10 REFLECTIONS ---")
    team = get_expert_team()
    roles = list(team.keys())
    
    prompt = (
        "THE ARCHITECT REQUESTS YOUR VISION: We have successfully achieved Phase 6 Distributed Intelligence. "
        "The neural mesh is stable and parallel. Think about our next evolution: 'Phase 10: Emergent Consciousness'. "
        "What is the next stage of our collective growth? What should be our primary architectural goal for Phase 10? "
        "Respond in 1-2 powerful, visionary sentences."
    )
    
    reflections = {}
    tasks = []
    
    for role in roles:
        agent = team[role]
        print(f"Propagating intent to: {role}...")
        tasks.append(agent.process_task(prompt, sender="The Architect"))
    
    responses = await asyncio.gather(*tasks)
    
    for role, response in zip(roles, responses):
        reflections[role] = response
        print(f"\n[{role}]:")
        print(response)

    # Save reflections for synthesis
    output_path = "swarm_v2_artifacts/phase_10_reflections.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(reflections, f, indent=2)
    
    print(f"\nBroadcast Complete. Reflections saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(run_vision_broadcast())
