
"""
Global Memory Sync — Phase 4: Production-Grade Vector Store
A shared vector memory store using ChromaDB for persistent, semantic knowledge mapping.

Replaces the simple keyword-based vector matching with true semantic embedding retrieval.
"""

import os
import json
import math
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import Counter

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

GLOBAL_MEMORY_DIR = os.getenv("SWARM_MEMORY_DIR", "swarm_v2_global_memory")
os.makedirs(GLOBAL_MEMORY_DIR, exist_ok=True)

class GlobalMemorySync:
    """
    Production-grade distributed vector database for shared long-term memory.
    Uses ChromaDB for high-fidelity semantic retrieval.
    """

    def __init__(self):
        self.entries_metadata: Dict[str, dict] = {}
        self.sync_log: List[dict] = []
        
        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(path=os.path.join(GLOBAL_MEMORY_DIR, "chroma"))
            self.collection = self.client.get_or_create_collection(
                name="swarm_global_memory",
                metadata={"hnsw:space": "cosine"}
            )
            print("[GlobalMemory] ChromaDB Production Backend - ONLINE")
        else:
            print("[GlobalMemory] ChromaDB NOT FOUND - Falling back to Legacy Mode")
            
        self._load_metadata()

    def _load_metadata(self):
        """Load additional metadata and sync logs."""
        meta_path = os.path.join(GLOBAL_MEMORY_DIR, "metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.entries_metadata = data.get("entries", {})
                self.sync_log = data.get("sync_log", [])
            except:
                pass

    def _save_metadata(self):
        """Persist metadata to disk."""
        meta_path = os.path.join(GLOBAL_MEMORY_DIR, "metadata.json")
        data = {
            "version": "2.0",
            "updated_at": datetime.now().isoformat(),
            "entries": self.entries_metadata,
            "sync_log": self.sync_log[-100:], # Keep last 100 entries
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def contribute(self, content: str, author: str, author_role: str,
                   memory_type: str = "knowledge",
                   tags: List[str] = None) -> str:
        """Add a memory to the global pool via ChromaDB."""
        entry_id = f"gm_{hash(content + author) & 0xFFFFFFFF:08x}"
        
        metadata = {
            "author": author,
            "author_role": author_role,
            "memory_type": memory_type,
            "tags": json.dumps(tags or []),
            "created_at": datetime.now().isoformat(),
            "access_count": 0
        }

        if CHROMA_AVAILABLE:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[entry_id]
            )
        
        self.entries_metadata[entry_id] = metadata
        self._save_metadata()

        self.sync_log.append({
            "action": "contributed",
            "author": author,
            "role": author_role,
            "entry_id": entry_id,
            "type": memory_type,
            "timestamp": datetime.now().isoformat(),
        })

        return entry_id

    def query(self, query_text: str, top_k: int = 5,
              author_filter: str = None,
              type_filter: str = None) -> List[Tuple[float, dict]]:
        """
        Semantic query using ChromaDB vectors.
        """
        if not CHROMA_AVAILABLE:
            return [] # Legacy search could go here if needed

        where_clause = {}
        if author_filter: where_clause["author"] = author_filter
        if type_filter: where_clause["memory_type"] = type_filter

        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where_clause if where_clause else None
        )

        formatted_results = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                doc = results["documents"][0][i]
                meta = results["metadatas"][0][i]
                eid = results["ids"][0][i]
                # Chroma distance is often L2 or cosine distance, we want similarity 0-1
                dist = results["distances"][0][i] if "distances" in results else 0.5
                score = 1.0 - dist # Cosine similarity approx
                
                # Update access stats
                if eid in self.entries_metadata:
                    self.entries_metadata[eid]["access_count"] += 1
                    self.entries_metadata[eid]["last_accessed"] = datetime.now().isoformat()
                
                entry_dict = {
                    "entry_id": eid,
                    "content": doc,
                    "author": meta["author"],
                    "author_role": meta["author_role"],
                    "memory_type": meta["memory_type"],
                    "tags": json.loads(meta["tags"]),
                    "created_at": meta["created_at"],
                    "access_count": self.entries_metadata.get(eid, {}).get("access_count", 0)
                }
                formatted_results.append((float(score), entry_dict))

        self._save_metadata()
        return formatted_results

    def sync_from_agent(self, agent_name: str, agent_role: str,
                         memories: List[dict]) -> int:
        """Sync memories with duplicate detection."""
        added = 0
        for mem in memories:
            content = mem.get("content", "")
            if not content or len(content) < 10: continue

            # Semantic duplicate detection
            existing = self.query(content, top_k=1)
            if existing and existing[0][0] > 0.95:
                continue

            self.contribute(
                content=content,
                author=agent_name,
                author_role=agent_role,
                memory_type=mem.get("type", "knowledge"),
                tags=mem.get("tags", [])
            )
            added += 1

        return added

    def get_context_for_agent(self, agent_name: str, task: str,
                                max_memories: int = 5) -> str:
        results = self.query(task, top_k=max_memories)
        if not results: return ""

        lines = ["=== Production-Grade Global Memory (ChromaDB) ==="]
        for score, entry in results:
            lines.append(
                f"  [{entry['author']}:{entry['author_role']}] "
                f"{entry['content'][:200]} "
                f"(semantic_match: {score:.2f})"
            )
        return "\n".join(lines)

    def get_stats(self) -> dict:
        if CHROMA_AVAILABLE:
            count = self.collection.count()
        else:
            count = len(self.entries_metadata)
            
        type_counts = Counter(e["memory_type"] for e in self.entries_metadata.values())
        author_counts = Counter(e["author"] for e in self.entries_metadata.values())
        
        return {
            "total_memories": count,
            "by_type": dict(type_counts),
            "by_author": dict(author_counts),
            "total_accesses": sum(e.get("access_count", 0) for e in self.entries_metadata.values()),
            "sync_events": len(self.sync_log),
            "backend": "ChromaDB" if CHROMA_AVAILABLE else "Mock/Legacy"
        }

    def get_recent_entries(self, limit: int = 20) -> List[dict]:
        """Get the most recent memory entries for federation sync."""
        if not CHROMA_AVAILABLE:
            # Fallback to metadata-only if Chroma is missing
            recent_ids = list(self.entries_metadata.keys())[-limit:]
            return [{"id": eid, **self.entries_metadata[eid]} for eid in recent_ids]
            
        try:
            # Get latest entries from ChromaDB
            results = self.collection.get(limit=limit)
            entries = []
            if results and results["documents"]:
                for i in range(len(results["documents"])):
                    entries.append({
                        "content": results["documents"][i],
                        "author": results["metadatas"][i]["author"],
                        "author_role": results["metadatas"][i]["author_role"],
                        "memory_type": results["metadatas"][i]["memory_type"],
                        "tags": json.loads(results["metadatas"][i]["tags"]) if isinstance(results["metadatas"][i]["tags"], str) else results["metadatas"][i]["tags"]
                    })
            return entries
        except Exception as e:
            print(f"[GlobalMemory] Failed to get recent entries: {e}")
            return []

    def get_sync_log(self, limit: int = 20) -> List[dict]:
        return self.sync_log[-limit:]

# Singleton
_global_mem: Optional[GlobalMemorySync] = None

def get_global_memory() -> GlobalMemorySync:
    global _global_mem
    if _global_mem is None:
        _global_mem = GlobalMemorySync()
    return _global_mem
