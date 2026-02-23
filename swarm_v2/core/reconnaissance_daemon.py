"""
Swarm V2 Reconnaissance Daemon
Phase 5: Seeker (Researcher) Upgrade

A background task that autonomously searches for and summarizes new AI research
papers using WebSearchSkill, storing findings in global memory.

Runs on a configurable interval (default: 24 hours).
"""

import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from threading import Thread
import time

try:
    from swarm_v2.skills.web_search_skill import WebSearchSkill
    from swarm_v2.core.global_memory import get_global_memory
except ImportError:
    WebSearchSkill = None
    def get_global_memory():
        return None

RECONNAISSANCE_DIR = "swarm_v2_reconnaissance"
os.makedirs(RECONNAISSANCE_DIR, exist_ok=True)

# Default research topics for AI papers
DEFAULT_RESEARCH_TOPICS = [
    "latest AI research papers 2024",
    "transformer architecture improvements",
    "large language model innovations",
    "autonomous AI agents research",
    "machine learning optimization techniques",
    "neural network efficiency papers",
    "AI safety and alignment research",
    "multimodal AI models papers",
    "reinforcement learning advances",
    "AI code generation research"
]


class ResearchFinding:
    """Represents a single research finding."""
    
    def __init__(self, topic: str, summary: str, sources: List[str], timestamp: str = None):
        self.topic = topic
        self.summary = summary
        self.sources = sources
        self.timestamp = timestamp or datetime.now().isoformat()
        self.finding_id = f"rf_{hash(summary) & 0xFFFFFFFF:08x}"
    
    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "topic": self.topic,
            "summary": self.summary,
            "sources": self.sources,
            "timestamp": self.timestamp
        }


class ReconnaissanceDaemon:
    """
    Background daemon that autonomously searches for AI research.
    
    Features:
    - Configurable search interval (default 24 hours)
    - Multiple research topics covered per cycle
    - Results stored in global memory for agent access
    - Findings persisted to disk for historical tracking
    """
    
    def __init__(self, interval_hours: float = 24, topics: List[str] = None):
        self.interval_seconds = interval_hours * 3600
        self.topics = topics or DEFAULT_RESEARCH_TOPICS
        self.search_skill = WebSearchSkill() if WebSearchSkill else None
        self.is_running = False
        self._thread: Optional[Thread] = None
        self.findings: List[ResearchFinding] = []
        self.last_run: Optional[str] = None
        self.run_count = 0
        
        # Load previous findings
        self._load_findings()
    
    def _load_findings(self):
        """Load previous findings from disk."""
        findings_path = os.path.join(RECONNAISSANCE_DIR, "findings.json")
        if os.path.exists(findings_path):
            try:
                with open(findings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.findings = [ResearchFinding(**fd) for fd in data.get("findings", [])]
                    self.last_run = data.get("last_run")
                    self.run_count = data.get("run_count", 0)
            except Exception as e:
                print(f"[Reconnaissance] Failed to load findings: {e}")
    
    def _save_findings(self):
        """Save findings to disk."""
        findings_path = os.path.join(RECONNAISSANCE_DIR, "findings.json")
        data = {
            "last_run": self.last_run,
            "run_count": self.run_count,
            "findings": [f.to_dict() for f in self.findings[-100:]],  # Keep last 100
            "topics": self.topics
        }
        with open(findings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def start(self):
        """Start the reconnaissance daemon."""
        if self.is_running:
            return
        
        self.is_running = True
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"[Reconnaissance] Daemon started. Interval: {self.interval_seconds/3600:.1f} hours")
    
    def stop(self):
        """Stop the daemon."""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[Reconnaissance] Daemon stopped.")
    
    def _run_loop(self):
        """Main loop that runs research cycles."""
        while self.is_running:
            try:
                # Run a research cycle
                self._run_research_cycle()
                
                # Wait for next cycle
                for _ in range(int(self.interval_seconds)):
                    if not self.is_running:
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"[Reconnaissance] Error in cycle: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _run_research_cycle(self, force: bool = False):
        """Execute a full research cycle across all topics."""
        print(f"[Reconnaissance] Starting research cycle #{self.run_count + 1}")
        self.last_run = datetime.now().isoformat()
        
        # Run async research in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._async_research_cycle(force=force))
        finally:
            loop.close()
        
        self.run_count += 1
        self._save_findings()
        print(f"[Reconnaissance] Cycle complete. Total findings: {len(self.findings)}")
    
    async def _async_research_cycle(self, force: bool = False):
        """Async research cycle."""
        for topic in self.topics:
            if not self.is_running and not force:
                break
            await self._research_topic(topic)
    
    async def _research_topic(self, topic: str):
        """Research a single topic."""
        if not self.search_skill:
            return
        
        try:
            # Search for research
            results = self.search_skill.search(f"{topic} arxiv paper 2024", max_results=3)
            
            # Create finding
            finding = ResearchFinding(
                topic=topic,
                summary=results[:1000],  # Truncate for storage
                sources=[topic],  # Could extract URLs from results
            )
            
            # Store in memory
            self.findings.append(finding)
            
            # Contribute to global memory
            global_mem = get_global_memory()
            if global_mem:
                global_mem.contribute(
                    content=f"Research Finding [{topic}]: {results[:500]}",
                    author="Seeker",
                    author_role="Researcher",
                    memory_type="research",
                    tags=["ai_research", "autonomous", topic.replace(" ", "_")[:20]]
                )
            
            print(f"[Reconnaissance] Researched: {topic}")
            
        except Exception as e:
            print(f"[Reconnaissance] Failed to research {topic}: {e}")
    
    def run_immediate(self):
        """Trigger an immediate research cycle."""
        print("[Reconnaissance] Running immediate research cycle...")
        self._run_research_cycle(force=True)
    
    def get_recent_findings(self, limit: int = 10) -> List[dict]:
        """Get the most recent findings."""
        return [f.to_dict() for f in self.findings[-limit:]]
    
    def get_findings_by_topic(self, topic: str) -> List[dict]:
        """Get findings for a specific topic."""
        return [f.to_dict() for f in self.findings if topic.lower() in f.topic.lower()]
    
    def get_stats(self) -> dict:
        """Get daemon statistics."""
        return {
            "is_running": self.is_running,
            "interval_hours": self.interval_seconds / 3600,
            "topics_count": len(self.topics),
            "total_findings": len(self.findings),
            "last_run": self.last_run,
            "run_count": self.run_count
        }
    
    def add_topic(self, topic: str):
        """Add a new research topic."""
        if topic not in self.topics:
            self.topics.append(topic)
            self._save_findings()
    
    def remove_topic(self, topic: str):
        """Remove a research topic."""
        if topic in self.topics:
            self.topics.remove(topic)
            self._save_findings()


# Singleton instance
_reconnaissance_daemon: Optional[ReconnaissanceDaemon] = None

def get_reconnaissance_daemon() -> ReconnaissanceDaemon:
    """Get or create the singleton reconnaissance daemon."""
    global _reconnaissance_daemon
    if _reconnaissance_daemon is None:
        _reconnaissance_daemon = ReconnaissanceDaemon()
    return _reconnaissance_daemon

def start_reconnaissance(interval_hours: float = 24):
    """Start the reconnaissance daemon."""
    daemon = get_reconnaissance_daemon()
    daemon.interval_seconds = interval_hours * 3600
    daemon.start()
    return daemon