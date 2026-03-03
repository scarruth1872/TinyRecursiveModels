
"""
Artifact Pipeline: pending → approved → tested → integrated
Tracks all generated files, manages review, testing, and integration.
"""
import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

ARTIFACTS_DIR = "swarm_v2_artifacts"
AGENT_SKILLS_DIR = ".agent/skills"  # AntiGravity agent skill definitions
INTEGRATION_DIR = "swarm_v2_integrated"
PIPELINE_DB = "swarm_v2_memory/artifact_pipeline.json"


class ArtifactStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TESTED = "tested"
    TEST_FAILED = "test_failed"
    INTEGRATED = "integrated"


class ArtifactPipeline:
    def __init__(self):
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        os.makedirs(INTEGRATION_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(PIPELINE_DB), exist_ok=True)
        self.artifacts: Dict[str, Dict] = self._load()

    def _load(self) -> Dict:
        if os.path.exists(PIPELINE_DB):
            try:
                with open(PIPELINE_DB, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        # Atomic-ish save
        temp_file = self.filename + ".tmp" if hasattr(self, "filename") else PIPELINE_DB + ".tmp"
        with open(PIPELINE_DB, "w", encoding="utf-8") as f:
            json.dump(self.artifacts, f, indent=2, default=str)

    def scan_artifacts(self) -> List[Dict]:
        """Scan the artifacts directory and agent skills recursively and register any new files."""
        now = datetime.now().isoformat()
        new_discoveries = []
        
        # We'll batch save at the end
        modified = False
        
        # Scan main artifacts directory
        for root, dirs, files in os.walk(ARTIFACTS_DIR):
            # Skip hidden, cache, and massive dependency dirs
            to_skip = ["__pycache__", ".git", "node_modules", "venv", ".next", "dist", "build"]
            for d in to_skip:
                if d in dirs:
                    dirs.remove(d)
            
            for filename in files:
                rel_path = os.path.relpath(os.path.join(root, filename), ARTIFACTS_DIR)
                filepath = os.path.join(root, filename)
                
                # Skip massive node_modules/venv if they exist in artifacts
                if any(ext in rel_path for ext in ["node_modules", "venv", ".git", "__pycache__"]):
                    continue

                if rel_path in self.artifacts:
                    # Update size if changed
                    try:
                        sz = os.path.getsize(filepath)
                        if self.artifacts[rel_path].get("size") != sz:
                            self.artifacts[rel_path]["size"] = sz
                            modified = True
                    except: pass
                    continue

                # NEW: Auto-Approval Policy
                modified = True
                auto_integrate = False
                ext = os.path.splitext(rel_path)[1].lower()
                maintenance_keywords = ["monitor", "backup", "maintenance", "setup", "install", "health", "log"]
                
                is_doc = ext in ('.md', '.txt')
                is_maintenance = any(kw in rel_path.lower() for kw in maintenance_keywords)
                
                status = ArtifactStatus.PENDING
                notes = None
                
                if is_doc or is_maintenance:
                    status = ArtifactStatus.APPROVED
                    notes = "Auto-approved by system policy (Doc/Maintenance)"
                    auto_integrate = True

                self.artifacts[rel_path] = {
                    "filename": rel_path,
                    "status": status,
                    "size": os.path.getsize(filepath),
                    "created_at": now,
                    "created_by": "System_Scan",
                    "reviewed_by": "System" if auto_integrate else None,
                    "reviewed_at": now if auto_integrate else None,
                    "review_notes": notes,
                    "test_file": None,
                    "test_result": None,
                    "integrated_at": None,
                    "integrated_path": None,
                    "security_status": "verified" if auto_integrate else "pending_scan",
                }
                
                if auto_integrate:
                    # Determine subdir for docs/maintenance
                    subdir = "docs" if is_doc else "maintenance"
                    self.integrate(rel_path, target_subdir=subdir, batch_save=True)
                    new_discoveries.append(rel_path)

        # Scan agent skills directory (.agent/skills/) - these are CRITICAL for agent personas
        if os.path.exists(AGENT_SKILLS_DIR):
            for filename in os.listdir(AGENT_SKILLS_DIR):
                if not filename.endswith('.md'):
                    continue
                rel_path = f".agent/skills/{filename}"
                filepath = os.path.join(AGENT_SKILLS_DIR, filename)
                
                if rel_path in self.artifacts:
                    # Update size if changed
                    try:
                        sz = os.path.getsize(filepath)
                        if self.artifacts[rel_path].get("size") != sz:
                            self.artifacts[rel_path]["size"] = sz
                            modified = True
                    except: pass
                    continue
                
                # NEW: Agent skills are CRITICAL - auto-approve immediately
                modified = True
                self.artifacts[rel_path] = {
                    "filename": rel_path,
                    "status": ArtifactStatus.APPROVED,
                    "size": os.path.getsize(filepath),
                    "created_at": now,
                    "created_by": "System_Scan",
                    "reviewed_by": "System",
                    "reviewed_at": now,
                    "review_notes": "Auto-approved: Critical agent skill definition",
                    "test_file": None,
                    "test_result": None,
                    "integrated_at": None,
                    "integrated_path": None,
                    "security_status": "verified",
                }
                new_discoveries.append(rel_path)

        if modified:
            self._save()
        return self.list_all()

    def register_artifact(self, filename: str, created_by: str):
        """Register an artifact from an agent build."""
        filepath = os.path.join(ARTIFACTS_DIR, filename)
        if not os.path.exists(filepath):
            return None
        self.artifacts[filename] = {
            "filename": filename,
            "status": ArtifactStatus.PENDING,
            "size": os.path.getsize(filepath),
            "created_at": datetime.now().isoformat(),
            "created_by": created_by,
            "reviewed_by": None,
            "reviewed_at": None,
            "review_notes": None,
            "test_file": None,
            "test_result": None,
            "integrated_at": None,
            "integrated_path": None,
            "security_status": "pending_scan",
        }
        self._save()
        
        # Phase 2: Semantic Indexing
        try:
            from swarm_v2.core.semantic_index import get_semantic_index
            content = self.get_content(filename)
            if content:
                # We do this synchronously for now, or could use a thread
                import threading
                def run_indexing():
                    import asyncio
                    idx = get_semantic_index()
                    asyncio.run(idx.index_artifact(filename, content, {"created_by": created_by}))
                
                threading.Thread(target=run_indexing).start()
        except Exception as e:
            print(f"[Pipeline] Semantic indexing deferred: {e}")

        return self.artifacts[filename]

    def approve(self, filename: str, reviewer: str = "user", notes: str = "") -> Optional[Dict]:
        """Approve an artifact for testing."""
        if filename not in self.artifacts:
            return None
        self.artifacts[filename]["status"] = ArtifactStatus.APPROVED
        self.artifacts[filename]["reviewed_by"] = reviewer
        self.artifacts[filename]["reviewed_at"] = datetime.now().isoformat()
        self.artifacts[filename]["review_notes"] = notes
        self._save()
        return self.artifacts[filename]

    def reject(self, filename: str, reviewer: str = "user", notes: str = "") -> Optional[Dict]:
        """Reject an artifact."""
        if filename not in self.artifacts:
            return None
        self.artifacts[filename]["status"] = ArtifactStatus.REJECTED
        self.artifacts[filename]["reviewed_by"] = reviewer
        self.artifacts[filename]["reviewed_at"] = datetime.now().isoformat()
        self.artifacts[filename]["review_notes"] = notes
        self._save()
        return self.artifacts[filename]

    def set_tested(self, filename: str, test_file: str, passed: bool, result: str = "") -> Optional[Dict]:
        """Mark artifact as tested."""
        if filename not in self.artifacts:
            return None
        self.artifacts[filename]["status"] = ArtifactStatus.TESTED if passed else ArtifactStatus.TEST_FAILED
        self.artifacts[filename]["test_file"] = test_file
        self.artifacts[filename]["test_result"] = result[:500]
        self._save()
        return self.artifacts[filename]

    def integrate(self, filename: str, target_subdir: str = "", batch_save: bool = False) -> Optional[Dict]:
        """Copy tested artifact to the integration directory."""
        if filename not in self.artifacts:
            return None
        art = self.artifacts[filename]
        if art["status"] not in (ArtifactStatus.TESTED, ArtifactStatus.APPROVED):
            return None

        src = os.path.join(ARTIFACTS_DIR, filename)
        dest_dir = os.path.join(INTEGRATION_DIR, target_subdir) if target_subdir else INTEGRATION_DIR
        dest = os.path.join(dest_dir, filename)
        
        # Ensure parent directory of destination exists
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            shutil.copy2(src, dest)
            self.artifacts[filename]["status"] = ArtifactStatus.INTEGRATED
            self.artifacts[filename]["integrated_at"] = datetime.now().isoformat()
            self.artifacts[filename]["integrated_path"] = dest
            if not batch_save:
                self._save()
            
            # Phase 2: Semantic Indexing on Integration
            try:
                from swarm_v2.core.semantic_index import get_semantic_index
                content = self.get_content(filename)
                if content:
                    import threading
                    def run_indexing():
                        import asyncio
                        idx = get_semantic_index()
                        asyncio.run(idx.index_artifact(filename, content, {"status": "integrated"}))
                    threading.Thread(target=run_indexing).start()
            except Exception as e:
                print(f"[Pipeline] Semantic indexing error: {e}")

            return self.artifacts[filename]
        except Exception as e:
            print(f"Integration error {filename}: {e}")
            return None

    def get_artifact(self, filename: str) -> Optional[Dict]:
        return self.artifacts.get(filename)

    def get_content(self, filename: str) -> Optional[str]:
        """Read the content of an artifact file."""
        filepath = os.path.join(ARTIFACTS_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception as e:
                return f"[Error reading file: {e}]"
                return f.read()
        return None

    def list_all(self) -> List[Dict]:
        return list(self.artifacts.values())

    def list_by_status(self, status: str) -> List[Dict]:
        return [a for a in self.artifacts.values() if a["status"] == status]

    def _infer_category(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext in ('.html', '.css', '.js', '.jsx', '.tsx'): return "Frontend"
        if ext in ('.py', '.go', '.rs'): return "Backend"
        if ext in ('.md', '.txt'): return "Documentation"
        if ext in ('.sh', '.yml', '.yaml'): return "Infrastructure"
        return "System"

    def get_grouped_artifacts(self) -> Dict[str, List[Dict]]:
        """Group artifacts by status for the UI categorization."""
        groups = {
            "pending": [],
            "approved": [],
            "tested": [],
            "integrated": [],
            "rejected": []
        }
        for art in self.artifacts.values():
            raw_status = art["status"]
            # Extract string value whether it's an Enum member or a raw string
            status = raw_status.value if hasattr(raw_status, "value") else str(raw_status)
            status = status.lower()
            
            # Map internal test_failed to the UI's rejected category
            if status == "test_failed":
                status = "rejected"
                
            if status in groups:
                # Add category info on the fly for the UI
                art_with_cat = art.copy()
                art_with_cat["category"] = self._infer_category(art["filename"])
                groups[status].append(art_with_cat)
        return groups

    def integrate_batch(self, filenames: List[str], target_subdir: str = "") -> Dict:
        """Integrate multiple artifacts at once."""
        results = {"success": [], "failed": []}
        for fname in filenames:
            integrated = self.integrate(fname, target_subdir)
            if integrated:
                results["success"].append(fname)
            else:
                results["failed"].append(fname)
        return results

    def approve_batch(self, filenames: List[str] = None, status: str = None, category: str = None, reviewer: str = "user") -> int:
        """Batch approve artifacts by list, status or inferred category."""
        count = 0
        target_list = filenames if filenames is not None else list(self.artifacts.keys())
        
        for filename in target_list:
            if filename not in self.artifacts:
                continue
            art = self.artifacts[filename]
            if art["status"] != ArtifactStatus.PENDING:
                continue
            
            match = False
            if filenames is not None: match = True # If explicit list, match
            elif status and art["status"] == status: match = True
            elif category and self._infer_category(filename) == category: match = True
            elif not status and not category: match = True # Approve all pending if no filter

            if match:
                self.approve(filename, reviewer, "Batch approved")
                count += 1
        return count

    def has_pending_reviews(self) -> bool:
        """Check if there are any artifacts awaiting review."""
        return any(a["status"] == ArtifactStatus.PENDING for a in self.artifacts.values())

    def get_stats(self) -> Dict:
        statuses = [a["status"] for a in self.artifacts.values()]
        return {
            "total": len(statuses),
            "pending": statuses.count(ArtifactStatus.PENDING),
            "approved": statuses.count(ArtifactStatus.APPROVED),
            "rejected": statuses.count(ArtifactStatus.REJECTED),
            "tested": statuses.count(ArtifactStatus.TESTED),
            "test_failed": statuses.count(ArtifactStatus.TEST_FAILED),
            "integrated": statuses.count(ArtifactStatus.INTEGRATED),
        }

    def get_rejection_report(self) -> str:
        """Build a report of all rejected artifacts for the Architect to re-plan."""
        rejected = self.list_by_status(ArtifactStatus.REJECTED)
        failed = self.list_by_status(ArtifactStatus.TEST_FAILED)
        items = rejected + failed
        if not items:
            return ""
        lines = ["The following artifacts were REJECTED or FAILED testing and need to be rebuilt:\n"]
        for a in items:
            lines.append(f"  ❌ {a['filename']} (status: {a['status']})")
            if a.get("review_notes"):
                lines.append(f"     Reason: {a['review_notes']}")
            if a.get("test_result"):
                lines.append(f"     Test failure: {a['test_result'][:150]}")
            lines.append("")
        return "\n".join(lines)

    def get_rejection_report_for_agent(self, agent_name: str) -> str:
        """Phase 5: Get rejection/failure report for a specific agent's artifacts."""
        rejected = [a for a in self.list_by_status(ArtifactStatus.REJECTED) if a.get("created_by") == agent_name]
        failed = [a for a in self.list_by_status(ArtifactStatus.TEST_FAILED) if a.get("created_by") == agent_name]
        items = rejected + failed
        if not items:
            return ""
        lines = [f"### REJECTION REPORT for {agent_name}:\n"]
        for a in items:
            lines.append(f"- **{a['filename']}**: {a['status']}")
            if a.get("review_notes"):
                lines.append(f"  - Notes: {a['review_notes']}")
            if a.get("test_result"):
                lines.append(f"  - Failure: {a['test_result'][:300]}")
        return "\n".join(lines)

    def reset_artifact(self, filename: str) -> Optional[Dict]:
        """Reset a rejected/failed artifact back to pending after it's been rebuilt."""
        if filename not in self.artifacts:
            return None
        filepath = os.path.join(ARTIFACTS_DIR, filename)
        self.artifacts[filename]["status"] = ArtifactStatus.PENDING
        self.artifacts[filename]["size"] = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        self.artifacts[filename]["reviewed_by"] = None
        self.artifacts[filename]["reviewed_at"] = None
        self.artifacts[filename]["review_notes"] = None
        self.artifacts[filename]["test_file"] = None
        self.artifacts[filename]["test_result"] = None
        self._save()
        return self.artifacts[filename]


    def set_security_status(self, filename: str, status: str, result: str = "") -> Optional[Dict]:
        """Mark artifact security scan result."""
        if filename not in self.artifacts:
            return None
        self.artifacts[filename]["security_status"] = status
        self.artifacts[filename]["security_result"] = result[:500]
        self._save()
        return self.artifacts[filename]

    def list_unscanned(self) -> List[Dict]:
        """List artifacts that need security scanning."""
        result = []
        for a in self.artifacts.values():
            if a.get("security_status") == "pending_scan" and a["status"] != ArtifactStatus.REJECTED:
                result.append(a)
        return result

    def get_integrated_manifest(self) -> str:
        """Build a manifest of all integrated files for deployment."""
        integrated = self.list_by_status(ArtifactStatus.INTEGRATED)
        if not integrated:
            return "No artifacts have been integrated yet."
        lines = ["INTEGRATED ARTIFACTS MANIFEST:\n"]
        for a in integrated:
            lines.append(f"  📦 {a['filename']} ({a['size']}b) → {a.get('integrated_path', 'unknown')}")
        return "\n".join(lines)

    def prune_v2_artifacts(self, age_hours: int = 24):
        """Strategic Cleanup: Remove redundant test files and old artifacts to prevent fragmentation."""
        count = 0
        now = datetime.now()
        to_delete = []
        
        for rel_path, meta in list(self.artifacts.items()):
            # Logic: If it starts with 'test_' and is older than threshold
            if rel_path.startswith("test_"):
                created_at = meta.get("created_at")
                if created_at:
                    dt = datetime.fromisoformat(created_at)
                    hours_old = (now - dt).total_seconds() / 3600
                    if hours_old > age_hours:
                        filepath = os.path.join(ARTIFACTS_DIR, rel_path)
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        to_delete.append(rel_path)
                        count += 1
        
        for path in to_delete:
            del self.artifacts[path]
            
        if count > 0:
            self._save()
            print(f"[Pipeline] Strategic Cleanup: Removed {count} fragmented artifacts.")
        return count


_pipeline_instance = None

def get_artifact_pipeline() -> ArtifactPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ArtifactPipeline()
    return _pipeline_instance
