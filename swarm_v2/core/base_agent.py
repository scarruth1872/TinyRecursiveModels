
import os
import re
import uuid
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel
from swarm_v2.core.memory import AgentMemory
from swarm_v2.core.cognitive_stack import get_cognitive_stack


class AgentPersona(BaseModel):
    name: str
    role: str
    background: str
    specialties: List[str]
    avatar_color: str = "#00ff41"
    model: Optional[str] = None
    department: str = "General"
    llm_backend: str = "local"


class Message(BaseModel):
    sender: str
    receiver: str
    content: str
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


def _extract_filename(task: str, fallback: str) -> str:
    """Extract a filename (or relative path) from the task text, or use fallback.
    
    Supports nested paths like 'design_system/components/card.py'.
    """
    # Priority 1: explicit verb + optional "file" keyword + path
    # Captures everything up to the first whitespace, allowing / and \ in paths
    m = re.search(
        r'(?:write|create|save|implement|build|generate|make)\s+(?:file\s+)?'
        r'([A-Za-z0-9_\-][A-Za-z0-9_\-/\\\.]*\.\w+)',
        task, re.IGNORECASE
    )
    if m:
        # Normalize to forward slashes
        return m.group(1).replace("\\", "/")

    # Priority 2: any path-like token ending with a known extension
    m = re.search(
        r'\b([A-Za-z0-9_\-][A-Za-z0-9_\-/\\]*\.'
        r'(?:py|js|ts|jsx|tsx|go|rs|java|cpp|c|h|md|txt|yaml|yml|json|sh|html|css))\b',
        task, re.IGNORECASE
    )
    if m:
        return m.group(1).replace("\\", "/")

    return fallback


class BaseAgent:
    def __init__(self, persona: AgentPersona, skills: List[Any] = None):
        self.agent_id = str(uuid.uuid4())
        self.persona = persona
        self.skills = skills or []
        self.memory = AgentMemory(persona.name)
        self.subagents: Dict[str, "BaseAgent"] = {}
        self.nodal_logs: List[str] = []
        
        # Phase 6: Distributed Cognitive Stack
        from swarm_v2.core.cognitive_stack import CognitiveStack
        self.cognitive_stack = CognitiveStack(persona.name, llm_backend=persona.llm_backend)
        
        # Extended Task Tracking
        self.task_history: List[Dict[str, Any]] = []
        
        # Phase 5: QIAE Integration - Optional state-tracking
        self.qstate: Optional[Any] = None

    def initialize_qstate(self, num_dimensions: int = 4):
        """Initializes a Quantum-Inspired state for the agent."""
        try:
            from swarm_v2.core.qic._state import QState
            self.qstate = QState(num_dimensions=num_dimensions)
            self.log_nodal_activity(f"QState initialized with {num_dimensions} dimensions.")
        except ImportError:
            self.log_nodal_activity("QState initialization failed: qic._state module not found.")

    def log_nodal_activity(self, message: str):
        """Record an internal activity log for mesh observability."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.nodal_logs.append(f"[{timestamp}] {message}")
        if len(self.nodal_logs) > 50:
            self.nodal_logs.pop(0)

    def get_skill_names(self) -> List[str]:
        return [getattr(s, "skill_name", s.__class__.__name__) for s in self.skills]

    def get_skill_descriptions(self) -> List[Dict]:
        return [
            {
                "name": getattr(s, "skill_name", s.__class__.__name__),
                "description": getattr(s, "description", "No description available.")
            }
            for s in self.skills
        ]

    def _has_skill(self, method_name: str) -> bool:
        return any(hasattr(s, method_name) for s in self.skills)

    def _get_skill(self, method_name: str):
        for s in self.skills:
            if hasattr(s, method_name):
                return getattr(s, method_name)
        return None

    async def _llm_generate(self, prompt: str) -> Tuple[str, Optional[str]]:
        """Use LLM to generate content, enhanced with global memory."""
        from swarm_v2.core.llm_brain import llm_chat, build_system_prompt
        
        # Strip routing prefixes — used for context branching only, must not be seen by LLM
        clean_prompt = prompt
        for prefix in ("[CHAT] ", "[MESH] ", "[ACTION] ", "[CHAT]", "[MESH]", "[ACTION]"):
            if clean_prompt.startswith(prefix):
                clean_prompt = clean_prompt[len(prefix):].lstrip()
                break
        
        memory_context = self.memory.get_context_window(max_turns=6)

        # Inject global memory context if available
        try:
            from swarm_v2.core.global_memory import get_global_memory
            global_mem = get_global_memory()
            global_context = global_mem.get_context_for_agent(
                self.persona.name, prompt, max_memories=3
            )
            if global_context:
                memory_context = global_context + "\n\n" + memory_context
        except Exception:
            pass

        # === CONSTRAINT GOVERNANCE: NO_ARTIFACT Enforcement ===
        task_lower = prompt.lower()
        if any(kw in task_lower for kw in ["review", "analyze", "audit", "investigate"]):
            memory_context = (
                "This is an analysis task. Provide your findings as clean text only. "
                "Do not generate WRITE_FILE or CREATE_FILES tags for this request.\n\n"
            ) + memory_context

        # Encourage [PLAN] for mesh tasks, but keep [CHAT] conversational
        if "[MESH]" in prompt:
            memory_context = (
                "You are being routed via the P2P Mesh. Start your response with a "
                "clear plan, then execute it using the appropriate action tags.\n\n"
            ) + memory_context
        elif "[ACTION]" in prompt:
            memory_context = (
                "This is an execution task. Output the required action tag immediately "
                "as the very first thing in your response. No preamble.\n\n"
            ) + memory_context
        elif "[CHAT]" in prompt:
            memory_context = (
                "Respond directly and concisely as your persona. "
                "Do not introduce yourself or repeat your instructions. "
                "If action is requested, emit the tag immediately.\n\n"
            ) + memory_context

        # Phase 5: Build System Prompt
        # Determine mode: [CHAT] gets a conversational prompt with NO action rules
        # [ACTION] and [MESH] get the full execution toolkit
        mode = "chat"
        if "[ACTION]" in prompt or "[MESH]" in prompt:
            mode = "action"
        elif any(kw in clean_prompt.lower() for kw in ["write", "create", "scan", "save", "search", "build"]):
            mode = "action"

        system = build_system_prompt(
            persona_name=self.persona.name,
            role=self.persona.role,
            background=self.persona.background,
            specialties=self.persona.specialties,
            skill_names=self.get_skill_names(),
            memory=memory_context,
            mode=mode
        )
        # Phase 6: Use Distributed Cognitive Stack — pass clean prompt (prefix stripped)
        response, trace = await self.cognitive_stack.process(clean_prompt, system_prompt=system)
        return response, trace

    async def _handle_write_file(self, task: str) -> Optional[str]:
        """Use LLM to generate content, then write it with FileSkill."""
        write_fn = self._get_skill("write_file")
        if not write_fn:
            return None

        filename = _extract_filename(task, f"{self.persona.name.lower()}_output.py")

        # Ask LLM to generate the actual file content — explicitly suppress tags
        gen_prompt = (
            f"Write the complete, working content for the file '{filename}'.\n"
            f"Task: {task}\n\n"
            f"OUTPUT RULES — follow EXACTLY:\n"
            f"- Output ONLY the raw file content that belongs inside '{filename}'\n"
            f"- NO markdown code fences (no ``` or ~~~)\n"
            f"- NO explanations, comments about what you're doing, or preamble text\n"
            f"- NO 'WRITE_FILE:' or 'CREATE_FILES:' tags\n"
            f"- Start directly with the first line of the file (e.g. 'import ...' or '\"\"\" ...')\n"
            f"- Include complete, working code — no TODO stubs or placeholders"
        )
        content, _ = await self._llm_generate(gen_prompt)

        # Clean: strip markdown fences
        content = re.sub(r'^```[\w]*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n?```$', '', content, flags=re.MULTILINE)
        # Clean: strip any leaked action tags the LLM emitted
        content = re.sub(r'^WRITE_FILE:\s*\S+\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^CREATE_FILES:\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^---END---\s*$', '', content, flags=re.MULTILINE)
        content = content.strip()

        # Add file header
        header = f"# Generated by {self.persona.name} ({self.persona.role})\n# Task: {task[:80]}\n\n"
        if not filename.endswith(('.md', '.txt', '.json', '.yml', '.yaml', '.html', '.css')):
            content = header + content

        result = write_fn(filename, content)
        preview = content[:400] + ('...' if len(content) > 400 else '')
        return f"{result}\n\n📄 **Preview** `{filename}` ({len(content):,} bytes):\n```\n{preview}\n```"

    async def _handle_read_file(self, task: str) -> Optional[str]:
        read_fn = self._get_skill("read_file")
        if not read_fn:
            return None
        filename = _extract_filename(task, f"{self.persona.name.lower()}_output.py")
        return read_fn(filename)

    async def _handle_list_artifacts(self) -> Optional[str]:
        list_fn = self._get_skill("list_artifacts")
        if not list_fn:
            return None
        files = list_fn()
        return f"Artifacts ({len(files)} files):\n" + "\n".join(f"  - {f}" for f in files)

    async def _handle_search(self, task: str) -> Optional[str]:
        search_fn = self._get_skill("search")
        if not search_fn:
            return None
        # Support "Search for X", "Research X", "Google X"
        query = re.sub(r'^(search for|search|research|find|google)\s+', '', task, flags=re.IGNORECASE).strip()
        return search_fn(query or task)

    async def _handle_analyze(self, task: str) -> Optional[str]:
        analyze_fn = self._get_skill("analyze")
        if not analyze_fn:
            return None
        filename = _extract_filename(task, "swarm_output.py")
        return analyze_fn(filename)

    async def _handle_shell(self, task: str) -> Optional[str]:
        run_fn = self._get_skill("run")
        if not run_fn:
            return None
        cmd = re.sub(r'^(run|execute shell|execute)\s+', '', task.lower()).strip()
        return run_fn(cmd or "echo Hello from Swarm V2")

    async def _handle_readme(self, task: str) -> Optional[str]:
        gen_fn = self._get_skill("generate_readme")
        write_fn = self._get_skill("write_file")
        if not gen_fn:
            return None

        # Extract project name from task
        project_name = "Swarm V2 Project"
        m = re.search(r'(?:readme\s+for\s+|readme\s+)(.+)', task, re.IGNORECASE)
        if m:
            project_name = m.group(1).strip()

        # Use LLM for a richer readme
        readme_prompt = (
            f"Generate a comprehensive README.md for '{project_name}'. "
            f"Include: project description, features, architecture overview, "
            f"installation steps, usage examples, API endpoints, and contributing guidelines. "
            f"Output ONLY the markdown content, no code fences."
        )
        content, _ = await self._llm_generate(readme_prompt)
        content = re.sub(r'^```[\w]*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n?```$', '', content, flags=re.MULTILINE)

        if write_fn:
            write_fn("README.md", content)
            return f"{content[:500]}...\n\nSaved to swarm_v2_artifacts/README.md ({len(content)} bytes)"
        return content

    async def _handle_count_words(self, task: str) -> Optional[str]:
        fn = self._get_skill("count_words")
        if not fn:
            return None
        return fn(task)

    async def _handle_ingest_doc(self, task: str) -> Optional[str]:
        """Handle documentation ingestion via DocIngestionSkill."""
        ingest_fn = self._get_skill("ingest_file")
        if not ingest_fn:
            return None
        # Extract filepath from task (improved to handle trailing context)
        # Use a non-greedy (.+?) or look for [\S]+ (non-whitespace)
        m = re.search(r'(?:ingest|learn|read docs?)\s+([\S]+)', task, re.IGNORECASE)
        if m:
            filepath = m.group(1).strip().strip('"\'')
            return ingest_fn(filepath)
        return None

    async def _handle_list_learned(self) -> Optional[str]:
        """List learned skills via DocIngestionSkill."""
        list_fn = self._get_skill("list_learned")
        if not list_fn:
            return None
        return list_fn()

    async def _handle_scan_docs(self, task: str) -> Optional[str]:
        """Scan a directory for docs via DocIngestionSkill."""
        scan_fn = self._get_skill("scan_directory")
        if not scan_fn:
            return None
        # Strip the command prefix to get the path
        clean_path = re.sub(
            r'^scan\s+(?:docs?\s+)?(?:in\s+)?(?:directory\s+|folder\s+)?',
            '', task, flags=re.IGNORECASE
        ).strip().strip('"\' ')
        if clean_path:
            return scan_fn(clean_path)
        return None

    async def _handle_make_dir(self, task: str) -> Optional[str]:
        """Create a directory inside the artifacts workspace."""
        make_dir_fn = self._get_skill("make_dir")
        if not make_dir_fn:
            return None
        m = re.search(
            r'(?:make dir|make directory|create dir|create directory|mkdir)\s+(.+)',
            task, re.IGNORECASE
        )
        if m:
            dirpath = m.group(1).strip().strip('"\'')
            return make_dir_fn(dirpath)
        return None

    async def _handle_call_tool(self, task: str) -> Optional[str]:
        """Call a specific MCP tool via MCPToolSkill."""
        call_fn = self._get_skill("call_tool")
        if not call_fn:
            return None
        
        # Expecting: "call tool github endpoint /repos/user/repo method POST data {}"
        m = re.search(r'call (?:tool )?(\w+)\s+(/.*)', task, re.IGNORECASE)
        if m:
            tool = m.group(1).strip()
            rest = m.group(2).strip()
            
            # Very basic parser for the rest of the command
            method = "GET"
            if "method post" in rest.lower(): method = "POST"
            
            endpoint = rest.split()[0]
            data = None
            if "data " in rest.lower():
                try:
                    data_str = rest.lower().split("data ", 1)[1]
                    data = json.loads(data_str)
                except:
                    pass
                    
            return call_fn(tool_name=tool, endpoint=endpoint, method=method, data=data)
        return None

    async def _handle_list_tools(self) -> Optional[str]:
        """List available MCP tools via MCPToolSkill."""
        list_fn = self._get_skill("list_tools")
        if not list_fn:
            return None
        return list_fn()

    async def _route_skill(self, task: str) -> Optional[str]:
        """Route task to appropriate skill handler with more flexible matching."""
        task_lower = task.lower()
        
        # COMPLEXITY GUARD: If the task looks like a multi-step plan or complex instruction,
        # skip skill hijacking and route directly to the LLM Brain.
        is_complex = len(task) > 150 or "\n" in task or any(marker in task for marker in ["1.", "Step 1", "Objective:"])
        if is_complex:
            return None

        # Phase 3: Doc ingestion routes - more specific intent matching
        if any(kw in task_lower for kw in ["ingest file", "learn doc", "read docs"]):
            result = await self._handle_ingest_doc(task)
            if result:
                return result
        if any(kw in task_lower for kw in ["list learned skills", "show available skills"]):
            result = await self._handle_list_learned()
            if result:
                return result
        if any(kw in task_lower for kw in ["scan docs in", "scan directory", "scan folder"]):
            result = await self._handle_scan_docs(task)
            if result:
                return result

        # Original skill routes - more robust keyword matching
        if any(kw in task_lower for kw in ["build ", "implement ", "generate ", "code "]) \
                or any(kw in task_lower for kw in ["write code", "create code", "write the code"]):
            return await self._handle_write_file(task)
        if any(kw in task_lower for kw in ["write file", "create file", "save file"]):
            return await self._handle_write_file(task)
        if "read file" in task_lower:
            return await self._handle_read_file(task)
        if any(kw in task_lower for kw in ["list files", "list artifacts", "show artifacts"]):
            return await self._handle_list_artifacts()
        
        # Search: match "search for", "research", "google", "find info on"
        if any(kw in task_lower for kw in ["search", "research", "google", "find info", "look up"]):
            return await self._handle_search(task)
            
        if any(kw in task_lower for kw in ["analyze ", "audit ", "review code"]):
            return await self._handle_analyze(task)
        if any(kw in task_lower for kw in ["run ", "execute shell", "execute command"]):
            return await self._handle_shell(task)
        if any(kw in task_lower for kw in ["generate readme", "write readme", "create readme"]):
            return await self._handle_readme(task)
        if "count words" in task_lower:
            return await self._handle_count_words(task)
        if any(kw in task_lower for kw in ["make dir", "make directory", "create dir", "create directory", "mkdir"]):
            return await self._handle_make_dir(task)
            
        # Phase 3/4: MCP Tool calls - Fuzzy matching
        is_list_req = any(kw in task_lower for kw in ["list", "show", "available", "what are"])
        is_tool_req = any(kw in task_lower for kw in ["tool", "skill", "capability", "expert"])
        
        if is_list_req and is_tool_req:
            # Check if user specifically mentioned "learned" or "doc" skills
            if "learned" in task_lower or "doc" in task_lower:
                result = await self._handle_list_learned()
                if result: return result
            # Otherwise default to listing the powerful MCP tools
            if "my tool" in task_lower or "all tool" in task_lower:
                result = await self._handle_list_tools()
                if result: return result

        # Dynamic Tool Discovery & Intent Resolution
        mcp_skill = next((s for s in self.skills if hasattr(s, "tool_map")), None)
        if mcp_skill:
            for tool_name in mcp_skill.tool_map.keys():
                if tool_name in task_lower:
                    # Specific handler for weather (city extraction)
                    if tool_name == "weather":
                        m = re.search(r'(?:in|for) ([\w\s]+)', task, re.IGNORECASE)
                        city = m.group(1).strip() if m else "New York City"
                        return mcp_skill.call_tool("weather", f"/data/2.5/weather?q={city.replace(' ', '%20')}")
                    
                    # Generic heuristic for other tools: search for best matching endpoint
                    path = mcp_skill.search_endpoint(tool_name, task)
                    if not path:
                        # Default to status/health or root if nothing else found
                        path = "/health"
                    return mcp_skill.call_tool(tool_name, path)

        if task_lower.startswith("call "):
            result = await self._handle_call_tool(task)
            if result: return result
            
        return None

    async def _execute_action_tags(self, response: str, task_context: str = "") -> str:
        """Scan LLM response for action tags and execute them with FileSkill.

        Supported tags:

          Single file:
            WRITE_FILE: filename.py
            ```
            <content>
            ```

          Multiple files:
            CREATE_FILES:
            --- filename1.py ---
            <content 1>
            --- filename2.py ---
            <content 2>
            ---END---

        Returns the response with an execution summary appended.
        """
        write_fn = self._get_skill("write_file")
        if not write_fn:
            return response  # No file skill attached — nothing to execute

        executed = []

        # Pattern 1a — WRITE_FILE: filename\n```[lang]\n<content>\n```  (backtick style)
        # (Flexible: allows tag before or after the code block)
        write_pattern = re.compile(
            r'^\s*WRITE_FILE:\s*(\S+)[\s\S]*?```[\w]*\n([\s\S]*?)\n?```|```[\w]*\n([\s\S]*?)\n?```[\s\S]*?^\s*WRITE_FILE:\s*(\S+)',
            re.MULTILINE
        )
        for m in write_pattern.finditer(response):
            if m.group(1): # Tag before code
                filename = m.group(1).strip().strip('`')
                content = m.group(2).rstrip()
            else: # Tag after code
                filename = m.group(4).strip().strip('`')
                content = m.group(3).rstrip()

            if not filename.endswith(('.md', '.txt', '.json', '.yml', '.yaml', '.html', '.css', '.sh')):
                header = f"# Generated by {self.persona.name} ({self.persona.role})\n"
                content = header + content
            result = write_fn(filename, content)
            executed.append(f"[OK] {result} ({len(content):,} bytes)")
            
            # Phase 5: Register with Pipeline
            from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
            get_artifact_pipeline().register_artifact(filename, created_by=self.persona.name)

        # Pattern 1b — WRITE_FILE: filename\n[START]\n<content>\n[END]  (marker style for 1b model)
        write_marker_pattern = re.compile(
            r'^\s*WRITE_FILE:\s*(\S+)\s*\n\[START\]\n([\s\S]*?)\n?\[END\]',
            re.MULTILINE
        )
        for m in write_marker_pattern.finditer(response):
            filename = m.group(1).strip()
            content = m.group(2).rstrip()
            if not filename.endswith(('.md', '.txt', '.json', '.yml', '.yaml', '.html', '.css', '.sh')):
                header = f"# Generated by {self.persona.name} ({self.persona.role})\n"
                content = header + content
            result = write_fn(filename, content)
            executed.append(f"[OK] {result} ({len(content):,} bytes)")
            from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
            get_artifact_pipeline().register_artifact(filename, created_by=self.persona.name)

        # Pattern 2 — CREATE_FILES:\n--- filename ---\n<content>\n---END---
        multi_match = re.search(
            r'^\s*CREATE_FILES:\s*\n([\s\S]*?)\n?---END---',
            response, re.MULTILINE
        )
        if multi_match:
            block = multi_match.group(1)
            # Split on --- filename --- delimiters
            file_blocks = re.split(r'---\s*(\S+)\s*---', block)
            # Interleaved: ["", name1, content1, name2, content2, ...]
            i = 1
            while i + 1 < len(file_blocks):
                filename = file_blocks[i].strip().strip('`')
                content = file_blocks[i + 1].rstrip()
                if filename and content.strip():
                    if not filename.endswith(('.md', '.txt', '.json', '.yml', '.yaml', '.html', '.css', '.sh')):
                        header = f"# Generated by {self.persona.name} ({self.persona.role})\n"
                        content = header + content
                    result = write_fn(filename, content)
                    executed.append(f"[OK] {result} ({len(content):,} bytes)")
                    
                    # Phase 5: Register with Pipeline
                    from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
                    get_artifact_pipeline().register_artifact(filename, created_by=self.persona.name)
                i += 2

        # Pattern 4 — SEARCH_QUERY: query
        search_fn = self._get_skill("search")
        if search_fn:
            for m in re.finditer(r'^\s*SEARCH_QUERY:\s*(.*)$', response, re.MULTILINE):
                query = m.group(1).strip()
                if query:
                    result = search_fn(query)
                    executed.append(f"Search Result for '{query}':\n{result[:500]}...")

        # Pattern 5 — CALL_TOOL: tool_name endpoint method data
        call_fn = self._get_skill("call_tool")
        if call_fn:
            for m in re.finditer(r'^\s*CALL_TOOL:\s*(\w+)\s*(\S+)\s*(\w+)?\s*(.*)?$', response, re.MULTILINE):
                tool = m.group(1).strip()
                endpoint = m.group(2).strip()
                method = (m.group(3) or "GET").strip()
                data_str = m.group(4).strip() if m.group(4) else None
                
                data = None
                if data_str:
                    try: data = json.loads(data_str)
                    except: pass
                
                result = call_fn(tool_name=tool, endpoint=endpoint, method=method, data=data)
                executed.append(f"[TOOL] Tool Call ({tool.upper()}): {result[:500]}...")

        # Pattern 4b — LIST_ARTIFACTS (Tag based)
        list_fn = self._get_skill("list_artifacts")
        for m in re.finditer(r'^\s*LIST_ARTIFACTS:', response, re.MULTILINE):
            if list_fn:
                artifacts = list_fn()
                executed.append(f"[LIST] Artifacts:\n```\n{json.dumps(artifacts, indent=2)}\n```")

        # Pattern 6 — DELEGATE_TASK: TargetRole | task
        # Limit recursion to prevent infinite loops (max depth 3)
        if not hasattr(self, "_recursion_depth"):
            self._recursion_depth = 0

        if self._recursion_depth < 3:
            # Flexible regex: allows optional markdown markers like "1. ", "- ", etc.
            for m in re.finditer(r'(?:^\d+\.\s*|^\-\s*|^)?DELEGATE_TASK:\s*([^|]+)\|\s*(.*)$', response, re.MULTILINE):
                role = m.group(1).strip()
                sub_task = m.group(2).strip()
                
                from swarm_v2.core.expert_registry import get_expert_registry
                registry = get_expert_registry()
                target_agent = registry.get_agent(role)
                
                if target_agent and target_agent != self:
                    target_agent._recursion_depth = self._recursion_depth + 1
                    self.log_nodal_activity(f"DELEGATING to {role}: {sub_task[:40]}")
                    try:
                        # Pass the original prompt context down so the delegated agent has the data to work with
                        contextual_sub_task = f"{sub_task}\n\n[DELEGATED CONTEXT FROM {self.persona.name}]:\n{task_context}"
                        sub_resp_obj = await target_agent.process_task(contextual_sub_task, sender=self.persona.name)
                        
                        # Handle dict vs string return from process_task
                        if isinstance(sub_resp_obj, dict):
                            sub_response = sub_resp_obj.get("response", "[No Response Content]")
                        else:
                            sub_response = sub_resp_obj
                            
                        executed.append(f"Delegated to {role}: {sub_task[:100]}\nResult: {sub_response[:300]}...")
                    except Exception as e:
                        executed.append(f"Failed delegation to {role}: {e}")
                else:
                    executed.append(f"Could not find peer expert: {role}")
        # Pattern 7 - PLAN_FILE alias (Ensures Archi saves his plans)
        for m in re.finditer(r'^\s*PLAN_FILE:\s*(\S+)\n```[\w]*\n([\s\S]*?)\n?```', response, re.MULTILINE):
            filename = m.group(1).strip()
            content = m.group(2).rstrip()
            if write_fn:
                result = write_fn(filename, content)
                executed.append(f"[PLAN] Integration Plan Saved: {result}")

        # Pattern 8 - REJECT_ARTIFACT: filename | notes
        for m in re.finditer(r'^\s*REJECT_ARTIFACT:\s*([^|]+)\|\s*(.*)$', response, re.MULTILINE):
            fname = m.group(1).strip()
            notes = m.group(2).strip()
            from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
            pipe = get_artifact_pipeline()
            art = pipe.reject(fname, reviewer=self.persona.name, notes=notes)
            if art:
                executed.append(f"[REJECT] Artifact Rejected: {fname} - {notes}")
            else:
                executed.append(f"[WARN] Could not find artifact to reject: {fname}")

        # Pattern 9 - APPROVE_ARTIFACT: filename | notes
        for m in re.finditer(r'^\s*APPROVE_ARTIFACT:\s*([^|]+)\|\s*(.*)$', response, re.MULTILINE):
            fname = m.group(1).strip()
            notes = m.group(2).strip()
            from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
            pipe = get_artifact_pipeline()
            art = pipe.approve(fname, reviewer=self.persona.name, notes=notes)
            if art:
                executed.append(f"[APPROVE] Artifact Approved: {fname}")
            else:
                executed.append(f"[WARN] Could not find artifact to approve: {fname}")

        # Pattern 10 - TEST_ARTIFACT: filename | test_file | passed | result
        for m in re.finditer(r'^\s*TEST_ARTIFACT:\s*([^|]+)\|\s*([^|]+)\|\s*(\w+)\|\s*(.*)$', response, re.MULTILINE):
            fname = m.group(1).strip()
            tfile = m.group(2).strip()
            passed = m.group(3).strip().lower() == "true"
            res_str = m.group(4).strip()
            from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
            pipe = get_artifact_pipeline()
            art = pipe.set_tested(fname, tfile, passed, res_str)
            if art:
                marker = "[PASS]" if passed else "[FAIL]"
                status = "Passed" if passed else "Failed"
                executed.append(f"{marker} Artifact Tested: {fname} ({status})")
            else:
                executed.append(f"[WARN] Could not find artifact to test: {fname}")

        if executed:
            summary = "\n\n**Autonomous Execution Summary:**\n" + "\n".join(executed)
            return response + summary

        return response

    def _is_greeting(self, task: str) -> bool:
        """Check if the task is a simple greeting that should trigger persona introduction."""
        task_lower = task.lower().strip()
        
        # Get just the first word/phrase to check for greeting
        first_word = task_lower.split()[0] if task_lower.split() else ""
        
        # Greeting patterns - simple greetings without complex tasks
        greeting_patterns = [
            "hello", "hi", "hey", "hiya", "howdy", "greetings",
            "what's up", "whats up", "wassup", "sup",
        ]
        
        # Also check for greeting questions (first 15 chars to catch "who are you" etc)
        short_check = task_lower[:15] if len(task_lower) >= 15 else task_lower
        
        # Check if it starts with a greeting OR is a greeting question
        is_greeting = any(pattern in task_lower for pattern in greeting_patterns)
        is_greeting_question = any(q in short_check for q in ["who are you", "who r u", "what is your name", "tell me ab"])
        
        # Make sure there's no actual task - this should be purely conversational
        task_keywords = ["write", "create", "build", "implement", "fix", "bug", "error", 
                       "help", "search", "find", "make", "generate", "code", "file",
                       "read", "list", "show", "get", "do", "run", "test", "craft",
                       "proposal", "response"]
        has_task = any(kw in task_lower for kw in task_keywords)
        
        return (is_greeting or is_greeting_question) and not has_task

    def _generate_greeting(self) -> str:
        """Generate a persona-appropriate greeting."""
        greetings = {
            "Archi": "Hello! I'm Archi, your Architect. I specialize in system design, scalable architecture, and infrastructure planning. How can I help design your next system?",
            "Devo": "Hey! I'm Devo, Lead Developer. I love building clean, elegant code. What should we create today?",
            "Seeker": "Greetings! I'm Seeker, your Researcher. I excel at finding information and synthesizing knowledge. What would you like to explore?",
            "Logic": "Hello. I'm Logic, specialized in complex reasoning, algorithms, and mathematical deductions. What problem shall we solve?",
            "Shield": "Hello. I'm Shield, your Security Auditor. I identify vulnerabilities and ensure robust security. What needs auditing?",
            "Flow": "Hey there! I'm Flow, DevOps Engineer. I handle CI/CD, containers, and cloud deployments. Ready to deploy something?",
            "Vision": "Hi! I'm Vision, UI/UX Designer. I craft beautiful, accessible interfaces. What should we design?",
            "Verify": "Hello! I'm Verify, QA Engineer. I test, find bugs, and ensure quality. What should we verify?",
            "Orchestra": "Greetings! I'm Orchestra, Swarm Manager. I coordinate agent teams and optimize task delegation. What needs orchestrating?",
            "Scribe": "Hello! I'm Scribe, Technical Writer. I create clear documentation and tutorials. What should we document?",
            "Bridge": "Hey! I'm Bridge, Integration Specialist. I connect APIs, protocols, and tools. What integrations do you need?",
            "Pulse": "Hello! I'm Pulse, Data Analyst. I process data and generate insights. What data should we analyze?",
        }
        return greetings.get(self.persona.name, 
            f"Hello! I'm {self.persona.name}, a {self.persona.role}. I specialize in {', '.join(self.persona.specialties[:2])}. How can I help?")

    async def process_task(self, task: str, sender: str = "user") -> str:
        # Update Mesh Heartbeat
        if hasattr(self, "mesh_node_id") and self.mesh_node_id:
            try:
                from swarm_v2.core.agent_mesh import get_agent_mesh
                get_agent_mesh().heartbeat(self.mesh_node_id)
            except Exception:
                pass

        # Reset logs and recursion depth for new external task
        sender_clean = str(sender).lower()
        if sender_clean == "user" or sender_clean == "self": 
            self.nodal_logs = []
            self._recursion_depth = 0
            # PERSISTENCE FIX: Register the user turn in memory so the agent knows what was asked
            self.memory.add_turn("user", task)
        
        # Handle greeting BEFORE other routing - respond immediately to simple greetings
        if sender_clean == "user" and self._is_greeting(task):
            self.log_nodal_activity(f"Greeting detected from user: {task[:20]}")
            greeting_response = self._generate_greeting()
            self.memory.add_turn("agent", greeting_response, role=self.persona.name)
            return greeting_response

        # Phase 4: Submit to Task Arbiter for resource orchestration
        from swarm_v2.core.task_arbiter import route_task_to_arbiter
        arbiter_task = await route_task_to_arbiter(
            agent_id=str(id(self)), # Use instance ID as fallback agent ID
            role=self.persona.role,
            task=task,
            model=getattr(self, 'model', None)
        )
        
        task_id = arbiter_task.task_id if arbiter_task else "unknown"
        self.log_nodal_activity(f"INBOUND_TASK [{task_id}]: {task[:60]}")
        
        result = None
        error = None
        try:
            skill_result = await self._route_skill(task)
            if skill_result is not None:
                self.log_nodal_activity("Skill routing successful.")
                self.memory.add_turn("agent", skill_result[:300], role=self.persona.name)
                self.memory.add_task_result(task[:60], skill_result[:200])
                self._contribute_to_global_memory(task, skill_result)
                result = skill_result
                return skill_result

            # 2. Pure LLM response + action-tag execution
            self.log_nodal_activity("Engaging LLM Brain for reasoning...")
            
            # === SMART PREFIXING: ground the model in action vs. chat mode ===
            # Detect if the task is action-oriented (output files, search, etc.)
            action_keywords = ["write", "create", "build", "implement", "scan", "perform", "run",
                               "save", "generate", "make", "produce", "execute", "proceed"]
            task_lower = task.lower()
            is_action_task = any(kw in task_lower for kw in action_keywords)
            
            if sender_clean == "user" and is_action_task:
                # Label the mode; tag instructions live in the system prompt only
                prefix_msg = f"[ACTION] {task}"
            elif sender_clean == "user":
                prefix_msg = f"[CHAT] {task}"
            else:
                prefix_msg = f"[MESH] {task}"
            
            try:
                # PHASE 6: Strict timeout to prevent dashboard/socket hangs
                response_data = await asyncio.wait_for(
                    self._llm_generate(prefix_msg),
                    timeout=45.0
                )
                response, reasoning_trace = response_data
            except asyncio.TimeoutError:
                self.log_nodal_activity("LLM Timeout detected. Applying safe fallback.")
                response = f"I'm sorry, my neural core ({self.persona.model or 'Gemma'}) is currently over-taxed. Please repeat the request or check system resources."
                reasoning_trace = "[TIMEOUT_EXCEEDED]"
            
            self.log_nodal_activity("Commencing execution of action tags...")
            response = await self._execute_action_tags(response, task_context=task)
            
            self.memory.add_turn("agent", response[:300], role=self.persona.name)
            self.memory.add_task_result(task[:60], response[:200])
            self._contribute_to_global_memory(task, response)
            
            # Pack reasoning metadata if available
            metadata = {
                "name": self.persona.name,
                "role": self.persona.role
            }
            if reasoning_trace:
                metadata["reasoning_trace"] = reasoning_trace

            # Refactoring Loop (moved up to be reachable)
            if sender_clean in ["user", "self"]:
                from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
                pipeline = get_artifact_pipeline()
                if pipeline.has_pending_reviews():
                    self.log_nodal_activity("Detected pending artifacts. Queuing for dashboard review.")

                # Check for code artifacts needing verification
                # Identify which files were actually written
                written_files = []
                # Match both WRITE_FILE and CREATE_FILES patterns roughly
                for m in re.finditer(r'WRITE_FILE:\s*(\S+)', response):
                    written_files.append(m.group(1).strip().strip('`'))
                
                for fname in set(written_files):
                    if fname.endswith(('.py', '.js', '.sh', '.py`')): # Include the backtick case for safety during transition
                        clean_name = fname.strip('`')
                        self.log_nodal_activity(f"Validating artifact: {clean_name}")
                        content = pipeline.get_content(clean_name) or "File content missing"
                        
                        verify_task = (
                            f"AUDIT ARTIFACT: {self.persona.name} created '{clean_name}' with content:\n\n"
                            f"```python\n{content}\n```\n\n"
                            f"Review this for logic errors, security flaws, and performance issues. "
                            f"If flawed, emit 'REJECT_ARTIFACT: {clean_name} | [reason]'. "
                            f"If perfect, emit 'APPROVE_ARTIFACT: {clean_name} | Verified autonomously'. "
                            "Do NOT just repeat the content. Provide a decision."
                        )
                        from swarm_v2.core.expert_registry import get_expert_registry
                        verify_agent = get_expert_registry().get_agent("Verify") or get_expert_registry().get_agent("QA Engineer")
                        if verify_agent:
                            await verify_agent.process_task(verify_task, sender=self.persona.name)
                        else:
                            self.log_nodal_activity("Verify agent not found for autonomous audit.")

                for attempt in range(1, 4):
                    report = pipeline.get_rejection_report_for_agent(self.persona.name)
                    if not report:
                        break
                        
                    self.log_nodal_activity(f"Issue found. Commencing remediation attempt {attempt}...")
                    # Reset pipeline status so we can re-verify
                    for a in pipeline.list_all():
                        if a.get("created_by") == self.persona.name and a["status"] in ["rejected", "test_failed"]:
                            pipeline.reset_artifact(a["filename"])
                    
                    response = await self._autonomous_remediate(task, response, report, attempt)
                    
                    # Re-verify after remediation
                    self.log_nodal_activity(f"Remediation {attempt} applied. Re-verifying...")
                    if verify_agent:
                        await verify_agent.process_task(verify_task, sender=self.persona.name)

            self.log_nodal_activity("Task execution complete.")
            # PERSISTENCE: turns were already added during skill match or initial pre-processing
            # We only return the final result here.
            
            if reasoning_trace:
                return {
                    "response": response,
                    "reasoning_trace": reasoning_trace,
                    "metadata": metadata
                }
            return response
        except Exception as e:
            error = str(e)
            fallback = (
                f"[{self.persona.name}] Task processing error ({e}). "
                f"I'm your {self.persona.role} — specializing in {', '.join(self.persona.specialties[:2])}. "
            )
            self.memory.add_turn("agent", fallback, role=self.persona.name)
            result = fallback
            return fallback
        finally:
            # Notify arbiter of completion
            try:
                from swarm_v2.core.task_arbiter import get_task_arbiter
                get_task_arbiter().complete_task(task_id, result=result, error=error)
            except Exception:
                pass

    async def _autonomous_remediate(self, task: str, last_response: str, report: str, attempt: int) -> str:
        """Phase 5: Self-correction loop for recursive fixing."""
        self.log_nodal_activity(f"Engaging LLM for Remediation ({attempt}/3)...")
        remediation_prompt = (
            f"### AUTONOMOUS REFACTORING LOOP (Attempt {attempt}/3)\n\n"
            f"Your previous attempt to solve this task failed code/security validation.\n\n"
            f"**Original Goal:** {task}\n\n"
            f"**Validation Report:**\n{report}\n\n"
            f"Please analyze the errors, identify the root cause, and provide a corrected implementation. "
            f"CRITICAL: You MUST use the 'WRITE_FILE' action tag to save the fixed code. "
            f"Example:\nWRITE_FILE: filename.py\n```python\n(fixed code)\n```\n"
            f"DO NOT just provide a text explanation. You MUST emit the tag."
        )
        response_data = await self._llm_generate(remediation_prompt)
        # Handle tuple return from _llm_generate
        if isinstance(response_data, tuple):
            response, trace = response_data
        else:
            response, trace = response_data, None
            
        return await self._execute_action_tags(response)

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 5: CHAIN-OF-VERIFICATION (Logic Upgrade)
    # Self-audit for logical fallacies before final output
    # ═══════════════════════════════════════════════════════════════════════════

    async def verify_reasoning(self, text: str, auto_correct: bool = False) -> Dict[str, Any]:
        """
        Phase 5: Verify reasoning for logical fallacies.
        
        This method runs a Chain-of-Verification self-audit on the reasoning
        output, checking for logical fallacies before the final output is used.
        
        Args:
            text: The reasoning text to verify
            auto_correct: If True, generate corrected reasoning with notes
            
        Returns:
            Dict with verification result including pass/fail, score, and suggestions
        """
        from swarm_v2.core.chain_of_verification import get_chain_of_verification
        
        cov = get_chain_of_verification()
        result = cov.verify(text, auto_correct=auto_correct)
        
        self.log_nodal_activity(
            f"CoV Verification: {'PASSED' if result.passed else 'FAILED'} (score: {result.score:.2f})"
        )
        
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
                    "suggestion": f.suggestion
                }
                for f in result.detected_fallacies
            ],
            "suggestions": result.suggestions,
            "corrected_reasoning": result.corrected_reasoning
        }

    async def process_with_verification(self, task: str, sender: str = "user") -> Dict[str, Any]:
        """
        Process a task with Chain-of-Verification self-audit.
        
        This combines process_task with automatic reasoning verification.
        If reasoning fails verification, suggestions are appended to the response.
        
        Args:
            task: The task to process
            sender: Who sent the task
            
        Returns:
            Dict with response, verification status, and any corrections
        """
        # First, process the task normally
        response = await self.process_task(task, sender=sender)
        
        # Then verify the reasoning
        verification = await self.verify_reasoning(response, auto_correct=True)
        
        # Build enhanced response
        result = {
            "response": response,
            "verification": verification,
            "agent": self.persona.name,
            "role": self.persona.role
        }
        
        # If verification failed, append suggestions
        if not verification["passed"]:
            self.log_nodal_activity(f"CoV detected {verification['fallacy_count']} reasoning issues")
            result["verified_response"] = verification.get("corrected_reasoning", response)
        
        return result


    def _contribute_to_global_memory(self, task: str, response: str):
        """Contribute significant agent outputs to the global shared memory."""
        try:
            from swarm_v2.core.global_memory import get_global_memory
            global_mem = get_global_memory()
            # Only contribute task results, not casual conversation
            summary = f"Task: {task[:100]} | Result: {response[:200]}"
            global_mem.contribute(
                content=summary,
                author=self.persona.name,
                author_role=self.persona.role,
                memory_type="experience",
                tags=self.persona.specialties[:3],
            )
        except Exception:
            pass  # Global memory is optional

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 5: AUTONOMOUS CODE REFACTORER (Devo Upgrade)
    # Self-correction cycles: Code -> Test -> Fix (3 attempts)
    # ═══════════════════════════════════════════════════════════════════════════

    async def autonomous_code_test_fix(self, filename: str, max_cycles: int = 3) -> Dict[str, Any]:
        """
        Phase 5: Autonomous Code -> Test -> Fix loop.
        
        This method runs a self-correction cycle:
        1. Generate code for the artifact
        2. Run tests/validation
        3. If tests fail, analyze and fix
        4. Repeat up to max_cycles times
        
        Returns a dict with cycle results and final status.
        """
        from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
        pipeline = get_artifact_pipeline()
        
        results = {
            "filename": filename,
            "cycles": [],
            "final_status": "unknown",
            "total_attempts": 0
        }
        
        for cycle in range(1, max_cycles + 1):
            self.log_nodal_activity(f"[Cycle {cycle}/{max_cycles}] Testing {filename}...")
            cycle_result = {"cycle": cycle, "status": "running"}
            
            # Step 1: Get current artifact content
            content = pipeline.get_content(filename)
            if not content:
                cycle_result["status"] = "error"
                cycle_result["error"] = "File not found"
                results["cycles"].append(cycle_result)
                continue
            
            # Step 2: Run automated test
            test_result = await self._run_autonomous_test(filename, content)
            cycle_result["test_result"] = test_result
            
            if test_result.get("passed", False):
                # Tests passed - mark as verified
                cycle_result["status"] = "passed"
                results["cycles"].append(cycle_result)
                results["final_status"] = "verified"
                pipeline.set_tested(filename, test_result.get("test_file", ""), True, "Autonomous verification passed")
                self.log_nodal_activity(f"[Cycle {cycle}] ✅ Tests PASSED for {filename}")
                break
            else:
                # Tests failed - attempt fix
                cycle_result["status"] = "fixing"
                results["cycles"].append(cycle_result)
                
                if cycle < max_cycles:
                    self.log_nodal_activity(f"[Cycle {cycle}] ❌ Tests failed. Attempting autonomous fix...")
                    
                    # Step 3: Generate fix based on test failure
                    fix_result = await self._generate_fix(filename, content, test_result)
                    
                    if fix_result.get("success"):
                        # Reset artifact status for re-test
                        pipeline.reset_artifact(filename)
                        results["total_attempts"] = cycle
                    else:
                        self.log_nodal_activity(f"[Cycle {cycle}] Fix generation failed")
                else:
                    # Max cycles reached - mark as failed
                    results["final_status"] = "failed_after_retries"
                    pipeline.set_tested(filename, test_result.get("test_file", ""), False, 
                                       f"Failed after {max_cycles} cycles: {test_result.get('error', 'Unknown')}")
                    self.log_nodal_activity(f"[Cycle {cycle}] Max cycles reached. Notifying user...")
        
        return results

    async def _run_autonomous_test(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Run automated tests on the artifact.
        Returns test result with pass/fail status and details.
        """
        result = {
            "passed": False,
            "test_file": None,
            "error": None,
            "output": None
        }
        
        # Determine test file name
        if filename.startswith("test_"):
            result["test_file"] = filename
        else:
            result["test_file"] = f"test_{filename}"
        
        # Security check first
        security_issues = await self._run_security_check(filename, content)
        if security_issues:
            result["error"] = f"Security issues found: {security_issues}"
            return result
        
        # Syntax check for Python files
        if filename.endswith(".py"):
            syntax_ok = self._check_python_syntax(content)
            if not syntax_ok["valid"]:
                result["error"] = f"Syntax error: {syntax_ok['error']}"
                return result
        
        # For now, basic validation passes
        # In a full implementation, this would run pytest or similar
        result["passed"] = True
        result["output"] = "Basic validation passed (syntax + security)"
        
        return result

    async def _run_security_check(self, filename: str, content: str) -> Optional[str]:
        """Run security scan on content. Returns None if safe, error string if issues."""
        # Basic security patterns to check
        dangerous_patterns = [
            (r"eval\s*\(", "Use of eval() is dangerous"),
            (r"exec\s*\(", "Use of exec() is dangerous"),
            (r"__import__\s*\(", "Dynamic imports can be dangerous"),
            (r"subprocess\.call\s*\([^)]*shell\s*=\s*True", "shell=True in subprocess is dangerous"),
            (r"os\.system\s*\(", "os.system() can be dangerous"),
            (r"password\s*=\s*['\"]", "Hardcoded password detected"),
            (r"api_key\s*=\s*['\"]", "Hardcoded API key detected"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return message
        
        return None

    def _check_python_syntax(self, content: str) -> Dict[str, Any]:
        """Check Python syntax without executing."""
        try:
            compile(content, "<string>", "exec")
            return {"valid": True}
        except SyntaxError as e:
            return {"valid": False, "error": str(e)}

    async def _generate_fix(self, filename: str, content: str, test_result: Dict) -> Dict[str, Any]:
        """
        Generate a fix for the failed artifact using LLM analysis.
        """
        self.log_nodal_activity(f"Generating fix for {filename}...")
        
        fix_prompt = (
            f"### AUTONOMOUS FIX GENERATION\n\n"
            f"The following code failed validation:\n\n"
            f"**File:** {filename}\n\n"
            f"**Test Result:**\n{test_result.get('error', 'Unknown error')}\n\n"
            f"**Current Code:**\n```python\n{content}\n```\n\n"
            f"Please analyze the error and provide a corrected version.\n"
            f"Output the fixed code using WRITE_FILE tag:\n\n"
            f"WRITE_FILE: {filename}\n"
            f"```python\n(fixed code here)\n```\n\n"
            f"Do NOT just explain - you MUST emit the WRITE_FILE tag with the corrected code."
        )
        
        response = await self._llm_generate(fix_prompt)
        executed = await self._execute_action_tags(response)
        
        return {
            "success": "WRITE_FILE" in response or "OK" in executed,
            "response": executed[:500]
        }

    async def notify_user_of_failure(self, filename: str, results: Dict[str, Any]):
        """
        Notify the user after all self-correction attempts have failed.
        Creates a failure report in the artifacts.
        """
        write_fn = self._get_skill("write_file")
        if not write_fn:
            return
        
        report = f"""# Autonomous Remediation Failure Report
        
**File:** {filename}
**Agent:** {self.persona.name} ({self.persona.role})
**Total Attempts:** {results.get('total_attempts', 0)}
**Final Status:** {results.get('final_status', 'unknown')}

## Cycle History:
"""
        for cycle in results.get('cycles', []):
            report += f"\n### Cycle {cycle.get('cycle')}:\n"
            report += f"- Status: {cycle.get('status')}\n"
            if cycle.get('test_result'):
                tr = cycle['test_result']
                report += f"- Test: {'PASSED' if tr.get('passed') else 'FAILED'}\n"
                if tr.get('error'):
                    report += f"- Error: {tr.get('error')}\n"
        
        report += f"""
## Next Steps:
This artifact requires human intervention. Please review and manually correct.

---
*Generated by Swarm OS Phase 5 Autonomous Code Refactorer*
"""
        
        report_file = f"failure_report_{filename.replace('/', '_').replace('.', '_')}.md"
        write_fn(report_file, report)
        self.log_nodal_activity(f"Failure report generated: {report_file}")

    def spawn_subagent(self, role: str, task: str) -> "BaseAgent":
        sub_persona = AgentPersona(
            name=f"{self.persona.name}_Sub{len(self.subagents) + 1}",
            role=role,
            background=f"Spawned by {self.persona.name} to handle: {task[:60]}",
            specialties=self.persona.specialties[:2],
            avatar_color="#ffaa00"
        )
        sub = BaseAgent(sub_persona, skills=list(self.skills))
        self.subagents[sub.agent_id] = sub
        self.memory.add_fact(f"Spawned subagent '{sub.persona.name}' as {role} for: {task[:40]}")
        return sub

    def get_subagents(self) -> List[Dict]:
        return [
            {"id": sid, "name": s.persona.name, "role": s.persona.role,
             "background": s.persona.background, "skills": s.get_skill_names()}
            for sid, s in self.subagents.items()
        ]

    def get_memory_stats(self) -> Dict:
        return self.memory.get_stats()

    def register_skill(self, skill: Any):
        self.skills.append(skill)
