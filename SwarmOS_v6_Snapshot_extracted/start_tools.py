
import os
import json
import subprocess
import sys
import time
import requests

SYNTH_DIR = "swarm_v2_synthesized"
REGISTRY_PATH = os.path.join(SYNTH_DIR, "registry.json")

def start_tools():
    if not os.path.exists(REGISTRY_PATH):
        print("Registry not found.")
        return

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    tools = registry.get("tools", [])
    processes = []

    print(f"Starting {len(tools)} tools...")

    for tool in tools:
        name = tool["name"]
        port = tool["port"]
        script_name = f"mcp_{name.lower()}_server.py"
        script_path = os.path.join(SYNTH_DIR, script_name)
        
        if not os.path.exists(script_path):
            print(f"Server script {script_path} not found.")
            continue

        print(f"Starting {name} on port {port}...")
        # Use python from the venv
        cmd = [sys.executable, script_path]
        try:
            # We use created_new_console=True on Windows to avoid capturing Ctrl+C if we kill main script
            creationflags = subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            proc = subprocess.Popen(cmd, creationflags=creationflags)
            processes.append((name, port, proc))
        except Exception as e:
            print(f"Failed to start {name}: {e}")

    print("All tools initiated. Waiting 5s for startup...")
    time.sleep(5)

    # Verify health
    for name, port, proc in processes:
        try:
            res = requests.get(f"http://localhost:{port}/health", timeout=2)
            if res.status_code == 200:
                print(f"✅ {name} online on {port}")
            else:
                print(f"❌ {name} health check failed: {res.status_code}")
        except Exception as e:
            print(f"❌ {name} unreachable on {port}: {e}")

    print("\nTools are running in background.")

if __name__ == "__main__":
    start_tools()
