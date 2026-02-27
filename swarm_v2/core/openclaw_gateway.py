
import os
import json
import time
import asyncio
import requests
import re
from datetime import datetime

# Configuration
SWARM_API_URL = "http://127.0.0.1:8001"
INBOX_FILE = "swarm_v2_artifacts/openclaw_inbox.json"
HEARTBEAT_FILE = "HEARTBEAT.md"

class OpenClawGateway:
    """
    OpenClaw Gateway (Perception Layer) Stub.
    Simulates a multi-channel interface (Telegram/WhatsApp) that routes to Swarm OS.
    """
    def __init__(self):
        os.makedirs(os.path.dirname(INBOX_FILE), exist_ok=True)
        if not os.path.exists(INBOX_FILE):
             with open(INBOX_FILE, "w") as f:
                 json.dump([], f)

    async def start(self):
        print("[OpenClaw] Gateway Active. Monitoring multi-channel signals...")
        while True:
            try:
                await self.poll_inbox()
                await self.check_proactive_triggers()
            except Exception as e:
                print(f"[OpenClaw] Error in gateway loop: {e}")
            await asyncio.sleep(5)

    async def poll_inbox(self):
        """Read simulated messages from the inbox file."""
        if not os.path.exists(INBOX_FILE):
            return

        with open(INBOX_FILE, "r") as f:
            messages = json.load(f)

        if not messages:
            return

        # Process and clear inbox
        for msg in messages:
            print(f"[OpenClaw] Inbound via {msg.get('channel', 'unknown')}: {msg.get('text')}")
            await self.route_to_swarm(msg)

        with open(INBOX_FILE, "w") as f:
            json.dump([], f)

    async def route_to_swarm(self, msg):
        """Send message to Swarm API."""
        try:
            # We'll use the mesh/route endpoint or a direct expert call
            # For simplicity, we route to the Architect
            payload = {
                "task": msg.get("text"),
                "required_specialty": "Architect"
            }
            resp = requests.post(f"{SWARM_API_URL}/mesh/route", json=payload)
            if resp.status_code == 200:
                print(f"[OpenClaw] Routed to Swarm. Response: {resp.json().get('response', '')[:100]}...")
            else:
                print(f"[OpenClaw] Failed to route: {resp.status_code}")
        except Exception as e:
            print(f"[OpenClaw] Routing error: {e}")

    async def check_proactive_triggers(self):
        """Simulate a proactive check that might add a task to HEARTBEAT.md."""
        # Simple logic: If it's been a while since the last heartbeat, maybe add a status check
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                content = f.read()
            
            # If no uncompleted tasks, maybe add one periodically (every hour, simulated here with random)
            import random
            if "- [ ]" not in content and random.random() < 0.05:
                print("[OpenClaw] Proactive trigger: Requesting system resonance check.")
                new_task = f"\n- [ ] Perform a system-wide resonance check and report harmony status."
                # Append before the last section
                if "## neural_checkpoints" in content:
                    content = content.replace("## neural_checkpoints", f"{new_task}\n\n## neural_checkpoints")
                else:
                    content += new_task
                
                with open(HEARTBEAT_FILE, "w") as f:
                    f.write(content)

if __name__ == "__main__":
    gateway = OpenClawGateway()
    asyncio.run(gateway.start())
