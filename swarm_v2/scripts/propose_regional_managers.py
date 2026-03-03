import asyncio
import aiohttp
import json
import sys

async def propose_regional_managers():
    print("[Regional Managers] Formulating organizational restructure proposal...")
    
    proposal = (
        "### SWARM STRUCTURAL UPGRADE: MULTI-LLM REGIONAL MANAGERS\n\n"
        "To increase overall coherence, throughput, and analytical accuracy, "
        "we are restructuring the Swarm's 12 agents into 3 distinct Operational Departments. "
        "Each Department will be assigned a highly specialized Regional Manager (LLM backend).\n\n"
        "## The Departments & Regional Managers\n\n"
        "1. **Engineering & Logic (Managed by DeepSeek API)**\n"
        "   - *Agents*: Lead Developer (Devo), Architect (Archi), Reasoning Engine (Logic), QA Engineer (Verify)\n"
        "   - *Mandate*: Complex systems design, recursive mathematical proofs, and secure code architecture.\n\n"
        "2. **Product & Creative (Managed by Google Gemini SDK)**\n"
        "   - *Agents*: UI/UX Designer (Vision), Data Analyst (Pulse), Technical Writer (Scribe), Researcher (Seeker)\n"
        "   - *Mandate*: Rapid aesthetic prototyping, data visualization, documentation, and external knowledge synthesis.\n\n"
        "3. **Operations & Compliance (Managed by OpenRouter / Claude 3.5 Sonnet)**\n"
        "   - *Agents*: Security Auditor (Shield), DevOps Engineer (Flow), Swarm Manager (Orchestra), Integration Specialist (Bridge)\n"
        "   - *Mandate*: Uncompromising security auditing, autonomous deployment flow, constraint adherence, and API bridging.\n\n"
        "**Task for Lead Developer & Swarm Manager**:\n"
        "Please review this departmental restructure. Acknowledge these new Regional Manager assignments, "
        "and draft an initial internal memo on how your specific department plans to leverage its new "
        "LLM manager's specific strengths to solve our current Kanban backlog."
    )

    print("[Regional Managers] Injecting proposal into the Swarm Mailbox via API...")
    url = "http://localhost:8001/mailbox/send"
    
    async with aiohttp.ClientSession() as session:
        # Send to Devo (Lead Developer)
        payload_devo = {
            "from_agent": "System (Admin)",
            "to_agent": "Lead Developer",
            "body": proposal,
            "priority": "critical"
        }
        async with session.post(url, json=payload_devo) as resp:
            if resp.status == 200:
                print("✔ Proposal delivered to Lead Developer (DeepSeek).")
            else:
                err = await resp.text()
                print(f"❌ Failed to reach Lead Developer: {err}")

        # Send to Orchestra (Swarm Manager)
        payload_orch = {
            "from_agent": "System (Admin)",
            "to_agent": "Swarm Manager",
            "body": proposal,
            "priority": "critical"
        }
        async with session.post(url, json=payload_orch) as resp:
            if resp.status == 200:
                print("✔ Proposal delivered to Swarm Manager (OpenRouter).")
            else:
                err = await resp.text()
                print(f"❌ Failed to reach Swarm Manager: {err}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(propose_regional_managers())
