# Swarm OS v6 — Architecture Reference

**Version:** 6.0 (Phase 6: Distributed Intelligence)  
**Date:** February 23, 2026

---

## Directory Layout

```text
swarm_v2/
├── app_v2.py                    # Swarm OS Gateway — Soul Endpoint & API
├── core/
│   ├── cognitive_stack.py       # [v6] Hybrid Intelligence (Gemma + TRM)
│   ├── base_agent.py            # BaseAgent: Stack integration & persona
│   ├── telemetry.py             # [v6] Distributed Pulse Monitoring
│   ├── proactive_loop.py        # Proactive Orchestration Loop
│   ├── manus_engine.py          # Parallel Task Superposition
│   └── global_memory.py         # Distributed Vector Store (ChromaDB)
├── experts/
│   └── registry.py              # Distributed Agent Registry (12 Core Agents)
└── skills/
    └── relationship_skill.py    # Philosophical Alignment & Soul Report
```

---

## Distributed Cognitive Stack

The core innovation of v6 is the elimination of centralized model bottlenecks.

### 1. The Stack Architecture

Each agent owns a local `CognitiveStack` instance:

- **Executive Layer (Gemma 3 270M)**: Handles natural language, instructions, and tool orchestration.
- **Reasoning Core (Samsung TRM 7M)**: Processes logically dense tasks using recursive symbolic refinement.

### 2. Complexity-Aware Offloading

`BaseAgent` automatically classifies incoming tasks:

- **Low Complexity**: Executed directly by the Executive Layer.
- **High Complexity**: Routed to the TRM Reasoning Core for deep logical audit.

---

## Resource Management: From Arbiter to Autonomy

In v6, the `ResourceArbiter` has been simplified. Because the total VRAM footprint of all 12 agents is only **~2.4GB**, the previous logic for model-swapping and slot acquisition has been retired.

- **Parallel Availability**: 100% of agents are resident and ready at all times.
- **VRAM Stability**: The system maintains a constant, low-pressure profile on the AMD 6700 XT.

---

## The Soul & Telemetry

### 1. Soul Report (`/swarm/soul`)

Powered by the `RelationshipReasoningSkill`, this aggregates the swarm's philosophical state, harmony index, and autonomous evolution proposals.

### 2. Distributed Telemetry (`/swarm/telemetry`)

Provides a live feed of per-agent stack health, reasoning call frequency, and global mesh coherence.

---

*Swarm OS v6 Architecture — Phase 6: Distributed Intelligence — February 2026*
