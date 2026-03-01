import asyncio
import aiohttp
import json

async def main():
    print("================================================================")
    print(" SWARM OS V2 - PHASE 6 EMERGENCE KICKOFF")
    print("================================================================\n")
    
    # Message to broadcast
    task_prompt = """
[CRITICAL DIRECTIVE - PHASE 5 COMPLETE]
We have successfully implemented Total Autonomy. The infrastructure is self-healing, tools can self-evolve, and our memory is globally federated. 

We are now moving to Phase 6: Emergence.

As the Architect and Lead Developer, please review our progress and define the roadmap for Phase 6. 
What does true emergence look like for this Swarm? What are the next technical leaps we must make to achieve it? 
Draft your thoughts and write them to a file named 'PHASE_6_EMERGENCE_ROADMAP.md'.
"""
    
    payload = {
        "message": task_prompt,
        "sender": "Human_Director"
    }

    print("Broadcasting directive to the Swarm collective...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post('http://127.0.0.1:8001/swarm/broadcast', json=payload, timeout=120) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("\n--- Swarm Response ---")
                    responses = data.get("responses", {})
                    
                    for role, response in responses.items():
                        print(f"\n[{role}]")
                        if isinstance(response, dict):
                            print(response.get("response", "No response text"))
                        else:
                            print(response)
                else:
                    print(f"Broadcast failed with status: {resp.status}")
                    print(await resp.text())
        except Exception as e:
            print(f"Error communicating with swarm: {e}")

if __name__ == "__main__":
    asyncio.run(main())
