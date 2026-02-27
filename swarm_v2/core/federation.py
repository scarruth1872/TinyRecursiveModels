"""
Swarm Federation Protocol — Phase 5: Mesh Federation
Enables multiple Swarm OS instances to connect and share global memory vectors across network boundaries.

Features:
- P2P handshake protocol for connecting to other Swarm instances
- Federation registry to track connected swarms
- Memory sync endpoints to share vectors across instances
- Discovery mechanism using configurable seed nodes
"""

import os
import json
import asyncio
import hashlib
import requests
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from threading import Thread
import time

# Try to import from existing modules
try:
    from swarm_v2.core.global_memory import get_global_memory, GlobalMemorySync
except ImportError:
    GlobalMemorySync = None
    def get_global_memory():
        return None

FEDERATION_DIR = os.getenv("SWARM_FEDERATION_DIR", "swarm_v2_federation")
os.makedirs(FEDERATION_DIR, exist_ok=True)

FEDERATION_API_PREFIX = "/federation"


@dataclass
class SwarmNode:
    """Represents a node in the Swarm Federation."""
    node_id: str
    name: str
    host: str
    port: int
    api_key: str = ""
    status: str = "offline"  # online, offline, connecting
    last_seen: str = ""
    capabilities: List[str] = field(default_factory=list)
    memory_count: int = 0
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "status": self.status,
            "last_seen": self.last_seen,
            "capabilities": self.capabilities,
            "memory_count": self.memory_count
        }


class FederationRegistry:
    """Registry of connected Swarm Federation nodes."""
    
    def __init__(self):
        self.local_node: Optional[SwarmNode] = None
        self.connected_nodes: Dict[str, SwarmNode] = {}
        self.pending_connections: Set[str] = set()
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from disk."""
        registry_path = os.path.join(FEDERATION_DIR, "registry.json")
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r') as f:
                    data = json.load(f)
                    # Load connected nodes
                    for node_data in data.get("connected_nodes", []):
                        node = SwarmNode(**node_data)
                        self.connected_nodes[node.node_id] = node
            except Exception as e:
                print(f"[Federation] Failed to load registry: {e}")
    
    def _save_registry(self):
        """Save registry to disk."""
        registry_path = os.path.join(FEDERATION_DIR, "registry.json")
        data = {
            "connected_nodes": [n.to_dict() for n in self.connected_nodes.values()],
            "last_updated": datetime.now().isoformat()
        }
        with open(registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_local(self, node_id: str, name: str, host: str, port: int, api_key: str):
        """Register this local node."""
        self.local_node = SwarmNode(
            node_id=node_id,
            name=name,
            host=host,
            port=port,
            api_key=api_key,
            status="online",
            last_seen=datetime.now().isoformat(),
            capabilities=["memory_sync", "peer_discovery", "handshake"]
        )
    
    def add_node(self, node: SwarmNode) -> bool:
        """Add a node to the registry."""
        if node.node_id == self.local_node.node_id:
            return False  # Don't add self
        
        existing = self.connected_nodes.get(node.node_id)
        if existing and existing.status == "online":
            return False  # Already connected
        
        self.connected_nodes[node.node_id] = node
        self._save_registry()
        return True
    
    def remove_node(self, node_id: str):
        """Remove a node from the registry."""
        if node_id in self.connected_nodes:
            del self.connected_nodes[node_id]
            self._save_registry()
    
    def get_node(self, node_id: str) -> Optional[SwarmNode]:
        """Get a node by ID."""
        return self.connected_nodes.get(node_id)
    
    def get_online_nodes(self) -> List[SwarmNode]:
        """Get all online nodes."""
        return [n for n in self.connected_nodes.values() if n.status == "online"]
    
    def mark_online(self, node_id: str):
        """Mark a node as online."""
        if node_id in self.connected_nodes:
            self.connected_nodes[node_id].status = "online"
            self.connected_nodes[node_id].last_seen = datetime.now().isoformat()
            self._save_registry()
    
    def mark_offline(self, node_id: str):
        """Mark a node as offline."""
        if node_id in self.connected_nodes:
            self.connected_nodes[node_id].status = "offline"
            self._save_registry()


class FederationProtocol:
    """
    Federation Protocol implementation for Swarm OS Mesh Federation.
    Enables P2P handshake, memory sync, and peer discovery.
    """
    
    def __init__(self, local_node_id: str, local_name: str, local_port: int = 8001):
        self.registry = FederationRegistry()
        self.local_node_id = local_node_id
        self.local_name = local_name
        self.local_port = local_port
        self.global_memory = get_global_memory()
        self.is_running = False
        self._heartbeat_thread: Optional[Thread] = None
        
        # Generate local API key
        self.api_key = hashlib.sha256(
            f"{local_node_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        # Register local node
        self.registry.register_local(
            local_node_id, local_name, "localhost", local_port, self.api_key
        )
        
        print(f"[Federation] Initialized for {local_name} (ID: {local_node_id[:8]}...)")
    
    def generate_node_id(self) -> str:
        """Generate a unique node ID."""
        return hashlib.sha256(
            f"{self.local_name}_{self.local_port}_{datetime.now().isoformat()}".encode()
        ).hexdigest()
    
    async def handshake(self, target_host: str, target_port: int) -> Optional[SwarmNode]:
        """
        Perform P2P handshake with another Swarm instance.
        
        Steps:
        1. Send handshake request to target
        2. Verify target's identity
        3. Exchange capabilities
        4. Register in both registries
        """
        target_url = f"http://{target_host}:{target_port}{FEDERATION_API_PREFIX}/handshake"
        
        handshake_data = {
            "node_id": self.local_node_id,
            "name": self.local_name,
            "host": "localhost",
            "port": self.local_port,
            "api_key": self.api_key,
            "capabilities": ["memory_sync", "peer_discovery", "handshake"],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(
                target_url,
                json=handshake_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Create node from response
                node = SwarmNode(
                    node_id=data["node_id"],
                    name=data["name"],
                    host=data["host"],
                    port=data["port"],
                    api_key=data["api_key"],
                    status="online",
                    last_seen=datetime.now().isoformat(),
                    capabilities=data.get("capabilities", [])
                )
                
                # Add to registry
                self.registry.add_node(node)
                
                print(f"[Federation] Handshake successful with {node.name}")
                return node
            
        except Exception as e:
            print(f"[Federation] Handshake failed: {e}")
        
        return None
    
    async def discover_peers(self, seed_host: str, seed_port: int) -> List[SwarmNode]:
        """
        Discover peers using a seed node.
        """
        seed_url = f"http://{seed_host}:{seed_port}{FEDERATION_API_PREFIX}/peers"
        
        try:
            response = requests.get(
                seed_url,
                params={"node_id": self.local_node_id},
                timeout=10
            )
            
            if response.status_code == 200:
                peers_data = response.json()
                discovered = []
                
                for peer_data in peers_data.get("peers", []):
                    if peer_data["node_id"] != self.local_node_id:
                        node = SwarmNode(
                            node_id=peer_data["node_id"],
                            name=peer_data["name"],
                            host=peer_data["host"],
                            port=peer_data["port"],
                            api_key="",  # Will be set during handshake
                            status="online"
                        )
                        
                        if self.registry.add_node(node):
                            discovered.append(node)
                
                print(f"[Federation] Discovered {len(discovered)} new peers")
                return discovered
        
        except Exception as e:
            print(f"[Federation] Peer discovery failed: {e}")
        
        return []
    
    async def sync_memories(self, target_node_id: str) -> dict:
        """
        Sync memories with a specific target node.
        """
        node = self.registry.get_node(target_node_id)
        if not node or node.status != "online":
            return {"error": "Node not available"}
        
        target_url = f"{node.base_url}{FEDERATION_API_PREFIX}/memory/sync"
        
        # Get local memories to share
        if self.global_memory:
            stats = self.global_memory.get_stats()
            local_count = stats.get("total_memories", 0)
        else:
            local_count = 0
        
        try:
            # Request memories from target
            response = requests.post(
                target_url,
                json={
                    "source_node_id": self.local_node_id,
                    "source_name": self.local_name,
                    "local_memory_count": local_count
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                received = data.get("memories", [])
                
                # Store received memories
                if self.global_memory and received:
                    for mem in received:
                        self.global_memory.contribute(
                            content=mem.get("content", ""),
                            author=mem.get("author", "federation"),
                            author_role=mem.get("author_role", "federated"),
                            memory_type=mem.get("memory_type", "federated_knowledge"),
                            tags=mem.get("tags", ["federated"])
                        )
                
                return {
                    "status": "success",
                    "synced_from": node.name,
                    "memories_received": len(received)
                }
        
        except Exception as e:
            return {"error": str(e)}
        
        return {"error": "Sync failed"}

    def handle_handshake(self, data: dict) -> dict:
        """Handle incoming handshake request from a peer."""
        try:
            node = SwarmNode(
                node_id=data["node_id"],
                name=data["name"],
                host=data["host"],
                port=data["port"],
                api_key=data["api_key"],
                status="online",
                last_seen=datetime.now().isoformat(),
                capabilities=data.get("capabilities", [])
            )
            # Add/Update in our registry
            self.registry.add_node(node)
            print(f"[Federation] Accepted handshake from {node.name} ({node.node_id[:8]})")
            
            # Return our local info so the relationship is mutual
            return {
                "node_id": self.local_node_id,
                "name": self.local_name,
                "host": "localhost", # Should be resolved to external IP in production
                "port": self.local_port,
                "api_key": self.api_key,
                "capabilities": ["memory_sync", "peer_discovery", "handshake"]
            }
        except Exception as e:
            print(f"[Federation] Handshake handling failed: {e}")
            return {"error": "Internal server error during handshake"}

    def handle_peer_request(self, requester_node_id: str) -> dict:
        """Handle request for known peers to facilitate discovery."""
        # Return online nodes, excluding the requester
        peers = [n.to_dict() for n in self.registry.get_online_nodes() 
                if n.node_id != requester_node_id and n.node_id != self.local_node_id]
        return {"peers": peers}

    def handle_memory_sync(self, data: dict) -> dict:
        """Handle memory sync request by sharing local knowledge assets."""
        source_name = data.get("source_name", "Unknown Node")
        
        # Pull recent entries from global memory if available
        memories = []
        if self.global_memory:
            memories = self.global_memory.get_recent_entries(limit=20)

        print(f"[Federation] Memory sync event with {source_name}")
        return {
            "status": "success",
            "memories": memories 
        }
    
    def get_federation_stats(self) -> dict:
        """Get federation statistics."""
        online_nodes = self.registry.get_online_nodes()
        
        return {
            "local_node": self.registry.local_node.to_dict() if self.registry.local_node else None,
            "connected_nodes": len(online_nodes),
            "total_nodes": len(self.registry.connected_nodes),
            "node_list": [n.to_dict() for n in online_nodes]
        }
    
    def start_heartbeat(self, interval: int = 30):
        """Start sending heartbeats to connected nodes."""
        self.is_running = True
        
        def heartbeat_loop():
            while self.is_running:
                # Update local node timestamp
                if self.registry.local_node:
                    self.registry.local_node.last_seen = datetime.now().isoformat()
                
                # Check connectivity to all nodes
                for node in self.registry.connected_nodes.values():
                    try:
                        health_url = f"{node.base_url}/health"
                        response = requests.get(health_url, timeout=5)
                        if response.status_code == 200:
                            self.registry.mark_online(node.node_id)
                        else:
                            self.registry.mark_offline(node.node_id)
                    except:
                        self.registry.mark_offline(node.node_id)
                
                time.sleep(interval)
        
        self._heartbeat_thread = Thread(target=heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        print("[Federation] Heartbeat started")
    
    def stop_heartbeat(self):
        """Stop heartbeat."""
        self.is_running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)


# Singleton instance
_federation: Optional[FederationProtocol] = None

def get_federation() -> Optional[FederationProtocol]:
    return _federation

def init_federation(node_id: str, name: str, port: int = 8001) -> FederationProtocol:
    """Initialize the federation protocol."""
    global _federation
    _federation = FederationProtocol(node_id, name, port)
    return _federation
