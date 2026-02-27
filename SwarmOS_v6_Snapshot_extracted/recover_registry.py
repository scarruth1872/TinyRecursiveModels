
import os
import re
import json
from datetime import datetime

SYNTH_DIR = "swarm_v2_synthesized"
REGISTRY_PATH = os.path.join(SYNTH_DIR, "registry.json")

def recover_registry():
    if not os.path.exists(SYNTH_DIR):
        print(f"Directory {SYNTH_DIR} not found.")
        return

    tools = []
    max_port = 9100

    for filename in os.listdir(SYNTH_DIR):
        if filename.endswith("_server.py") and filename.startswith("mcp_"):
            path = os.path.join(SYNTH_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract metadata
            name_match = re.search(r'MCP Tool Server: (\w+)', content)
            port_match = re.search(r'Port: (\d+)', content)
            source_match = re.search(r'Source: (.+)', content)
            
            if name_match and port_match:
                name = name_match.group(1)
                port = int(port_match.group(1))
                source = source_match.group(1).strip() if source_match else "unknown"
                
                if port > max_port:
                    max_port = port

                # Extract endpoints roughly
                endpoints = []
                # Pattern: @app.get("/path") or @app.post("/path")
                # followed by async def func_name
                endpoint_matches = re.findall(r'@app\.(get|post|put|delete)\("([^"]+)"\)\s+async def (\w+)', content)
                for method, path, func in endpoint_matches:
                    endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "function": func
                    })

                tools.append({
                    "name": name,
                    "tool_type": "mcp_server",
                    "source_skill": name,
                    "port": port,
                    "endpoints": endpoints,
                    "created_at": datetime.now().isoformat(),
                    "status": "generated",
                    "code_length": len(content)
                })
                print(f" recovered {name} on port {port}")

    # Save registry
    data = {
        "next_port": max_port + 1,
        "updated_at": datetime.now().isoformat(),
        "tools": tools
    }
    
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"Registry recovered with {len(tools)} tools. Next port: {max_port + 1}")

if __name__ == "__main__":
    recover_registry()
