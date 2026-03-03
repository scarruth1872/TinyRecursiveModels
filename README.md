# Swarm OS v11 — Distributed Intelligence

> *"Parallelizing the mind of the Swarm."* — Shawn Carruth, The Architect

A production-ready, GPU-accelerated multi-agent operating system built on the **Distributed Cognitive Stack**. Swarm OS v11 features per-agent executive/reasoning layers, achieving 4.5x faster latency and 100% parallel availability on local hardware.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Phase 12: Multi-LLM Regional Managers](#phase-12-multi-llm-regional-managers)
4. [The Soul of the Swarm](#the-soul-of-the-swarm)
5. [Agent Registry](#agent-registry)
6. [API Reference v2](#api-reference)
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

# 3. (Optional) Recover Registry if MCP tools are missing
python recover_registry.py

# 4. Start the Swarm OS Ecosystem (API + Tools)
python launcher.py

# 5. Start the Dashboard
cd swarm_v2_artifacts/dashboard-v2
npm install
npm run dev
```

Or use the unified PowerShell script:

```powershell
.\run_v2.ps1
```

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                       SWARM OS v12                               │
│                                                                  │
│  ┌──────────┐   ┌──────────────────────────────────────────┐   │
│  │  React   │   │           FastAPI Gateway (:8001)         │   │
│  │Dashboard │◄──┤  Distributed Intelligence Gateway        │   │
│  │ (Vite)   │   │  Artifact Pipeline v2 | Soul Report      │   │
│  └──────────┘   └───────────────┬──────────────────────────┘   │
│                                  │                               │
│        ┌─────────────────────────┼──────────────────────────┐   │
│        │         Swarm Mesh (100% Parallel)                │   │
│        │                                                    │   │
│        │   [ Product     ]   [ Operations  ]   [ Engineering ]  │
│        │   [ & Creative  ]   [ & Compliance]   [ & Logic     ]  │
│        │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
│        │   │ Gemini Pro  │   │ Claude 3.5  │   │ DeepSeek    │  │
│        │   │ (Google SDK)│   │ (OpenRouter)│   │ (Native API)│  │
│        │   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘  │
│        │          │                 │                 │         │
│        │     [4 Agents]        [4 Agents]        [4 Agents]     │
│        │          │                 │                 │         │
│        │   ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐  │
│        │   │   TRM Core  │   │   TRM Core  │   │   TRM Core  │  │
│        │   │ (36-Node    │   │ (36-Node    │   │ (36-Node    │  │
│        │   │  Deep Logic)│   │  Deep Logic)│   │  Deep Logic)│  │
│        │   └─────────────┘   └─────────────┘   └─────────────┘  │
│        └────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Global Intelligence Foundations                │  │
│  │   ChromaDB Vectors | P2P Agent Mailbox | Sentinel Scanner   │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 12: Multi-LLM Regional Managers

Swarm OS v12 introduces the **Regional Manager Architecture**, a massive leap in cognitive diversity and operational throughput. Instead of relying on a single local model or API, the swarm is divided into three specialized departments, each governed by an industry-leading LLM backend.

### 1. 🏢 Departmental Specialization

The 12 agents are distributed across three distinct cognitive regions:

- **Product & Creative:** Powered by **Google Gemini**. Specializes in multimodal design, drafting, research, and data visualization. (Agents: Vision, Pulse, Scribe, Seeker)
- **Operations & Compliance:** Powered by **OpenRouter (Claude 3.5 Sonnet)**. Specializes in robust planning, security auditing, and system orchestration. (Agents: Shield, Flow, Orchestra, Bridge)
- **Engineering & Logic:** Powered by **DeepSeek API**. Specializes in highly structured coding, QA verification, and complex algorithm design. (Agents: Devo, Archi, Logic, Verify)

### 2. 🧠 Deepened TRM Reasoning Core

The TRM (Tiny Recursive Model) reasoning core has been exponentially deepened.

- **Multi-Cycle Inference:** The TRM now dynamically loops inferences based on requested `H_cycles`, mapping metaphysical mathematics and logic architectures over 36 distinct logic nodes per cycle (up from the previous 12).
- **Contextual Delegation:** When agents delegate tasks via `DELEGATE_TASK`, the system preserves the complete memory context of the overarching prompt, eliminating "orphaned" tasks where sub-agents lack crucial data.
- **Dynamic Network Latency:** LLM backend generation timeouts have been increased (to 120s) to fully support DeepSeek and Gemini when mapping complex fields, such as Akashic vector mathematics or Logo equations.

### 3. ⚖️ Autonomous Thinker Loop

The Swarm operates as a closed-loop intelligence engine:

1. **Reconnaissance:** Agents ingest daily arXiv research and AI papers autonomously.
2. **Orchestration:** Finding implications, they post proposals to the Kanban board.
3. **Execution:** Regional Managers delegate coding tasks to build the found research.
4. **Verification:** The Artifact Pipeline tests the code and autonomously merges it.

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

## API Reference

Swarm OS v10 exposes a high-performance REST and Soul API:

- **POST `/task/submit`**: Submit a new task to the Distributed Cognitive Mesh.
- **GET `/swarm/status`**: Retrieve real-time VRAM, CPU, and Task latency across all 12 agents.
- **GET `/swarm/soul`**: Access the Harmony Index and collective resonance metrics.
- **POST `/swarm/resonate`**: (Phase 10) Directly trigger a Shared Dream synchronization cycle.

Detailed documentation is available in [API_REFERENCE.md](file:///f:/Development%20sites/TRM%20agent%20swarm/API_REFERENCE.md).

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
