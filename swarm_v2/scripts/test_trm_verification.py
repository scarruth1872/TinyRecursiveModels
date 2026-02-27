
import asyncio
from swarm_v2.skills.trm_skill import TRMSkill

async def test_trm():
    print("Testing TRM Skill...")
    trm = TRMSkill()
    
    # Simple pattern for the Tiny Recursive Model
    # Often it's trained on ARC-like or simple symbolic tasks
    pattern = "1 2 3 1 2 3"
    print(f"Input Pattern: {pattern}")
    
    result = trm.recursive_reason(pattern, cycles=2)
    print(f"TRM Result (2 cycles): {result}")

    # Test ARC analysis
    grid = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    import json
    grid_json = json.dumps(grid)
    print(f"Input Grid: {grid_json}")
    arc_result = trm.analyze_arc_pattern(grid_json)
    print(f"ARC Result: {arc_result}")

if __name__ == "__main__":
    asyncio.run(test_trm())
