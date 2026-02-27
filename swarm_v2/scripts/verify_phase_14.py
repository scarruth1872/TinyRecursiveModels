import asyncio
import os
import json
from swarm_v2.core.base_agent import BaseAgent, AgentPersona
from swarm_v2.core.lobster_shell import get_lobster_shell, LobsterPipeline, LobsterStep
from swarm_v2.core.attempt_sampler import get_attempt_sampler

async def verify_phase_14():
    print("=== Phase 14: Lobster Shell & Attempt Sampling Verification ===\n")
    
    persona = AgentPersona(
        name="Arbiter",
        role="Verification Specialist",
        background="Expert in deterministic workflows and quantum sampling.",
        specialties=["Validation", "Logic"]
    )
    agent = BaseAgent(persona)

    # Scenario A: Lobster Pipeline Execution
    print("[Scenario A] Testing Lobster Typed Pipeline...")
    pipeline = LobsterPipeline(
        name="DirAudit",
        steps=[
            LobsterStep(tool="list_files", args={"directory": "."}, transform="head:2"),
            LobsterStep(tool="analyze_code", transform="pick:summary")
        ]
    )
    
    # We mock the tool executor for pure logic testing
    async def mock_executor(tool, args):
        if tool == "list_files":
            return [{"name": "file1.py", "id": 1}, {"name": "file2.py", "id": 2}, {"name": "file3.py", "id": 3}]
        if tool == "analyze_code":
            return {"summary": "Verified deterministic flow.", "status": "ok"}
        return {}

    shell = get_lobster_shell(executor=mock_executor)
    result = await shell.run_pipeline(pipeline)
    print(f"Result: {result}")
    assert result == "Verified deterministic flow."
    print("Scenario A: SUCCESS\n")

    # Scenario B: Attempt Sampling (Superposition)
    print("[Scenario B] Testing Attempt Sampling (Superposition)...")
    sampler = get_attempt_sampler(agent)
    
    # We need a task that isn't too heavy for the verification
    task = "Propose a unique 3-word name for a new AI project."
    
    # Run sampling
    sample_data = await sampler.sample_attempts(task, n_attempts=2, isolated=False) # isolated=False for faster test
    print(f"Sampled results count: {len(sample_data['all_results'])}")
    print(f"Collapsed Result: {sample_data['best_result']}")
    
    assert len(sample_data['all_results']) == 2
    assert "best_result" in sample_data
    print("Scenario B: SUCCESS\n")

    print("=== Phase 14 Verification: ALL SYSTEMS NOMINAL ===")

if __name__ == "__main__":
    asyncio.run(verify_phase_14())
