
import asyncio
import sys
import os

# Set PYTHONPATH
sys.path.append(os.getcwd())

from swarm_v2.core.base_agent import BaseAgent, AgentPersona

async def test():
    print("Initializing Archi test...")
    persona = AgentPersona(
        name="Archi",
        role="Architect",
        background="System design specialist",
        specialties=["System Design", "Scalability"]
    )
    agent = BaseAgent(persona)
    
    print("Simulating task processing...")
    try:
        # We use a simple task to avoid heavy LLM calls if possible, 
        # but we want to trigger the code path with asyncio.wait_for
        # Use a prompt that triggers reasoning (analytical keywords)
        result = await agent.process_task("Analyze the architecture. Start your response with <think>I am analyzing the neural stability</think>. Provide a brief summary.", sender="user")
        print(f"Result Type: {type(result)}")
        if isinstance(result, dict):
            print(f"Response: {result.get('response')[:100]}...")
            print(f"Reasoning Trace:\n{result.get('reasoning_trace')}")
        else:
            print(f"Result: {result}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test())
