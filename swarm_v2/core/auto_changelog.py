"""
Swarm V2 Auto-Changelog Engine
Phase 5: Scribe (Technical Writer)

Monitors the `swarm_v2_integrated` directory and automatically updates
`CHANGELOG.md` whenever a new module is finalized.

Features:
- File system monitoring for new/modified modules
- Automatic changelog entry generation
- Module classification and categorization
- Integration with artifact pipeline for status tracking
"""

import os
import re
import json
import hashlib
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoChangelog")


class ChangeType(Enum):
    """Types of changes for changelog entries."""
    ADDED = "Added"
    CHANGED = "Changed"
    FIXED = "Fixed"
    DEPRECATED = "Deprecated"
    REMOVED = "Removed"
    SECURITY = "Security"


class ModuleCategory(Enum):
    """Categories for modules."""
    CORE = "Core"
    API = "API"
    SKILL = "Skill"
    MCP = "MCP Tool"
    INFRASTRUCTURE = "Infrastructure"
    INTEGRATION = "Integration"
    UNKNOWN = "Unknown"


@dataclass
class ChangelogEntry:
    """Represents a single changelog entry."""
    version: str
    date: str
    changes: List[Dict[str, str]]  # [{type, category, module, description}]
    
    def to_markdown(self) -> str:
        """Convert entry to markdown format."""
        lines = [f"## [{self.version}] - {self.date}\n"]
        
        # Group changes by type
        by_type: Dict[str, List[Dict]] = {}
        for change in self.changes:
            change_type = change.get("type", "Changed")
            if change_type not in by_type:
                by_type[change_type] = []
            by_type[change_type].append(change)
        
        # Format each type section
        for change_type in ["Added", "Changed", "Fixed", "Security", "Deprecated", "Removed"]:
            if change_type in by_type:
                lines.append(f"\n### {change_type}\n")
                for change in by_type[change_type]:
                    category = change.get("category", "")
                    module = change.get("module", "")
                    desc = change.get("description", "")
                    if module:
                        lines.append(f"- **{module}** ({category}): {desc}")
                    else:
                        lines.append(f"- ({category}): {desc}")
        
        return "\n".join(lines)


@dataclass
class ModuleInfo:
    """Information about a monitored module."""
    path: str
    name: str
    category: ModuleCategory
    hash: str
    last_modified: float
    status: str = "active"  # active, finalized, deprecated
    description: str = ""
    exports: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "category": self.category.value,
            "hash": self.hash,
            "last_modified": self.last_modified,
            "status": self.status,
            "description": self.description,
            "exports": self.exports
        }


class AutoChangelogEngine:
    """
    Automatic changelog generation engine.
    
    Monitors directories for new/modified modules and updates
    CHANGELOG.md automatically.
    """
    
    def __init__(
        self,
        watch_dir: str = "swarm_v2_integrated",
        changelog_path: str = "CHANGELOG.md",
        registry_path: str = "swarm_v2_artifacts/changelog_registry.json"
    ):
        self.watch_dir = watch_dir
        self.changelog_path = changelog_path
        self.registry_path = registry_path
        
        self.module_registry: Dict[str, ModuleInfo] = {}
        self.pending_changes: List[Dict] = []
        self.version = "0.5.0"  # Phase 5 version
        self._running = False
        self._stats = {
            "modules_tracked": 0,
            "changes_detected": 0,
            "changelogs_generated": 0,
            "last_scan": None
        }
        
        # File patterns to monitor
        self.patterns = {
            ".py": self._analyze_python_module,
            ".md": self._analyze_markdown_module,
            ".json": self._analyze_json_module,
            ".yaml": self._analyze_yaml_module,
            ".yml": self._analyze_yaml_module,
        }
        
        # Create directories if needed
        os.makedirs(os.path.dirname(self.registry_path) if os.path.dirname(self.registry_path) else ".", exist_ok=True)
        
        # Load existing registry
        self._load_registry()
    
    def _load_registry(self):
        """Load existing module registry."""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for path, info in data.get("modules", {}).items():
                    self.module_registry[path] = ModuleInfo(
                        path=path,
                        name=info["name"],
                        category=ModuleCategory(info.get("category", "Unknown")),
                        hash=info["hash"],
                        last_modified=info["last_modified"],
                        status=info.get("status", "active"),
                        description=info.get("description", ""),
                        exports=info.get("exports", [])
                    )
                self.version = data.get("version", self.version)
                logger.info(f"Loaded registry with {len(self.module_registry)} modules")
            except Exception as e:
                logger.warning(f"Could not load registry: {e}")
    
    def _save_registry(self):
        """Save module registry to disk."""
        data = {
            "version": self.version,
            "updated_at": datetime.now().isoformat(),
            "modules": {path: info.to_dict() for path, info in self.module_registry.items()}
        }
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def _calculate_hash(self, filepath: str) -> str:
        """Calculate MD5 hash of file content."""
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def _classify_module(self, filepath: str, content: str = None) -> ModuleCategory:
        """Classify module based on path and content."""
        filepath_lower = filepath.lower()
        
        # Path-based classification
        if "mcp" in filepath_lower or "tool" in filepath_lower:
            return ModuleCategory.MCP
        if "skill" in filepath_lower:
            return ModuleCategory.SKILL
        if "api" in filepath_lower or "app" in filepath_lower:
            return ModuleCategory.API
        if "infra" in filepath_lower or "daemon" in filepath_lower:
            return ModuleCategory.INFRASTRUCTURE
        if "integrated" in filepath_lower:
            return ModuleCategory.INTEGRATION
        if "core" in filepath_lower:
            return ModuleCategory.CORE
        
        # Content-based classification
        if content:
            if "FastAPI" in content or "@app" in content:
                return ModuleCategory.API
            if "class.*Skill" in content:
                return ModuleCategory.SKILL
            if "MCP" in content or "mcp_server" in content:
                return ModuleCategory.MCP
        
        return ModuleCategory.UNKNOWN
    
    def _extract_description(self, content: str) -> str:
        """Extract module description from docstring or comments."""
        # Look for module docstring
        match = re.search(r'"""([\s\S]*?)"""', content)
        if match:
            desc = match.group(1).strip()
            # Get first line only
            return desc.split("\n")[0][:100]
        
        # Look for single-line docstring
        match = re.search(r"'''([\s\S]*?)'''", content)
        if match:
            return match.group(1).strip().split("\n")[0][:100]
        
        return ""
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extract exported functions/classes from module."""
        exports = []
        
        # Find class definitions
        classes = re.findall(r'class\s+(\w+)', content)
        exports.extend(classes)
        
        # Find function definitions (top-level)
        functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
        exports.extend(functions)
        
        # Find async functions
        async_funcs = re.findall(r'async\s+def\s+(\w+)', content)
        exports.extend(async_funcs)
        
        return list(set(exports))[:10]  # Limit to 10 exports
    
    def _analyze_python_module(self, filepath: str) -> Dict:
        """Analyze a Python module file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            return {
                "description": self._extract_description(content),
                "exports": self._extract_exports(content),
                "category": self._classify_module(filepath, content),
                "line_count": len(content.split("\n"))
            }
        except Exception as e:
            return {"description": "", "exports": [], "category": ModuleCategory.UNKNOWN}
    
    def _analyze_markdown_module(self, filepath: str) -> Dict:
        """Analyze a Markdown documentation file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract title
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else os.path.basename(filepath)
            
            return {
                "description": title,
                "exports": [],
                "category": ModuleCategory.INFRASTRUCTURE
            }
        except:
            return {"description": "", "exports": [], "category": ModuleCategory.UNKNOWN}
    
    def _analyze_json_module(self, filepath: str) -> Dict:
        """Analyze a JSON configuration file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            desc = data.get("description", data.get("name", ""))
            return {
                "description": desc,
                "exports": list(data.keys())[:10],
                "category": ModuleCategory.INFRASTRUCTURE
            }
        except:
            return {"description": "", "exports": [], "category": ModuleCategory.UNKNOWN}
    
    def _analyze_yaml_module(self, filepath: str) -> Dict:
        """Analyze a YAML configuration file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            return {
                "description": os.path.basename(filepath),
                "exports": [],
                "category": ModuleCategory.INFRASTRUCTURE
            }
        except:
            return {"description": "", "exports": [], "category": ModuleCategory.UNKNOWN}
    
    def scan_directory(self) -> List[Dict]:
        """Scan watch directory for new/modified modules."""
        changes = []
        
        if not os.path.exists(self.watch_dir):
            logger.warning(f"Watch directory does not exist: {self.watch_dir}")
            return changes
        
        current_files = set()
        
        for root, dirs, files in os.walk(self.watch_dir):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in self.patterns:
                    continue
                
                filepath = os.path.join(root, filename)
                current_files.add(filepath)
                
                # Get file stats
                try:
                    stat = os.stat(filepath)
                    mtime = stat.st_mtime
                    current_hash = self._calculate_hash(filepath)
                except:
                    continue
                
                # Check if new or modified
                existing = self.module_registry.get(filepath)
                is_new = filepath not in self.module_registry
                is_modified = existing and existing.hash != current_hash
                
                if is_new or is_modified:
                    # Analyze the module
                    analyzer = self.patterns.get(ext)
                    analysis = analyzer(filepath) if analyzer else {}
                    
                    module_name = os.path.splitext(filename)[0]
                    
                    # Create change entry
                    change = {
                        "type": ChangeType.ADDED.value if is_new else ChangeType.CHANGED.value,
                        "filepath": filepath,
                        "module": module_name,
                        "category": analysis.get("category", ModuleCategory.UNKNOWN).value,
                        "description": analysis.get("description", f"Module {module_name}"),
                        "exports": analysis.get("exports", []),
                        "hash": current_hash,
                        "timestamp": datetime.now().isoformat()
                    }
                    changes.append(change)
                    
                    # Update registry
                    self.module_registry[filepath] = ModuleInfo(
                        path=filepath,
                        name=module_name,
                        category=analysis.get("category", ModuleCategory.UNKNOWN),
                        hash=current_hash,
                        last_modified=mtime,
                        description=analysis.get("description", ""),
                        exports=analysis.get("exports", [])
                    )
        
        # Check for removed modules
        removed = set(self.module_registry.keys()) - current_files
        for filepath in removed:
            if not filepath.startswith("."):
                change = {
                    "type": ChangeType.REMOVED.value,
                    "filepath": filepath,
                    "module": self.module_registry[filepath].name,
                    "category": self.module_registry[filepath].category.value,
                    "description": f"Removed {self.module_registry[filepath].name}",
                    "timestamp": datetime.now().isoformat()
                }
                changes.append(change)
                del self.module_registry[filepath]
        
        self._stats["modules_tracked"] = len(self.module_registry)
        self._stats["last_scan"] = datetime.now().isoformat()
        
        return changes
    
    def generate_changelog_entry(self, changes: List[Dict]) -> ChangelogEntry:
        """Generate a changelog entry from detected changes."""
        formatted_changes = []
        
        for change in changes:
            formatted_changes.append({
                "type": change["type"],
                "category": change["category"],
                "module": change["module"],
                "description": change["description"]
            })
        
        entry = ChangelogEntry(
            version=self.version,
            date=datetime.now().strftime("%Y-%m-%d"),
            changes=formatted_changes
        )
        
        return entry
    
    def update_changelog(self, entry: ChangelogEntry):
        """Update CHANGELOG.md with new entry."""
        existing_content = ""
        
        # Read existing changelog
        if os.path.exists(self.changelog_path):
            try:
                with open(self.changelog_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()
            except:
                pass
        
        # Generate new entry markdown
        new_entry_md = entry.to_markdown()
        
        # Insert after header
        if existing_content:
            # Find where to insert (after first ## or after header)
            lines = existing_content.split("\n")
            insert_idx = 0
            
            # Skip header and find first version entry
            for i, line in enumerate(lines):
                if line.startswith("## ["):
                    insert_idx = i
                    break
                elif line.startswith("# "):
                    insert_idx = i + 2
            
            # Insert new entry
            lines.insert(insert_idx, "\n" + new_entry_md + "\n")
            final_content = "\n".join(lines)
        else:
            # Create new changelog
            header = "# Changelog\n\nAll notable changes to Swarm OS will be documented in this file.\n"
            final_content = header + new_entry_md + "\n"
        
        # Write updated changelog
        with open(self.changelog_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        self._stats["changelogs_generated"] += 1
        logger.info(f"Updated changelog with {len(entry.changes)} changes")
    
    async def monitor_loop(self, interval: int = 60):
        """Background loop to monitor directory and update changelog."""
        self._running = True
        logger.info(f"Auto-changelog monitoring started: {self.watch_dir}")
        
        while self._running:
            try:
                # Scan for changes
                changes = self.scan_directory()
                
                if changes:
                    self._stats["changes_detected"] += len(changes)
                    logger.info(f"Detected {len(changes)} module changes")
                    
                    # Generate and update changelog
                    entry = self.generate_changelog_entry(changes)
                    self.update_changelog(entry)
                    
                    # Save registry
                    self._save_registry()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(interval)
    
    def stop(self):
        """Stop the monitoring loop."""
        self._running = False
        self._save_registry()
        logger.info("Auto-changelog monitoring stopped")
    
    def force_update(self) -> Dict:
        """Force an immediate scan and changelog update."""
        changes = self.scan_directory()
        
        if changes:
            entry = self.generate_changelog_entry(changes)
            self.update_changelog(entry)
            self._save_registry()
            return {
                "status": "updated",
                "changes": changes,
                "entry": entry.to_markdown()
            }
        
        return {"status": "no_changes", "changes": []}
    
    def get_status(self) -> Dict:
        """Get current engine status."""
        return {
            "running": self._running,
            "watch_dir": self.watch_dir,
            "changelog_path": self.changelog_path,
            "version": self.version,
            "stats": self._stats,
            "modules": list(self.module_registry.keys())
        }
    
    def get_recent_changes(self, limit: int = 10) -> List[Dict]:
        """Get recent changes from changelog."""
        if not os.path.exists(self.changelog_path):
            return []
        
        try:
            with open(self.changelog_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse recent entries
            entries = []
            sections = re.split(r'## \[', content)[1:limit+1]  # Skip header
            
            for section in sections:
                lines = section.strip().split("\n")
                if lines:
                    header = lines[0]  # version - date
                    entries.append({
                        "header": header,
                        "preview": "\n".join(lines[1:6])[:200]
                    })
            
            return entries
        except:
            return []


# Singleton
_changelog_engine: Optional[AutoChangelogEngine] = None

def get_changelog_engine() -> AutoChangelogEngine:
    """Get or create the changelog engine singleton."""
    global _changelog_engine
    if _changelog_engine is None:
        _changelog_engine = AutoChangelogEngine()
    return _changelog_engine

async def start_changelog_monitoring(interval: int = 60):
    """Start the changelog monitoring loop."""
    engine = get_changelog_engine()
    await engine.monitor_loop(interval)


if __name__ == "__main__":
    # Demo: Scan and generate changelog
    engine = AutoChangelogEngine()
    changes = engine.scan_directory()
    
    if changes:
        print(f"Detected {len(changes)} changes:")
        for c in changes:
            print(f"  [{c['type']}] {c['module']}: {c['description'][:50]}")
        
        entry = engine.generate_changelog_entry(changes)
        print("\nGenerated changelog entry:")
        print(entry.to_markdown())
    else:
        print("No changes detected")