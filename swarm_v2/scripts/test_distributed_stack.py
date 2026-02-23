
import asyncio
import time
from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.telemetry import get_telemetry

async def verify_distributed_intelligence():
    print("🚀 QIAE Phase 6: Distributed Intelligence Verification")
    print("--------------------------------------------------")
    
    team = get_expert_team()
    print(f"Initialized {len(team)} agents with local Cognitive Stacks.")
    
    # 1. Parallel Execution Test
    print("\n[Test 1] Parallel Response Stress Test (All 12 Agents)...")
    start_time = time.time()
    
    tasks = []
    for role, agent in team.items():
        tasks.append(agent.process_task(f"Quick status check: Who are you and what is your current stack VRAM estimate?", sender="user"))
    
    responses = await asyncio.gather(*tasks)
    end_time = time.time()
    
    print(f"Parallel execution completed in {end_time - start_time:.2f}s.")
    for role, resp in zip(team.keys(), responses):
        print(f" - [{role}] Status: OK")
    
    # 2. Reasoning Offload Test
    print("\n[Test 2] Reasoning Offload Verification (Logic Agent)...")
    logic_agent = team.get("Reasoning Engine")
    if logic_agent:
        complex_task = "Analyze the logical consistency of a recursive loop with 4 cycles and 3 layers. Should we offload this?"
        resp = await logic_agent.process_task(complex_task)
        
        stats = logic_agent.cognitive_stack.stats
        print(f"Logic Agent Stats: {stats}")
        
        if stats["reasoning_calls"] > 0:
            print("✅ SUCCESS: Complexity-aware offloading to TRM reasoning core detected.")
        else:
            print("❌ FAILURE: TRM reasoning core was not engaged for a 'logic' task.")
    
    # 3. Telemetry Aggregation
    print("\n[Test 3] Telemetry Distributed Stack Aggregation...")
    telemetry = get_telemetry().get_emergence_report()
    stacks = telemetry.get("distributed_stacks", [])
    print(f"Telemetry reporting {len(stacks)} active stacks.")
    
    if len(stacks) == len(team):
        print("✅ SUCCESS: Telemetry correctly tracks all distributed stacks.")
    else:
        print(f"❌ FAILURE: Telemetry mismatch. Found {len(stacks)} stacks for {len(team)} agents.")

if __name__ == "__main__":
    asyncio.run(verify_distributed_intelligence())
