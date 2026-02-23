
import asyncio
from swarm_v2.core.deterministic_forge import get_deterministic_forge
from swarm_v2.skills.learning_engine import get_learning_engine

async def test_deterministic_forge():
    print("🛠️ Starting Deterministic Forge Verification...")
    forge = get_deterministic_forge()
    engine = get_learning_engine()
    
    # 1. Create a mock skill to synthesize
    skill_name = "CloudStorage"
    await engine.learn_from_text(
        name=skill_name,
        content="Service for uploading and downloading files to S3. Endpoint: /upload (POST), /download (GET).",
        source="manual_test"
    )
    
    # 2. Run Verified Synthesis
    print(f"\n[Test 1] Synthesizing '{skill_name}' with TRM Audit...")
    tool = await forge.synthesize_verified_tool(skill_name)
    
    if tool:
        print(f"Result: {tool.status.upper()}")
        print(f"Audit Stats: {forge.get_audit_stats()}")
    else:
        print("Result: Failed - Skill not found")

    print("\n🏁 Deterministic Forge Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_deterministic_forge())
