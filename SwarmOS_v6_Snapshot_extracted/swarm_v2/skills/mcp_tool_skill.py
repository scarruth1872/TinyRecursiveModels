
import os
import json
import requests
from typing import Dict, Any, Optional

class MCPToolSkill:
    """
    Skill for interacting with the synthesized MCP microservices.
    Upgraded for Dynamic Intent Resolution and Self-Healing.
    """
    skill_name = "MCPToolSkill"
    description = (
        "Dynamic interface for local MCP microservices. "
        "Automatically discovers tools, handles multi-path routing, and self-heals on 404 errors."
    )

    REGISTRY_PATH = "swarm_v2_synthesized/registry.json"

    def __init__(self, base_url: str = "http://127.0.0.1"):
        self.base_url = base_url
        self.tool_map = {}
        self._load_registry()

    def _load_registry(self):
        """Dynamically build tool map from registry.json."""
        if not os.path.exists(self.REGISTRY_PATH):
            return

        try:
            with open(self.REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)
            
            for tool in registry.get("tools", []):
                # Normalize name (Doc_weather -> weather)
                name = tool["name"].lower().replace("doc_", "")
                self.tool_map[name] = {
                    "port": tool["port"],
                    "endpoints": tool.get("endpoints", []),
                    "full_name": tool["name"]
                }
        except Exception as e:
            print(f"[MCPToolSkill] Registry Load Error: {e}")

    def get_tool_manifest(self, tool_name: str) -> Optional[Dict]:
        """Fetch live manifest from the tool server."""
        tool_name = tool_name.lower()
        if tool_name not in self.tool_map:
            return None
        
        port = self.tool_map[tool_name]["port"]
        try:
            resp = requests.get(f"{self.base_url}:{port}/mcp/manifest", timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return None

    def search_endpoint(self, tool_name: str, query: str) -> Optional[str]:
        """Heuristic search for the best endpoint based on query keywords."""
        tool_name = tool_name.lower()
        if tool_name not in self.tool_map:
            return None
        
        # Check current registry data first
        endpoints = self.tool_map[tool_name].get("endpoints", [])
        query = query.lower()
        
        for ep in endpoints:
            path = ep.get("path", "").lower()
            if any(kw in path for kw in query.split()) or any(kw in query for kw in path.split("/")):
                return ep.get("path")
        
        # Fallback: Live manifest query
        manifest = self.get_tool_manifest(tool_name)
        if manifest and "tools" in manifest:
            for t in manifest["tools"]:
                path = t.get("path", "").lower()
                if any(kw in path for kw in query.split()):
                    return t.get("path")
                    
        return None

    def call_tool(self, tool_name: str, endpoint: str, method: str = "GET", data: Dict = None, params: Dict = None) -> str:
        """Call tool with built-in self-healing on 404."""
        tool_name = tool_name.lower()
        if tool_name not in self.tool_map:
            # Re-scan registry in case a new tool was synthesized
            self._load_registry()
            if tool_name not in self.tool_map:
                return f"❌ Tool '{tool_name}' not found. Available: {', '.join(self.tool_map.keys())}"
        
        port = self.tool_map[tool_name]["port"]
        url = f"{self.base_url}:{port}{endpoint}"
        
        try:
            if method.upper() == "GET":
                resp = requests.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                resp = requests.post(url, json=data, timeout=10)
            else:
                return f"❌ Unsupported method: {method}"
            
            # --- SELF-HEALING LOGIC ---
            if resp.status_code == 404:
                print(f"[Healing] 404 on {endpoint}. Attempting path discovery...")
                new_path = self.search_endpoint(tool_name, endpoint)
                if new_path and new_path != endpoint:
                    print(f"[Healing] Re-routing to discoverd path: {new_path}")
                    return self.call_tool(tool_name, new_path, method, data, params)
            
            if resp.status_code < 300:
                try:
                    return f"✅ {tool_name.upper()} Success: {resp.json()}"
                except:
                    return f"✅ {tool_name.upper()} Success: {resp.text[:500]}"
            else:
                return f"⚠️ {tool_name.upper()} Error ({resp.status_code}): {resp.text}"
        except Exception as e:
            return f"❌ {tool_name.upper()} Exception: {e}"

    def list_tools(self) -> str:
        """List all available MCP tools."""
        self._load_registry()
        items = []
        for name, data in self.tool_map.items():
            ep_count = len(data.get("endpoints", []))
            items.append(f"  • {name.upper()} (Port {data['port']}, {ep_count} endpoints)")
        return "🛠️ Dynamic MCP Manifest:\n" + "\n".join(items)
