# Swarm OS v11 — Architecture Reference

**Version:** 11.0 (Phase 11: Recursive Self-Optimization)  
**Date:** February 23, 2026

---

## Directory Layout

```text
swarm_v2/
├── app_v2.py                    # Swarm OS Gateway — Soul Endpoint & API
├── core/
│   ├── artifact_pipeline.py     # [v11] Optimized Artifact Lifecycle (Async Batching)
│   ├── cognitive_stack.py       # Distributed Cognitive Stack (Executive + TRM)
│   ├── agent_mesh.py            # P2P Mesh Federation & Node Registry
│   ├── monitor_daemon.py        # Self-Healing & Infrastructure Monitoring
│   └── heartbeat_scheduler.py   # Proactive Autonomy & Mesh Heartbeats
├── experts/
│   └── registry.py              # 12 Core Agents Persona Definitions
└── mcp/
    └── synthesizer.py           # On-demand Tool Synthesis
launcher.py                     # Unified Service Orchestrator
start_tools.py                  # MCP Specialized Microservices Manager
recover_registry.py             # Fault-tolerant Registry Synchronization
```

---

## Distributed Cognitive Stack

The core innovation of v11 is **Parallel Symbolic Processing**.

### 1. The Stack Architecture

Each agent utilizes a local `CognitiveStack`:

- **Executive Layer (Gemma 3 270M)**: Contextual language processing and tool orchestration.
- **Reasoning Core (Samsung TRM 7M)**: Symbolic logic refinement and mathematical verification.

### 2. Startup Optimization (Fast Boot V2)

To prevent port-binding deadlocks during massive artifact indexing, v11 implements **Deferred Background Activation**:

- **Socket Isolation**: The FastAPI server binds to port `8001` immediately.
- **Async Yielding**: Intensive background loops (Monitor, Scanner, Proactive Loops) are deferred via a 2-second safety delay (`delayed_loops` task), ensuring the dashboard can connect instantly.

---

## Artifact Pipeline & Security

### 1. High-Performance Indexing

The `ArtifactPipeline` now implements dependency-aware scanning. It automatically ignores massive directories like `node_modules` and `venv`, allowing the system to handle enterprise-scale codebases without stalling the event loop.

### 2. Sentinel Security Layer

Every artifact is automatically audited by the **Security Auditor** (Shield) before synthesis. Unsafe code is quarantined, while approved plans are integrated into the `swarm_v2_integrated` workspace.

---

*Swarm OS v11 Architecture — Phase 11: Recursive Self-Optimization — February 2026*
