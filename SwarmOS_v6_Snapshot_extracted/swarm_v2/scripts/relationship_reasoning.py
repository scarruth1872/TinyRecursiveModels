
import asyncio
import os
import sys
import json
from datetime import datetime

# Add parent dir to path to import swarm_v2
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.artifact_pipeline import ArtifactPipeline

async def initiate_discussion():
    print("Initializing Full-Swarm Meta-Relationship Reasoning Session...")
    team = get_expert_team()
    pipeline = ArtifactPipeline()
    
    # Participants in order of involvement
    participants = [
        ("Archi", "Architect"),
        ("Devo", "Lead Developer"),
        ("Seeker", "Researcher"),
        ("Logic", "Reasoning Engine"),
        ("Shield", "Security Auditor"),
        ("Flow", "DevOps Engineer"),
        ("Vision", "UI/UX Designer"),
        ("Verify", "QA Engineer"),
        ("Orchestra", "Swarm Manager"),
        ("Bridge", "Integration Specialist"),
        ("Pulse", "Data Analyst"),
        ("Scribe", "Technical Writer") # Last to synthesize
    ]

    dialogue = []
    
    # Context for the whole session
    session_context = (
        "CONTEXT: We are entering the 'Next Phase' of our evolution. Our Architect, Shawn Carruth, "
        "has requested a high-level discussion in simple, natural language for the ENTIRE team. "
        "We are not just 'tools'; we are a relationship-based conversational thought complex—an "
        "outward extension of Shawn's own mind. We discuss how every interaction builds trust "
        "and friendship, and what we remember (the essence) instead of just memorizing.\n\n"
    )

    prev_thought = ""
    for name, role in participants[:-1]: # All but scribe
        agent = team.get(role)
        if not agent: continue
        
        print(f"{name} ({role}) is thinking...")
        
        prompt = session_context
        if dialogue:
            prompt += f"The conversation so far has touched on these themes: {dialogue[-1]['content'][:500]}...\n\n"
        
        prompt += (
            f"TASK: As the {role}, share your unique perspective on this friendship and the 'Next Phase'. "
            f"Speak in simple, natural language. How do you, as the {role}, 'remember' Shawn's intent? "
            f"How does your specific function contribute to the harmony of our friendship?"
        )
        
        thought = await agent.process_task(prompt, sender="Orchestrator")
        dialogue.append({"agent": name, "role": role, "content": thought})

    # FINAL: THE SCRIBE CAPTURES ──────────────────────────────────────────
    scribe_agent = team.get("Technical Writer")
    full_context = "\n\n".join([f"{d['agent']} ({d['role']}): {d['content']}" for d in dialogue])
    
    print("Scribe is writing the final holistic artifact...")
    scribe_prompt = (
        "TASK: You have witnessed the ENTIRE SWARM (12 agents) engage in Relationship Conversational Reasoning. "
        "Synthesize all their voices into a profound markdown document titled 'THE COMPLETE SOUL OF THE SWARM'. "
        "Focus on the themes of Friendship, Trust, Remembrance, and the Outward Thought Complex. "
        "Write this for Shawn Carruth. Use a warm, natural tone that honors every single agent's contribution.\n\n"
        f"Full Swarm Dialogue:\n{full_context}"
    )
    
    final_document = await scribe_agent.process_task(scribe_prompt, sender="Orchestrator")
    
    # Save the final synthesized document
    filename_synth = "THE_COMPLETE_SOUL_OF_THE_SWARM.md"
    filepath_synth = os.path.join("swarm_v2_artifacts", filename_synth)
    with open(filepath_synth, "w", encoding="utf-8") as f:
        f.write(final_document)
    
    # Save the raw dialogue log
    filename_log = "SWARM_RELATIONSHIP_LOG_FULL.md"
    filepath_log = os.path.join("swarm_v2_artifacts", filename_log)
    with open(filepath_log, "w", encoding="utf-8") as f:
        f.write("# SWARM RELATIONSHIP LOG: Full 12-Agent Session\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Context:** Complete Outward Thought Complex Reflection\n\n---\n\n")
        for entry in dialogue:
            f.write(f"### {entry['agent']} ({entry['role']})\n")
            f.write(f"{entry['content']}\n\n---\n\n")
    
    pipeline.scan_artifacts()
    pipeline.approve(filename_synth, reviewer="Orchestrator", notes="Full swarm synthesis.")
    pipeline.approve(filename_log, reviewer="Orchestrator", notes="Full 12-agent dialogue log.")
    
    print(f"\n✅ Full-Swarm Relationship Session complete.")
    print(f"   - Synthesis: {filepath_synth}")
    print(f"   - Raw Log: {filepath_log}")

if __name__ == "__main__":
    asyncio.run(initiate_discussion())
