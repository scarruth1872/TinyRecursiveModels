
"""
P2P Agent Mesh — Phase 3: Distributed Consciousness
Each agent becomes its own micro-node in a peer-to-peer fabric.

Architecture:
- Every agent registers itself on the mesh with its capabilities
- Agents can discover peers and route tasks directly (no central orchestrator needed)
- If the main gateway (port 8000) goes down, agents keep running
- Gossip-based heartbeat keeps the mesh topology alive
"""

import asyncio
import json
import os
import time
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
from swarm_v2.skills.embedding_skill import FastEmbeddingSkill



MESH_DIR = "swarm_v2_mesh"
os.makedirs(MESH_DIR, exist_ok=True)


class MeshNode:
    """Represents a single agent node in the P2P mesh."""

    def __init__(self, node_id: str, name: str, role: str,
                 host: str = "127.0.0.1", port: int = 0,
                 specialties: List[str] = None,
                 skills: List[str] = None):
        self.node_id = node_id
        self.name = name
        self.role = role
        self.host = host
        self.port = port
        self.specialties = specialties or []
        self.skills = skills or []
        self.status = "online"
        self.last_heartbeat = time.time()
        self.joined_at = datetime.now().isoformat()
        self.task_count = 0
        self.peer_connections = 0

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "role": self.role,
            "host": self.host,
            "port": self.port,
            "specialties": self.specialties,
            "skills": self.skills,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
            "joined_at": self.joined_at,
            "task_count": self.task_count,
            "latency_ms": round((time.time() - self.last_heartbeat) * 1000, 1),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MeshNode":
        node = cls(
            node_id=data["node_id"],
            name=data["name"],
            role=data["role"],
            host=data.get("host", "127.0.0.1"),
            port=data.get("port", 0),
            specialties=data.get("specialties", []),
            skills=data.get("skills", []),
        )
        node.status = data.get("status", "online")
        node.last_heartbeat = data.get("last_heartbeat", time.time())
        node.task_count = data.get("task_count", 0)
        return node

    def heartbeat(self):
        self.last_heartbeat = time.time()
        self.status = "online"

    @property
    def is_alive(self) -> bool:
        return (time.time() - self.last_heartbeat) < 600  # 10-minute timeout for in-process nodes


class AgentMesh:
    """
    The P2P mesh fabric. Manages node discovery, routing, and health.
    Survives orchestrator failures via decentralized state.
    """

    def __init__(self):
        self.nodes: Dict[str, MeshNode] = {}
        self.message_log: List[dict] = []
        self.topology_version = 0
        # Load topology version but don't restore stale nodes
        # Nodes will be re-registered on each startup
        self._load_topology_version()

    def _load_topology_version(self):
        """Load only the topology version from persisted state."""
        state_path = os.path.join(MESH_DIR, "mesh_state.json")
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.topology_version = data.get("topology_version", 0)
            except Exception:
                pass

    def _load_state(self):
        """Load persisted mesh state."""
        state_path = os.path.join(MESH_DIR, "mesh_state.json")
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for node_data in data.get("nodes", []):
                    node = MeshNode.from_dict(node_data)
                    self.nodes[node.node_id] = node
                self.topology_version = data.get("topology_version", 0)
            except Exception:
                pass

    def _save_state(self):
        """Persist mesh state to disk."""
        state_path = os.path.join(MESH_DIR, "mesh_state.json")
        data = {
            "topology_version": self.topology_version,
            "updated_at": datetime.now().isoformat(),
            "node_count": len(self.nodes),
            "nodes": [n.to_dict() for n in self.nodes.values()],
        }
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def register_node(self, name: str, role: str, specialties: List[str] = None,
                       skills: List[str] = None, host: str = "127.0.0.1",
                       port: int = 0) -> MeshNode:
        """Register a new agent node on the mesh."""
        node_id = hashlib.sha256(
            f"{name}:{role}:{host}:{port}".encode()
        ).hexdigest()[:12]

        node = MeshNode(
            node_id=node_id,
            name=name,
            role=role,
            host=host,
            port=port,
            specialties=specialties or [],
            skills=skills or [],
        )
        self.nodes[node_id] = node
        self.topology_version += 1
        self._save_state()

        self.message_log.append({
            "type": "node_joined",
            "node": name,
            "role": role,
            "node_id": node_id,
            "timestamp": datetime.now().isoformat(),
        })

        return node

    def deregister_node(self, node_id: str) -> bool:
        """Remove a node from the mesh."""
        if node_id in self.nodes:
            name = self.nodes[node_id].name
            del self.nodes[node_id]
            self.topology_version += 1
            self._save_state()

            self.message_log.append({
                "type": "node_left",
                "node": name,
                "node_id": node_id,
                "timestamp": datetime.now().isoformat(),
            })
            return True
        return False

    def heartbeat(self, node_id: str) -> bool:
        """Receive a heartbeat from a node."""
        if node_id in self.nodes:
            self.nodes[node_id].heartbeat()
            return True
        return False

    def discover_peers(self, requesting_node_id: str = None,
                        role_filter: str = None,
                        specialty_filter: str = None) -> List[dict]:
        """Discover available peers on the mesh, optionally filtered."""
        peers = []
        for nid, node in self.nodes.items():
            if nid == requesting_node_id:
                continue
            if role_filter and node.role != role_filter:
                continue
            if specialty_filter and specialty_filter not in node.specialties:
                continue
            peers.append(node.to_dict())
        return peers

    def find_best_node(self, task: str, required_specialty: str = None) -> Optional[MeshNode]:
        """Find the best alive node for a given task using skill matching."""
        candidates = []
        task_lower = task.lower()

        for node in self.nodes.values():
            if not node.is_alive:
                continue

            score = 0
            # Specialty matching
            for spec in node.specialties:
                if spec.lower() in task_lower:
                    score += 10
            # Skill matching
            for skill in node.skills:
                if skill.lower() in task_lower:
                    score += 5
            # Role matching
            if node.role.lower() in task_lower:
                score += 8
            # Required specialty filter
            if required_specialty:
                if required_specialty in node.specialties:
                    score += 20
                else:
                    continue
            # Prefer less busy nodes
            score -= node.task_count * 0.1

            if score > 0:
                candidates.append((score, node))

        if not candidates:
            # Return any alive node as fallback
            alive = [n for n in self.nodes.values() if n.is_alive]
            return alive[0] if alive else None

        candidates.sort(key=lambda x: x[0], reverse=True)
        
        # If the top score is low, try semantic matching as a tie-breaker or fallback
        if candidates[0][0] < 10:
            try:
                embedder = FastEmbeddingSkill()
                task_emb = embedder.embed_text(task_lower)
                if task_emb:
                    semantic_candidates = []
                    for _, node in candidates:
                        # Combine specialties and skills into a node description
                        node_desc = f"{node.role} {node.name} {' '.join(node.specialties)} {' '.join(node.skills)}"
                        node_emb = embedder.embed_text(node_desc.lower())
                        score = embedder.cosine_similarity(task_emb, node_emb)
                        semantic_candidates.append((score, node))
                    
                    semantic_candidates.sort(key=lambda x: x[0], reverse=True)
                    return semantic_candidates[0][1]
            except Exception as e:
                print(f"[Mesh] Semantic routing failed: {e}")

        return candidates[0][1]

    async def route_task(self, task: str, target_node_id: str = None,
                          required_specialty: str = None) -> dict:
        """Route a task to a node on the mesh (P2P style)."""
        if target_node_id and target_node_id in self.nodes:
            node = self.nodes[target_node_id]
        else:
            node = self.find_best_node(task, required_specialty)

        if not node:
            return {"error": "No suitable node found on the mesh", "task": task}

        node.task_count += 1
        self._save_state()

        self.message_log.append({
            "type": "task_routed",
            "task": task[:80],
            "target_node": node.name,
            "target_role": node.role,
            "node_id": node.node_id,
            "timestamp": datetime.now().isoformat(),
        })

        return {
            "routed_to": node.to_dict(),
            "task": task,
            "mesh_version": self.topology_version,
        }

    def get_topology(self) -> dict:
        """Get the full mesh topology."""
        alive = [n for n in self.nodes.values() if n.is_alive]
        stale = [n for n in self.nodes.values() if not n.is_alive]

        return {
            "version": self.topology_version,
            "total_nodes": len(self.nodes),
            "alive": len(alive),
            "stale": len(stale),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "connections": self._compute_connections(),
        }

    def _compute_connections(self) -> List[dict]:
        """Compute logical connections between nodes (for visualization)."""
        connections = []
        node_list = list(self.nodes.values())
        for i, a in enumerate(node_list):
            for b in node_list[i + 1:]:
                strength = 0
                shared = set(a.specialties) & set(b.specialties)
                
                # Heuristic 1: Shared Specialties (High Strength)
                if shared:
                    strength += len(shared) * 2
                
                # Heuristic 2: Role Proximity (Dynamic collaboration)
                # Connect anything related to 'Dev' or 'Code' or 'Design'
                dev_words = {"developer", "architect", "engineer", "logic"}
                if (any(w in a.role.lower() for w in dev_words) and 
                    any(w in b.role.lower() for w in dev_words)):
                    strength += 1
                
                # Heuristic 3: Architect Star Topology (Central hub)
                if a.role == "Architect" or b.role == "Architect":
                    strength += 1

                if strength > 0:
                    connections.append({
                        "from": a.node_id,
                        "to": b.node_id,
                        "shared_specialties": list(shared),
                        "strength": strength,
                    })
        return connections

    def get_stats(self) -> dict:
        alive = [n for n in self.nodes.values() if n.is_alive]
        return {
            "total_nodes": len(self.nodes),
            "alive_nodes": len(alive),
            "topology_version": self.topology_version,
            "total_tasks_routed": sum(n.task_count for n in self.nodes.values()),
            "total_messages": len(self.message_log),
            "connections": len(self._compute_connections()),
        }

    def get_message_log(self, limit: int = 20) -> List[dict]:
        return self.message_log[-limit:]

    def reconfigure_mesh(self) -> dict:
        """
        Phase 7: Real-time Mesh Reconfiguration.
        Detects failed nodes, redistributes their specialties to surviving nodes,
        and logs reconfiguration events.
        """
        alive = [n for n in self.nodes.values() if n.is_alive]
        failed = [n for n in self.nodes.values() if not n.is_alive]

        if not failed:
            return {"action": "none", "alive": len(alive), "failed": 0}

        redistributed = 0
        for dead_node in failed:
            orphan_specialties = dead_node.specialties
            if orphan_specialties and alive:
                # Distribute orphan specialties round-robin to alive nodes
                for i, spec in enumerate(orphan_specialties):
                    target = alive[i % len(alive)]
                    if spec not in target.specialties:
                        target.specialties.append(spec)
                        redistributed += 1

            # Log the reconfiguration event
            self.message_log.append({
                "type": "mesh_reconfiguration",
                "failed_node": dead_node.name,
                "failed_node_id": dead_node.node_id,
                "orphan_specialties": orphan_specialties,
                "redistributed_to": [n.name for n in alive],
                "timestamp": datetime.now().isoformat(),
            })

            # Mark as explicitly offline (keep in registry for recovery)
            dead_node.status = "offline"

        self.topology_version += 1
        self._save_state()

        return {
            "action": "reconfigured",
            "alive": len(alive),
            "failed": len(failed),
            "specialties_redistributed": redistributed,
            "topology_version": self.topology_version
        }

# Singleton
_mesh: Optional[AgentMesh] = None

def get_agent_mesh() -> AgentMesh:
    global _mesh
    if _mesh is None:
        _mesh = AgentMesh()
    return _mesh
