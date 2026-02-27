import asyncio
import os
import torch
from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.artifact_pipeline import ArtifactPipeline
from swarm_v2.core.qic._state import QState, QOperator

async def run_entangled_pipeline():
    print("🚀 Initializing QIAE Entangled Pipeline Demo...")
    
    # 1. Setup Task and Infrastructure
    task = "Create a React 'Identity Card' component for a Swarm OS agent."
    pipeline = ArtifactPipeline()
    team = get_expert_team()
    
    # Selection of participants for the "Superposition"
    participants = [
        ("Vision", "UI/UX Designer"),
        ("Devo", "Lead Developer"),
        ("Archi", "Architect")
    ]
    
    # 2. Initialize the Task Wavefunction
    # We have 3 participants, so 3 dimensions in our QState
    task_state = QState(num_dimensions=len(participants))
    print(f"📊 Task Wavefunction Initialized: {task_state.probabilities().tolist()}")
    
    attempts = {}
    
    # 3. Parallel Execution (Superposition of Efforts)
    print("\n--- ENTERING SUPERPOSITION ---")
    
    async def agent_attempt(name, role, idx):
        agent = team.get(role)
        if not agent: return
        
        # Initialize internal agent state
        agent.initialize_qstate(num_dimensions=2) # Simple self-confidence state
        
        print(f"🧬 {name} ({role}) is generating their version...")
        prompt = (
            f"TASK: {task}\n"
            "Respond ONLY with the code for a single React component file 'IdentityCard.jsx'. "
            "Use Tailwind classes for styling. Make it look professional and 'Swarm OS' themed."
        )
        # We don't use full process_task to avoid hitting the real pipeline for this demo
        response = await agent._llm_generate(prompt)
        
        # Basic heuristic for "Quality" as Evidence Strength
        quality = 0.5
        if "framer-motion" in response.lower(): quality += 0.2
        if "prop-types" in response.lower() or "interface" in response.lower(): quality += 0.1
        if len(response) > 500: quality += 0.1
        
        attempts[idx] = {
            "name": name,
            "role": role,
            "content": response,
            "quality": quality
        }
    
    # Run all attempts in parallel
    await asyncio.gather(*(agent_attempt(name, role, i) for i, (name, role) in enumerate(participants)))
    
    # 4. Applying Operators based on Evidence
    print("\n--- APPLYING QUANTUM INTERFERENCE ---")
    for idx, data in attempts.items():
        # Apply a priority operator to the task state based on the measured quality
        op = QOperator.create_priority_op(len(participants), idx, weight=1.0 + data["quality"])
        task_state = task_state.apply_operator(op)
        print(f"✨ Applied {data['name']}'s Interference. New Probabilities: {task_state.probabilities().tolist()}")
    
    # 5. Measurement Gate (Collapse of the Wavefunction)
    print("\n--- MEASUREMENT GATE: COLLAPSING WAVEFUNCTION ---")
    winner_idx = task_state.resolve()
    winner = attempts[winner_idx]
    
    print(f"✅ State Collapsed! Selected Path: {winner['name']} ({winner['role']})")
    print(f"📄 Winning Content Length: {len(winner['content'])} bytes")
    
    # 6. Promotion to Artifacts
    filename = "IdentityCard_COLLAPSED.jsx"
    from swarm_v2.skills.file_skill import FileSkill
    file_skill = FileSkill()
    file_skill.write_file(filename, winner['content'])
    
    pipeline.register_artifact(filename, created_by=winner['name'])
    pipeline.approve(filename, reviewer="Measurement Gate", notes=f"Collapsed from superposition of {len(participants)} agents.")
    
    print(f"\n🏆 Final Artifact Saved: swarm_v2_artifacts/{filename}")

if __name__ == "__main__":
    asyncio.run(run_entangled_pipeline())
