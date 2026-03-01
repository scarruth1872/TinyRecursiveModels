import asyncio
from swarm_v2.core.collaborative_reasoning import get_cra_engine

async def main():
    engine = get_cra_engine()
    
    # Test a complex reasoning problem
    problem = """
    We have a distributed multi-agent system where memory is federated across 5 nodes. 
    Node A and Node B both attempt to update the same memory vector simultaneously with conflicting information.
    Node A has higher priority, but Node B's information is more recent. 
    How should the swarm handle this conflict to ensure eventual consistency without losing data?
    """
    
    print(f"Initiating Collaborative Reasoning Amplification on problem:\n{problem}\n")
    
    result = await engine.amplify_reasoning(problem_statement=problem, required_roles=["Logic", "Archi", "Devo"])
    
    print("\n" + "="*50)
    print("FINAL AMPLIFIED SOLUTION:")
    print("="*50)
    print(result.get("amplified_solution", "Failed to generate solution."))
    
if __name__ == "__main__":
    asyncio.run(main())
