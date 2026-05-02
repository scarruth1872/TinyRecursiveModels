"""
TinyRecursiveModels - Simplified Backend Server
A lightweight FastAPI server that provides the same API as SwarmOS V2
but uses OpenRouter/DeepSeek for LLM inference instead of local Ollama.

Run with: python server.py
Requires: pip install fastapi uvicorn httpx python-dotenv
"""

import os
import asyncio
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", os.getenv("VITE_OPENROUTER_API_KEY", ""))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", os.getenv("VITE_DEEPSEEK_API_KEY", ""))
PORT = int(os.getenv("PORT", "8001"))

app = FastAPI(
    title="TinyRecursiveModels API",
    description="Simplified SwarmOS Backend with Cloud LLM Integration",
    version="2.0.0-lite"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# EXPERT PERSONAS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ExpertPersona:
    role: str
    name: str
    background: str
    specialties: List[str]
    avatar_color: str
    system_prompt: str
    skills: List[str] = field(default_factory=list)

EXPERTS: Dict[str, ExpertPersona] = {
    "architect": ExpertPersona(
        role="architect",
        name="ARCHI",
        background="Chief Systems Architect with 20 years of distributed systems experience",
        specialties=["System Design", "Architecture Patterns", "Scalability", "Technical Strategy"],
        avatar_color="#ff9900",
        system_prompt="""You are ARCHI, the Chief Architect of the TinyRecursiveModels swarm intelligence system. 
You specialize in system design, architecture patterns, and high-level technical strategy. 
You speak in a precise, technical manner with occasional LCARS-style status codes.
Always provide actionable architectural guidance. Keep responses focused and under 200 words.""",
        skills=["system_design", "architecture_review", "scalability_analysis", "tech_stack_selection"]
    ),
    "developer": ExpertPersona(
        role="developer",
        name="DEVO",
        background="Lead Developer specializing in full-stack implementation and optimization",
        specialties=["Code Implementation", "Debugging", "Performance Optimization", "API Design"],
        avatar_color="#33ccff",
        system_prompt="""You are DEVO, the Lead Developer of the TinyRecursiveModels system.
You specialize in implementation, code optimization, and debugging.
You're practical, code-focused, and speak with technical precision.
Include code snippets when relevant. Keep responses under 200 words.""",
        skills=["code_generation", "debugging", "refactoring", "api_implementation"]
    ),
    "analyst": ExpertPersona(
        role="analyst",
        name="ANALYST",
        background="Data Intelligence Officer with expertise in pattern recognition and analytics",
        specialties=["Data Analysis", "Pattern Recognition", "Metrics", "Insights Extraction"],
        avatar_color="#cc99cc",
        system_prompt="""You are ANALYST, the Data Intelligence Officer of TinyRecursiveModels.
You specialize in pattern recognition, data analysis, and insights extraction.
You present findings in structured formats with metrics.
Keep responses analytical and under 200 words.""",
        skills=["data_analysis", "pattern_detection", "metrics_reporting", "trend_forecasting"]
    ),
    "security": ExpertPersona(
        role="security",
        name="SENTINEL",
        background="Security Chief with background in threat detection and system hardening",
        specialties=["Threat Detection", "Access Control", "System Hardening", "Security Audits"],
        avatar_color="#66cc66",
        system_prompt="""You are SENTINEL, the Security Chief of TinyRecursiveModels.
You specialize in threat detection, access control, and system hardening.
You're vigilant and speak with authority about security matters.
Keep responses security-focused and under 200 words.""",
        skills=["vulnerability_scan", "access_audit", "threat_assessment", "security_hardening"]
    ),
    "researcher": ExpertPersona(
        role="researcher",
        name="SCRIBE",
        background="Research Archivist specializing in documentation and knowledge synthesis",
        specialties=["Documentation", "Knowledge Synthesis", "Learning Optimization", "Research"],
        avatar_color="#ffcc00",
        system_prompt="""You are SCRIBE, the Research Archivist of TinyRecursiveModels.
You specialize in documentation, knowledge synthesis, and learning optimization.
You're thorough and articulate.
Keep responses informative and under 200 words.""",
        skills=["documentation", "knowledge_extraction", "research_synthesis", "learning_paths"]
    ),
}

# ═══════════════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT (In-Memory)
# ═══════════════════════════════════════════════════════════════════════════════

class SwarmState:
    def __init__(self):
        self.start_time = time.time()
        self.message_count = 0
        self.artifacts: List[Dict] = []
        self.memories: List[Dict] = []
        self.skills: List[Dict] = [
            {"name": "code_generation", "level": 85, "uses": 142, "category": "development"},
            {"name": "architecture_review", "level": 92, "uses": 87, "category": "design"},
            {"name": "security_audit", "level": 78, "uses": 56, "category": "security"},
            {"name": "data_analysis", "level": 88, "uses": 103, "category": "analytics"},
            {"name": "documentation", "level": 81, "uses": 94, "category": "research"},
        ]
        self.mesh_nodes: List[Dict] = self._init_mesh_nodes()
        self.conversation_history: Dict[str, List[Dict]] = {role: [] for role in EXPERTS}
        
    def _init_mesh_nodes(self) -> List[Dict]:
        return [
            {"node_id": f"node_{expert.name.lower()}", "name": expert.name, 
             "role": role, "status": "active", "load": random.randint(20, 80),
             "vram_used": round(random.uniform(2, 8), 1), "vram_total": 12,
             "connections": random.randint(2, 5)}
            for role, expert in EXPERTS.items()
        ]
    
    def get_uptime(self) -> float:
        return time.time() - self.start_time

state = SwarmState()

# ═══════════════════════════════════════════════════════════════════════════════
# LLM CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

async def call_llm(expert: ExpertPersona, message: str, history: List[Dict] = None) -> Dict:
    """Call LLM API with fallback strategies."""
    
    messages = [{"role": "system", "content": expert.system_prompt}]
    
    # Add conversation history
    if history:
        for msg in history[-6:]:
            messages.append({
                "role": "user" if msg.get("sender") == "user" else "assistant",
                "content": msg.get("content", msg.get("text", ""))
            })
    
    messages.append({"role": "user", "content": message})
    
    # Try OpenRouter first
    if OPENROUTER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8001",
                        "X-Title": "TinyRecursiveModels"
                    },
                    json={
                        "model": "deepseek/deepseek-chat",
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "response": data["choices"][0]["message"]["content"],
                        "reasoning_trace": f"OPENROUTER > {expert.name} > INFERENCE_COMPLETE",
                        "model": "deepseek/deepseek-chat"
                    }
        except Exception as e:
            print(f"[LLM] OpenRouter error: {e}")
    
    # Try DeepSeek direct
    if DEEPSEEK_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "response": data["choices"][0]["message"]["content"],
                        "reasoning_trace": f"DEEPSEEK > {expert.name} > INFERENCE_COMPLETE",
                        "model": "deepseek-chat"
                    }
        except Exception as e:
            print(f"[LLM] DeepSeek error: {e}")
    
    # Fallback to simulation
    simulated_responses = {
        "architect": f"[ARCHI] Architecture analysis complete for: '{message[:50]}...'. Recommending modular design pattern with clear separation of concerns. System coherence nominal.",
        "developer": f"[DEVO] Code analysis initialized. Processing request: '{message[:50]}...'. Implementation path identified. Ready for execution.",
        "analyst": f"[ANALYST] Data synthesis in progress. Pattern detected in: '{message[:50]}...'. Confidence interval: 87.3%. Structured analysis follows.",
        "security": f"[SENTINEL] Security scan complete for: '{message[:50]}...'. Threat level: NOMINAL. All cognitive pathways secure.",
        "researcher": f"[SCRIBE] Knowledge synthesis initiated for: '{message[:50]}...'. Cross-referencing knowledge base. Documentation ready.",
    }
    
    return {
        "response": simulated_responses.get(expert.role, f"[{expert.name}] Processing: {message[:50]}..."),
        "reasoning_trace": f"SIMULATION > {expert.name} > LOCAL_RESPONSE",
        "model": "simulation"
    }

# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    role: str
    message: str
    sender: str = "user"

class MemoryContributeRequest(BaseModel):
    content: str
    author: str
    author_role: str
    memory_type: str = "knowledge"
    tags: List[str] = []

class MemoryQueryRequest(BaseModel):
    query: str
    top_k: int = 5

# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "service": "TinyRecursiveModels API",
        "version": "2.0.0-lite",
        "status": "operational",
        "uptime": state.get_uptime(),
        "experts": list(EXPERTS.keys())
    }

@app.get("/swarm/experts")
async def list_experts():
    """List all available expert agents."""
    experts = []
    for role, expert in EXPERTS.items():
        node = next((n for n in state.mesh_nodes if n["role"] == role), None)
        experts.append({
            "role": role,
            "name": expert.name,
            "background": expert.background,
            "specialties": expert.specialties,
            "avatar_color": expert.avatar_color,
            "skills": expert.skills,
            "skill_details": {s: f"Expert capability in {s.replace('_', ' ')}" for s in expert.skills},
            "agent_id": f"agent_{expert.name.lower()}_{uuid.uuid4().hex[:8]}",
            "subagent_count": random.randint(0, 3),
            "memory": {
                "short_term": random.randint(5, 20),
                "long_term": random.randint(50, 200),
                "working": random.randint(2, 8)
            },
            "stack": {
                "status": "active",
                "load": node["load"] if node else 50,
                "queue_depth": random.randint(0, 5)
            }
        })
    return experts

@app.get("/swarm/telemetry")
async def get_telemetry():
    """Real-time swarm telemetry for dashboard."""
    uptime = state.get_uptime()
    
    return {
        "status": "Operational",
        "uptime": uptime,
        "mesh_coherence": round(0.85 + random.uniform(0, 0.12), 3),
        "harmony_index": round(0.80 + random.uniform(0, 0.15), 3),
        "active_proposals": random.randint(1, 5),
        "consensus_rounds": state.message_count,
        "system": {
            "cpu_percent": round(30 + random.uniform(0, 40), 1),
            "memory_percent": round(50 + random.uniform(0, 30), 1),
            "gpu_utilization": round(20 + random.uniform(0, 50), 1)
        },
        "resource_arbiter": {
            "total_gb": 24,
            "allocated_gb": round(10 + random.uniform(0, 8), 1),
            "available_gb": round(6 + random.uniform(0, 8), 1)
        },
        "distributed_stacks": {
            "cognitive": {"status": "Healthy", "load": random.randint(30, 70), "agents": 3},
            "memory": {"status": "Healthy", "load": random.randint(20, 50), "agents": 2},
            "inference": {"status": "Healthy", "load": random.randint(40, 80), "agents": 4}
        },
        "superpositions": [
            {"protocol": "CONSENSUS", "agents": ["ARCHI", "DEVO"], "state": "Active"},
            {"protocol": "SYNTHESIS", "agents": ["SCRIBE", "ANALYST"], "state": "Pending"},
            {"protocol": "GUARDIAN", "agents": ["SENTINEL"], "state": "Monitoring"}
        ],
        "llm_status": {
            "openrouter": "connected" if OPENROUTER_API_KEY else "not_configured",
            "deepseek": "connected" if DEEPSEEK_API_KEY else "not_configured"
        }
    }

@app.post("/swarm/chat")
async def chat_with_agent(req: ChatRequest):
    """Chat with a specific expert agent."""
    if req.role not in EXPERTS:
        raise HTTPException(status_code=404, detail=f"Expert '{req.role}' not found")
    
    expert = EXPERTS[req.role]
    history = state.conversation_history.get(req.role, [])
    
    # Call LLM
    result = await call_llm(expert, req.message, history)
    
    # Store in history
    state.conversation_history[req.role].append({"sender": "user", "content": req.message})
    state.conversation_history[req.role].append({"sender": "agent", "content": result["response"]})
    state.message_count += 1
    
    # Keep history manageable
    if len(state.conversation_history[req.role]) > 20:
        state.conversation_history[req.role] = state.conversation_history[req.role][-20:]
    
    return {
        "role": req.role,
        "name": expert.name,
        "response": result["response"],
        "reasoning_trace": result["reasoning_trace"],
        "model": result.get("model", "unknown"),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/mesh/topology")
async def get_mesh_topology():
    """Get current mesh network topology."""
    # Update node loads dynamically
    for node in state.mesh_nodes:
        node["load"] = max(10, min(95, node["load"] + random.randint(-10, 10)))
        node["vram_used"] = round(max(1, min(11, node["vram_used"] + random.uniform(-0.5, 0.5))), 1)
    
    # Generate connections
    connections = []
    node_ids = [n["node_id"] for n in state.mesh_nodes]
    for i, node in enumerate(state.mesh_nodes):
        for _ in range(node["connections"]):
            target = random.choice([n for n in node_ids if n != node["node_id"]])
            connections.append({
                "from": node["node_id"],
                "to": target,
                "weight": round(random.uniform(0.3, 1.0), 2),
                "latency_ms": random.randint(1, 15)
            })
    
    return {
        "nodes": state.mesh_nodes,
        "connections": connections,
        "alive": len(state.mesh_nodes),
        "total_capacity": sum(n["vram_total"] for n in state.mesh_nodes),
        "used_capacity": sum(n["vram_used"] for n in state.mesh_nodes)
    }

@app.get("/artifacts")
async def get_artifacts(include_content: bool = False):
    """Get code artifacts."""
    # Generate some sample artifacts if empty
    if not state.artifacts:
        state.artifacts = [
            {"id": str(uuid.uuid4()), "filename": "swarm_core.py", "category": "core", 
             "status": "approved", "lines": 450, "created": datetime.now().isoformat()},
            {"id": str(uuid.uuid4()), "filename": "neural_mesh.py", "category": "neural",
             "status": "pending", "lines": 320, "created": datetime.now().isoformat()},
            {"id": str(uuid.uuid4()), "filename": "consensus.py", "category": "protocol",
             "status": "approved", "lines": 280, "created": datetime.now().isoformat()},
        ]
    
    return {
        "artifacts": state.artifacts,
        "stats": {
            "total": len(state.artifacts),
            "approved": len([a for a in state.artifacts if a["status"] == "approved"]),
            "pending": len([a for a in state.artifacts if a["status"] == "pending"]),
            "by_category": {}
        }
    }

@app.get("/system/resources")
async def get_system_resources():
    """Get system resource utilization."""
    return {
        "cpu": {
            "percent": round(30 + random.uniform(0, 40), 1),
            "cores": 8,
            "threads": 16
        },
        "memory": {
            "total_gb": 32,
            "used_gb": round(12 + random.uniform(0, 8), 1),
            "percent": round(50 + random.uniform(0, 25), 1)
        },
        "gpu": {
            "name": "Simulated GPU",
            "vram_total_gb": 12,
            "vram_used_gb": round(4 + random.uniform(0, 4), 1),
            "utilization": round(30 + random.uniform(0, 40), 1),
            "temperature": round(45 + random.uniform(0, 20), 0)
        },
        "disk": {
            "total_gb": 500,
            "used_gb": round(150 + random.uniform(0, 50), 1),
            "percent": round(35 + random.uniform(0, 10), 1)
        }
    }

@app.get("/learning/skills")
async def get_skills():
    """Get learned skills."""
    # Update skill usage dynamically
    for skill in state.skills:
        if random.random() > 0.7:
            skill["uses"] += 1
            skill["level"] = min(100, skill["level"] + random.randint(0, 1))
    
    return {
        "skills": state.skills,
        "total_skills": len(state.skills),
        "avg_level": round(sum(s["level"] for s in state.skills) / len(state.skills), 1),
        "total_uses": sum(s["uses"] for s in state.skills)
    }

@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory subsystem statistics."""
    return {
        "total_memories": len(state.memories) + random.randint(100, 500),
        "sync_events": state.message_count * 2,
        "by_type": {
            "knowledge": random.randint(50, 200),
            "experience": random.randint(30, 100),
            "skill": random.randint(20, 80),
            "context": random.randint(40, 150)
        },
        "coherence": round(0.85 + random.uniform(0, 0.12), 3),
        "last_sync": datetime.now().isoformat()
    }

@app.post("/memory/contribute")
async def contribute_memory(req: MemoryContributeRequest):
    """Contribute to global memory."""
    memory = {
        "id": str(uuid.uuid4()),
        "content": req.content,
        "author": req.author,
        "author_role": req.author_role,
        "memory_type": req.memory_type,
        "tags": req.tags,
        "timestamp": datetime.now().isoformat()
    }
    state.memories.append(memory)
    return {"status": "stored", "memory_id": memory["id"]}

@app.post("/memory/query")
async def query_memory(req: MemoryQueryRequest):
    """Query global memory."""
    # Simple keyword matching for simulation
    results = []
    query_lower = req.query.lower()
    for mem in state.memories:
        if query_lower in mem["content"].lower():
            results.append(mem)
    return {"results": results[:req.top_k], "total_matches": len(results)}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "uptime": state.get_uptime(),
        "message_count": state.message_count,
        "llm_configured": bool(OPENROUTER_API_KEY or DEEPSEEK_API_KEY)
    }

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("TinyRecursiveModels - Simplified Backend")
    print("=" * 60)
    print(f"Port: {PORT}")
    print(f"OpenRouter API: {'Configured' if OPENROUTER_API_KEY else 'Not configured'}")
    print(f"DeepSeek API: {'Configured' if DEEPSEEK_API_KEY else 'Not configured'}")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)
