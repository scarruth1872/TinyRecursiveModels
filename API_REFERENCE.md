# Swarm OS v11 — API Reference

**Base URL:** `http://127.0.0.1:8001`  
**Interactive Docs:** `http://127.0.0.1:8001/docs`  
**OpenAPI spec:** `http://127.0.0.1:8001/openapi.json`

All endpoints accept and return `application/json`.

---

## Health & Soul

### `GET /health`

Complete system status — agents, distributed mesh, memory.

```json
{
  "status": "v11_online", "phase": 11, "agents": 12,
  "mesh": { "distributed": true, "parallel_availability": "100%" }
}
```

### `GET /swarm/soul`

Aggregates philosophical status, harmony index, and autonomous evolution proposals.

```json
{
  "harmony_index": 1.0,
  "reflection": "The swarm is aligned with the Architect's vision...",
  "autonomous_proposals": ["PROPOSAL_integration_plan.md"]
}
```

### `GET /swarm/telemetry`

Real-time emergence telemetry including per-agent stack health and VRAM stats.

---

## Swarm / Chat

### `GET /swarm/experts`

List all 12 agents with skills, mesh node IDs, and **Cognitive Stack status**.

```json
{
  "role": "Architect",
  "stack": { 
    "executive": "gemma3:270m", 
    "reasoning": "TRM-7M", 
    "offloads": 12 
  },
  "config": {
    "H_cycles": 2,
    "L_cycles": 1,
    "complexity_threshold": 0.6
  }
}
```

### `POST /swarm/chat`

```json
{ "role": "Lead Developer", "message": "write a FastAPI hello world" }
```

### `POST /swarm/broadcast`

Parallel coordination across all 12 agents.

```json
{ "message": "what are your primary specialties?" }
```

Returns responses from all 12 agents simultaneously.

### `POST /swarm/pipeline`

```json
{ "task": "build a JWT auth module", "agents": ["Architect", "Lead Developer", "QA Engineer"] }
```

Full multi-agent build pipeline.

### `POST /swarm/spawn`

```json
{ "parent_role": "Lead Developer", "sub_role": "Frontend Developer", "task": "build a login form" }
```

### `GET /swarm/subagents/{role}`

List sub-agents spawned by a parent role.

### `GET /swarm/memory/{role}`

View an agent's short-term conversation and long-term facts.

---

## Autonomous Action Tags

Agents emit structured tags in their chat responses (`/swarm/chat`, `/swarm/broadcast`) to trigger local side-effects. These are parsed and executed automatically by the backend.

### `WRITE_FILE:`

Single file creation.

```text
WRITE_FILE: path/to/file.py
# (Code content starts here)
```

### `CREATE_FILES:`

Multi-file generation block.

```text
CREATE_FILES:
--- file1.py ---
(content)
--- file2.py ---
(content)
---END---
```

### `MAKE_DIR:`

Explicit directory creation.

```text
MAKE_DIR: folder/subfolder
```

---

## Artifact Pipeline

### `GET /artifacts`

List all artifacts with status (`pending`, `approved`, `rejected`, `tested`, `integrated`).

### `GET /artifacts/{filename}`

Read artifact content and metadata.

### `GET /artifacts/stats`

Pipeline statistics summary.

### `POST /artifacts/review`

```json
{ "filename": "auth.py", "action": "approve", "notes": "LGTM" }
```

`action`: `"approve"` | `"reject"`

### `POST /artifacts/test`

```json
{ "filename": "auth.py" }
```

Run automated tests. Timeout: 120s.

### `POST /artifacts/integrate`

```json
{ "filename": "auth.py" }
```

Move approved artifact into `swarm_v2_integrated/`.

### `POST /artifacts/deploy`

```json
{ "project_name": "Nexus Platform" }
```

Full autonomous deployment pipeline. Timeout: 300s.

### `POST /artifacts/remediate`

Trigger autonomous remediation of rejected artifacts. Timeout: 300s.

---

## Learning Engine (Phase 3)

### `POST /learning/ingest`

```json
{ "name": "stripe-api", "content": "# Stripe API...", "source": "https://stripe.com/docs" }
```

Ingests documentation text, extracts endpoints/examples, registers a new skill.

**Response:**

```json
{ "status": "learned", "skill": "stripe-api", "endpoints_found": 12, "examples_found": 3 }
```

### `POST /learning/ingest-file`

```json
{ "filepath": "C:/docs/github_api.md" }
```

### `GET /learning/skills`

List all learned skills with usage stats and ingestion log.

**Response:**

```json
{
  "skills": [{ "skill_name": "stripe-api", "endpoints": {}, "usage_count": 4 }],
  "stats": { "total_learned": 1, "total_usages": 4 },
  "log": [{ "action": "learned", "skill": "stripe-api", "timestamp": "..." }]
}
```

### `POST /learning/use`

```json
{ "skill_name": "stripe-api", "task": "create a payment intent for $50 USD", "agent_role": "Lead Developer" }
```

### `DELETE /learning/skills/{name}`

Remove a learned skill from the registry.

---

## MCP Tool Synthesizer (Phase 3)

### `POST /synthesize/mcp`

Generate a complete FastAPI MCP server from a learned skill.

```json
{ "skill_name": "stripe-api", "description": "Stripe MCP bridge", "use_llm": false }
```

Set `use_llm: true` to have Devo review and enhance the code (slower, higher quality).

**Response:**

```json
{
  "status": "synthesized",
  "tool": { "name": "stripe-api", "port": 9100, "file": "swarm_v2_synthesized/stripe-api_server.py" },
  "message": "Run with: python swarm_v2_synthesized/stripe-api_server.py"
}
```

### `POST /synthesize/skill`

```json
{ "skill_name": "stripe-api" }
```

Generate a hot-loadable Python `Skill` class.

| Method | Path | Description |
| :---: | :--- | :--- |
| `POST` | `/synthesize/skill` | Generate Python Skill class from a learned skill |
| `GET` | `/synthesize/tools` | List all synthesized tools |
| `GET` | `/synthesize/log` | View synthesis history & port mappings |

List all synthesized MCP tools with port assignments.

---

## P2P Agent Mesh (Phase 3)

### `GET /mesh/topology`

Full mesh topology — all 12 nodes with status, specialties, task counts.

```json
{
  "version": 110, "total_nodes": 12, "alive": 12, "stale": 0,
  "nodes": [{ "node_id": "64c41ea12216", "name": "Archi", "status": "online" }],
  "connections": []
}
```

### `GET /mesh/stats`

```json
{ "total_nodes": 12, "alive_nodes": 12, "topology_version": 110, "total_tasks_routed": 8 }
```

### `GET /mesh/peers`

Discover peers with optional query filters:

- `?role=Security Auditor`
- `?specialty=Docker`

### `POST /mesh/route`

Route task to the best-matching node automatically.

```json
{ "task": "audit JWT auth for security vulnerabilities" }
```

**Response:**

```json
{
  "routed_to": { "node_id": "c9af0d296bae", "name": "Shield", "role": "Security Auditor" },
  "task": "audit JWT auth for security vulnerabilities",
  "mesh_version": 60
}
```

**Routing scoring:**

- +10 per specialty keyword match
- +8 if role name appears in task
- +5 per skill keyword match
- +20 if `required_specialty` matches
- -0.1 per accumulated task count (load balancing)

### `GET /mesh/log`

Recent mesh events (node joins, task routes). Optional `?limit=N` (default 20).

---

## Global Memory (Phase 3)

### `POST /memory/contribute`

```json
{
  "author": "Devo", "author_role": "Lead Developer",
  "content": "FastAPI Depends() enables clean auth middleware injection",
  "memory_type": "fact",
  "tags": ["fastapi", "auth"]
}
```

`memory_type`: `"fact"` | `"experience"` | `"observation"` | `"skill_use"`

### `POST /memory/query`

Keyword-vector cosine similarity search across all agent memories.

```json
{ "query": "JWT authentication security", "top_k": 5 }
```

**Response:**

```json
{
  "results": [{
    "score": 0.87,
    "entry": { "author": "Shield", "content": "Always validate JWT exp claim...", "memory_type": "fact" }
  }]
}
```

### `GET /memory/stats`

```json
{
  "total_memories": 24,
  "by_type": { "fact": 10, "experience": 14 },
  "by_author": { "Devo": 8, "Shield": 4 },
  "total_accesses": 31, "sync_events": 3
}
```

### `GET /memory/export`

Full JSON export of all global memories.

| Method | Path | Description |
| :---: | :--- | :--- |
| `GET` | `/memory/export` | Export full memory pool |
| `POST` | `/memory/sync/{agent_role}` | Sync agent local memories to global |
| `GET` | `/memory/health` | Check ChromaDB connectivity & occupancy |

Sync an agent's local memories into the global pool.

```bash
curl -X POST http://localhost:8001/memory/sync/Lead%20Developer
```

---

## Error Responses

| Code | Meaning |
| :---: | :--- |
| `200` | Success |
| `400` | Bad request |
| `404` | Not found (unknown skill, artifact, or agent role) |
| `422` | Validation error |
| `500` | Internal error (LLM unavailable, I/O error) |

```json
{ "detail": "Skill 'unknown-api' not found in registry" }
```

---

### System Status Disclaimer

Swarm OS v11 — 35 endpoints across 7 domains — February 2026
