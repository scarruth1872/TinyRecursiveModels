
"""Nexus Self-Build: Have each agent generate REAL artifacts with LLM-powered content."""
import httpx
import time

API = "http://localhost:8001"
client = httpx.Client(timeout=300)

print("=" * 60)
print("  NEXUS SELF-BUILD: LLM-Powered Agent Pipeline")
print("=" * 60)

# Each agent gets a specific, concrete task that uses their skills
agent_tasks = [
    ("Architect", "write file nexus_architecture.py with a complete Python module that defines the Nexus microservices architecture including classes for AgentManager, TaskRouter, and MemoryStore services with message queue integration"),

    ("Lead Developer", "write file agent_manager.py with a complete FastAPI microservice for managing agent lifecycles including endpoints for registering agents, listing agents, health checks, and sending tasks to agents"),

    ("Lead Developer", "write file task_router.py with a Python module implementing a task routing engine that analyzes incoming tasks, matches them to the best agent based on skills and availability, and distributes work"),

    ("DevOps Engineer", "write file docker_compose.yml with a complete Docker Compose configuration for running the Nexus platform including services for the API gateway, RabbitMQ message broker, Redis cache, and three microservices"),

    ("DevOps Engineer", "write file deploy.sh with a comprehensive deployment script that builds Docker images, runs health checks, sets up networking, and deploys the Nexus platform"),

    ("Security Auditor", "write file security_audit.py with a Python security scanning module that checks for common vulnerabilities including SQL injection patterns, exposed secrets, insecure configurations, and CORS issues"),

    ("QA Engineer", "write file test_nexus.py with a comprehensive pytest test suite for the Nexus platform including tests for agent registration, task routing, message queue integration, and API endpoint validation"),

    ("Technical Writer", "generate readme for Nexus Microservices Platform"),
]

for i, (role, task) in enumerate(agent_tasks, 1):
    print(f"\n[{i}/{len(agent_tasks)}] {role}: {task[:70]}...")
    start = time.time()
    try:
        r = client.post(f"{API}/swarm/chat", json={"role": role, "message": task})
        data = r.json()
        elapsed = time.time() - start
        resp = data["response"]
        print(f"  [{elapsed:.1f}s] {resp[:250]}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Final check
print("\n" + "=" * 60)
print("  ARTIFACTS CREATED")
print("=" * 60)

import os
artifact_dir = "swarm_v2_artifacts"
for f in sorted(os.listdir(artifact_dir)):
    size = os.path.getsize(os.path.join(artifact_dir, f))
    print(f"  {f:30s}  {size:6d} bytes")

print("\n" + "=" * 60)
print("  MEMORY STATUS")
print("=" * 60)
r = client.get(f"{API}/swarm/experts")
for exp in r.json():
    mem = exp.get("memory", {})
    tc = mem.get("tasks_completed", 0)
    if tc > 0:
        print(f"  {exp['name']:12s} | Tasks: {tc} | ST: {mem.get('short_term_count',0)} | LT: {mem.get('long_term_count',0)}")

print("\nDone!")
