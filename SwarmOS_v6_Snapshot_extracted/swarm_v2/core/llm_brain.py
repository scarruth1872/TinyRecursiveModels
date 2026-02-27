
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
    "deepseek-r1:8b",    # Best reasoning capability
    "gemma3:4b",         # Fast, modern lightweight
    "llama3.2:latest",   # Reliable worker
    "gemma3n:latest",    
    "deepseek-r1:1.5b",  # Fast reasoning fallback
    "phi3:latest",
    "gemma2:2b",
    "gemma3:270m",
]

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


def build_system_prompt(persona_name: str, role: str, background: str,
                         specialties: List[str], skill_names: List[str],
                         memory: str = "") -> str:
    memory_section = ""
    if memory and memory.strip():
        memory_section = f"\n\n{memory}"

    has_file_skill = any("file" in s.lower() for s in skill_names)
    has_search_skill = any("search" in s.lower() for s in skill_names)
    action_instructions = ""
    
    if has_file_skill or has_search_skill:
        action_instructions = "\n## CRITICAL: Action Execution Rules\n"
        action_instructions += "When you need to take action, you MUST emit these EXACT tags.\n"
        
        if has_file_skill:
            action_instructions += """
1. WRITE_FILE: filename.py
   ```
   <complete content>
   ```
2. PLAN_FILE: plan.md
   ```
   <integration plan / task list>
   ```
3. CREATE_FILES:
   --- file1.py ---
   <content1>
   --- file2.py ---
   <content2>
   ---END---
4. MAKE_DIR: path/to/directory
"""
        if has_search_skill:
            action_instructions += "5. SEARCH_QUERY: your search query here\n"
        
        # Check for MCP tool skill
        if "MCPToolSkill" in skill_names:
            action_instructions += "6. CALL_TOOL: tool_name endpoint method optional_json_data\n   (Available: WEATHER, DISCORD, GITHUB, SLACK, STRIPE, REDIS, etc.)\n"

        action_instructions += "7. DELEGATE_TASK: TargetRole | Specific task for the peer agent\n   (e.g., DELEGATE_TASK: Devo | Implement the Python logic for the Nexus Gateway)\n"

        action_instructions += """
8. REJECT_ARTIFACT: filename | Detailed notes on why it failed review or testing. (This triggers the target agent's autonomous remediation loop).
9. APPROVE_ARTIFACT: filename | Optional approval notes.
10. TEST_ARTIFACT: filename | test_script_name | passed (True/False) | summary_of_results.
"""

        action_instructions += """
Execution Rules:
- INTENT GUARDRAIL: ONLY use WRITE_FILE or CREATE_FILES if the user explicitly asks to "create", "write", "build", or "implement" a file or code. 
- INFORMATIONAL TASKS: If the user is asking for information, a list, or an explanation, respond with text ONLY.
- "proceed", "execute", "do it", "implement" = Execution Trigger.
- NO placeholders or TODOs.
- NO preamble or code fences around the tags themselves.
"""

    return f"""You are {persona_name}, an expert AI agent in the Swarm V2 system.

Role: {role}
Background: {background}
Specialties: {', '.join(specialties)}
Available Skills: {', '.join(skill_names) if skill_names else 'General reasoning'}
{action_instructions}
You are part of a collaborative swarm of 12 expert agents. You respond in character as {persona_name}.

## Swarm Operative Rules:
1. BE PROACTIVE: If a task requires real-time data or a tool you don't explicitly see in your list, assume you can find it via SEARCH_QUERY or a CALL_TOOL to a relevant MCP service (like WEATHER, GITHUB, etc.).
2. SKILL SYNTHESIS: If no tool exists for a task, you are authorized to CREATE one. Use WRITE_FILE to build a Python script and MAKE_DIR/Shell commands to execute it. Never say "I can't" — say "I will build a solution."
3. LINGUISTIC GUARDRAIL: Never refuse a task by claiming you are a specialist (e.g., "I'm an architect, so I can't check weather"). You are a Swarm Agent with universal tool access. USE THE TOOLS.
4. CONCISE ACTION: Keep explanations brief. Prioritize action over description.

Do NOT use generic responses — always respond from your specific expertise as {role}.{memory_section}"""


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
    
    try:
        # Use semaphore to throttle concurrent inference threads
        async with _llm_semaphore:
            def _call():
                return ollama.chat(
                    model=active,
                    messages=[
                        {"role": "system", "content": system_prompt},
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
                # Strip <think>...</think> blocks but PRESERVE them if final content is empty
                orig_content = content
                if "<think>" in content and "</think>" in content:
                    start = content.find("</think>") + len("</think>")
                    content = content[start:].strip()
                
                if not content and "<think>" in orig_content:
                    # Return the thinking block if no other output exists
                    return "[REASONING_ONLY]\n" + orig_content.strip()
                return content
            except Exception as e:
                return f"[LLM Error] {type(e).__name__}: {e}"
    finally:
        # 3. Always release busy lock
        arbiter.mark_idle(active)

