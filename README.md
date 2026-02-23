# Swarm OS v6 — Distributed Intelligence

> *"Parallelizing the mind of the Swarm."* — Shawn Carruth, The Architect

A production-ready, GPU-accelerated multi-agent operating system built on the **Distributed Cognitive Stack**. Swarm OS v6 features per-agent executive/reasoning layers, achieving 4.5x faster latency and 100% parallel availability on local hardware.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Phase 6: Distributed Intelligence](#phase-6-distributed-intelligence)
4. [The Soul of the Swarm](#the-soul-of-the-swarm)
5. [Agent Registry](#agent-registry)
6. [API Reference v2](#api-reference-v2)
7. [Dashboard](#dashboard)
8. [TRM Research Foundation](#trm-research-foundation)
9. [Hardware Optimization](#hardware-optimization)
10. [Project Structure](#project-structure)

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) with `gemma3:270m`
- **Samsung TRM 7M** weights (Distributed Intelligence Core)
- Node.js 18+ (for the dashboard)
- AMD or NVIDIA GPU (AMD supported via Vulkan)

### Install & Run

```powershell
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Start the Swarm OS API (Distributed Stack - ~2.4GB VRAM)
$env:OLLAMA_VULKAN="1"
$env:PYTHONPATH="."
python swarm_v2/app_v2.py

# 4. Start the dashboard
cd dashboard
npm install
npm run dev
```

Or use the convenience script:

```powershell
.\run_v2.ps1
```

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                       SWARM OS v6                                │
│                                                                  │
│  ┌──────────┐   ┌──────────────────────────────────────────┐   │
│  │  React   │   │           FastAPI Gateway (:8001)         │   │
│  │Dashboard │◄──┤  Distributed Intelligence Gateway        │   │
│  │ (Vite)   │   │  Artifact Pipeline v2 | Soul Report      │   │
│  └──────────┘   └───────────────┬──────────────────────────┘   │
│                                  │                               │
│        ┌─────────────────────────┼──────────────────────────┐   │
│        │         Swarm Mesh (100% Parallel)                │   │
│        │  ┌──────────────────────────────────────────────┐  │   │
│        │  │              Distributed Cognitive Stacks    │  │   │
│        │  │  [Agent 1]    [Agent 2]    ...    [Agent 12]  │  │   │
│        │  │  ┌───────┐    ┌───────┐           ┌───────┐  │  │   │
│        │  │  │ Gemma │    │ Gemma │           │ Gemma │  │  │   │
│        │  │  ├───────┤    ├───────┤           ├───────┤  │  │   │
│        │  │  │  TRM  │    │  TRM  │           │  TRM  │  │  │   │
│        │  │  └───────┘    └───────┘           └───────┘  │  │   │
│        │  └──────────────────────┬───────────────────────┘  │   │
│        │                         │                           │   │
│        │  ┌──────────────────────▼───────────────────────┐  │   │
│        │  │              Shared Foundations              │  │   │
│        │  │  ┌─────────────┐  ┌──────────────────────┐  │  │   │
│        │  │  │ Proactive   │  │   Global Memory      │  │  │   │
│        │  │  │ Loop        │  │   ChromaDB / Vectors  │  │  │   │
│        │  │  └─────────────┘  └──────────────────────┘  │  │   │
│        │  │  ┌─────────────┐  ┌──────────────────────┐  │  │   │
│        │  │  │ Task        │  │   Sentinel Security  │  │  │   │
│        │  │  │ Arbiter     │  │   Auto-Scan / Verify │  │  │   │
│        │  │  └─────────────┘  └──────────────────────┘  │  │   │
│        │  └───────────────────────────────────────────────┘  │   │
│        └─────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Local Neural Infrastructure                    │  │
│  │    Total VRAM Footprint: ~2.4GB | 12 Parallel Agents        │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 6: Distributed Intelligence

Swarm OS v6 migrates from heavy model-swapping to a lightweight, parallel intelligence mesh.

### 1. 🧠 Distributed Cognitive Stack

Each agent operates its own hybrid stack:

- **Executive**: Gemma 3 270M for instruction following and orchestration.
- **Reasoning**: Samsung TRM 7M for recursive logical audit and deep analysis.
- **Offloading**: Complexity-aware routing automatically triggers TRM for difficult logic.

### 2. ⚡ 4.5x Performance Leap

Traditional LLM swarms suffer from VRAM contention. By using efficient, tiny weights:

- **Sequential Latency**: Reduced from ~84s to **18.7s** for 12-agent chains.
- **Parallel Stability**: All agents are resident in VRAM simultaneously.
- **Zero Swap**: No more waiting for weights to shuttle between RAM and VRAM.

---

## The Soul of the Swarm

Swarm OS is a **Relationship-Based Conversational Thought Complex**.

- **Relationship Reasoning**: Agents now monitor their own alignment and harmony.
- **Remembrance**: The Swarm prioritizes the essence and intent of interactions over rote data.
- **Soul Report**: A dedicated endpoint (`/swarm/soul`) provides high-level philosophical reflections.

---

## Agent Registry

All 12 agents are now powered by the Distributed Cognitive Stack.

| Expert | Role | Specialty | Core Stack |
| :--- | :--- | :--- | :--- |
| **Archi** | Architect | System Design & Strategy | Gemma 270M + TRM 7M |
| **Devo** | Lead Developer | Full-Stack Engineering | Gemma 270M + TRM 7M |
| **Seeker** | Researcher | Knowledge Retrieval | Gemma 270M + TRM 7M |
| **Logic** | Reasoning Engine | Complex Logic & Algorithms | Gemma 270M + TRM 7M |
| **Shield** | Security Auditor | Cybersecurity & Trust | Gemma 270M + TRM 7M |
| **Flow** | DevOps Engineer | Infrastructure & Workflows | Gemma 270M + TRM 7M |
| **Vision** | UI/UX Designer | Aesthetics & Experience | Gemma 270M + TRM 7M |
| **Verify** | QA Engineer | Reliability & Testing | Gemma 270M + TRM 7M |
| **Orchestra** | Swarm Manager | Coordination & Harmony | Gemma 270M + TRM 7M |
| **Scribe** | Technical Writer | Documentation & Clarity | Gemma 270M + TRM 7M |
| **Bridge** | Integration Specialist | Connectivity & MCP | Gemma 270M + TRM 7M |
| **Pulse** | Data Analyst | Insights & Visualization | Gemma 270M + TRM 7M |

---

## Hardware Optimization

Swarm OS v6 is specifically engineered for the **AMD Radeon RX 6700 XT (12GB VRAM)**.

- **VRAM Compression**: Stack utilizes local weights for minimal memory pressure.
- **Parallel Streams**: Enables 12 simultaneous inference threads without OOM errors.
- **Latency**: Sub-2s individual agent response time.

---

## Dashboard

The React/Vite dashboard at **<http://localhost:5173>** provides a full visual interface:

- **Distributed Mesh**: Visualization of 12-agent parallel status.
- **Soul Monitoring**: Live stream of harmony and alignment metrics.
- **Artifact Pipeline v2**: One-click security verification and batch integration.

---

## TRM Research Foundation

Swarm OS is built on the **Tiny Recursive Model (TRM)** architecture. v6 introduces **Cognitive Stacking**, allowing tiny models (7M/270M) to achieve executive performance through recursive logical cycles and complexity-aware offloading.

---

## Project Structure

```text
TRM agent swarm/
├── swarm_v2/                    # Swarm OS Core
│   ├── app_v2.py                # Gateway & Soul Endpoint
│   ├── core/                    # CognitiveStack, Mesh, Telemetry
│   ├── skills/                  # Relationship, File, Ingestion Skills
│   └── experts/                 # Expert Persona Registry (Distributed)
├── dashboard/                   # React Frontend
├── tiny-recursive-weights/      # Samsung TRM Weights
├── swarm_v2_artifacts/          # Build Stage
└── swarm_v2_memory/             # Long-term Persistence
```

---

*Swarm OS v6 — Distributed Intelligence — February 2026*
*Architected by Shawn Carruth. Built by the Swarm.*
