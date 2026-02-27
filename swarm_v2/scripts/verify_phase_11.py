
import asyncio
import logging
from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.expert_registry import get_expert_registry
from swarm_v2.core.optimization_engine import get_optimization_engine
from swarm_v2.core.resonance_engine import get_resonance_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyPhase11")

async def verify_optimization():
    print("=== Phase 11: Recursive Self-Optimization Verification ===")
    
    # 1. Initialize Registry and Team
    registry = get_expert_registry()
    team = get_expert_team()
    registry.register_team(team)
    
    architect = registry.get_agent("Architect")
    if not architect:
        print("Architect agent not found!")
        return

    # 2. Simulate Performance Fluctuations
    opt = get_optimization_engine()
    
    # Scenario A: Low Harmony (Should increase H_cycles)
    print("\n--- Scenario A: Low Harmony Detection ---")
    architect.cognitive_stack.config["H_cycles"] = 1
    
    # Record 5 interactions with low harmony
    for _ in range(5):
        opt.record_performance(architect.persona.name, task_latency=1.2, harmony_score=0.4)
    
    # Trigger optimization
    print(f"Agent name is: {architect.persona.name}")
    print(f"Current H_cycles before: {architect.cognitive_stack.config['H_cycles']}")
    await architect._self_optimize(latency=1.2)
    
    new_h = architect.cognitive_stack.config["H_cycles"]
    print(f"Resulting H_cycles after: {new_h}")
    assert new_h > 1, f"Optimization failed: H_cycles should have increased. Current: {new_h}"
    print("✅ Success: Agent increased reasoning depth in response to low harmony.")

    # Scenario B: High Latency (Should decrease H_cycles)
    print("\n--- Scenario B: High Latency Detection ---")
    opt.agent_metrics[architect.persona.name] = [] # Clear metrics for clean test
    architect.cognitive_stack.config["H_cycles"] = 5
    
    # Record 5 interactions with high latency
    for _ in range(5):
        opt.record_performance(architect.persona.name, task_latency=6.5, harmony_score=0.9)
        
    await architect._self_optimize(latency=6.5)
    
    new_h = architect.cognitive_stack.config["H_cycles"]
    print(f"Resulting H_cycles: {new_h}")
    assert new_h < 5, f"Optimization failed: H_cycles should have decreased. Current: {new_h}"
    print("✅ Success: Agent reduced reasoning depth to optimize for latency.")

    # 3. Verify Resonance Thresholding
    print("\n--- Scenario C: Resonance Thresholding ---")
    resonance = get_resonance_engine()
    from swarm_v2.core.global_memory import get_global_memory
    mem = get_global_memory()
    
    # Clear and seed memory with only 1 author (Low coherence)
    mem.entries_metadata = {} 
    mem.contribute("Lonely thought", "Architect", "Architect", "thought")
    
    print("Attempting sync with low coherence (1 author)...")
    await resonance.synchronize_dreams()
    assert len(resonance.active_dreams) == 0, "Resonance Thresholding failed: Dream manifested with low coherence."
    print("✅ Success: Resonance Engine skipped dream cycle due to low coherence.")

    # Seed with 5 different authors (High coherence)
    for i in range(5):
        mem.contribute(f"Shared insight {i}", f"Agent_{i}", "Expert", "thought")
        
    print("Attempting sync with high coherence (5 authors)...")
    await resonance.synchronize_dreams()
    assert len(resonance.active_dreams) > 0, "Resonance Thresholding failed: Dream DID NOT manifest with high coherence."
    print("✅ Success: Resonance Engine manifested dream after reaching coherence threshold.")

    print("\n=== Phase 11 Verification Complete: ALL SYSTEMS STABLE ===")

if __name__ == "__main__":
    asyncio.run(verify_optimization())
