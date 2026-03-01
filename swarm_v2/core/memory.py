
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

    # Action tag prefixes — responses starting with these should be summarized, not stored raw
    ACTION_TAG_PREFIXES = ("WRITE_FILE:", "SEARCH_QUERY:", "CREATE_FILES:", "PLAN_FILE:",
                           "MAKE_DIR:", "CALL_TOOL:", "DELEGATE_TASK:", "REJECT_ARTIFACT:",
                           "APPROVE_ARTIFACT:", "TEST_ARTIFACT:")

    def _summarize_if_action(self, content: str) -> str:
        """If content starts with an action tag, replace it with a brief summary."""
        stripped = (content or "").strip()
        if stripped.startswith("WRITE_FILE:"):
            fname = stripped.split("\n")[0].replace("WRITE_FILE:", "").strip()
            return f"[wrote file: {fname}]"
        if stripped.startswith("SEARCH_QUERY:"):
            query = stripped.split("\n")[0].replace("SEARCH_QUERY:", "").strip()
            return f"[searched: {query}]"
        if stripped.startswith("CREATE_FILES:"):
            return "[created multiple files]"
        if stripped.startswith("PLAN_FILE:"):
            fname = stripped.split("\n")[0].replace("PLAN_FILE:", "").strip()
            return f"[wrote plan: {fname}]"
        if stripped.startswith("DELEGATE_TASK:"):
            return f"[delegated task: {stripped[14:60].strip()}]"
        if any(stripped.startswith(p) for p in self.ACTION_TAG_PREFIXES):
            return f"[action completed]"
        return content

    def add_turn(self, sender: str, content: str, role: str = None):
        """Add a conversation turn to short-term memory."""
        # Summarize action tag responses so they don't get echoed by the model
        stored_content = self._summarize_if_action(content) if sender != "user" else content

        turn = {
            "sender": sender,
            "content": stored_content,
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

    # Patterns that indicate a poisoned/echoed response — never inject or store these
    POISON_PATTERNS = (
        "[DIRECT NEURAL BRIDGE]",
        "[HMI BRIDGE ACTIVE]",
        "[EXECUTION MODE ACTIVE]",
        "[MESH OBSERVABILITY]",
        "[STRICT CONSTRAINT]",
        "I am currently processing this request internally.",
        "My linguistic output is currently stalled",
        "## CRITICAL: Action Execution Rules",
        "WRITE_FILE: architecture_overview.md",
        "SEARCH_QUERY: architecture_overview.md",
        "[Archi:Architect] Task:",
        "[PLAN]\nI will outline the steps",
    )

    def _is_poisoned(self, text: str) -> bool:
        return any(p in (text or "") for p in self.POISON_PATTERNS)

    def add_task_result(self, task: str, result: str, status: str = "completed"):
        """Store a completed task result in long-term memory."""
        # Never store poisoned/echoed responses
        if self._is_poisoned(result) or self._is_poisoned(task):
            return
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

        # Recent task results — filter out any poisoned entries
        tasks = [
            e for e in self.long_term
            if e.get("type") == "task_result"
            and not self._is_poisoned(e.get("result", ""))
            and not self._is_poisoned(e.get("task", ""))
        ]
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

    def compress_history(self, keep_recent: int = 10) -> Dict[str, Any]:
        """
        Recursively compress older messages for near-infinite context.
        Messages beyond `keep_recent` are compressed into concise summaries.
        """
        if len(self.short_term) <= keep_recent:
            return {"original": len(self.short_term), "compressed": 0, "ratio": 1.0}

        recent = self.short_term[-keep_recent:]
        older = self.short_term[:-keep_recent]

        compressed = []
        for turn in older:
            content = turn.get("content", "")
            first_sentence = content.split(".")[0][:80].strip()
            if not first_sentence:
                first_sentence = content[:60].strip()
            compressed.append({
                "sender": turn["sender"],
                "content": f"[compressed] {first_sentence}",
                "role": turn.get("role", ""),
                "timestamp": turn.get("timestamp", ""),
                "compressed": True,
            })

        original_chars = sum(len(t.get("content", "")) for t in older)
        compressed_chars = sum(len(t.get("content", "")) for t in compressed)
        self.short_term = compressed + recent

        return {
            "original": len(older) + len(recent),
            "compressed": len(compressed),
            "kept_verbatim": len(recent),
            "original_chars": original_chars,
            "compressed_chars": compressed_chars,
            "ratio": round(compressed_chars / max(1, original_chars), 3),
        }

    def get_compressed_context(self, max_turns: int = 20) -> str:
        """Build context with automatic compression applied."""
        if len(self.short_term) > max_turns:
            self.compress_history(keep_recent=max_turns // 2)
        return self.get_context_window(max_turns=max_turns)

    def export_all(self) -> Dict:
        return {
            "agent": self.agent_name,
            "short_term": self.short_term,
            "long_term": self.long_term,
        }
