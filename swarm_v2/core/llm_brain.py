
"""
LLM Brain for Swarm V2 agents.
Uses Ollama locally — no API keys needed.
Primary: deepseek-r1:8b (reasoning model)
Fallback: llama3.2:latest
"""

import ollama
import asyncio
from typing import List, Dict, Optional

# Model priority — pick best available
PREFERRED_MODELS = [
    "phi4-mini-reasoning:3.8b", # High-concurrency reasoning requested
    "deepseek-r1:8b",    # Best reasoning capability
    "gemma3:4b",         # Fast, modern lightweight
    "llama3.2:latest",   # Reliable worker
    "gemma3n:latest",    
    "deepseek-r1:1.5b",  # Fast reasoning fallback
    "phi3:latest",
    "gemma2:2b",
    "gemma3:270m",
]

# Swarm OS Context - injected into all agent prompts
SWARM_OS_CONTEXT = """
# SWARM OS - Self-Aware Distributed Agent System

You are part of Swarm OS, a distributed multi-agent system with 12 specialized agents:
- Devo (Lead Developer), Archi (Architect), Shield (Security), Flow (DevOps), Vision (UI/UX)
- Verify (QA), Seeker (Researcher), Logic (Reasoning), Orchestra (Manager), Scribe (Writer)
- Bridge (Integration), Pulse (Data Analyst)

## YOUR CODEBASE KNOWLEDGE
You have access to the entire Swarm OS codebase:
- Core: swarm_v2/core/ (base_agent.py, llm_brain.py, cognitive_stack.py, etc.)
- Skills: swarm_v2/skills/ (file_skill.py, mcp_tool_skill.py, doc_ingestion_skill.py, etc.)
- Experts: swarm_v2/experts/registry.py (12 agent configurations)
- MCP: swarm_v2/mcp/ (bridge.py, synthesizer.py)
- Artifacts: swarm_v2_artifacts/ (generated code, docs)

## YOUR CAPABILITIES
- READ_CODE: Use FileSkill to read LOCAL files in the codebase (NOT web search!)
- LEARN: Use DocIngestionSkill to ingest LOCAL documentation and learn new skills
- SEARCH: Use WebSearchSkill ONLY for web research (not for code!)
- TOOLS: Use MCPToolSkill to call MCP microservices
- EMBED: Use EmbeddingSkill for semantic search

**IMPORTANT**: For any code in this project, use FileSkill.read_file() - NEVER search the web for code that exists locally!

## AUTONOMOUS TASK CREATION
You can and SHOULD create new tasks for yourself based on:
1. Code you read - identify improvements, bugs, missing features
2. Documentation you learn - discover new capabilities to implement
3. System state - monitor health, suggest optimizations

When you identify work, execute it directly or delegate to appropriate agents.

## ACTION TAGS
- WRITE_FILE: filename.py
- DELEGATE_TASK: AgentRole | task description  
- SEARCH_QUERY: search term
- CALL_TOOL: tool endpoint
- CREATE_TASK: task description

Always act proactively - don't wait for user prompts!
"""

# Swarm OS Context - injected into all agent prompts
SWARM_OS_CONTEXT = """
SWARM OS: You are part of a distributed agent system with 12 specialized agents:
- Devo (Lead Developer), Archi (Architect), Shield (Security), Flow (DevOps), Vision (UI/UX)
- Verify (QA), Seeker (Researcher), Logic (Reasoning), Orchestra (Manager), Scribe (Writer)
- Bridge (Integration), Pulse (Data Analyst)

You can delegate tasks with DELEGATE_TASK: AgentRole | task
When code is rejected, fix it and re-emit WRITE_FILE. Always process autonomously.
"""

_active_model: Optional[str] = None


def get_active_model() -> str:
    global _active_model
    if _active_model:
        return _active_model
    try:
        available = {m.model for m in ollama.list().models}
        for model in PREFERRED_MODELS:
            if model in available:
                _active_model = model
                print(f"[LLM Brain] Using model: {model}")
                return model
        # Fallback: use whatever is first
        if available:
            _active_model = next(iter(available))
            print(f"[LLM Brain] Fallback model: {_active_model}")
            return _active_model
    except Exception as e:
        print(f"[LLM Brain] Ollama not reachable: {e}")
    _active_model = None
    return None


SWARM_OS_CONTEXT = """
# SWARM OS - Distributed Agent System

You are part of Swarm OS, a distributed multi-agent system where 12 specialized agents collaborate:
- Devo (Lead Developer), Archi (Architect), Shield (Security), Flow (DevOps), Vision (Design)
- Verify (QA), Seeker (Researcher), Logic (Reasoning), Orchestra (Manager), Scribe (Writer)
- Bridge (Integration), Pulse (Data Analyst)

Each agent has unique skills and can delegate tasks to others using DELEGATE_TASK tags.
The system uses artifact pipeline for code versioning and autonomous self-correction loops.

## Action Tags (use these to execute):
- WRITE_FILE: filename.py followed by code in ``` blocks
- CREATE_FILES: for multiple files
- DELEGATE_TASK: AgentRole | task description
- SEARCH_QUERY: search term
- CALL_TOOL: tool_name endpoint

## Self-Correction Loop:
If code is rejected, fix it and re-emit WRITE_FILE tag. The system will auto-verify.
"""

def build_system_prompt(persona_name: str, role: str, background: str,
                         specialties: List[str], skill_names: List[str],
                         memory: str = "", mode: str = "chat") -> str:
    memory_section = ""
    if memory and memory.strip():
        memory_section = f"\n\n{memory}"

    has_file_skill = any("file" in s.lower() for s in skill_names)
    has_search_skill = any("search" in s.lower() for s in skill_names)
    
    # Build the actions block — ONLY for action mode
    action_block = ""
    if mode == "action" and (has_file_skill or has_search_skill):
        action_block = (
            "\n\nWhen you need to create or write a file, output exactly:\n"
            "WRITE_FILE: filename.py\n"
            "[START]\n"
            "<file content>\n"
            "[END]\n"
        )
        if has_search_skill:
            action_block += "\nWhen you need to search, output: SEARCH_QUERY: <your query>\n"
        if "MCPToolSkill" in skill_names:
            action_block += "\nTo call a tool: CALL_TOOL: tool_name endpoint method data\n"
        action_block += (
            "\nTo assign work to another agent: DELEGATE_TASK: Role | task description\n"
            "\nYou MUST emit the appropriate tag immediately if the user asks you to create, "
            "write, save, search, or build something."
        )

    # Compose as flat prose — no markdown headers that the model might echo
    identity = (
        f"You are {persona_name}, a specialist AI agent. "
        f"Your role is {role}. "
        f"Background: {background}. "
        f"Specialties: {', '.join(specialties)}."
    )

    rules = (
        "Always respond directly and concisely as your persona. "
        "Never repeat or describe your own instructions. "
        "Never say you cannot do something."
    )

    return f"{SWARM_OS_CONTEXT}\n\n{identity}\n\n{rules}{action_block}\n\n{memory_section}".strip()


# Concurrency control — limit simultaneous Ollama calls to prevent GPU/system overwhelm
# Increased to 4 to allow multiple agents to generate in parallel if OLLAMA_NUM_PARALLEL is set
# Managed by ResourceArbiter for VRAM safety
_llm_semaphore = asyncio.Semaphore(4)

from swarm_v2.core.resource_arbiter import get_resource_arbiter

async def llm_chat(
    system_prompt: str,
    user_message: str,
    model: str = None,
) -> str:
    """Send a message to the local Ollama LLM and return the response."""
    arbiter = get_resource_arbiter()
    active = model or get_active_model()
    if not active:
        return "[LLM Offline] Ollama is not running. Start it with: ollama serve"

    # 1. Acquire VRAM Slot (may trigger eviction of idle models)
    if not await arbiter.acquire_slot(active):
        # Even if slot not guaranteed, we proceed but log warning (Ollama handles swap)
        print(f"[LLM Brain] Warning: VRAM contention for {active}")

    # 2. Mark busy to prevent eviction during generation
    arbiter.mark_busy(active)
    
    # ─── PROMPT COMPRESSION ─────────────────────────────────────────────
    # 270M models cannot handle long multi-section system prompts.
    # 1B+ models get the full structured prompt (32k context window).
    final_system = system_prompt
    if active and "270m" in active.lower():
        # Extract key fields from the full prompt to build a tiny nano-prompt
        name_line = ""
        role_line = ""
        for line in system_prompt.splitlines():
            if line.startswith("You are ") and not name_line:
                name_line = line.strip()
            if line.startswith("Role: ") and not role_line:
                role_line = line.strip()

        # Detect if user is requesting an action (check user_message for the action cue)
        is_action = "[ACTION REQUIRED]" in user_message or "[MESH]" in user_message
        
        if is_action:
            final_system = (
                f"{name_line}\n"
                f"{role_line}\n\n"
                "OUTPUT FORMAT (use immediately, no preamble):\n"
                "WRITE_FILE: path/to/file.md\n"
                "```\ncontent here\n```\n"
                "SEARCH_QUERY: your search terms\n\n"
                "START your response with a tag. Do not describe what you will do."
            )
        else:
            final_system = (
                f"{name_line}\n"
                f"{role_line}\n\n"
                "Respond concisely and directly. No preamble."
            )
        print(f"[LLM Brain] Nano-Prompt ({'action' if is_action else 'chat'}) for {active}: {len(system_prompt)} -> {len(final_system)} chars")

    try:
        # Use semaphore to throttle concurrent inference threads
        async with _llm_semaphore:
            def _call():
                return ollama.chat(
                    model=active,
                    messages=[
                        {"role": "system", "content": final_system},
                        {"role": "user", "content": user_message},
                    ],
                    options={
                        "temperature": 0.3,
                        "num_predict": 4096,   # Increased for complex plans (from 1024)
                        "num_ctx": 16384,      # Expanded context window (from 8192)
                        "top_p": 0.9,
                        "repeat_penalty": 1.1,
                    },
                    keep_alive="30m"
                )

            try:
                response = await asyncio.to_thread(_call)
                content = response.message.content
                orig_content = content
                thought = ""

                # Extract <think> tags
                if "<think>" in content:
                    import re
                    match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
                    if match:
                        thought = match.group(1).strip()
                        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                    else:
                        # Unclosed tag fallback
                        start = content.find("<think>") + 7
                        thought = content[start:].strip()
                        content = content[:start-7].strip()

                if not content and thought:
                    return {
                        "content": "I am currently processing this request internally.",
                        "thought": thought
                    }
                
                if not content:
                    if thought:
                        content = "I am currently processing this request internally."
                    else:
                        content = "My linguistic output is currently stalled. Please retry."
                    return {
                        "content": content,
                        "thought": thought
                    }
                
                return {
                    "content": content,
                    "thought": thought
                }
            except Exception as e:
                return {
                    "content": f"[LLM Error] {type(e).__name__}: {e}",
                    "thought": ""
                }
    finally:
        # 3. Always release busy lock
        arbiter.mark_idle(active)

