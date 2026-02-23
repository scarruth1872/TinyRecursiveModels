
"""
Dynamic Skill Acquisition Engine (The "Learning Engine")
Phase 3 of Swarm OS Evolution.

Allows agents to dynamically learn new skills by:
1. Ingesting documentation (Markdown, text, or URL content)
2. Synthesizing a callable skill definition via LLM
3. Hot-registering the new skill onto a live agent
"""

import os
import json
import re
import time
from typing import Optional, Dict, List
from datetime import datetime


LEARNED_SKILLS_DIR = "swarm_v2_learned_skills"
os.makedirs(LEARNED_SKILLS_DIR, exist_ok=True)


class LearnedSkill:
    """A dynamically created skill from documentation analysis."""

    def __init__(self, name: str, description: str, source: str,
                 instructions: str, examples: List[str] = None,
                 endpoints: Dict[str, str] = None, base_url: str = None, 
                 created_at: str = None):
        self.skill_name = name
        self.description = description
        self.source = source  # Where the knowledge came from
        self.instructions = instructions  # LLM-synthesized usage instructions
        self.examples = examples or []
        self.endpoints = endpoints or {}  # API endpoints discovered
        self.base_url = base_url # Root URL for live API calls
        self.created_at = created_at or datetime.now().isoformat()
        self.usage_count = 0

    def execute(self, task: str) -> str:
        """Provide guidance based on learned knowledge."""
        self.usage_count += 1
        endpoint_info = ""
        if self.endpoints:
            endpoint_info = "\n\nAvailable endpoints:\n" + "\n".join(
                f"  {method} {url}" for url, method in self.endpoints.items()
            )
        example_info = ""
        if self.examples:
            example_info = "\n\nExamples:\n" + "\n".join(
                f"  - {ex}" for ex in self.examples[:3]
            )
        return (
            f"[{self.skill_name}] Applying learned knowledge from: {self.source}\n\n"
            f"Instructions:\n{self.instructions}\n"
            f"{endpoint_info}{example_info}\n\n"
            f"Applying to task: {task}"
        )

    def to_dict(self) -> dict:
        return {
            "skill_name": self.skill_name,
            "description": self.description,
            "source": self.source,
            "instructions": self.instructions,
            "examples": self.examples,
            "endpoints": self.endpoints,
            "base_url": self.base_url,
            "created_at": self.created_at,
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LearnedSkill":
        skill = cls(
            name=data["skill_name"],
            description=data["description"],
            source=data["source"],
            instructions=data["instructions"],
            examples=data.get("examples", []),
            endpoints=data.get("endpoints", {}),
            created_at=data.get("created_at"),
        )
        skill.usage_count = data.get("usage_count", 0)
        return skill


class LearningEngine:
    """
    The core engine for dynamic skill acquisition.
    Reads documentation → extracts knowledge → creates skills → registers them.
    """

    def __init__(self):
        self.learned_skills: Dict[str, LearnedSkill] = {}
        self.learning_log: List[dict] = []
        self._load_persisted_skills()

    def _load_persisted_skills(self):
        """Load previously learned skills from disk."""
        manifest_path = os.path.join(LEARNED_SKILLS_DIR, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data.get("skills", []):
                    skill = LearnedSkill.from_dict(entry)
                    self.learned_skills[skill.skill_name] = skill
            except Exception:
                pass

    def _persist_skills(self):
        """Save all learned skills to disk."""
        manifest_path = os.path.join(LEARNED_SKILLS_DIR, "manifest.json")
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "skills": [s.to_dict() for s in self.learned_skills.values()],
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def extract_knowledge(self, content: str) -> dict:
        """
        Extract structured knowledge from raw documentation text.
        Returns endpoints, examples, and key instructions.
        """
        endpoints = {}
        examples = []
        instructions = []
        base_url = None

        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()

            # Detect API endpoints (REST patterns)
            endpoint_match = re.search(
                r'(GET|POST|PUT|DELETE|PATCH)\s+(\/\S+)', stripped, re.IGNORECASE
            )
            if endpoint_match:
                method = endpoint_match.group(1).upper()
                path = endpoint_match.group(2)
                endpoints[path] = method

            # Detect Base URL (Real-world production endpoint)
            base_url_match = re.search(
                r'(?:base\s+url|endpoint|api\s+root):\s*(https?://\S+)', stripped, re.IGNORECASE
            )
            if base_url_match:
                base_url = base_url_match.group(1).rstrip('/')

            # Detect code examples
            if stripped.startswith("```") or stripped.startswith(">>>"):
                examples.append(stripped)

            # Detect curl examples
            if "curl " in stripped.lower():
                examples.append(stripped)

            # Key instruction patterns
            if any(kw in stripped.lower() for kw in
                   ["must", "required", "important", "note:", "warning:",
                    "usage:", "syntax:", "format:", "returns"]):
                instructions.append(stripped)

        return {
            "endpoints": endpoints,
            "examples": examples[:10],
            "instructions": "\n".join(instructions[:20]) if instructions else content[:500],
            "base_url": base_url,
        }

    async def learn_from_text(self, name: str, content: str, source: str,
                              llm_generate=None) -> LearnedSkill:
        """
        Ingest documentation text and create a new LearnedSkill.
        Optionally uses an LLM to synthesize a summary.
        """
        knowledge = self.extract_knowledge(content)

        # If LLM is available, synthesize a better description
        description = f"Learned skill from: {source}"
        instructions = knowledge["instructions"]

        if llm_generate:
            try:
                synthesis_prompt = (
                    f"You are analyzing documentation to create a reusable skill.\n"
                    f"Source: {source}\n"
                    f"Content (first 1000 chars):\n{content[:1000]}\n\n"
                    f"Provide:\n"
                    f"1. A one-line description of what this skill does\n"
                    f"2. Step-by-step instructions for using this skill\n"
                    f"Keep it under 200 words."
                )
                llm_result = await llm_generate(synthesis_prompt)
                # Split LLM result into description + instructions
                parts = llm_result.split("\n", 1)
                description = parts[0].strip()
                if len(parts) > 1:
                    instructions = parts[1].strip()
            except Exception:
                pass

        skill = LearnedSkill(
            name=name,
            description=description,
            source=source,
            instructions=instructions,
            examples=knowledge["examples"],
            endpoints=knowledge["endpoints"],
        )

        self.learned_skills[name] = skill
        self.learning_log.append({
            "action": "learned",
            "skill": name,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "endpoints_found": len(knowledge["endpoints"]),
            "examples_found": len(knowledge["examples"]),
        })
        self._persist_skills()
        return skill

    async def learn_from_file(self, filepath: str, llm_generate=None) -> LearnedSkill:
        """Learn a new skill from a local documentation file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Documentation not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Generate a skill name from the filename
        basename = os.path.basename(filepath)
        name = re.sub(r'[^a-zA-Z0-9]', '_', basename.rsplit('.', 1)[0])
        name = f"Learned_{name}"

        return await self.learn_from_text(
            name=name, content=content, source=f"file://{filepath}",
            llm_generate=llm_generate
        )

    def get_skill(self, name: str) -> Optional[LearnedSkill]:
        return self.learned_skills.get(name)

    def list_skills(self) -> List[dict]:
        return [s.to_dict() for s in self.learned_skills.values()]

    def forget_skill(self, name: str) -> bool:
        if name in self.learned_skills:
            del self.learned_skills[name]
            self.learning_log.append({
                "action": "forgotten",
                "skill": name,
                "timestamp": datetime.now().isoformat(),
            })
            self._persist_skills()
            return True
        return False

    def get_learning_log(self) -> List[dict]:
        return self.learning_log

    def get_stats(self) -> dict:
        return {
            "total_learned": len(self.learned_skills),
            "total_usages": sum(s.usage_count for s in self.learned_skills.values()),
            "log_entries": len(self.learning_log),
            "skills": list(self.learned_skills.keys()),
        }


# Singleton instance
_engine: Optional[LearningEngine] = None


def get_learning_engine() -> LearningEngine:
    global _engine
    if _engine is None:
        _engine = LearningEngine()
    return _engine
