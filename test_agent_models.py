
import asyncio
from swarm_v2.experts.registry import get_expert_team

async def test_models():
    team = get_expert_team()
    
    # 1. Test Architect (should use gemma3:4b)
    archi = team["Architect"]
    print(f"Testing Architect ({archi.persona.name}) with model: {archi.persona.model}")
    resp1 = await archi.process_task("Explain the core benefit of a microservices architecture in one sentence.")
    print(f"Response: {resp1}")
    print("-" * 50)
    
    # 2. Test a Worker (should use gemma3:270m)
    devo = team["Lead Developer"]
    print(f"Testing Lead Developer ({devo.persona.name}) with model: {devo.persona.model}")
    resp2 = await devo.process_task("Write a hello world function in Python.")
    print(f"Response: {resp2}")
    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_models())
