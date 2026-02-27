#!/usr/bin/env python3
"""
Diagnostic script to check why agents aren't doing autonomous work.
"""
import asyncio
import aiohttp
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"

async def check_endpoint(session, endpoint, name):
    """Check if an endpoint responds."""
    try:
        async with session.get(f"{BASE_URL}{endpoint}", timeout=10) as resp:
            status = resp.status
            if status == 200:
                data = await resp.json()
                return {"name": name, "status": "up", "data": data}
            else:
                return {"name": name, "status": f"error {status}", "data": None}
    except Exception as e:
        return {"name": name, "status": f"error: {str(e)[:50]}", "data": None}

async def test_agent_response(session):
    """Test if Lead Developer agent responds to a simple task."""
    try:
        payload = {
            "role": "Lead Developer",
            "message": "Hello, are you active? Please respond with a short confirmation.",
            "sender": "diagnostic"
        }
        async with session.post(
            f"{BASE_URL}/swarm/chat", 
            json=payload,
            timeout=30
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {"status": "success", "response": data.get("response", "no response")}
            else:
                return {"status": f"error {resp.status}", "response": None}
    except Exception as e:
        return {"status": f"error: {str(e)[:50]}", "response": None}

async def main():
    print("=" * 60)
    print("DIAGNOSTIC: Checking Swarm V2 Autonomous Activity")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Check basic health
        endpoints = [
            ("/health", "Health"),
            ("/swarm/experts", "Experts"),
            ("/research/stats", "Research Stats"),
            ("/system/task-arbiter", "Task Arbiter"),
            ("/system/resources", "Resources"),
            ("/artifacts?grouped=false", "Artifacts"),
            ("/mesh/topology", "Mesh Topology"),
            ("/swarm/orchestrator/stats", "Orchestrator Stats"),
        ]
        
        print("\n1. Checking endpoint availability:")
        results = []
        for endpoint, name in endpoints:
            result = await check_endpoint(session, endpoint, name)
            results.append(result)
            print(f"  • {name}: {result['status']}")
        
        # Check proactive loop
        print("\n2. Checking autonomous systems:")
        
        # Check research daemon
        research_result = await check_endpoint(session, "/research/stats", "Research Daemon")
        if research_result['data']:
            print(f"  • Research Daemon: running={research_result['data'].get('is_running', False)}, "
                  f"findings={research_result['data'].get('total_findings', 0)}")
        
        # Check artifacts pipeline
        artifacts_result = await check_endpoint(session, "/artifacts?grouped=false", "Artifacts")
        if artifacts_result['data']:
            stats = artifacts_result['data'].get('stats', {})
            print(f"  • Artifacts: total={stats.get('total', 0)}, "
                  f"pending={stats.get('pending', 0)}, approved={stats.get('approved', 0)}")
        
        # Check orchestrator stats
        orch_result = await check_endpoint(session, "/swarm/orchestrator/stats", "Orchestrator")
        if orch_result['data']:
            print(f"  • Orchestrator: active_tasks={orch_result['data'].get('active_tasks', 0)}, "
                  f"proposals={orch_result['data'].get('triggered_proposals_count', 0)}")
        
        # Test agent activation
        print("\n3. Testing agent activation:")
        agent_test = await test_agent_response(session)
        print(f"  • Lead Developer response: {agent_test['status']}")
        if agent_test['response']:
            print(f"    Response: {agent_test['response'][:200]}")
        
        # Check proactive loop gaps
        print("\n4. Checking QIAE integration plan gaps:")
        try:
            with open("swarm_v2_artifacts/QIAE_INTEGRATION_PLAN_V2.md", "r") as f:
                content = f.read()
                import re
                gaps = re.findall(r'- \[ \] (.*)', content)
                print(f"  • Unchecked items in plan: {len(gaps)}")
                if gaps:
                    print("    Gaps found:")
                    for i, gap in enumerate(gaps[:3], 1):
                        print(f"      {i}. {gap[:60]}...")
        except Exception as e:
            print(f"  • Error reading plan: {e}")
        
        # Check for proactive loop log
        print("\n5. Checking proactive loop logs:")
        try:
            with open("swarm_v2_memory/orchestration.log", "r") as f:
                lines = f.readlines()[-5:]
                print(f"  • Last 5 log entries:")
                for line in lines:
                    print(f"    {line.strip()}")
        except FileNotFoundError:
            print("  • No orchestration.log found")
        except Exception as e:
            print(f"  • Error reading log: {e}")
        
        print("\n" + "=" * 60)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())