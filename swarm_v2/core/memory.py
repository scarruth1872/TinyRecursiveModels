
"""
Persistent Memory System for Swarm V2 agents.
Short-term: in-memory list (recent conversation turns)
Long-term: JSON file persisted to disk per agent
"""
import os
import json
from typing import List, Dict, Any
from datetime import datetime

MEMORY_DIR = "swarm_v2_memory"


class AgentMemory:
    """Dual-layer memory: short-term (recent context) + long-term (persisted knowledge)."""

    def __init__(self, agent_name: str, short_term_limit: int = 20):
        self.agent_name = agent_name
        self.short_term_limit = short_term_limit

        # Short-term: recent conversation turns (in-memory)
        self.short_term: List[Dict] = []

        # Long-term: persisted knowledge, summaries, facts (on disk)
        self.long_term_path = os.path.join(MEMORY_DIR, f"{agent_name}_memory.json")
        os.makedirs(MEMORY_DIR, exist_ok=True)
        self.long_term: List[Dict] = self._load_long_term()

    def _load_long_term(self) -> List[Dict]:
        if os.path.exists(self.long_term_path):
            try:
                with open(self.long_term_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_long_term(self):
        with open(self.long_term_path, "w", encoding="utf-8") as f:
            json.dump(self.long_term, f, indent=2, default=str)

    def add_turn(self, sender: str, content: str, role: str = None):
        """Add a conversation turn to short-term memory."""
        turn = {
            "sender": sender,
            "content": content,
            "role": role or self.agent_name,
            "timestamp": datetime.now().isoformat(),
        }
        self.short_term.append(turn)

        # Trim short-term if it exceeds limit
        if len(self.short_term) > self.short_term_limit:
            # Move oldest turns to long-term as a summary
            overflow = self.short_term[:5]
            self.short_term = self.short_term[5:]
            self._archive_to_long_term(overflow)

    def _archive_to_long_term(self, turns: List[Dict]):
        """Archive short-term overflow to long-term storage."""
        summary = {
            "type": "conversation_archive",
            "archived_at": datetime.now().isoformat(),
            "turn_count": len(turns),
            "turns": turns,
        }
        self.long_term.append(summary)
        self._save_long_term()

    def add_fact(self, fact: str, source: str = "self"):
        """Store a learned fact in long-term memory."""
        entry = {
            "type": "fact",
            "content": fact,
            "source": source,
            "learned_at": datetime.now().isoformat(),
        }
        self.long_term.append(entry)
        self._save_long_term()

    def add_task_result(self, task: str, result: str, status: str = "completed"):
        """Store a completed task result in long-term memory."""
        entry = {
            "type": "task_result",
            "task": task,
            "result": result[:500],
            "status": status,
            "completed_at": datetime.now().isoformat(),
        }
        self.long_term.append(entry)
        self._save_long_term()

    def get_context_window(self, max_turns: int = 10) -> str:
        """Build a context string for the LLM from both memory layers."""
        parts = []

        # Long-term facts
        facts = [e for e in self.long_term if e.get("type") == "fact"]
        if facts:
            parts.append("=== Long-term Knowledge ===")
            for f in facts[-5:]:
                parts.append(f"  • {f['content']}")

        # Recent task results
        tasks = [e for e in self.long_term if e.get("type") == "task_result"]
        if tasks:
            parts.append("\n=== Recent Task Results ===")
            for t in tasks[-3:]:
                parts.append(f"  [{t['status']}] {t['task'][:60]} → {t['result'][:80]}")

        # Short-term conversation
        recent = self.short_term[-max_turns:]
        if recent:
            parts.append("\n=== Recent Conversation ===")
            for turn in recent:
                parts.append(f"  [{turn['sender']}]: {turn['content'][:120]}")

        return "\n".join(parts)

    def get_stats(self) -> Dict:
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "facts": len([e for e in self.long_term if e.get("type") == "fact"]),
            "tasks_completed": len([e for e in self.long_term if e.get("type") == "task_result"]),
            "archived_conversations": len([e for e in self.long_term if e.get("type") == "conversation_archive"]),
        }

    def clear_short_term(self):
        self.short_term = []

    def export_all(self) -> Dict:
        return {
            "agent": self.agent_name,
            "short_term": self.short_term,
            "long_term": self.long_term,
        }
