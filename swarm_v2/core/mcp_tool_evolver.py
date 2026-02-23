"""
Swarm V2 MCP Tool Evolver
Phase 5: Bridge (Integration Specialist)

Evolves synthesized MCP tools based on new documentation ingested by Seeker.
Creates a continuous improvement loop where tools get upgraded with new knowledge.

Features:
- Periodic review of synthesized tools
- Integration with Reconnaissance Daemon for new research
- LLM-powered code evolution
- Version tracking and rollback support
"""

import os
import json
import re
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPToolEvolver")


class EvolutionTrigger(Enum):
    """Triggers for tool evolution."""
    SCHEDULED = "scheduled"           # Periodic review
    NEW_RESEARCH = "new_research"     # New documentation ingested
    PERFORMANCE = "performance"       # Performance threshold met
    MANUAL = "manual"                 # Manual trigger
    SECURITY = "security"            # Security update needed


class EvolutionStatus(Enum):
    """Status of tool evolution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ToolVersion:
    """Represents a version of a synthesized tool."""
    version: str
    code: str
    timestamp: datetime
    trigger: EvolutionTrigger
    changes: List[str] = field(default_factory=list)
    performance_score: float = 0.0
    checksum: str = ""
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "trigger": self.trigger.value,
            "changes": self.changes,
            "performance_score": self.performance_score,
            "checksum": self.checksum
        }


@dataclass
class EvolutionResult:
    """Result of a tool evolution attempt."""
    tool_name: str
    old_version: str
    new_version: str
    status: EvolutionStatus
    changes_made: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "status": self.status.value,
            "changes_made": self.changes_made,
            "improvements": self.improvements,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }


class MCPToolEvolver:
    """
    Evolves synthesized MCP tools based on new knowledge.
    
    Integration Points:
    - Reads tools from swarm_v2_synthesized/
    - Gets new research from Reconnaissance Daemon
    - Uses LLM to generate improved code
    - Maintains version history for rollback
    """
    
    def __init__(
        self,
        synthesized_dir: str = "swarm_v2_synthesized",
        versions_dir: str = "swarm_v2_tool_versions",
        llm_generate: Callable = None
    ):
        self.synthesized_dir = synthesized_dir
        self.versions_dir = versions_dir
        self.llm_generate = llm_generate
        
        self.tool_versions: Dict[str, List[ToolVersion]] = {}
        self.evolution_history: List[EvolutionResult] = []
        self._running = False
        self._stats = {
            "total_evolutions": 0,
            "successful_evolutions": 0,
            "failed_evolutions": 0,
            "rollbacks": 0,
            "last_evolution": None
        }
        
        # Create versions directory
        os.makedirs(self.versions_dir, exist_ok=True)
        
        # Load existing versions
        self._load_versions()
    
    def _load_versions(self):
        """Load existing tool versions from disk."""
        version_file = os.path.join(self.versions_dir, "versions.json")
        if os.path.exists(version_file):
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for tool_name, versions in data.get("tools", {}).items():
                    self.tool_versions[tool_name] = [
                        ToolVersion(
                            version=v["version"],
                            code="",  # Code loaded separately
                            timestamp=datetime.fromisoformat(v["timestamp"]),
                            trigger=EvolutionTrigger(v["trigger"]),
                            changes=v.get("changes", []),
                            performance_score=v.get("performance_score", 0),
                            checksum=v.get("checksum", "")
                        )
                        for v in versions
                    ]
                logger.info(f"Loaded versions for {len(self.tool_versions)} tools")
            except Exception as e:
                logger.warning(f"Could not load versions: {e}")
    
    def _save_versions(self):
        """Save tool versions to disk."""
        version_file = os.path.join(self.versions_dir, "versions.json")
        data = {
            "updated_at": datetime.now().isoformat(),
            "tools": {
                tool_name: [v.to_dict() for v in versions]
                for tool_name, versions in self.tool_versions.items()
            }
        }
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def _calculate_checksum(self, code: str) -> str:
        """Calculate checksum for code."""
        import hashlib
        return hashlib.md5(code.encode()).hexdigest()[:8]
    
    def _get_current_tools(self) -> Dict[str, str]:
        """Get all current synthesized tools and their code."""
        tools = {}
        
        if not os.path.exists(self.synthesized_dir):
            return tools
        
        for filename in os.listdir(self.synthesized_dir):
            if filename.endswith(".py"):
                filepath = os.path.join(self.synthesized_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        code = f.read()
                    tool_name = filename[:-3]  # Remove .py
                    tools[tool_name] = code
                except Exception as e:
                    logger.warning(f"Could not read tool {filename}: {e}")
        
        return tools
    
    def _get_current_version(self, tool_name: str) -> str:
        """Get current version number for a tool."""
        if tool_name in self.tool_versions and self.tool_versions[tool_name]:
            return self.tool_versions[tool_name][-1].version
        return "0.1.0"
    
    def _increment_version(self, current: str) -> str:
        """Increment version number."""
        parts = current.split(".")
        if len(parts) == 3:
            patch = int(parts[2]) + 1
            return f"{parts[0]}.{parts[1]}.{patch}"
        return "0.1.1"
    
    async def analyze_tool_for_evolution(
        self,
        tool_name: str,
        current_code: str,
        new_knowledge: List[str]
    ) -> Dict:
        """Analyze a tool and determine evolution opportunities."""
        
        if not self.llm_generate:
            return {"should_evolve": False, "reason": "No LLM available"}
        
        # Build analysis prompt
        prompt = f"""Analyze this MCP tool and determine if it should be evolved based on new knowledge.

TOOL: {tool_name}

CURRENT CODE:
```python
{current_code[:3000]}
```

NEW KNOWLEDGE:
{chr(10).join(f'- {k}' for k in new_knowledge[:5])}

Analyze and respond in JSON format:
{{
    "should_evolve": true/false,
    "reason": "explanation",
    "suggested_improvements": ["list of improvements"],
    "priority": "low/medium/high",
    "affected_functions": ["list of functions to modify"]
}}
"""
        
        try:
            response = await self.llm_generate(prompt)
            
            # Parse JSON response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Analysis failed for {tool_name}: {e}")
        
        return {"should_evolve": False, "reason": f"Analysis failed: {e}"}
    
    async def evolve_tool(
        self,
        tool_name: str,
        current_code: str,
        new_knowledge: List[str],
        trigger: EvolutionTrigger = EvolutionTrigger.MANUAL
    ) -> EvolutionResult:
        """Evolve a tool based on new knowledge."""
        
        current_version = self._get_current_version(tool_name)
        new_version = self._increment_version(current_version)
        
        logger.info(f"Evolving {tool_name} from v{current_version} to v{new_version}")
        
        if not self.llm_generate:
            return EvolutionResult(
                tool_name=tool_name,
                old_version=current_version,
                new_version=new_version,
                status=EvolutionStatus.FAILED,
                error="No LLM generate function available"
            )
        
        # Build evolution prompt
        prompt = f"""You are an expert code evolver. Upgrade this MCP tool based on new knowledge.

TOOL: {tool_name}
CURRENT VERSION: {current_version}
NEW VERSION: {new_version}

CURRENT CODE:
```python
{current_code}
```

NEW KNOWLEDGE TO INTEGRATE:
{chr(10).join(f'- {k}' for k in new_knowledge)}

Generate the UPGRADED code that:
1. Integrates the new knowledge
2. Maintains backward compatibility
3. Improves error handling
4. Adds any new capabilities suggested by the knowledge
5. Keeps the same function signatures where possible

Output ONLY the complete upgraded Python code, no explanations.
"""
        
        try:
            # Generate evolved code
            evolved_code = await self.llm_generate(prompt)
            
            # Extract code from response
            code_match = re.search(r'```python\s*([\s\S]*?)```', evolved_code)
            if code_match:
                evolved_code = code_match.group(1).strip()
            elif "```" in evolved_code:
                evolved_code = evolved_code.split("```")[1].strip()
            
            # Validate evolved code
            if len(evolved_code) < 100:
                raise ValueError("Evolved code too short")
            
            # Create version record
            version_record = ToolVersion(
                version=new_version,
                code=evolved_code,
                timestamp=datetime.now(),
                trigger=trigger,
                changes=["Integrated new knowledge", "Improved error handling"],
                checksum=self._calculate_checksum(evolved_code)
            )
            
            # Save version
            if tool_name not in self.tool_versions:
                self.tool_versions[tool_name] = []
            self.tool_versions[tool_name].append(version_record)
            
            # Write evolved tool
            tool_path = os.path.join(self.synthesized_dir, f"{tool_name}.py")
            with open(tool_path, "w", encoding="utf-8") as f:
                f.write(evolved_code)
            
            # Save version history
            self._save_versions()
            
            # Update stats
            self._stats["total_evolutions"] += 1
            self._stats["successful_evolutions"] += 1
            self._stats["last_evolution"] = datetime.now().isoformat()
            
            result = EvolutionResult(
                tool_name=tool_name,
                old_version=current_version,
                new_version=new_version,
                status=EvolutionStatus.COMPLETED,
                changes_made=["Integrated new knowledge"],
                improvements=["Improved error handling", "Added new capabilities"]
            )
            
            self.evolution_history.append(result)
            logger.info(f"Successfully evolved {tool_name} to v{new_version}")
            
            return result
            
        except Exception as e:
            self._stats["total_evolutions"] += 1
            self._stats["failed_evolutions"] += 1
            
            result = EvolutionResult(
                tool_name=tool_name,
                old_version=current_version,
                new_version=new_version,
                status=EvolutionStatus.FAILED,
                error=str(e)
            )
            
            self.evolution_history.append(result)
            logger.error(f"Failed to evolve {tool_name}: {e}")
            
            return result
    
    def rollback_tool(self, tool_name: str, target_version: str = None) -> Dict:
        """Rollback a tool to a previous version."""
        
        if tool_name not in self.tool_versions or not self.tool_versions[tool_name]:
            return {"status": "error", "message": "No version history for tool"}
        
        versions = self.tool_versions[tool_name]
        
        # Find target version
        if target_version:
            target = next((v for v in versions if v.version == target_version), None)
            if not target:
                return {"status": "error", "message": f"Version {target_version} not found"}
        else:
            # Rollback to previous version
            if len(versions) < 2:
                return {"status": "error", "message": "No previous version to rollback to"}
            target = versions[-2]
        
        try:
            # Restore code
            tool_path = os.path.join(self.synthesized_dir, f"{tool_name}.py")
            with open(tool_path, "w", encoding="utf-8") as f:
                f.write(target.code)
            
            # Add rollback record
            rollback_version = ToolVersion(
                version=f"{target.version}-rollback",
                code=target.code,
                timestamp=datetime.now(),
                trigger=EvolutionTrigger.MANUAL,
                changes=[f"Rolled back to v{target.version}"]
            )
            self.tool_versions[tool_name].append(rollback_version)
            self._save_versions()
            
            self._stats["rollbacks"] += 1
            
            return {
                "status": "success",
                "tool": tool_name,
                "rolled_back_to": target.version,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def evolution_cycle(
        self,
        new_knowledge: List[str] = None,
        trigger: EvolutionTrigger = EvolutionTrigger.SCHEDULED
    ) -> List[EvolutionResult]:
        """Run a full evolution cycle on all tools."""
        
        results = []
        tools = self._get_current_tools()
        
        # Get new knowledge from reconnaissance if not provided
        if new_knowledge is None:
            try:
                from swarm_v2.core.reconnaissance_daemon import get_reconnaissance_daemon
                daemon = get_reconnaissance_daemon()
                findings = daemon.get_recent_findings(limit=10)
                new_knowledge = [f.get("summary", "") for f in findings]
            except:
                new_knowledge = []
        
        if not new_knowledge:
            logger.info("No new knowledge available for evolution")
            return results
        
        logger.info(f"Running evolution cycle for {len(tools)} tools with {len(new_knowledge)} knowledge items")
        
        for tool_name, current_code in tools.items():
            # Analyze if evolution needed
            analysis = await self.analyze_tool_for_evolution(
                tool_name, current_code, new_knowledge
            )
            
            if analysis.get("should_evolve", False):
                # Perform evolution
                result = await self.evolve_tool(
                    tool_name, current_code, new_knowledge, trigger
                )
                results.append(result)
        
        return results
    
    async def monitor_loop(self, interval: int = 3600):
        """Background loop for periodic tool evolution."""
        self._running = True
        logger.info(f"MCP Tool Evolver started with {interval}s interval")
        
        while self._running:
            try:
                # Run evolution cycle
                results = await self.evolution_cycle(trigger=EvolutionTrigger.SCHEDULED)
                
                if results:
                    logger.info(f"Evolution cycle completed: {len(results)} tools evolved")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Evolution cycle error: {e}")
                await asyncio.sleep(interval)
    
    def stop(self):
        """Stop the evolution monitor loop."""
        self._running = False
        logger.info("MCP Tool Evolver stopped")
    
    def get_status(self) -> Dict:
        """Get evolver status."""
        tools = self._get_current_tools()
        
        return {
            "running": self._running,
            "synthesized_dir": self.synthesized_dir,
            "tools_count": len(tools),
            "tools_with_versions": len(self.tool_versions),
            "stats": self._stats,
            "recent_evolutions": [e.to_dict() for e in self.evolution_history[-5:]]
        }
    
    def get_tool_history(self, tool_name: str) -> List[Dict]:
        """Get version history for a tool."""
        if tool_name not in self.tool_versions:
            return []
        return [v.to_dict() for v in self.tool_versions[tool_name]]
    
    def get_available_knowledge(self) -> List[str]:
        """Get available knowledge for evolution."""
        knowledge = []
        
        try:
            from swarm_v2.core.reconnaissance_daemon import get_reconnaissance_daemon
            daemon = get_reconnaissance_daemon()
            findings = daemon.get_recent_findings(limit=20)
            knowledge = [f.get("summary", "") for f in findings]
        except:
            pass
        
        # Also check global memory
        try:
            from swarm_v2.core.global_memory import get_global_memory
            memory = get_global_memory()
            entries = memory.query("MCP tool improvement", top_k=10)
            knowledge.extend([e[1].get("content", "") for e in entries])
        except:
            pass
        
        return knowledge


# Singleton
_evolver: Optional[MCPToolEvolver] = None

def get_tool_evolver(llm_generate: Callable = None) -> MCPToolEvolver:
    """Get or create the tool evolver singleton."""
    global _evolver
    if _evolver is None:
        _evolver = MCPToolEvolver(llm_generate=llm_generate)
    return _evolver

async def start_tool_evolution(interval: int = 3600, llm_generate: Callable = None):
    """Start the tool evolution loop."""
    evolver = get_tool_evolver(llm_generate)
    await evolver.monitor_loop(interval)


if __name__ == "__main__":
    # Demo
    async def demo():
        evolver = MCPToolEvolver()
        tools = evolver._get_current_tools()
        print(f"Found {len(tools)} synthesized tools:")
        for name in tools.keys():
            version = evolver._get_current_version(name)
            print(f"  - {name} (v{version})")
        
        status = evolver.get_status()
        print(f"\nStats: {status['stats']}")
    
    asyncio.run(demo())