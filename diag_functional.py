
import asyncio
import sys
import os

# Set PYTHONPATH
sys.path.append(os.getcwd())

from swarm_v2.core.base_agent import BaseAgent, AgentPersona
from swarm_v2.skills.file_skill import FileSkill, WebSearchSkill

async def test():
    print("Initializing Archi functional test...")
    persona = AgentPersona(
        name="Archi",
        role="Architect",
        background="System design specialist",
        specialties=["System Design", "Scalability"]
    )
    skills = [FileSkill(), WebSearchSkill()]
    agent = BaseAgent(persona, skills=skills)
    
    from swarm_v2.core.llm_brain import build_system_prompt
    sys_prompt = build_system_prompt(
        persona.name, persona.role, persona.background, persona.specialties, agent.get_skill_names()
    )
    print(f"--- SYSTEM PROMPT (Length: {len(sys_prompt)}) ---\n{sys_prompt}\n--- END SYSTEM PROMPT ---")

    print("Requesting Archi to perform a scan and write results...")
    # This prompt strictly triggers the need for action
    prompt = "Archi, perform a system scan for security vulnerabilities and write the findings to 'security_audit.md'. Proceed immediately."
    
    try:
        result = await agent.process_task(prompt, sender="user")
        print(f"Result Type: {type(result)}")
        if isinstance(result, dict):
            print(f"Response Preview: {result.get('response')[:200]}...")
            print(f"Reasoning Trace Found: {bool(result.get('reasoning_trace'))}")
        else:
            print(f"Result: {result}")
            
        # Check if the file was actually 'intended' to be written
        if "WRITE_FILE: security_audit.md" in str(result):
            print("SUCCESS: Action tag EMITTED.")
        else:
            print("FAILURE: Action tag NOT emitted. Agent might be meta-talking.")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test())
