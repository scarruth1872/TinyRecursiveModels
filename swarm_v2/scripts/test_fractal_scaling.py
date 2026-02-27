
import asyncio
import os
from swarm_v2.experts.registry import get_expert_team

async def test_fractal_scaling():
    print("Testing Fractal Scaling (Ephemeral Subagents)...")
    team = get_expert_team()
    archi = team["Architect"]
    
    # Task that requires isolation (e.g. creating a new module)
    task = "Create a simple 'hello_world.py' in the current workspace and verify it."
    
    print(f"Spawning isolated subordinate for task: {task}")
    # isolated=True triggers WorktreeManager (Isolation 0)
    result = await archi.spawn_subordinate(task, isolated=True)
    
    print(f"Subordinate Result:\n{result}")

if __name__ == "__main__":
    asyncio.run(test_fractal_scaling())
