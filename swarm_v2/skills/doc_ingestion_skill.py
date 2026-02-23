
"""
MCP Auto-Onboarding: Documentation Skill
Phase 3 — Agents can now autonomously ingest documentation
from local files, URLs, or raw text, and add the extracted
knowledge directly into their latent memory + the Learning Engine.

This is the "read and learn" reflex every agent now carries.
"""

import os
import re
from typing import Optional


class DocIngestionSkill:
    """
    Gives any agent the ability to ingest documentation on-the-fly
    and absorb it into the Learning Engine + their own memory.
    """
    skill_name = "DocIngestionSkill"
    description = (
        "Ingest documentation from files, URLs, or raw text. "
        "Extracts API endpoints, code examples, and key instructions, "
        "then registers a new learned skill in the Neural Skill Registry."
    )

    def __init__(self):
        # Lazy import to avoid circular dependencies at startup
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from swarm_v2.skills.learning_engine import get_learning_engine
            self._engine = get_learning_engine()
        return self._engine

    def _resolve_path(self, path: str) -> str:
        """Resolve path, checking swarm_v2_artifacts if relative."""
        if os.path.isabs(path) or os.path.exists(path):
            return path
        alt = os.path.join("swarm_v2_artifacts", path)
        if os.path.exists(alt):
            return alt
        return path

    def ingest_file(self, filepath: str) -> str:
        """Read a local documentation file and register it as a skill."""
        filepath = self._resolve_path(filepath)
        if not os.path.exists(filepath):
            return f"❌ File not found: {filepath}"

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        basename = os.path.basename(filepath)
        name = re.sub(r'[^a-zA-Z0-9]', '_', basename.rsplit('.', 1)[0])
        name = f"Doc_{name}"

        engine = self._get_engine()
        knowledge = engine.extract_knowledge(content)

        # Create the skill synchronously (no LLM needed for raw ingestion)
        from swarm_v2.skills.learning_engine import LearnedSkill
        skill = LearnedSkill(
            name=name,
            description=f"Knowledge extracted from {basename}",
            source=f"file://{filepath}",
            instructions=knowledge["instructions"],
            examples=knowledge["examples"],
            endpoints=knowledge["endpoints"],
            base_url=knowledge.get("base_url"),
        )
        engine.learned_skills[name] = skill
        engine.learning_log.append({
            "action": "auto_ingested",
            "skill": name,
            "source": filepath,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "endpoints_found": len(knowledge["endpoints"]),
            "examples_found": len(knowledge["examples"]),
        })
        engine._persist_skills()

        return (
            f"📚 Auto-ingested: {basename}\n"
            f"  Skill registered: {name}\n"
            f"  Endpoints found: {len(knowledge['endpoints'])}\n"
            f"  Examples found: {len(knowledge['examples'])}\n"
            f"  Instructions: {knowledge['instructions'][:200]}"
        )

    def ingest_text(self, name: str, content: str, source: str = "agent_input") -> str:
        """Ingest raw documentation text and register as a skill."""
        engine = self._get_engine()
        knowledge = engine.extract_knowledge(content)

        from swarm_v2.skills.learning_engine import LearnedSkill
        skill = LearnedSkill(
            name=name,
            description=f"Knowledge from: {source}",
            source=source,
            instructions=knowledge["instructions"],
            examples=knowledge["examples"],
            endpoints=knowledge["endpoints"],
        )
        engine.learned_skills[name] = skill
        engine.learning_log.append({
            "action": "auto_ingested",
            "skill": name,
            "source": source,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "endpoints_found": len(knowledge["endpoints"]),
            "examples_found": len(knowledge["examples"]),
        })
        engine._persist_skills()

        return (
            f"📚 Knowledge absorbed: {name}\n"
            f"  Source: {source}\n"
            f"  Endpoints: {len(knowledge['endpoints'])}\n"
            f"  Examples: {len(knowledge['examples'])}"
        )

    def scan_directory(self, dirpath: str, extensions: list = None) -> str:
        """Scan a directory for documentation files and ingest them all."""
        if extensions is None:
            extensions = [".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".py", ".js"]

        dirpath = self._resolve_path(dirpath)
        if not os.path.isdir(dirpath):
            return f"❌ Directory not found: {dirpath}"

        results = []
        for root, _, files in os.walk(dirpath):
            for fname in files:
                if any(fname.endswith(ext) for ext in extensions):
                    fpath = os.path.join(root, fname)
                    result = self.ingest_file(fpath)
                    results.append(result)
            if len(results) >= 20:  # Safety limit
                results.append("⚠️ Limit reached (20 files). Use specific paths for more.")
                break

        if not results:
            return f"📂 No documentation files found in {dirpath}"

        return f"📂 Scanned {dirpath} — {len(results)} docs ingested:\n\n" + "\n\n".join(results)

    def list_learned(self) -> str:
        """List all skills currently in the Learning Engine."""
        engine = self._get_engine()
        skills = engine.list_skills()
        if not skills:
            return "🧠 No learned skills yet. Ingest some documentation!"

        lines = [f"🧠 Neural Skill Registry ({len(skills)} skills):"]
        for s in skills:
            ep_count = len(s.get("endpoints", {}))
            lines.append(
                f"  ✦ {s['skill_name']} — {s['description'][:60]} "
                f"({ep_count} endpoints, {s.get('usage_count', 0)} uses)"
            )
        return "\n".join(lines)

    def recall(self, skill_name: str, task: str) -> Optional[str]:
        """Recall a learned skill's knowledge for a specific task."""
        engine = self._get_engine()
        skill = engine.get_skill(skill_name)
        if not skill:
            return None
        return skill.execute(task)
