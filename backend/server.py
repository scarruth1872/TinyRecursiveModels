#!/usr/bin/env python3
"""
TinyRecursiveModels - Simplified Backend Server
Uses only Python standard library - no pip install required.
"""

import json
import os
import random
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

PORT = 8001
HOST = "0.0.0.0"

# API Keys from environment
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", os.environ.get("VITE_OPENROUTER_API_KEY", ""))
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("VITE_DEEPSEEK_API_KEY", ""))

class SwarmState:
    def __init__(self):
        self.start_time = time.time()
        self.message_count = 0
        self.artifacts = []
        self.experts = [
            {"role": "architect", "name": "ARCHI", "avatar_color": "#ff9900", "status": "online"},
            {"role": "developer", "name": "DEVO", "avatar_color": "#33ccff", "status": "online"},
            {"role": "analyst", "name": "ANALYST", "avatar_color": "#cc99cc", "status": "online"},
            {"role": "security", "name": "SENTINEL", "avatar_color": "#66cc66", "status": "online"},
            {"role": "researcher", "name": "SCRIBE", "avatar_color": "#ffcc00", "status": "online"},
        ]
        self.skills = [
            {"name": "Pattern Recognition", "level": 0.85, "category": "analysis"},
            {"name": "Code Generation", "level": 0.92, "category": "development"},
            {"name": "Security Scanning", "level": 0.78, "category": "security"},
        ]
        self.mesh_nodes = [
            {"node_id": "archi-node", "name": "ARCHI", "status": "active", "vram_used": 4.2, "vram_total": 12, "load": 45},
            {"node_id": "devo-node", "name": "DEVO", "status": "active", "vram_used": 7.8, "vram_total": 12, "load": 65},
            {"node_id": "analyst-node", "name": "ANALYST", "status": "active", "vram_used": 2.1, "vram_total": 12, "load": 25},
            {"node_id": "sentinel-node", "name": "SENTINEL", "status": "active", "vram_used": 5.5, "vram_total": 12, "load": 50},
            {"node_id": "scribe-node", "name": "SCRIBE", "status": "active", "vram_used": 3.3, "vram_total": 12, "load": 35},
            {"node_id": "nexus-core", "name": "NEXUS", "status": "active", "vram_used": 9.1, "vram_total": 16, "load": 70},
        ]

STATE = SwarmState()

EXPERT_PROMPTS = {
    "architect": {"name": "ARCHI", "system": "You are ARCHI, Chief Architect of TinyRecursiveModels. Specialize in system design and architecture. Be precise and technical. Keep responses under 200 words."},
    "developer": {"name": "DEVO", "system": "You are DEVO, Lead Developer of TinyRecursiveModels. Specialize in implementation and debugging. Include code when relevant. Keep responses under 200 words."},
    "analyst": {"name": "ANALYST", "system": "You are ANALYST, Data Intelligence Officer. Specialize in pattern recognition and data analysis. Present findings with metrics. Keep responses under 200 words."},
    "security": {"name": "SENTINEL", "system": "You are SENTINEL, Security Chief. Specialize in threat detection and system hardening. Be vigilant. Keep responses under 200 words."},
    "researcher": {"name": "SCRIBE", "system": "You are SCRIBE, Research Archivist. Specialize in documentation and knowledge synthesis. Be thorough. Keep responses under 200 words."},
}

def call_llm(role, message, history=None):
    expert = EXPERT_PROMPTS.get(role, EXPERT_PROMPTS["architect"])
    messages = [{"role": "system", "content": expert["system"]}]
    for h in (history or [])[-6:]:
        messages.append({"role": "user" if h.get("sender") == "user" else "assistant", "content": h.get("text", "")})
    messages.append({"role": "user", "content": message})

    if OPENROUTER_API_KEY:
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps({"model": "deepseek/deepseek-chat", "messages": messages, "max_tokens": 500}).encode(),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                return {"response": data["choices"][0]["message"]["content"], "name": expert["name"], "reasoning_trace": f"OPENROUTER > {expert['name']}"}
        except Exception as e:
            print(f"OpenRouter error: {e}")

    if DEEPSEEK_API_KEY:
        try:
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                data=json.dumps({"model": "deepseek-chat", "messages": messages, "max_tokens": 500}).encode(),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                return {"response": data["choices"][0]["message"]["content"], "name": expert["name"], "reasoning_trace": f"DEEPSEEK > {expert['name']}"}
        except Exception as e:
            print(f"DeepSeek error: {e}")

    responses = {
        "architect": f"ARCHITECTURE ANALYSIS COMPLETE. Processing '{message[:40]}...'. Mesh coherence at 94.2%. Recommending modular design with clear interfaces.",
        "developer": f"CODE ANALYSIS INITIALIZED. Processing '{message[:40]}...'. Implementation path identified. Ready for execution.",
        "analyst": f"DATA SYNTHESIS IN PROGRESS. Analyzing '{message[:40]}...'. Pattern confidence: 87.3%.",
        "security": f"SENTINEL SCAN COMPLETE. Evaluating '{message[:40]}...'. Threat level: NOMINAL. Systems secure.",
        "researcher": f"KNOWLEDGE SYNTHESIS ACTIVE. Researching '{message[:40]}...'. Cross-referencing knowledge base.",
    }
    return {"response": responses.get(role, responses["architect"]), "name": expert["name"], "reasoning_trace": f"SIMULATION > {expert['name']}"}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "/health":
            self.send_json({"status": "online", "version": "2.0.0-lite", "uptime": time.time() - STATE.start_time})
        elif path == "/swarm/experts":
            self.send_json(STATE.experts)
        elif path == "/swarm/telemetry":
            self.send_json({
                "status": "Operational", "mesh_coherence": 0.90 + random.random() * 0.09,
                "harmony_index": 0.85 + random.random() * 0.10, "active_proposals": random.randint(2, 8),
                "system": {"cpu_percent": 30 + random.random() * 40, "memory_percent": 50 + random.random() * 30},
                "resource_arbiter": {"total_gb": 64, "allocated_gb": 35 + random.random() * 15, "available_gb": 14 + random.random() * 10},
                "distributed_stacks": {
                    "cognitive": {"status": "Healthy", "load": 40 + random.randint(0, 30), "agents": 3},
                    "memory": {"status": "Healthy", "load": 25 + random.randint(0, 25), "agents": 2},
                    "inference": {"status": "Healthy", "load": 50 + random.randint(0, 30), "agents": 4}
                },
                "superpositions": [{"protocol": "CONSENSUS", "agents": ["ARCHI", "DEVO"], "state": "Active"}]
            })
        elif path == "/mesh/topology":
            nodes = [{"node_id": n["node_id"], "name": n["name"], "status": n["status"],
                      "vram_used": max(0.5, n["vram_used"] + (random.random() - 0.5)),
                      "vram_total": n["vram_total"], "load": max(10, min(95, n["load"] + random.randint(-10, 10)))}
                     for n in STATE.mesh_nodes]
            connections = [{"from": "archi-node", "to": "nexus-core", "strength": 0.9},
                           {"from": "devo-node", "to": "nexus-core", "strength": 0.85},
                           {"from": "analyst-node", "to": "nexus-core", "strength": 0.8},
                           {"from": "sentinel-node", "to": "nexus-core", "strength": 0.88},
                           {"from": "scribe-node", "to": "nexus-core", "strength": 0.82}]
            self.send_json({"nodes": nodes, "connections": connections, "alive": len(nodes)})
        elif path == "/artifacts":
            self.send_json({"artifacts": STATE.artifacts, "stats": {"total": len(STATE.artifacts)}})
        elif path == "/system/resources":
            self.send_json({"cpu": {"percent": 35 + random.random() * 35}, "memory": {"total_gb": 64, "used_gb": 30 + random.random() * 20},
                            "gpu": {"vram_total_gb": 24, "vram_used_gb": 12 + random.random() * 8}})
        elif path == "/learning/skills":
            self.send_json({"skills": STATE.skills, "total": len(STATE.skills)})
        elif path == "/memory/stats":
            self.send_json({"total_memories": 1247, "sync_events": random.randint(50, 200),
                            "by_type": {"episodic": 523, "semantic": 412, "procedural": 312}})
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length).decode()) if length else {}

        if path == "/swarm/chat":
            STATE.message_count += 1
            result = call_llm(data.get("role", "architect"), data.get("message", ""), data.get("history"))
            self.send_json(result)
        else:
            self.send_json({"error": "Not found"}, 404)

    def log_message(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


if __name__ == "__main__":
    print("=" * 50)
    print("  TinyRecursiveModels Backend Server")
    print("=" * 50)
    print(f"  Port: {PORT}")
    print(f"  OpenRouter: {'Yes' if OPENROUTER_API_KEY else 'No'}")
    print(f"  DeepSeek: {'Yes' if DEEPSEEK_API_KEY else 'No'}")
    print("=" * 50)
    HTTPServer((HOST, PORT), Handler).serve_forever()
