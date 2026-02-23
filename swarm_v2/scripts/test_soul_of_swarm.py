
import asyncio
from swarm_v2.core.telemetry import get_telemetry
from swarm_v2.core.proactive_loop import get_proactive_loop
from swarm_v2.skills.relationship_skill import RelationshipReasoningSkill

async def test_soul_of_swarm():
    print("🌌 Starting QIAE Phase 5: Soul of the Swarm Verification...")
    
    telemetry = get_telemetry()
    proactive = get_proactive_loop()
    relationship = RelationshipReasoningSkill()
    
    # 1. Test Neural Harmony
    print("\n[Test 1] Simulating Neural Check-in...")
    interaction = "Devo integrated the TRM Core with high precision, maintaining alignment with Shawn's focus on human impact."
    report = await relationship.perform_neural_checkin("Devo", interaction)
    print(f"Harmony Score: {report['harmony_score']}")
    print(f"Reflection: {relationship.generate_alignment_reflection()}")
    
    # 2. Test Proactive Gap Detection
    print("\n[Test 2] Scanning for Plan Gaps...")
    gaps = await proactive._scan_for_gaps()
    print(f"Detected Gaps: {gaps}")
    
    active_proposals = proactive.get_active_proposals()
    print(f"Active Proposals: {len(active_proposals)}")
    for p in active_proposals:
        print(f" - [{p['id']}] {p['gap']}")
        
    # 3. Test Soul Report (Telemetry Aggregation)
    print("\n[Test 3] Fetching Soul Report...")
    # Note: Telemetry has its own internal harmony monitor instance, 
    # but we can check if it returns valid structure
    soul_report = telemetry.get_soul_report()
    print(f"Global Harmony: {soul_report['harmony_index']}")
    print(f"Autonomous Proposals: {len(soul_report['autonomous_proposals'])}")
    
    print("\n🏁 Phase 5 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_soul_of_swarm())
