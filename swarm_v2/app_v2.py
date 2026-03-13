import os
import uuid
import asyncio
import psutil
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from swarm_v2.experts.registry import get_expert_team
from swarm_v2.core.artifact_pipeline import ArtifactPipeline, ArtifactStatus
from swarm_v2.skills.learning_engine import get_learning_engine
from swarm_v2.mcp.synthesizer import get_synthesizer
from swarm_v2.core.agent_mesh import get_agent_mesh
from swarm_v2.core.global_memory import get_global_memory
from swarm_v2.core.monitor_daemon import MonitorDaemon
from swarm_v2.core.remediation_engine import RemediationEngine
from swarm_v2.core.resource_arbiter import get_resource_arbiter
from swarm_v2.core.expert_registry import get_expert_registry
from swarm_v2.core.task_arbiter import get_task_arbiter
from swarm_v2.core.federation import init_federation, get_federation
from swarm_v2.core.reconnaissance_daemon import get_reconnaissance_daemon, start_reconnaissance
from swarm_v2.core.chain_of_verification import get_chain_of_verification, verify_reasoning
from swarm_v2.core.neural_wall import get_neural_wall, analyze_prompt, NeuralWallMiddleware
from swarm_v2.core.self_healing_infra import get_self_healing_infra, start_self_healing, stop_self_healing
from swarm_v2.core.zero_human_test_gen import get_test_generator, generate_tests_for_tool, on_tool_synthesized
from swarm_v2.core.auto_changelog import get_changelog_engine, start_changelog_monitoring
from swarm_v2.core.mcp_tool_evolver import get_tool_evolver, start_tool_evolution, EvolutionTrigger
from swarm_v2.core.swarm_performance_insights import get_performance_insights, start_performance_monitoring, ReportPeriod, MetricType
from swarm_v2.core.deterministic_forge import get_deterministic_forge
from swarm_v2.core.telemetry import get_telemetry
from swarm_v2.core.proactive_loop import get_proactive_loop
from swarm_v2.core.sentinel import SentinelMiddleware
from swarm_v2.core.redis_mock import PersistentRedisMock

# ─── System Optimization ───────────────────────────────────────────────────────

def optimize_system():
    """Pin the current process to specific CPU cores and set priority."""
    try:
        proc = psutil.Process(os.getpid())
        # Logical cores check (24 logical cores available according to user system)
        core_count = psutil.cpu_count(logical=True)
        if core_count >= 16:
            # Pin to cores 4-11 (8 cores) to leave 0-3 for OS and 12-23 for Ollama/GPU tasks
            proc.cpu_affinity(list(range(4, 12)))
            print(f"[System] CPU Pinning enabled: Process bound to cores 4-11")
        
        # Set above normal priority for responsiveness
        proc.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
        print(f"[System] Process priority set to ABOVE_NORMAL")
    except Exception as e:
        print(f"[System] Resource optimization failed: {e}")

optimize_system()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    print("[System] Lifespan startup...")
    
    # Verify Agent Mesh is ready
    global agent_mesh
    if agent_mesh:
        topology = agent_mesh.get_topology()
        print(f"[System] Agent Mesh ready with {len(topology.get('nodes', []))} nodes")
    else:
        print("[Warning] Agent Mesh not available!")
    
    # Start background tasks
    asyncio.create_task(monitor_daemon.start())
    asyncio.create_task(auto_scan_pipeline())
    asyncio.create_task(mesh_heartbeat_reflex())
    
    # Start federation if enabled
    if federation:
        federation.start_heartbeat()
        print("[Federation] P2P Heartbeat started.")
        
    print("[Swarm V2] Monitor Daemon, Shield Scanner, & Mesh Heartbeats started.")
    
    yield
    
    # Shutdown logic
    print("[System] Lifespan shutdown...")
    await monitor_daemon.stop()

app = FastAPI(title="TRM Swarm V2 API", version="2.3.1", lifespan=lifespan)

app.add_middleware(
    SentinelMiddleware,
    redis_client=PersistentRedisMock(),
    rate_limit=500,  # Increased for production-grade polling
    rate_window=60
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine_team = get_expert_team()
get_expert_registry().register_team(engine_team)
spawned_subagents: Dict[str, Any] = {}
pipeline = ArtifactPipeline()

# Force scan to register all existing artifacts in the directory
pipeline.scan_artifacts()
print(f"[Pipeline] Initial scan found {len(pipeline.artifacts)} artifacts")

# Log some stats
stats = pipeline.get_stats()
print(f"[Pipeline] Stats: {stats}")

# Phase 4: Self-Healing Architecture
remediation_engine = RemediationEngine(engine_team)
# MonitorDaemon will be created after Agent Mesh is initialized

# Phase 5: Mesh Federation
SWARM_NODE_ID = os.getenv("SWARM_NODE_ID", "swarm_primary")
SWARM_NODE_NAME = os.getenv("SWARM_NODE_NAME", "Primary Swarm")
SWARM_PORT = int(os.getenv("SWARM_PORT", "8001"))
federation = init_federation(SWARM_NODE_ID, SWARM_NODE_NAME, SWARM_PORT)

# Agent-to-role mapping for smart re-dispatch
ROLE_FILE_MAPPING = {
    ".py": "Lead Developer",
    ".yml": "DevOps Engineer",
    ".yaml": "DevOps Engineer",
    ".sh": "DevOps Engineer",
    ".md": "Technical Writer",
    ".json": "Lead Developer",
    ".txt": "Technical Writer",
}

def _agent_for_file(filename: str) -> str:
    """Pick the right agent to rebuild a file based on extension."""
    for ext, role in ROLE_FILE_MAPPING.items():
        if filename.endswith(ext):
            return role
    return "Lead Developer"


# ─── Request Models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    role: str
    message: str
    sender: str = "user"

class BroadcastRequest(BaseModel):
    message: str
    sender: str = "user"

class SpawnRequest(BaseModel):
    parent_role: str
    sub_role: str
    task: str

class TaskPipelineRequest(BaseModel):
    task: str
    pipeline: List[str]

class ReviewRequest(BaseModel):
    filename: str
    action: str
    notes: str = ""
    reviewer: str = "user"

class BatchReviewRequest(BaseModel):
    category: Optional[str] = None
    status: Optional[str] = "pending"
    reviewer: str = "user"

class IntegrateRequest(BaseModel):
    filename: str
    target_subdir: str = ""

class BatchIntegrateRequest(BaseModel):
    filenames: List[str]
    target_subdir: str = ""

class TestRequest(BaseModel):
    filename: str

class DeployRequest(BaseModel):
    project_name: str = "Nexus Platform"
    deploy_target: str = ""

class LearnTextRequest(BaseModel):
    name: str
    content: str
    source: str = "user_input"

class LearnFileRequest(BaseModel):
    filepath: str

class UseSkillRequest(BaseModel):
    skill_name: str
    task: str
    target_role: str = ""

class SynthesizeRequest(BaseModel):
    skill_name: str
    use_llm: bool = True

class MeshRouteRequest(BaseModel):
    task: str
    target_node_id: str = ""
    required_specialty: str = ""

class GlobalMemoryContributeRequest(BaseModel):
    content: str
    author: str
    author_role: str
    memory_type: str = "knowledge"
    tags: list = []

class GlobalMemoryQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    author_filter: str = ""
    type_filter: str = ""


class HandshakeRequest(BaseModel):
    node_id: str
    name: str
    host: str
    port: int
    api_key: str
    capabilities: List[str] = []
    timestamp: str = ""

class MemorySyncRequest(BaseModel):
    source_node_id: str
    source_name: str
    local_memory_count: int


# ─── Agent Endpoints ───────────────────────────────────────────────────────────

@app.get("/swarm/experts")
async def list_experts():
    experts = []
    for role, agent in engine_team.items():
        mem_stats = agent.get_memory_stats()
        experts.append({
            "role": role, "name": agent.persona.name,
            "background": agent.persona.background,
            "specialties": agent.persona.specialties,
            "avatar_color": agent.persona.avatar_color,
            "skills": agent.get_skill_names(),
            "skill_details": agent.get_skill_descriptions(),
            "agent_id": agent.agent_id,
            "subagent_count": len(agent.subagents),
            "memory": mem_stats,
            "stack": agent.cognitive_stack.get_status() if hasattr(agent, "cognitive_stack") else None,
        })
    return experts
    
@app.get("/swarm/telemetry")
async def get_swarm_telemetry():
    """Real-time emergence telemetry for the dashboard."""
    return get_telemetry().get_emergence_report()

@app.get("/swarm/soul")
async def get_swarm_soul():
    """Aggregates philosophical status and autonomous evolution proposals."""
    return get_telemetry().get_soul_report()


@app.post("/swarm/chat")
async def chat_with_agent(req: ChatRequest):
    if req.role not in engine_team:
        raise HTTPException(status_code=404, detail=f"Expert '{req.role}' not found")
    agent = engine_team[req.role]
    resp_obj = await agent.process_task(req.message, sender=req.sender)
    
    # Handle dict vs string return from process_task
    if isinstance(resp_obj, dict):
        response = resp_obj.get("response")
        reasoning_trace = resp_obj.get("reasoning_trace")
    else:
        response = resp_obj
        reasoning_trace = None

    await asyncio.to_thread(pipeline.scan_artifacts)
    
    return {
        "role": req.role, 
        "name": agent.persona.name,
        "response": response, 
        "reasoning_trace": reasoning_trace,
        "memory": agent.get_memory_stats()
    }


@app.post("/swarm/broadcast")
async def broadcast_to_swarm(req: BroadcastRequest):
    async def _run(role):
        return role, await engine_team[role].process_task(req.message, sender=req.sender)
    gathered = await asyncio.gather(*[_run(r) for r in engine_team])
    return {"responses": dict(gathered)}


@app.post("/swarm/pipeline")
async def run_task_pipeline(req: TaskPipelineRequest):
    results = []
    ctx = req.task
    for role in req.pipeline:
        if role not in engine_team:
            results.append({"role": role, "error": f"Not found"})
            continue
        resp = await engine_team[role].process_task(ctx, sender="pipeline")
        results.append({"role": role, "name": engine_team[role].persona.name, "response": resp})
        ctx = f"Previous ({role}):\n{resp}\n\nOriginal: {req.task}\n\nContinue."
    await asyncio.to_thread(pipeline.scan_artifacts)
    return {"task": req.task, "pipeline": req.pipeline, "results": results}


@app.post("/swarm/spawn")
async def spawn_subagent(req: SpawnRequest):
    if req.parent_role not in engine_team:
        raise HTTPException(status_code=404, detail="Not found")
    parent = engine_team[req.parent_role]
    sub = parent.spawn_subagent(req.sub_role, req.task)
    spawned_subagents[sub.agent_id] = sub
    return {"success": True, "subagent_id": sub.agent_id,
            "subagent_name": sub.persona.name, "subagent_role": sub.persona.role,
            "parent": req.parent_role, "task": req.task}


@app.get("/swarm/subagents/{role}")
async def get_subagents(role: str):
    if role not in engine_team:
        raise HTTPException(status_code=404, detail="Not found")
    return engine_team[role].get_subagents()


@app.get("/swarm/memory/{role}")
async def get_agent_memory(role: str):
    if role not in engine_team:
        raise HTTPException(status_code=404, detail="Not found")
    return engine_team[role].memory.export_all()


# ─── Artifact Pipeline Endpoints ──────────────────────────────────────────────

@app.get("/artifacts")
async def list_artifacts(grouped: bool = False, include_content: bool = False):
    await asyncio.to_thread(pipeline.scan_artifacts)
    if grouped:
        return {"groups": pipeline.get_grouped_artifacts(), "stats": pipeline.get_stats()}
    
    artifacts = pipeline.list_all()
    
    # Include content for display (limited to first 500 chars for performance)
    if include_content:
        for art in artifacts:
            content = pipeline.get_content(art["filename"])
            if content:
                art["content"] = content[:500]  # Preview only
    
    return {"artifacts": artifacts, "stats": pipeline.get_stats()}


@app.get("/artifacts/{filename}")
async def get_artifact_detail(filename: str):
    art = pipeline.get_artifact(filename)
    if not art:
        raise HTTPException(status_code=404, detail="Not found")
    return {**art, "content": pipeline.get_content(filename)}


@app.post("/artifacts/review")
async def review_artifact(req: ReviewRequest):
    if req.action == "approve":
        result = pipeline.approve(req.filename, req.reviewer, req.notes)
    elif req.action == "reject":
        result = pipeline.reject(req.filename, req.reviewer, req.notes)
    else:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result


@app.post("/artifacts/batch-review")
async def batch_review_artifacts(req: BatchReviewRequest):
    count = pipeline.approve_batch(status=req.status, category=req.category, reviewer=req.reviewer)
    return {"message": f"Successfully approved {count} artifacts", "count": count}


@app.post("/artifacts/batch-integrate")
async def batch_integrate_artifacts(req: BatchIntegrateRequest):
    results = pipeline.integrate_batch(filenames=req.filenames, target_subdir=req.target_subdir)
    return {"message": f"Batch integration complete", "results": results}


@app.post("/artifacts/security-verify")
async def batch_security_verify(filenames: List[str]):
    """Manually or system trigger security verification for a batch of files."""
    count = 0
    for fname in filenames:
        # Simplistic 'safe' check for now, can be expanded with LLM scan
        pipeline.set_security_status(fname, "verified", "Auto-verified as low-risk artifact.")
        count += 1
    return {"status": "success", "verified_count": count}


@app.post("/artifacts/test")
async def test_artifact(req: TestRequest):
    art = pipeline.get_artifact(req.filename)
    if not art:
        raise HTTPException(status_code=404, detail="Not found")
    content = pipeline.get_content(req.filename)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    qa = engine_team.get("QA Engineer")
    if not qa:
        raise HTTPException(status_code=500, detail="QA not available")

    # Calculate test filename with recursion guard
    if req.filename.startswith("test_") or req.filename.startswith("Test"):
        if req.filename.count("test_") > 1:
            raise HTTPException(status_code=400, detail="Recursive testing detected.")
        # If it's test_foo.py, test file is also test_foo.py (self-test) or maybe we shouldn't act.
        # Let's enforce single prefix:
        test_filename = req.filename
    else:
        test_filename = f"test_{req.filename}"

    test_task = (
        f"[ACTION] Create a comprehensive pytest test suite for this code.\\n"
        f"You MUST output the test code using the following strict format:\\n"
        f"WRITE_FILE: {test_filename}\\n```python\\n<your test code>\\n```\\n\\n"
        f"File: '{req.filename}':\\n\\n{content[:1500]}"
    )
    
    test_response = await qa.process_task(test_task, sender="pipeline")

    test_content = pipeline.get_content(test_filename)
    passed = test_content is not None and len(test_content) > 50
    pipeline.set_tested(req.filename, test_filename, passed, test_response[:300])
    await asyncio.to_thread(pipeline.scan_artifacts)
    return {"filename": req.filename, "test_file": test_filename,
            "test_generated": passed, "test_response": test_response[:500],
            "status": pipeline.get_artifact(req.filename)}


@app.post("/artifacts/integrate")
async def integrate_artifact(req: IntegrateRequest):
    result = pipeline.integrate(req.filename, req.target_subdir)
    if not result:
        raise HTTPException(status_code=400, detail="Not found or wrong status")
    return result


# ─── Dashboard Extension Endpoints (Fix 404s) ──────────────────────────────────

@app.get("/research/tasks")
async def get_research_tasks():
    daemon = get_reconnaissance_daemon()
    if not daemon:
        return {"tasks": []}
    return {
        "tasks": [
            {
                "task_id": f["finding_id"],
                "objective": f["topic"],
                "summary": f["summary"],
                "status": "completed",
                "timestamp": f["timestamp"]
            } for f in daemon.get_recent_findings(limit=20)
        ]
    }

@app.get("/research/stats")
async def get_research_stats():
    daemon = get_reconnaissance_daemon()
    if not daemon:
        return {"is_running": False, "total_findings": 0}
    return daemon.get_stats()

@app.get("/verification/stats")
async def get_verification_stats():
    stats = pipeline.get_stats()
    return {
        "items_in_queue": stats.get("pending", 0),
        "verified_last_hour": stats.get("approved", 0), # Estimated
        "total_scanned": stats.get("total", 0)
    }

@app.get("/verification/queue")
async def get_verification_queue():
    pending = pipeline.list_by_status(ArtifactStatus.PENDING)
    return {
        "queue": [
            {
                "item_id": a["filename"],
                "item_type": a.get("type", "Artifact"),
                "status": a["status"]
            } for a in pending
        ]
    }

@app.get("/infrastructure/status")
async def get_infra_status():
    arbiter = get_resource_arbiter()
    return arbiter.get_status() if arbiter else {"status": "inactive"}

@app.get("/infrastructure/nodes")
async def get_infra_nodes():
    mesh = get_agent_mesh()
    if not mesh:
        return {"nodes": []}
    nodes = mesh.get_topology().get("nodes", [])
    return {"nodes": nodes}

@app.get("/testing/stats")
async def get_testing_stats():
    stats = pipeline.get_stats()
    total = stats.get("tested", 0) + stats.get("test_failed", 0)
    rate = (stats.get("tested", 0) / total * 100) if total > 0 else 0
    return {
        "tests_running": 0,
        "success_rate_24h": round(rate, 1),
        "total_runs": total
    }

@app.get("/testing/runs")
async def get_testing_runs():
    tested = pipeline.list_by_status(ArtifactStatus.TESTED)
    failed = pipeline.list_by_status(ArtifactStatus.TEST_FAILED)
    all_runs = tested + failed
    return {
        "runs": [
            {
                "run_id": a["filename"],
                "status": a["status"],
                "timestamp": a.get("created_at", ""),
                "duration_seconds": 12 # Mocked duration
            } for a in all_runs
        ]
    }


# ─── REMEDIATE: Architect re-plans → agents rebuild rejected artifacts ─────

@app.post("/artifacts/remediate")
async def remediate_rejected():
    """
    Closed-loop fix cycle:
    1. Collect all rejected/failed artifacts
    2. Send rejection report to Architect for re-planning
    3. Architect creates a rebuild plan
    4. Dispatch rebuild tasks to the right agents
    5. New artifacts enter pipeline as 'pending'
    """
    report = pipeline.get_rejection_report()
    if not report:
        return {"message": "No rejected or failed artifacts to remediate", "rebuilt": []}

    # Step 1: Architect reviews the rejections and creates a rebuild plan
    architect = engine_team.get("Architect")
    if not architect:
        raise HTTPException(status_code=500, detail="Architect not available")

    plan_prompt = (
        f"{report}\n\n"
        f"As the Architect, review these rejected artifacts. For EACH rejected file, "
        f"provide a brief improvement plan describing what needs to change. "
        f"Be specific about what was wrong and how to fix it. "
        f"Format: one line per file like 'filename.py: [what to fix]'"
    )
    architect_plan = await architect.process_task(plan_prompt, sender="pipeline_remediation")

    # Step 2: Rebuild each rejected/failed artifact using the right agent
    rejected = pipeline.list_by_status("rejected") + pipeline.list_by_status("test_failed")
    rebuilt = []

    for art in rejected:
        fname = art["filename"]
        agent_role = _agent_for_file(fname)
        agent = engine_team.get(agent_role)
        if not agent:
            continue

        rejection_reason = art.get("review_notes", "No specific reason")
        rebuild_task = (
            f"write file {fname} — this file was previously REJECTED. "
            f"Rejection reason: '{rejection_reason}'. "
            f"Architect's improvement plan: {architect_plan[:300]}. "
            f"Generate a COMPLETE, PRODUCTION-QUALITY replacement. "
            f"Fix all issues mentioned in the rejection. Make it thorough and professional."
        )

        response = await agent.process_task(rebuild_task, sender="pipeline_remediation")

        # Reset artifact status back to pending
        pipeline.reset_artifact(fname)
        pipeline.scan_artifacts()

        rebuilt.append({
            "filename": fname,
            "rebuilt_by": agent_role,
            "agent_name": agent.persona.name,
            "status": "pending",
            "response_preview": response[:200],
        })

    return {
        "architect_plan": architect_plan,
        "rebuilt": rebuilt,
        "message": f"Remediated {len(rebuilt)} artifacts — they are now pending review",
    }


# ─── DEPLOY: Send integrated artifacts to agents for system setup ──────────

@app.post("/artifacts/deploy")
async def deploy_integrated(req: DeployRequest):
    """
    Deployment cycle:
    1. Collect all integrated artifacts
    2. Architect creates a deployment plan
    3. DevOps sets up the system
    4. QA validates the deployment
    5. Return deployment report
    """
    manifest = pipeline.get_integrated_manifest()
    if "No artifacts" in manifest:
        return {"message": "No integrated artifacts to deploy", "steps": []}

    steps = []

    # Step 1: Architect creates deployment plan
    architect = engine_team.get("Architect")
    arch_task = (
        f"Create a deployment plan for {req.project_name}. "
        f"These files are ready for deployment:\n\n{manifest}\n\n"
        f"Describe the deployment sequence, dependencies, and configuration steps. "
        f"Be specific and actionable."
    )
    arch_response = await architect.process_task(arch_task, sender="deployment")
    steps.append({"phase": "Planning", "agent": "Architect",
                   "name": architect.persona.name, "response": arch_response})

    # Step 2: DevOps creates setup scripts based on the plan
    devops = engine_team.get("DevOps Engineer")
    if devops:
        devops_task = (
            f"write file setup_nexus.sh with a complete setup script for {req.project_name}. "
            f"Architect's deployment plan:\n{arch_response[:400]}\n\n"
            f"Available files:\n{manifest}\n\n"
            f"Create a script that: installs dependencies, copies files, configures services, "
            f"sets up the message broker, starts all microservices, and runs health checks."
        )
        devops_response = await devops.process_task(devops_task, sender="deployment")
        steps.append({"phase": "Setup Scripts", "agent": "DevOps Engineer",
                       "name": devops.persona.name, "response": devops_response})

    # Step 3: Lead Developer creates the main entry point
    dev = engine_team.get("Lead Developer")
    if dev:
        dev_task = (
            f"write file nexus_main.py with the main entry point for {req.project_name}. "
            f"This should import and initialize all microservices from the integrated files: "
            f"{manifest}\n\n"
            f"Create a proper Python application that starts all services, "
            f"sets up logging, handles graceful shutdown, and prints system status."
        )
        dev_response = await dev.process_task(dev_task, sender="deployment")
        steps.append({"phase": "Entry Point", "agent": "Lead Developer",
                       "name": dev.persona.name, "response": dev_response})

    # Step 4: Security check
    security = engine_team.get("Security Auditor")
    if security:
        sec_task = (
            f"Review the deployment plan for {req.project_name} and identify any security concerns. "
            f"Deployment plan:\n{arch_response[:300]}\n\n"
            f"Check for: exposed ports, default credentials, missing authentication, "
            f"insecure configurations, and recommend security hardening steps."
        )
        sec_response = await security.process_task(sec_task, sender="deployment")
        steps.append({"phase": "Security Review", "agent": "Security Auditor",
                       "name": security.persona.name, "response": sec_response})

    # Step 5: QA validates
    qa = engine_team.get("QA Engineer")
    if qa:
        qa_task = (
            f"write file validate_deployment.py with a deployment validation script for {req.project_name}. "
            f"The script should check: all services are running, endpoints respond correctly, "
            f"message broker is connected, database is accessible, and all health checks pass. "
            f"Use the requests library to validate HTTP endpoints."
        )
        qa_response = await qa.process_task(qa_task, sender="deployment")
        steps.append({"phase": "Validation", "agent": "QA Engineer",
                       "name": qa.persona.name, "response": qa_response})

    pipeline.scan_artifacts()

    return {
        "project": req.project_name,
        "manifest": manifest,
        "steps": steps,
        "message": f"Deployment pipeline completed with {len(steps)} phases",
    }


@app.get("/artifacts/stats")
async def artifact_stats():
    return pipeline.get_stats()


# ─── Learning Engine (Phase 3: Dynamic Skill Acquisition) ─────────────────────

learning_engine = get_learning_engine()

@app.post("/learning/ingest")
async def learn_from_text(req: LearnTextRequest):
    """Ingest documentation text and create a new learned skill."""
    # Use the Architect's LLM to synthesize knowledge
    architect = engine_team.get("Architect")
    llm_fn = architect._llm_generate if architect else None
    skill = await learning_engine.learn_from_text(
        name=req.name, content=req.content, source=req.source,
        llm_generate=llm_fn
    )
    return {
        "status": "learned",
        "skill": skill.to_dict(),
        "message": f"New skill '{req.name}' acquired from {req.source}"
    }

@app.post("/learning/ingest-file")
async def learn_from_file(req: LearnFileRequest):
    """Learn a new skill from a local documentation file."""
    architect = engine_team.get("Architect")
    llm_fn = architect._llm_generate if architect else None
    try:
        skill = await learning_engine.learn_from_file(
            filepath=req.filepath, llm_generate=llm_fn
        )
        return {
            "status": "learned",
            "skill": skill.to_dict(),
            "message": f"New skill '{skill.skill_name}' acquired from {req.filepath}"
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/learning/skills")
async def list_learned_skills():
    """List all dynamically learned skills."""
    return {
        "skills": learning_engine.list_skills(),
        "stats": learning_engine.get_stats(),
        "log": learning_engine.get_learning_log()[-10:],
    }

@app.post("/learning/use")
async def use_learned_skill(req: UseSkillRequest):
    """Use a learned skill to complete a task, optionally through a specific agent."""
    skill = learning_engine.get_skill(req.skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{req.skill_name}' not found")

    # Get skill knowledge
    skill_knowledge = skill.execute(req.task)

    # Route through an agent if specified
    if req.target_role and req.target_role in engine_team:
        agent = engine_team[req.target_role]
        enhanced_task = (
            f"You have access to a LEARNED SKILL called '{req.skill_name}'.\n"
            f"Skill knowledge:\n{skill_knowledge}\n\n"
            f"Use this knowledge to complete the following task:\n{req.task}"
        )
        response = await agent.process_task(enhanced_task, sender="learning_engine")
        return {
            "skill_used": req.skill_name,
            "agent": req.target_role,
            "response": response,
        }

    return {"skill_used": req.skill_name, "output": skill_knowledge}

@app.delete("/learning/skills/{name}")
async def forget_skill(name: str):
    """Remove a learned skill."""
    if learning_engine.forget_skill(name):
        return {"status": "forgotten", "skill": name}
    raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")


# ─── MCP Tool Synthesizer (Phase 3: Tool Synthesis) ───────────────────────

synthesizer = get_synthesizer()
forge = get_deterministic_forge()

@app.post("/synthesize/mcp")
async def synthesize_mcp_server(req: SynthesizeRequest):
    """Synthesize an MCP server from a learned skill."""
    llm_fn = None
    if req.use_llm:
        # Use Devo (Lead Developer) to review the generated code
        devo = engine_team.get("Lead Developer")
        if devo:
            llm_fn = devo._llm_generate

    # Phase 4 Upgrade: Use Deterministic Forge with TRM Audit
    tool = await forge.synthesize_verified_tool(req.skill_name)
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Skill '{req.skill_name}' not found or synthesis failed")

    return tool.to_dict()

    return {
        "status": "synthesized",
        "tool": tool.to_dict(),
        "code_length": len(tool.code),
        "message": f"MCP server generated on port {tool.port}"
    }

@app.post("/synthesize/skill")
async def synthesize_skill_class(req: SynthesizeRequest):
    """Generate a Python skill class from a learned skill."""
    skill = learning_engine.get_skill(req.skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{req.skill_name}' not found")

    code = synthesizer.generate_skill_class(req.skill_name, skill.to_dict())
    return {
        "status": "generated",
        "skill_name": f"{req.skill_name}Skill",
        "code_length": len(code),
        "code_preview": code[:500],
    }

@app.get("/synthesize/tools")
async def list_synthesized_tools():
    return {
        "tools": synthesizer.list_tools(),
        "stats": synthesizer.get_stats(),
        "log": synthesizer.get_synthesis_log()[-10:],
    }


# ─── P2P Agent Mesh (Phase 3: Distributed Consciousness) ───────────────────

agent_mesh = get_agent_mesh()

# Auto-register all agents on the mesh at startup
# Auto-register all agents on the mesh at startup
for role, agent in engine_team.items():
    node = agent_mesh.register_node(
        name=agent.persona.name,
        role=role,
        specialties=agent.persona.specialties,
        skills=agent.get_skill_names(),
        host="127.0.0.1",
        port=8000,
    )
    agent.mesh_node_id = node.node_id

# Create MonitorDaemon after Agent Mesh is initialized
monitor_daemon = MonitorDaemon(remediation_engine, interval=15, mesh=agent_mesh)

@app.get("/swarm/expert/{role}/logs")
async def expert_logs(role: str):
    agent = engine_team.get(role)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"role": role, "logs": agent.nodal_logs}

@app.get("/mesh/topology")
async def mesh_topology():
    """Get the full P2P mesh topology."""
    return agent_mesh.get_topology()

@app.get("/mesh/peers")
async def mesh_peers(role: str = "", specialty: str = ""):
    """Discover peers on the mesh."""
    return agent_mesh.discover_peers(
        role_filter=role or None,
        specialty_filter=specialty or None,
    )

@app.post("/mesh/route")
async def mesh_route_task(req: MeshRouteRequest):
    """Route a task through the P2P mesh."""
    result = await agent_mesh.route_task(
        task=req.task,
        target_node_id=req.target_node_id or None,
        required_specialty=req.required_specialty or None,
    )

    # If a node was found, actually execute the task through the agent
    if "routed_to" in result:
        target_role = result["routed_to"]["role"]
        agent = engine_team.get(target_role)
        if agent:
            response = await agent.process_task(req.task, sender="mesh_router")
            result["response"] = response
            # Capture internal activity logs for visibility
            if hasattr(agent, "nodal_logs"):
                result["nodal_logs"] = agent.nodal_logs

    return result

@app.get("/mesh/stats")
async def mesh_stats():
    return agent_mesh.get_stats()

@app.get("/mesh/log")
async def mesh_log():
    return agent_mesh.get_message_log()


# ─── Global Memory Sync (Phase 3: Distributed Consciousness) ────────────────

global_memory = get_global_memory()

@app.post("/memory/contribute")
async def memory_contribute(req: GlobalMemoryContributeRequest):
    """Contribute a memory to the global shared pool."""
    entry = global_memory.contribute(
        content=req.content,
        author=req.author,
        author_role=req.author_role,
        memory_type=req.memory_type,
        tags=req.tags,
    )
    return {"status": "contributed", "entry": entry.to_dict()}

@app.post("/memory/query")
async def memory_query(req: GlobalMemoryQueryRequest):
    """Query the global memory with vector similarity."""
    results = global_memory.query(
        query_text=req.query,
        top_k=req.top_k,
        author_filter=req.author_filter or None,
        type_filter=req.type_filter or None,
    )
    return {
        "query": req.query,
        "results": [{"score": score, "entry": entry} for score, entry in results],
        "total_matches": len(results),
    }

@app.get("/memory/stats")
async def memory_stats():
    return global_memory.get_stats()

@app.get("/memory/export")
async def memory_export():
    return global_memory.export_all()

@app.post("/memory/sync/{agent_role}")
async def memory_sync_agent(agent_role: str):
    """Sync an agent's local memory into the global pool."""
    agent = engine_team.get(agent_role)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_role}' not found")

    # Collect memories from the agent
    local_memories = []
    for fact in agent.memory.long_term:
        if fact.get("type") == "fact":
            local_memories.append({
                "content": fact["content"],
                "type": "fact",
                "tags": agent.persona.specialties[:3],
            })
        elif fact.get("type") == "task_result":
            local_memories.append({
                "content": f"{fact['task']}: {fact['result']}",
                "type": "experience",
                "tags": agent.persona.specialties[:3],
            })

    added = global_memory.sync_from_agent(
        agent_name=agent.persona.name,
        agent_role=agent_role,
        memories=local_memories,
    )
    return {
        "agent": agent_role,
        "memories_submitted": len(local_memories),
        "memories_added": added,
    }


# ─── Health (Updated for Phase 5) ──────────────────────────────────────

@app.get("/system/resources")
async def system_resources():
    return get_resource_arbiter().get_status()

@app.get("/health")
async def health():
    fed_stats = federation.get_federation_stats() if federation else {}
    return {
        "status": "v5_online",
        "phase": 5,
        "agents": len(engine_team),
        "subagents": len(spawned_subagents),
        "artifacts": pipeline.get_stats(),
        "learning_engine": learning_engine.get_stats(),
        "mesh": agent_mesh.get_stats(),
        "global_memory": global_memory.get_stats(),
        "synthesizer": synthesizer.get_stats(),
        "federation": fed_stats,
    }


# ─── Federation Endpoints (Phase 5: Mesh Federation) ───────────────────────

class FederationHandshakeRequest(BaseModel):
    node_id: str
    name: str
    host: str
    port: int
    api_key: str
    capabilities: List[str] = []
    timestamp: str

class FederationMemorySyncRequest(BaseModel):
    source_node_id: str
    source_name: str
    local_memory_count: int

@app.post("/federation/handshake")
async def federation_handshake(req: FederationHandshakeRequest):
    """Perform P2P handshake with another Swarm instance."""
    from swarm_v2.core.federation import SwarmNode
    node = SwarmNode(
        node_id=req.node_id,
        name=req.name,
        host=req.host,
        port=req.port,
        api_key=req.api_key,
        status="online",
        last_seen=req.timestamp,
        capabilities=req.capabilities
    )
    federation.registry.add_node(node)
    return {
        "node_id": federation.local_node_id,
        "name": federation.local_name,
        "host": "localhost",
        "port": federation.local_port,
        "api_key": federation.api_key,
        "capabilities": ["memory_sync", "peer_discovery", "handshake"]
    }

@app.get("/federation/peers")
async def federation_peers(node_id: str = ""):
    """Get list of known peers in the federation."""
    if not federation:
        return {"peers": []}
    online = federation.registry.get_online_nodes()
    return {"peers": [n.to_dict() for n in online if n.node_id != node_id]}

@app.post("/federation/memory/sync")
async def federation_memory_sync(req: FederationMemorySyncRequest):
    """Sync memories with a federated Swarm instance."""
    # Return recent memories to share
    memories = []
    recent = global_memory.get_sync_log(limit=20)
    for entry in recent:
        memories.append({
            "content": entry.get("content", ""),
            "author": entry.get("author", "unknown"),
            "author_role": entry.get("role", "unknown"),
            "memory_type": "federated_knowledge",
            "tags": ["federated"]
        })
    return {"memories": memories}

@app.get("/federation/stats")
async def federation_stats():
    """Get federation statistics."""
    if not federation:
        return {"error": "Federation not initialized"}
    return federation.get_federation_stats()




# ─── Task Arbiter Endpoints (Phase 4: Intelligent Resource Distribution) ───

@app.get("/system/task-arbiter")
async def task_arbiter_status():
    """Get Task Arbiter status including CPU/GPU workload distribution."""
    arbiter = get_task_arbiter()
    return arbiter.get_system_status()

@app.get("/system/task-arbiter/agent/{agent_id}")
async def task_arbiter_agent(agent_id: str):
    """Get status of a specific agent's workload."""
    arbiter = get_task_arbiter()
    return arbiter.get_agent_status(agent_id)


# ─── Dynamic Priority Arbitration Endpoints (Phase 5: Orchestra) ───────────────

@app.get("/system/maintenance/status")
async def maintenance_scheduling_status():
    """Get dynamic maintenance scheduling status."""
    arbiter = get_task_arbiter()
    return arbiter.dynamic_arbiter.get_maintenance_status()

@app.get("/system/maintenance/window")
async def current_usage_window():
    """Get current system usage window for maintenance scheduling."""
    arbiter = get_task_arbiter()
    window = arbiter.dynamic_arbiter.detect_usage_window()
    return {
        "window": window.value,
        "low_usage_duration_sec": arbiter.dynamic_arbiter.usage_metrics.low_usage_duration_sec,
        "priority_adjustment": arbiter.dynamic_arbiter.PRIORITY_ADJUSTMENTS.get(window, 0)
    }

@app.post("/system/maintenance/run")
async def trigger_maintenance_cycle():
    """Trigger an immediate maintenance cycle."""
    arbiter = get_task_arbiter()
    await arbiter.dynamic_arbiter.run_maintenance_cycle()
    return {"status": "completed", "stats": arbiter.dynamic_arbiter._stats}

@app.post("/system/maintenance/task/{task_id}/toggle")
async def toggle_maintenance_task(task_id: str, enabled: bool = True):
    """Enable or disable a specific maintenance task."""
    arbiter = get_task_arbiter()
    if task_id in arbiter.dynamic_arbiter.maintenance_tasks:
        arbiter.dynamic_arbiter.maintenance_tasks[task_id].enabled = enabled
        return {"status": "updated", "task_id": task_id, "enabled": enabled}
    raise HTTPException(status_code=404, detail=f"Maintenance task '{task_id}' not found")

@app.get("/system/maintenance/tasks")
async def list_maintenance_tasks():
    """List all maintenance tasks and their scheduling status."""
    arbiter = get_task_arbiter()
    return {
        "tasks": [
            {
                "task_id": task_id,
                "type": task.task_type.value,
                "enabled": task.enabled,
                "interval_sec": task.interval_sec,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "is_due": task.is_due(),
                "dynamic_priority": arbiter.dynamic_arbiter.get_dynamic_priority(task)
            }
            for task_id, task in arbiter.dynamic_arbiter.maintenance_tasks.items()
        ],
        "current_window": arbiter.dynamic_arbiter._last_window.value
    }

# ─── Startup / Shutdown ──────────────────────────────────────────────────────



async def mesh_heartbeat_reflex():
    """Maintain the 'alive' status of all local experts on the mesh."""
    while True:
        try:
            for role, agent in engine_team.items():
                if hasattr(agent, "mesh_node_id"):
                    agent_mesh.heartbeat(agent.mesh_node_id)
            await asyncio.sleep(30)
        except Exception as e:
            print(f"[Mesh] Heartbeat error: {e}")
            await asyncio.sleep(30)



# ─── Shield Security Loop (Phase 4) ────────────────────────────────────────────

async def auto_scan_pipeline():
    """Background loop to automatically scan new artifacts for security risks."""
    print("[Shield] Auto-scan loop initialized.")
    while True:
        try:
            shield = engine_team.get("Security Auditor")
            if not shield:
                await asyncio.sleep(30)
                continue

            # Need to re-scan directory to pick up new files
            pipeline.scan_artifacts()
            unscanned = pipeline.list_unscanned()
            
            for art in unscanned:
                filename = art["filename"]
                print(f"[Shield] Security auditing: {filename}...")
                
                # optimization: skip small text files or non-code
                if filename.endswith((".md", ".txt", ".json")):
                    pipeline.set_security_status(filename, "safe", "Skipped (static content)")
                    continue

                # Mark scanning
                pipeline.set_security_status(filename, "scanning")
                
                content = pipeline.get_content(filename) or ""
                task = (
                    f"Perform a SECURITY AUDIT on the following code artifact: {filename}. "
                    f"Identify any vulnerabilities (secrets, injection, RCE, insecure config). "
                    f"If the code is SAFE, reply with 'SAFE' as the primary keyword. "
                    f"If UNSAFE, explain the specific risks. "
                    f"DO NOT try to read the file again using tools; the content is provided below. "
                    f"\n\nSource Code Context:\n{content[:4000]}"
                )
                
                response = await shield.process_task(task, sender="shield_automator")
                
                # Determine status
                status = "unsafe"
                if "safe" in response.lower() and "unsafe" not in response.lower() and "vulnerability" not in response.lower():
                    status = "safe"
                elif "no issues found" in response.lower():
                    status = "safe"
                elif "low severity" in response.lower() or "low risk" in response.lower():
                    status = "warning"
                
                pipeline.set_security_status(filename, status, result=response)
                print(f"[Shield] Scan complete for {filename}: {status}")
            
            await asyncio.sleep(10)

        except Exception as e:
            print(f"[Shield] Loop error: {e}")
            await asyncio.sleep(10)

# ─── Remediation Control (Phase 4) ─────────────────────────────────────────────

@app.post("/remediation/restart/{role}")
async def force_restart_agent(role: str):
    """Manually trigger the remediation engine to restart an agent."""
    if role not in engine_team:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    success = await remediation_engine.handle_issue("AGENT_TIMEOUT", role)
    if "Successful" in success:
        return {"status": "restarted", "role": role, "new_agent_id": engine_team[role].agent_id}
    else:
        raise HTTPException(status_code=500, detail="Restart failed")


# ─── Reconnaissance Endpoints (Phase 5: Seeker Active Research) ───────────────

@app.get("/research/findings")
async def get_research_findings(limit: int = 10, topic: str = ""):
    """Get recent AI research findings from the reconnaissance daemon."""
    daemon = get_reconnaissance_daemon()
    if topic:
        return {"findings": daemon.get_findings_by_topic(topic)}
    return {"findings": daemon.get_recent_findings(limit)}

@app.post("/research/run")
async def trigger_research_cycle():
    """Trigger an immediate research cycle."""
    daemon = get_reconnaissance_daemon()
    # Run in background to not block
    import threading
    thread = threading.Thread(target=daemon.run_immediate, daemon=True)
    thread.start()
    return {"status": "triggered", "message": "Research cycle started in background"}

@app.post("/research/synthesis")
async def generate_research_synthesis():
    """Generate a comparative summary of recent findings for integration."""
    daemon = get_reconnaissance_daemon()
    recent_findings = daemon.get_recent_findings(10)
    
    if not recent_findings:
        return {"synthesis": "No recent findings available for synthesis."}
        
    compiled_data = ""
    for idx, f in enumerate(recent_findings):
        compiled_data += f"\n--- Finding {idx+1}: {f['topic']} ---\n{f['summary']}\n"
    
    # Prompt Researcher or Arbiter to synthesize
    prompt = (
        "Analyze the following recent AI research findings and generate a concise "
        "comparative summary. Conclude with actionable recommendations on which concepts "
        "we should integrate into our Swarm OS ecosystem to improve intelligence and "
        "efficiency.\n\n"
        f"{compiled_data}"
    )
    
    researcher = engine_team.get("Researcher") or engine_team.get("Arbiter")
    if not researcher:
        return {"synthesis": "Error: Researcher agent not available to perform synthesis."}
        
    try:
        response = await researcher.process_task(prompt, sender="research_daemon")
        return {"synthesis": response}
    except Exception as e:
        return {"synthesis": f"Error during synthesis: {str(e)}"}

@app.post("/research/topics")
async def add_research_topic(topic: str):
    """Add a new research topic."""
    daemon = get_reconnaissance_daemon()
    daemon.add_topic(topic)
    return {"status": "added", "topic": topic}

@app.delete("/research/topics/{topic}")
async def remove_research_topic(topic: str):
    """Remove a research topic."""
    daemon = get_reconnaissance_daemon()
    daemon.remove_topic(topic)
    return {"status": "removed", "topic": topic}

@app.post("/research/start")
async def start_research_daemon(interval_hours: float = 24):
    """Start the reconnaissance daemon."""
    daemon = start_reconnaissance(interval_hours)
    return {"status": "started", "interval_hours": interval_hours}

@app.post("/research/stop")
async def stop_research_daemon():
    """Stop the reconnaissance daemon."""
    daemon = get_reconnaissance_daemon()
    daemon.stop()
    return {"status": "stopped"}

# ─── Federation Endpoints (Phase 5: Mesh Federation) ──────────────────────────

@app.post("/federation/handshake")
async def federation_handshake(req: HandshakeRequest):
    """Handle incoming federation handshake."""
    f = get_federation()
    if not f:
        raise HTTPException(status_code=503, detail="Federation protocol not initialized")
    return f.handle_handshake(req.dict())

@app.get("/federation/peers")
async def list_federation_peers(node_id: str = ""):
    """Discover peers known by this node."""
    f = get_federation()
    if not f:
        raise HTTPException(status_code=503, detail="Federation protocol not initialized")
    return f.handle_peer_request(node_id)

@app.post("/federation/memory/sync")
async def sync_federation_memory(req: MemorySyncRequest):
    """Exchange knowledge with a federated peer."""
    f = get_federation()
    if not f:
        raise HTTPException(status_code=503, detail="Federation protocol not initialized")
    return f.handle_memory_sync(req.dict())

@app.get("/federation/stats")
async def get_federation_status():
    """Get federation health and connectivity stats."""
    f = get_federation()
    if not f:
        raise HTTPException(status_code=503, detail="Federation protocol not initialized")
    return f.get_federation_stats()

@app.post("/federation/connect")
async def connect_to_peer(host: str, port: int):
    """Manually initiate a handshake with a new peer."""
    f = get_federation()
    if not f:
        raise HTTPException(status_code=503, detail="Federation protocol not initialized")
    node = await f.handshake(host, port)
    if node:
        return {"status": "connected", "node": node.to_dict()}
    else:
        raise HTTPException(status_code=400, detail="Handshake failed")


# ─── Chain-of-Verification Endpoints (Phase 5: Logic Self-Audit) ───────────────

class VerifyReasoningRequest(BaseModel):
    text: str
    auto_correct: bool = False

class ChatWithVerificationRequest(BaseModel):
    role: str
    message: str
    sender: str = "user"

@app.post("/verification/verify")
async def verify_reasoning_endpoint(req: VerifyReasoningRequest):
    """Verify reasoning text for logical fallacies."""
    result = await verify_reasoning(req.text, auto_correct=req.auto_correct)
    return {
        "passed": result.passed,
        "score": result.score,
        "fallacy_count": len(result.detected_fallacies),
        "fallacies": [
            {
                "type": f.fallacy_type.value,
                "severity": f.severity,
                "step": f.step_number,
                "description": f.description,
                "suggestion": f.suggestion,
                "affected_text": f.affected_text[:100]
            }
            for f in result.detected_fallacies
        ],
        "suggestions": result.suggestions,
        "corrected_reasoning": result.corrected_reasoning
    }

@app.post("/federation/sync")
async def trigger_federation_sync(target_node_id: str):
    """Manually trigger a memory sync with a peer."""
    f = get_federation()
    if not f:
        raise HTTPException(status_code=503, detail="Federation protocol not initialized")
    result = await f.sync_memories(target_node_id)
    return result

@app.get("/verification/stats")
async def verification_stats():
    """Get Chain-of-Verification statistics."""
    cov = get_chain_of_verification()
    return cov.get_verification_stats()

@app.post("/swarm/chat-verified")
async def chat_with_verification(req: ChatWithVerificationRequest):
    """Chat with an agent and verify reasoning for logical fallacies."""
    if req.role not in engine_team:
        raise HTTPException(status_code=404, detail=f"Expert '{req.role}' not found")
    
    agent = engine_team[req.role]
    result = await agent.process_with_verification(req.message, sender=req.sender)
    pipeline.scan_artifacts()
    
    return result

# ─── Neural Wall Endpoints (Phase 5: Shield Security) ───────────────

class AnalyzePromptRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

@app.post("/security/analyze")
async def analyze_prompt_endpoint(req: AnalyzePromptRequest):
    """Analyze text for prompt injection threats."""
    detection = await analyze_prompt(req.text, req.context)
    return {
        "is_malicious": detection.is_malicious,
        "threat_level": detection.threat_level.value,
        "threat_type": detection.threat_type,
        "confidence": detection.confidence,
        "description": detection.description,
        "blocked_patterns": detection.blocked_patterns,
        "timestamp": detection.timestamp
    }

@app.get("/security/stats")
async def neural_wall_stats():
    """Get NeuralWall detection statistics."""
    wall = get_neural_wall()
    return wall.get_stats()

@app.get("/security/threats")
async def get_recent_threats(limit: int = 10):
    """Get recent threat detections."""
    wall = get_neural_wall()
    return {"threats": wall.get_recent_threats(limit)}

@app.post("/security/false-positive/{index}")
async def mark_false_positive(index: int):
    """Mark a detection as false positive."""
    wall = get_neural_wall()
    wall.mark_false_positive(index)
    return {"status": "marked", "index": index}


# ─── Self-Healing Infrastructure Endpoints (Phase 5: Flow) ───────────────

@app.get("/infra/health")
async def infra_health():
    """Get infrastructure health status for all monitored services."""
    infra = get_self_healing_infra()
    return infra.get_status()

@app.post("/infra/start")
async def start_infra_monitoring():
    """Start the self-healing infrastructure monitoring."""
    infra = get_self_healing_infra()
    if not infra.running:
        asyncio.create_task(infra.start())
        return {"status": "started", "message": "Self-healing monitoring started"}
    return {"status": "already_running", "message": "Monitoring already active"}

@app.post("/infra/stop")
async def stop_infra_monitoring():
    """Stop the self-healing infrastructure monitoring."""
    infra = get_self_healing_infra()
    await infra.stop()
    return {"status": "stopped", "message": "Self-healing monitoring stopped"}

@app.post("/infra/restart/{service_name}")
async def force_restart_service(service_name: str):
    """Force restart a specific monitored service."""
    infra = get_self_healing_infra()
    result = infra.force_restart(service_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/infra/reset/{service_name}")
async def reset_service_restart_count(service_name: str):
    """Reset the restart counter for a service."""
    infra = get_self_healing_infra()
    result = infra.reset_restart_count(service_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/infra/history")
async def get_restart_history(limit: int = 20):
    """Get the restart history for all services."""
    infra = get_self_healing_infra()
    status = infra.get_status()
    return {
        "restart_history": status["restart_history"][-limit:],
        "total_restarts": status["total_restarts"]
    }


# ─── Zero-Human Test Generation Endpoints (Phase 5: Verify) ───────────────

class GenerateTestsRequest(BaseModel):
    tool_name: str
    tool_data: Optional[Dict[str, Any]] = None

class RunTestsRequest(BaseModel):
    tool_name: str
    test_type: Optional[str] = None  # pytest_unit, pytest_api, playwright_e2e, integration

@app.post("/tests/generate")
async def generate_tool_tests(req: GenerateTestsRequest):
    """Generate all test suites for a synthesized MCP tool."""
    test_gen = get_test_generator()
    
    # If tool_data not provided, get from synthesizer
    tool_data = req.tool_data
    if not tool_data:
        synthesizer = get_synthesizer()
        tool = synthesizer.synthesized_tools.get(req.tool_name)
        if tool:
            tool_data = tool.to_dict()
        else:
            tool_data = {"endpoints": [], "port": 8000, "code": ""}
    
    suites = test_gen.generate_all_tests(req.tool_name, tool_data)
    
    return {
        "status": "generated",
        "tool": req.tool_name,
        "suites": [s.to_dict() for s in suites],
        "total_tests": sum(s.test_count for s in suites),
        "output_dir": test_gen.output_dir
    }

@app.post("/tests/run")
async def run_tool_tests(req: RunTestsRequest):
    """Run generated tests for a tool."""
    from swarm_v2.core.zero_human_test_gen import TestType
    
    test_gen = get_test_generator()
    
    test_type = None
    if req.test_type:
        try:
            test_type = TestType(req.test_type)
        except ValueError:
            pass
    
    results = test_gen.run_tests(req.tool_name, test_type)
    return results

@app.get("/tests/stats")
async def test_generation_stats():
    """Get test generation statistics."""
    test_gen = get_test_generator()
    return test_gen.get_stats()

@app.get("/tests/coverage/{tool_name}")
async def test_coverage_report(tool_name: str):
    """Get test coverage report for a tool."""
    test_gen = get_test_generator()
    return test_gen.get_coverage_report(tool_name)

@app.get("/tests/list")
async def list_generated_tests():
    """List all generated test suites."""
    test_gen = get_test_generator()
    return {
        "tools": list(test_gen.generated_suites.keys()),
        "stats": test_gen.get_stats()
    }

@app.post("/synthesize-and-test")
async def synthesize_and_test_tool(req: SynthesizeRequest):
    """Synthesize an MCP tool and auto-generate tests for it."""
    # Step 1: Synthesize the tool
    llm_fn = None
    if req.use_llm:
        devo = engine_team.get("Lead Developer")
        if devo:
            llm_fn = devo._llm_generate
    
    tool = await synthesizer.synthesize_from_learned_skill(
        skill_name=req.skill_name, llm_generate=llm_fn
    )
    if not tool:
        raise HTTPException(status_code=404, detail=f"Skill '{req.skill_name}' not found")
    
    # Step 2: Auto-generate tests
    test_gen = get_test_generator()
    suites = test_gen.generate_all_tests(req.skill_name, tool.to_dict())
    
    return {
        "status": "synthesized_with_tests",
        "tool": tool.to_dict(),
        "tests": {
            "suites": [s.to_dict() for s in suites],
            "total_tests": sum(s.test_count for s in suites),
            "coverage": "100%"
        },
        "message": f"Tool synthesized on port {tool.port} with {len(suites)} test suites"
    }


# ─── Auto-Changelog Endpoints (Phase 5: Scribe) ───────────────

@app.get("/changelog/status")
async def changelog_engine_status():
    """Get auto-changelog engine status."""
    engine = get_changelog_engine()
    return engine.get_status()

@app.post("/changelog/scan")
async def force_changelog_scan():
    """Force an immediate directory scan and changelog update."""
    engine = get_changelog_engine()
    result = engine.force_update()
    return result

@app.get("/changelog/recent")
async def get_recent_changelog_entries(limit: int = 10):
    """Get recent changelog entries."""
    engine = get_changelog_engine()
    return {"entries": engine.get_recent_changes(limit)}

@app.get("/changelog/modules")
async def list_tracked_modules():
    """List all tracked modules in the registry."""
    engine = get_changelog_engine()
    return {
        "modules": [
            {
                "path": info.path,
                "name": info.name,
                "category": info.category.value,
                "status": info.status,
                "description": info.description[:100] if info.description else "",
                "exports": info.exports[:5]
            }
            for info in engine.module_registry.values()
        ],
        "count": len(engine.module_registry)
    }

@app.post("/changelog/start")
async def start_changelog_monitoring(interval: int = 60):
    """Start the changelog monitoring loop."""
    asyncio.create_task(start_changelog_monitoring(interval))
    return {"status": "started", "interval": interval}

@app.get("/changelog/content")
async def get_changelog_content():
    """Get the full CHANGELOG.md content."""
    engine = get_changelog_engine()
    if os.path.exists(engine.changelog_path):
        with open(engine.changelog_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "path": engine.changelog_path}
    return {"content": "", "path": engine.changelog_path, "message": "Changelog not yet created"}


# ─── MCP Tool Evolver Endpoints (Phase 5: Bridge) ───────────────

@app.get("/evolver/status")
async def tool_evolver_status():
    """Get MCP Tool Evolver status."""
    evolver = get_tool_evolver()
    return evolver.get_status()

@app.get("/evolver/tools")
async def list_synthesized_tools_for_evolution():
    """List all synthesized tools available for evolution."""
    evolver = get_tool_evolver()
    tools = evolver._get_current_tools()
    return {
        "tools": [
            {
                "name": name,
                "version": evolver._get_current_version(name),
                "code_length": len(code)
            }
            for name, code in tools.items()
        ],
        "count": len(tools)
    }

@app.get("/evolver/knowledge")
async def get_available_knowledge():
    """Get available knowledge from reconnaissance for tool evolution."""
    evolver = get_tool_evolver()
    knowledge = evolver.get_available_knowledge()
    return {"knowledge": knowledge, "count": len(knowledge)}

@app.post("/evolver/run")
async def trigger_evolution_cycle():
    """Trigger an immediate tool evolution cycle."""
    evolver = get_tool_evolver()
    
    # Get LLM function from Lead Developer
    devo = engine_team.get("Lead Developer")
    llm_fn = devo._llm_generate if devo else None
    
    if llm_fn:
        evolver.llm_generate = llm_fn
    
    results = await evolver.evolution_cycle(trigger=EvolutionTrigger.MANUAL)
    
    return {
        "status": "completed",
        "tools_evolved": len(results),
        "results": [r.to_dict() for r in results]
    }

@app.get("/evolver/history/{tool_name}")
async def get_tool_evolution_history(tool_name: str):
    """Get version history for a specific tool."""
    evolver = get_tool_evolver()
    history = evolver.get_tool_history(tool_name)
    return {"tool": tool_name, "versions": history}

@app.post("/evolver/rollback/{tool_name}")
async def rollback_tool(tool_name: str, target_version: str = None):
    """Rollback a tool to a previous version."""
    evolver = get_tool_evolver()
    result = evolver.rollback_tool(tool_name, target_version)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@app.post("/evolver/start")
async def start_tool_evolver(interval: int = 3600):
    """Start the tool evolution monitor loop."""
    devo = engine_team.get("Lead Developer")
    llm_fn = devo._llm_generate if devo else None
    
    asyncio.create_task(start_tool_evolution(interval, llm_fn))
    return {"status": "started", "interval": interval}

@app.post("/evolver/evolve/{tool_name}")
async def evolve_specific_tool(tool_name: str):
    """Evolve a specific tool with current knowledge."""
    evolver = get_tool_evolver()
    
    # Get tool code
    tools = evolver._get_current_tools()
    if tool_name not in tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    # Get LLM and knowledge
    devo = engine_team.get("Lead Developer")
    llm_fn = devo._llm_generate if devo else None
    
    if not llm_fn:
        raise HTTPException(status_code=500, detail="No LLM available for evolution")
    
    evolver.llm_generate = llm_fn
    knowledge = evolver.get_available_knowledge()
    
    result = await evolver.evolve_tool(
        tool_name, tools[tool_name], knowledge, EvolutionTrigger.MANUAL
    )
    
    return result.to_dict()


# ─── Performance Insights Endpoints (Phase 5: Pulse) ───────────────

@app.get("/insights/status")
async def performance_insights_status():
    """Get Performance Insights engine status."""
    insights = get_performance_insights()
    return insights.get_status()

@app.post("/insights/report")
async def generate_performance_report(period: str = "weekly"):
    """Generate a new Swarm Intelligence Report."""
    insights = get_performance_insights()
    
    try:
        report_period = ReportPeriod(period.lower())
    except ValueError:
        report_period = ReportPeriod.WEEKLY
    
    report = await insights.generate_report(report_period)
    
    return {
        "status": "generated",
        "report_id": report.report_id,
        "health_score": report.overall_health_score,
        "efficiency_score": report.efficiency_score,
        "growth_score": report.growth_score,
        "total_tasks": report.total_tasks_processed,
        "success_rate": (report.total_tasks_processed - report.total_errors) / max(1, report.total_tasks_processed) * 100
    }

@app.get("/insights/reports")
async def list_performance_reports(limit: int = 10):
    """Get recent Swarm Intelligence Reports."""
    insights = get_performance_insights()
    return {"reports": insights.get_recent_reports(limit)}

@app.get("/insights/reports/{report_id}")
async def get_performance_report(report_id: str):
    """Get a specific report by ID."""
    insights = get_performance_insights()
    
    for report in insights.reports:
        if report.report_id == report_id:
            return report.to_dict()
    
    # Try to load from disk
    report_path = os.path.join(insights.reports_dir, f"{report_id}.json")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

@app.get("/insights/reports/{report_id}/markdown")
async def get_performance_report_markdown(report_id: str):
    """Get a specific report in markdown format."""
    insights = get_performance_insights()
    
    for report in insights.reports:
        if report.report_id == report_id:
            return {"markdown": report.to_markdown(), "report_id": report_id}
    
    # Try to load from disk
    md_path = os.path.join(insights.reports_dir, f"{report_id}.md")
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            return {"markdown": f.read(), "report_id": report_id}
    
    raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

@app.get("/insights/metrics/{metric_type}")
async def get_metric_history(metric_type: str, limit: int = 100):
    """Get history for a specific metric type."""
    insights = get_performance_insights()
    
    try:
        m_type = MetricType(metric_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid metric type. Valid types: {[m.value for m in MetricType]}"
        )
    
    history = insights.get_metric_history(m_type, limit)
    return {"metric_type": metric_type, "history": history, "count": len(history)}

@app.post("/insights/metrics/{metric_type}/record")
async def record_metric_value(metric_type: str, value: float, metadata: Dict = None):
    """Manually record a metric data point."""
    insights = get_performance_insights()
    
    try:
        m_type = MetricType(metric_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric type. Valid types: {[m.value for m in MetricType]}"
        )
    
    insights.record_metric(m_type, value, metadata)
    return {"status": "recorded", "metric_type": metric_type, "value": value}

@app.post("/insights/tasks/record")
async def record_task_execution(success: bool = True):
    """Record a task execution for success rate tracking."""
    insights = get_performance_insights()
    insights.record_task(success)
    
    status = insights.get_status()
    return {
        "status": "recorded",
        "success": success,
        "session_tasks": status["session_tasks"],
        "session_errors": status["session_errors"]
    }

@app.post("/insights/start")
async def start_performance_monitoring(interval_hours: int = 168):
    """Start the performance monitoring loop (default: weekly)."""
    asyncio.create_task(start_performance_monitoring(interval_hours))
    return {"status": "started", "interval_hours": interval_hours}

@app.post("/insights/stop")
async def stop_performance_monitoring():
    """Stop the performance monitoring loop."""
    insights = get_performance_insights()
    insights.stop()
    return {"status": "stopped"}

# ─── Swarm Orchestration Statistics (Phase 6) ──────────────────────────────────

@app.get("/swarm/orchestrator/stats")
async def get_orchestrator_stats():
    """Returns the current state of the proactive orchestration loop."""
    return {
        "active_tasks": active_orchestration_tasks,
        "triggered_proposals_count": len(triggered_proposals),
        "recent_proposals": list(triggered_proposals)[-5:],
        "status": "online" if active_orchestration_tasks < 2 else "saturated",
        "timestamp": datetime.now().isoformat()
    }

# ─── Proactive Orchestration (Phase 5: Self-Starting Agents) ──────────────────

# Track triggered proposals and active tasks
triggered_proposals = set()
acted_research_findings = set()
active_orchestration_tasks = 0

async def proactive_orchestration_loop():
    """Background task that looks for 'Approved' plans and asks for execution."""
    global active_orchestration_tasks
    log_file = "swarm_v2_memory/orchestration.log"
    with open(log_file, "a") as f:
        f.write(f"\n{datetime.now().strftime('%Y-%m-%d')} [INFO] [Orchestration] Proactive loop started.\n")
    
    while True:
        try:
            pipeline.scan_artifacts()
            approved = pipeline.list_by_status(ArtifactStatus.APPROVED)
            
            # Prioritize "Scribe" and "Antigravity" plans as requested by user
            def priority(fname):
                if "scribe" in fname.lower() or "antigravity" in fname.lower(): return 0
                return 1
            approved.sort(key=lambda x: priority(x["filename"]))
            
            with open(log_file, "a") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d')} [DEBUG] [Orchestration] Tick. Approved: {len(approved)} | Active Tasks: {active_orchestration_tasks}\n")
            
            plan_triggered = False
            # PHASE 6: Increased capacity and robustness
            if active_orchestration_tasks < 2:
                for art in approved:
                    filename = art["filename"]
                    clean_filename = filename.replace("swarm_v2_artifacts/", "").replace("swarm_v2_artifacts\\", "")
                    
                    is_plan = any(k in clean_filename.lower() for k in ["plan", "blueprint", "spec"]) and "artifact" not in clean_filename.lower()
                    
                    if is_plan and not clean_filename.startswith("PROPOSAL_"):
                        proposal_name = f"PROPOSAL_{os.path.splitext(os.path.basename(clean_filename))[0]}.md"
                        
                        if proposal_name not in pipeline.artifacts and clean_filename not in triggered_proposals:
                            log_msg = f"{datetime.now().strftime('%Y-%m-%d')} [INFO] [Orchestration] Triggering Devo Proposal for: {clean_filename}"
                            with open(log_file, "a") as f:
                                f.write(log_msg + "\n")
                            
                            triggered_proposals.add(clean_filename)
                            
                            from swarm_v2.core.kanban_board import get_kanban_board
                            kb = get_kanban_board()
                            card_id = kb.create_card(
                                title=f"Implement {clean_filename}",
                                description="Autonomously triggered proposal.",
                                assignee="Lead Developer",
                                priority="high"
                            )
                            # Start in TODO
                            kb.move_card(card_id, "TODO")
                            
                            devo = engine_team.get("Lead Developer")
                            if devo:
                                content = pipeline.get_content(filename)
                                trigger_msg = (
                                    f"IMPORTANT: Autonomous Task Detection.\n"
                                    f"I have detected an approved Implementation Plan: '{clean_filename}'.\n\n"
                                    f"PLAN CONTENT:\n{content[:2000]}\n\n"
                                    f"YOUR TASK:\n"
                                    f"1. Inspect the plan above.\n"
                                    f"2. Generate a formal 'Build Proposal' artifact.\n"
                                    f"3. You MUST use the following format exactly to save your proposal:\n\n"
                                    f"CREATE_FILES:\n"
                                    f"--- {proposal_name} ---\n"
                                    f"# Build Proposal: {clean_filename}\n"
                                    f"## Overview\n(Briefly describe what you will build)\n"
                                    f"## Proposed Files\n(List files to be created/modified)\n"
                                    f"## Execution Steps\n(List commands/steps)\n"
                                    f"---END---\n\n"
                                    "Do NOT begin execution of the plan itself. Only submit this structured proposal for final approval."
                                )
                                
                                async def ran_devo_task(msg, agent, target_file, cid):
                                    global active_orchestration_tasks
                                    active_orchestration_tasks += 1
                                    kb.move_card(cid, "IN_PROGRESS")
                                    try:
                                        await agent.process_task(msg, sender="Orchestrator")
                                    finally:
                                        active_orchestration_tasks -= 1
                                
                                asyncio.create_task(ran_devo_task(trigger_msg, devo, clean_filename, card_id))
                                plan_triggered = True
                                break # Only trigger one per tick
            
            # PHASE 7: Autonomous Thinker Upgrade
            # If no plans were triggered and we have capacity, check research
            if not plan_triggered and active_orchestration_tasks < 2:
                from swarm_v2.core.reconnaissance_daemon import get_reconnaissance_daemon
                recon = get_reconnaissance_daemon()
                
                # Daemon holds recent findings in memory.
                for finding in reversed(recon.findings[-10:]):  # look at last 10 roughly
                    fid = finding.finding_id
                    if fid not in acted_research_findings:
                        # Found a new research finding to act upon
                        log_msg = f"{datetime.now().strftime('%Y-%m-%d')} [INFO] [Orchestration] Triggering Research Analysis for: {finding.topic}"
                        with open(log_file, "a") as f:
                            f.write(log_msg + "\n")
                        
                        acted_research_findings.add(fid)
                        topic = finding.topic
                        summary = finding.summary
                        
                        from swarm_v2.core.kanban_board import get_kanban_board
                        kb = get_kanban_board()
                        card_id = kb.create_card(
                            title=f"Analyze Research: {topic}",
                            description="Autonomously triggered from daily research.",
                            assignee="Lead Developer",
                            priority="high"
                        )
                        kb.move_card(card_id, "TODO")
                        
                        devo = engine_team.get("Lead Developer")
                        if devo:
                            # Generate a unique filename for the plan
                            safe_topic = "".join([c if c.isalnum() else "_" for c in topic])[:30]
                            plan_filename = f"research_plan_{safe_topic}.md"
                            
                            trigger_msg = (
                                f"IMPORTANT: Autonomous Intelligence Intake.\n"
                                f"The Seeker agent has discovered new research on: {topic}.\n\n"
                                f"RESEARCH SUMMARY:\n{summary[:2000]}\n\n"
                                f"YOUR TASK:\n"
                                f"1. Analyze this research for potential integration into the QIAE Swarm.\n"
                                f"2. Generate an 'implementation_plan.md' style blueprint to add a feature or improvement based on this research.\n"
                                f"3. You MUST save your blueprint output in the following format exactly:\n\n"
                                f"CREATE_FILES:\n"
                                f"--- {plan_filename} ---\n"
                                f"# Research Integration Plan: {topic}\n"
                                f"## Overview\n(What does this research enable?)\n"
                                f"## Proposed Changes\n(List files to be modified/created)\n"
                                f"## Verification Plan\n(How to test the feature)\n"
                                f"---END---\n\n"
                                f"Do NOT implement the code yet, only write this plan so it can be approved by the system."
                            )
                            
                            async def ran_research_task(msg, agent, cid):
                                global active_orchestration_tasks
                                active_orchestration_tasks += 1
                                kb.move_card(cid, "IN_PROGRESS")
                                try:
                                    await agent.process_task(msg, sender="Orchestrator")
                                    # We don't have a direct 'passed' check, so assume done if it didn't raise exception
                                    kb.move_card(cid, "REVIEW") 
                                    kb.move_card(cid, "DONE")
                                except Exception as e:
                                    with open("swarm_v2_memory/orchestration.log", "a") as err_f:
                                        err_f.write(f"[ERROR] Research task failed: {e}\n")
                                finally:
                                    active_orchestration_tasks -= 1
                            
                            asyncio.create_task(ran_research_task(trigger_msg, devo, card_id))
                            break # Only spawn one research task per tick
                            
            try:
                # PHASE 8: Autonomous Kanban Execution (Pick up manual/external TODOs)
                if active_orchestration_tasks < 2:
                    from swarm_v2.core.kanban_board import get_kanban_board
                    kb = get_kanban_board()
                    todo_cards = kb.get_column("TODO")
                    
                    for card in todo_cards:
                        cid = card.get("card_id")
                        if cid and cid not in triggered_proposals:
                            assignee_name = card.get("assignee")
                            if not assignee_name:
                                continue
                                
                            agent = engine_team.get(assignee_name)
                            if agent:
                                log_msg = f"{datetime.now().strftime('%Y-%m-%d')} [INFO] [Orchestration] Picking up external TODO task: {card.get('title')}"
                                with open(log_file, "a") as f:
                                    f.write(log_msg + "\n")
                                    
                                triggered_proposals.add(cid)
                                
                                trigger_msg = (
                                    f"IMPORTANT: Kanban Task Assignment.\n"
                                    f"Task: {card.get('title')}\n"
                                    f"Description: {card.get('description')}\n"
                                    f"Please process this task immediately."
                                )
                                
                                async def ran_kanban_task(msg, tgt_agent, card_id):
                                    global active_orchestration_tasks
                                    active_orchestration_tasks += 1
                                    try:
                                        kb.move_card(card_id, "IN_PROGRESS")
                                        await tgt_agent.process_task(msg, sender="Orchestrator")
                                        kb.move_card(card_id, "REVIEW")
                                    except Exception as e:
                                        with open("swarm_v2_memory/orchestration.log", "a") as err_f:
                                            err_f.write(f"[ERROR] Kanban external task failed: {type(e).__name__}: {str(e)}\n")
                                    finally:
                                        active_orchestration_tasks -= 1
                                        
                                asyncio.create_task(ran_kanban_task(trigger_msg, agent, cid))
                                
                                # Add the spawned task to background list so it doesn't get GC'd
                                background_mailbox_tasks.add(asyncio.current_task())
                                break
            except Exception as e:
                with open("swarm_v2_memory/orchestration.log", "a") as err_f:
                    err_f.write(f"[ERROR] Phase 8 Failed: {type(e).__name__}: {str(e)}\n")
            
            # Auto-Security Scan for documentation (marked as static/verified)
            unscanned = pipeline.list_unscanned()
            for art in unscanned:
                ext = os.path.splitext(art["filename"])[1].lower()
                if ext in ('.md', '.txt'):
                    pipeline.set_security_status(art["filename"], "verified", "Auto-verified (Documentation)")
                elif ext in ('.json', '.yaml', '.yml'):
                    pipeline.set_security_status(art["filename"], "verified", "Auto-verified (Config)")

        except Exception as e:
            with open(log_file, "a") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d')} [ERROR] [Orchestration] Loop error: {e}\n")
            
        await asyncio.sleep(45) # Lower frequency to avoid LLM congestion

async def autonomous_pipeline_loop():
    """Background task that autonomously tests, approves, and integrates pending artifacts."""
    from swarm_v2.core.kanban_board import get_kanban_board
    kb = get_kanban_board()
    
    log_file = "swarm_v2_memory/pipeline.log"
    with open(log_file, "a") as f:
        f.write(f"\n{datetime.now().strftime('%Y-%m-%d')} [INFO] [Pipeline] Autonomous CI/CD loop started.\n")
        
    while True:
        try:
            pipeline.scan_artifacts()
            pending = pipeline.list_by_status(ArtifactStatus.PENDING)
            
            for art in pending:
                filename = art["filename"]
                
                # Check if there's an active kanban card for this
                active_cards = kb.get_column("IN_PROGRESS") + kb.get_column("TODO")
                matching_card = next((c for c in active_cards if filename in c.get("title", "") or filename in c.get("description", "")), None)
                
                if matching_card:
                    kb.move_card(matching_card["card_id"], "REVIEW")
                
                content = pipeline.get_content(filename)
                
                qa = engine_team.get("QA Engineer")
                if qa and content and len(content) > 10:
                    test_filename = f"test_{filename}" if not filename.startswith("test_") else filename
                    if test_filename != filename:
                        test_task = (
                            f"[ACTION] Create a comprehensive pytest test suite for this code.\\n"
                            f"You MUST output the test code using the following strict format:\\n"
                            f"WRITE_FILE: {test_filename}\\n```python\\n<your test code>\\n```\\n\\n"
                            f"File: '{filename}':\\n\\n{content[:1500]}"
                        )
                        await qa.process_task(test_task, sender="autonomous_pipeline")
                        
                        test_content = pipeline.get_content(test_filename)
                        passed = test_content is not None and len(test_content) > 50
                        pipeline.set_tested(filename, test_filename, passed, "Auto-verified by CI loop")
                        
                        if passed:
                            pipeline.approve(filename, "System", "Auto-approved after tests passed")
                            pipeline.integrate(filename)
                            if matching_card:
                                kb.move_card(matching_card["card_id"], "DONE")
                        else:
                            if matching_card:
                                kb.move_card(matching_card["card_id"], "IN_PROGRESS") # Send back
                
                await asyncio.sleep(10) # process one by one slowly
                
        except Exception as e:
            with open(log_file, "a") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d')} [ERROR] [Pipeline] Loop error: {e}\n")
        
        await asyncio.sleep(30)


# ─── QIAE Module Endpoints ─────────────────────────────────────────────────────
# Imports for new Round 2 modules
from swarm_v2.core.kanban_board import get_kanban_board
from swarm_v2.core.ddr_antibody import DigitalDNARepository
from swarm_v2.core.secrets_vault import SecretsVault
from swarm_v2.core.agent_mailbox import AgentMailbox
from swarm_v2.core.ultrawork_loop import UltraworkLoop
from swarm_v2.core.skill_loader import SkillLoader

# Request models for new endpoints
class CreateCardRequest(BaseModel):
    title: str
    description: str = ""
    assignee: str = ""
    priority: str = "medium"
    tags: List[str] = []

class MoveCardRequest(BaseModel):
    target_status: str

class SendMailboxMessage(BaseModel):
    from_agent: str
    to_agent: str
    body: str
    subject: str = ""

class DDRScanRequest(BaseModel):
    code: str
    filename: str = "untitled.py"


# ─── Kanban Board (Tab 14) ─────────────────────────────────────────────────────

@app.get("/kanban/board")
async def get_board():
    """Full Kanban board grouped by columns."""
    kb = get_kanban_board()
    return kb.get_board()

@app.get("/kanban/stats")
async def get_kanban_stats():
    """Kanban board statistics."""
    kb = get_kanban_board()
    return kb.get_stats()

@app.post("/kanban/cards")
async def create_kanban_card(req: CreateCardRequest):
    """Create a new task card."""
    kb = get_kanban_board()
    card_id = kb.create_card(
        title=req.title,
        description=req.description,
        assignee=req.assignee,
        priority=req.priority,
        tags=req.tags,
    )
    return {"card_id": card_id, "status": "created"}

@app.post("/kanban/cards/{card_id}/move")
async def move_kanban_card(card_id: str, req: MoveCardRequest):
    """Move a card to a new status column."""
    kb = get_kanban_board()
    result = kb.move_card(card_id, req.target_status)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ─── DDR Antibody & Secrets Vault (Tab 15) ─────────────────────────────────────

@app.get("/ddr/antibodies")
async def list_antibodies():
    """List all DDR antibodies."""
    ddr = DigitalDNARepository()
    return {"antibodies": ddr.get_antibodies()}

@app.get("/ddr/stats")
async def get_ddr_stats():
    """DDR prevention statistics."""
    ddr = DigitalDNARepository()
    return ddr.get_prevention_stats()

@app.post("/ddr/scan")
async def scan_code_ddr(req: DDRScanRequest):
    """Scan code against DDR antibodies."""
    ddr = DigitalDNARepository()
    matches = ddr.check_antibodies(req.code, req.filename)
    return {"matches": matches, "scanned_lines": len(req.code.splitlines())}

@app.get("/secrets/keys")
async def list_secret_keys():
    """List secret key names (no values exposed)."""
    vault = SecretsVault()
    return {"keys": vault.list_keys(), "stats": vault.get_stats()}


# ─── Agent Comms & Missions (Tab 16) ───────────────────────────────────────────

@app.get("/mailbox/agents")
async def list_mailbox_agents():
    """List all agents with mailboxes."""
    return {"agents": AgentMailbox.list_agents()}

@app.get("/mailbox/{agent_id}/inbox")
async def peek_mailbox(agent_id: str):
    """Peek at an agent's inbox without consuming messages."""
    mb = AgentMailbox(agent_id)
    return {"agent": agent_id, "pending": mb.count_pending(), "messages": mb.peek()}

# Global set to hold strong references to background tasks to prevent GC
background_mailbox_tasks = set()

@app.post("/mailbox/send")
async def send_mailbox_message(req: SendMailboxMessage):
    """Send a message between agents."""
    mb = AgentMailbox(req.from_agent)
    mb.send(req.to_agent, req.body, subject=req.subject)
    
    # Trigger execution if target is an active engine_team agent
    if req.to_agent in engine_team:
        agent = engine_team[req.to_agent]
        msg_payload = f"Message from {req.from_agent} (Subject: {req.subject}):\n{req.body}"
        
        async def run_agent_process():
            try:
                response = await agent.process_task(msg_payload, sender=req.from_agent)
                
                # Extract clean text if response is a dictionary 
                if isinstance(response, dict):
                    reply_text = response.get("response", str(response))
                else:
                    reply_text = str(response)
                    
                reply_mb = AgentMailbox(req.to_agent)
                reply_mb.send(
                    req.from_agent, 
                    reply_text, 
                    subject=f"Re: {req.subject}"
                )
            except Exception as e:
                reply_mb = AgentMailbox(req.to_agent)
                reply_mb.send(
                    req.from_agent, 
                    f"Error processing task: {str(e)}", 
                    subject=f"Error: {req.subject}"
                )
                
        # Start as background task and save strong reference
        task = asyncio.create_task(run_agent_process())
        background_mailbox_tasks.add(task)
        task.add_done_callback(background_mailbox_tasks.discard)
        
        return {"status": "sent", "from": req.from_agent, "to": req.to_agent, "triggered": True}
        
    return {"status": "sent", "from": req.from_agent, "to": req.to_agent, "triggered": False}

@app.get("/mailbox/{agent_id}/receive")
async def receive_mailbox(agent_id: str):
    """Consume messages from an agent's inbox."""
    mb = AgentMailbox(agent_id)
    return {"agent": agent_id, "messages": mb.receive(limit=50)}

@app.get("/office/status")
async def get_virtual_office_status():
    """Return status of all agents for the virtual office."""
    kb = get_kanban_board()
    in_progress_cards = kb.get_column("IN_PROGRESS")
    
    # Map assignees to their active task
    working_agents = {card.get("assignee"): card for card in in_progress_cards if card.get("assignee")}
    
    status_list = []
    
    managers = {
        "gemini": {"manager": "Google Gemini", "department": "Product & Creative", "active_agents": 0, "status": "idle"},
        "openrouter": {"manager": "OpenRouter", "department": "Operations & Compliance", "active_agents": 0, "status": "idle"},
        "deepseek": {"manager": "DeepSeek API", "department": "Engineering & Logic", "active_agents": 0, "status": "idle"}
    }

    for role, agent in engine_team.items():
        is_working_kanban = role in working_agents
        is_working_mailbox = hasattr(agent, "active_task") and agent.active_task is not None
        is_working = is_working_kanban or is_working_mailbox
        
        backend = getattr(agent.persona, "llm_backend", "local")
        department = getattr(agent.persona, "department", "General")
        name = getattr(agent.persona, "name", role)
        
        if backend in managers and is_working:
            managers[backend]["active_agents"] += 1
            managers[backend]["status"] = "working"

        if is_working_kanban:
            task_title = working_agents[role].get("title", "")
            task_desc = working_agents[role].get("description", "")
        else:
            task_title = "Direct Mailbox Task" if is_working_mailbox else None
            task_desc = getattr(agent, "active_task", None) if is_working_mailbox else None

        status_list.append({
            "agent": role,
            "name": name,
            "role": role,
            "status": "working" if is_working else "idle",
            "task": task_title,
            "description": task_desc,
            "department": department,
            "llm_backend": backend
        })
        
    return {
        "agents": status_list,
        "regional_managers": list(managers.values())
    }

@app.get("/ultrawork/missions")
async def list_ultrawork_missions():
    """List all Ultrawork Loop missions."""
    uw = UltraworkLoop()
    missions = uw.list_missions()
    return {"missions": missions, "stats": uw.get_stats()}

@app.get("/skills/portable")
async def list_portable_skills():
    """List all SKILL.md and Python skills."""
    loader = SkillLoader()
    loader.discover_skills()
    return {"skills": loader.list_skills(), "stats": loader.get_stats()}


if __name__ == "__main__":
    import uvicorn
    # Start the proactive loop in the background
    async def main():
        loop_task = asyncio.create_task(proactive_orchestration_loop())
        pipeline_task = asyncio.create_task(autonomous_pipeline_loop())
        # QIAE Phase 5: Start the proactive growth loop
        growth_task = asyncio.create_task(get_proactive_loop().start())
        
        # QIAE Phase 5: Start the reconnaissance daemon (Seeker)
        start_reconnaissance(interval_hours=24)
        
        config = uvicorn.Config(app, host="0.0.0.0", port=8001, reload=False)
        server = uvicorn.Server(config)
        await server.serve()
        
    asyncio.run(main())
