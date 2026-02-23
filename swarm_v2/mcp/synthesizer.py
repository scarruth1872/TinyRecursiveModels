
"""
MCP Tool Synthesizer — Phase 3: Tool Synthesis
Devo and Bridge collaborate to generate MCP-compatible tool servers
that bridge gaps in the swarm's capabilities.

This module can:
1. Analyze a learned skill's knowledge (endpoints, instructions)
2. Generate a complete MCP server (FastAPI microservice) from that knowledge
3. Write the server to the artifacts pipeline for review & deployment
"""

import os
import re
import json
from typing import Dict, List, Optional
from datetime import datetime


SYNTHESIZED_DIR = "swarm_v2_synthesized"
os.makedirs(SYNTHESIZED_DIR, exist_ok=True)


class SynthesizedTool:
    """Represents a tool that was automatically generated."""

    def __init__(self, name: str, tool_type: str, source_skill: str,
                 code: str, port: int, endpoints: List[dict]):
        self.name = name
        self.tool_type = tool_type  # "mcp_server", "skill", "bridge"
        self.source_skill = source_skill
        self.code = code
        self.port = port
        self.endpoints = endpoints
        self.created_at = datetime.now().isoformat()
        self.status = "generated"  # generated -> reviewed -> deployed

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tool_type": self.tool_type,
            "source_skill": self.source_skill,
            "port": self.port,
            "endpoints": self.endpoints,
            "created_at": self.created_at,
            "status": self.status,
            "code_length": len(self.code),
        }


class MCPSynthesizer:
    """
    Generates MCP-compatible tool servers from learned skill knowledge.
    Works in tandem with the Learning Engine and agent LLMs.
    """

    def __init__(self):
        self.synthesized_tools: Dict[str, SynthesizedTool] = {}
        self.synthesis_log: List[dict] = []
        self._next_port = 9100
        self._load_registry()

    def _load_registry(self):
        registry_path = os.path.join(SYNTHESIZED_DIR, "registry.json")
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._next_port = data.get("next_port", 9100)
            except Exception:
                pass

    def _save_registry(self):
        registry_path = os.path.join(SYNTHESIZED_DIR, "registry.json")
        data = {
            "next_port": self._next_port,
            "updated_at": datetime.now().isoformat(),
            "tools": [t.to_dict() for t in self.synthesized_tools.values()],
        }
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def generate_mcp_server(self, skill_name: str, skill_data: dict,
                             description: str = "") -> SynthesizedTool:
        """
        Generate a complete MCP server from a learned skill's knowledge.
        Returns a SynthesizedTool with the generated code.
        """
        endpoints = skill_data.get("endpoints", {})
        instructions = skill_data.get("instructions", "")
        source = skill_data.get("source", "unknown").replace("\\", "/")

        port = self._next_port
        self._next_port += 1

        # Production Logic: Determine base URL and Auth requirements
        base_url = skill_data.get("base_url", "")
        auth_env = re.sub(r'[^a-zA-Z0-9]', '_', skill_name.upper()).replace('DOC_', '') + "_API_KEY"
        if "github" in skill_name.lower(): auth_env = "GITHUB_TOKEN"
        if "discord" in skill_name.lower(): auth_env = "DISCORD_TOKEN"
        if "slack" in skill_name.lower(): auth_env = "SLACK_BOT_TOKEN"

        # Semantic Mock Engine: provides realistic responses based on service type
        MOCK_DATA_MAP = {
            "weather": {"temp": 22, "condition": "Sunny", "humidity": 45},
            "github": {"id": 1024, "status": "open", "labels": ["bug", "priority-high"]},
            "discord": {"message_id": "991234", "author": "System", "content": "Broadcast complete"},
            "slack": {"ok": True, "channel": "C12345", "ts": "123456789.0001"},
            "redis": {"status": "OK", "key_found": True, "val": "cached_data"},
            "stripe": {"id": "ch_123", "amount": 2000, "currency": "usd", "status": "succeeded"},
            "spotify": {"is_playing": True, "track": "Recursive Echoes", "artist": "The Swarm"},
            "huggingface": {"model": "trm-7b-phi", "status": "deployed", "latency": "12ms"},
        }
        
        # Determine best mock data
        mock_val = {"status": "ready"}
        for key, val in MOCK_DATA_MAP.items():
            if key in skill_name.lower():
                mock_val.update(val)
                break

        # Build route handlers from discovered endpoints
        route_code = []
        endpoint_defs = []
        for path, method in endpoints.items():
            # Sanitize the function name
            fn_name = re.sub(r'[^a-zA-Z0-9]', '_', path.strip('/'))
            fn_name = fn_name or "index"

            route_code.append(f'''
@app.{method.lower()}("{path}")
async def {fn_name}(request: Request):
    """Live-Proxy Handler for {method} {path}"""
    params = dict(request.query_params)
    body = None
    if request.method in ("POST", "PUT", "PATCH"):
        try: body = await request.json()
        except: body = {{}}

    # Try Live Production Proxy
    base = os.environ.get("{skill_name.upper()}_BASE_URL", "{base_url}")
    token = os.environ.get("{auth_env}")
    
    if base and base.startswith("http"):
        try:
            import httpx
            headers = {{"Authorization": f"Bearer {{token}}"}} if token else {{}}
            # URL Path param replacement (very basic)
            full_path = "{path}"
            for k, v in params.items():
                if f"{{{{{k}}}}}" in full_path:
                    full_path = full_path.replace(f"{{{{{k}}}}}", v)
            
            url = f"{{base.rstrip('/')}}{{full_path}}"
            async with httpx.AsyncClient() as client:
                if "{method}" == "GET":
                    r = await client.get(url, params=params, headers=headers, timeout=10)
                else:
                    r = await client.request("{method}", url, json=body, headers=headers, timeout=10)
                
                return {{
                    "tool": "{skill_name}",
                    "mode": "production_live",
                    "status": r.status_code,
                    "response": r.json() if "json" in r.headers.get("content-type", "") else r.text
                }}
        except Exception as e:
            return {{"status": "proxy_error", "error": str(e), "mode": "production_live"}}

    # Fallback to High-Fidelity Simulation
    return {{
        "tool": "{skill_name}",
        "endpoint": "{path}",
        "method": "{method}",
        "input": body,
        "instructions": """{instructions[:200]}""",
        "data": {json.dumps(mock_val)},
        "source": "{source}",
        "mode": "simulation_fallback"
    }}
''')
            endpoint_defs.append({
                "path": path,
                "method": method,
                "function": fn_name,
            })

        # If no endpoints were discovered, create a generic one
        if not route_code:
            route_code.append(f'''
@app.post("/invoke")
async def invoke(request: Request):
    """Generic tool invocation endpoint."""
    body = await request.json()
    return {{
        "tool": "{skill_name}",
        "input": body,
        "instructions": """{instructions[:300]}""",
        "source": "{source}",
        "status": "ready"
    }}
''')
            endpoint_defs.append({
                "path": "/invoke",
                "method": "POST",
                "function": "invoke",
            })

        # Assemble complete server
        server_code = f'''"""
MCP Tool Server: {skill_name}
Auto-synthesized by Swarm OS Phase 3 Tool Synthesizer
Source: {source}
Generated: {datetime.now().isoformat()}
Port: {port}
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
import httpx

app = FastAPI(
    title="MCP Tool: {skill_name}",
    description="{description or f'Synthesized tool bridge for {skill_name}'}",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {{
        "tool": "{skill_name}",
        "type": "mcp_server",
        "port": {port},
        "status": "online",
        "endpoints": {json.dumps([e["path"] for e in endpoint_defs])}
    }}

@app.get("/mcp/manifest")
async def mcp_manifest():
    """MCP-compatible manifest for tool discovery."""
    return {{
        "name": "{skill_name}",
        "description": "{description}",
        "version": "1.0.0",
        "tools": {json.dumps(endpoint_defs, indent=8)},
        "source": "{source}"
    }}

{"".join(route_code)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port={port})
'''

        # Save the generated server to disk
        server_filename = f"mcp_{skill_name.lower()}_server.py"
        server_path = os.path.join(SYNTHESIZED_DIR, server_filename)
        with open(server_path, "w", encoding="utf-8") as f:
            f.write(server_code)

        tool = SynthesizedTool(
            name=skill_name,
            tool_type="mcp_server",
            source_skill=skill_name,
            code=server_code,
            port=port,
            endpoints=endpoint_defs,
        )
        self.synthesized_tools[skill_name] = tool

        self.synthesis_log.append({
            "action": "synthesized",
            "tool": skill_name,
            "type": "mcp_server",
            "port": port,
            "endpoints": len(endpoint_defs),
            "filepath": server_path,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_registry()

        return tool

    async def synthesize_from_learned_skill(self, skill_name: str,
                                             llm_generate=None) -> Optional[SynthesizedTool]:
        """
        Pull a skill from the Learning Engine and synthesize an MCP server.
        Optionally uses an LLM (Devo/Bridge) to enhance the generated code.
        """
        from swarm_v2.skills.learning_engine import get_learning_engine
        engine = get_learning_engine()
        skill = engine.get_skill(skill_name)

        if not skill:
            return None

        skill_data = skill.to_dict()

        # Generate the base server
        tool = self.generate_mcp_server(
            skill_name=skill_name,
            skill_data=skill_data,
            description=skill.description,
        )

        # If an LLM is available, ask it to review/enhance the server
        if llm_generate:
            try:
                review_prompt = (
                    f"Review this auto-generated MCP server for '{skill_name}'.\n"
                    f"Source: {skill.source}\n"
                    f"Endpoints: {json.dumps(tool.endpoints, indent=2)}\n"
                    f"Port: {tool.port}\n\n"
                    f"The server is saved to {SYNTHESIZED_DIR}/mcp_{skill_name.lower()}_server.py\n"
                    f"Provide a brief assessment: Is this a useful bridge? Any improvements needed?\n"
                    f"Keep response under 100 words."
                )
                review = await llm_generate(review_prompt)
                self.synthesis_log[-1]["llm_review"] = review
            except Exception:
                pass

        return tool

    def generate_skill_class(self, skill_name: str, skill_data: dict) -> str:
        """
        Generate a Python skill class from learned knowledge
        that can be hot-loaded onto any agent.
        """
        endpoints = skill_data.get("endpoints", {})
        instructions = skill_data.get("instructions", "")
        source = skill_data.get("source", "unknown")

        methods = []
        for path, method in endpoints.items():
            fn_name = re.sub(r'[^a-zA-Z0-9]', '_', path.strip('/')) or "call"
            methods.append(f'''
    def {fn_name}(self, **kwargs) -> str:
        """Call {method} {path}"""
        import httpx
        url = f"{{self.base_url}}{path}"
        if "{method.upper()}" in ("GET", "DELETE"):
            resp = httpx.{method.lower()}(url, params=kwargs, timeout=30)
        else:
            resp = httpx.{method.lower()}(url, json=kwargs, timeout=30)
        return resp.text
''')

        class_code = f'''"""
Auto-generated Skill: {skill_name}
Source: {source}
Generated by Swarm OS Tool Synthesizer
"""


class {skill_name}Skill:
    """Dynamically synthesized skill for {skill_name}."""
    skill_name = "{skill_name}Skill"
    description = """{skill_data.get('description', f'Synthesized from {source}')}"""

    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
{"".join(methods) if methods else """
    def invoke(self, task: str) -> str:
        return f"[{skill_name}] Processing: {{task}}"
"""}
'''

        # Save to disk
        class_filename = f"skill_{skill_name.lower()}.py"
        class_path = os.path.join(SYNTHESIZED_DIR, class_filename)
        with open(class_path, "w", encoding="utf-8") as f:
            f.write(class_code)

        self.synthesis_log.append({
            "action": "skill_generated",
            "tool": f"{skill_name}Skill",
            "type": "skill_class",
            "filepath": class_path,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_registry()

        return class_code

    def list_tools(self) -> List[dict]:
        return [t.to_dict() for t in self.synthesized_tools.values()]

    def get_synthesis_log(self) -> List[dict]:
        return self.synthesis_log

    def get_stats(self) -> dict:
        return {
            "total_synthesized": len(self.synthesized_tools),
            "mcp_servers": len([t for t in self.synthesized_tools.values()
                                if t.tool_type == "mcp_server"]),
            "log_entries": len(self.synthesis_log),
            "next_port": self._next_port,
        }


# Singleton
_synthesizer: Optional[MCPSynthesizer] = None

def get_synthesizer() -> MCPSynthesizer:
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = MCPSynthesizer()
    return _synthesizer
