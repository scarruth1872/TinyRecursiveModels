import os
import subprocess
import platform

class FileSkill:
    """Read/write files in the swarm artifacts directory with auto-registration."""
    skill_name = "FileSkill"
    description = "Read, write, and list files in the swarm artifacts workspace. Supports nested subdirectories."

    def __init__(self, base_dir: str = "swarm_v2_artifacts"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def write_file(self, filename: str, content: str) -> str:
        """Write a file, auto-creating any missing parent directories, and register with pipeline."""
        # Normalize path separators
        filename = filename.replace("\\", "/")
        path = os.path.join(self.base_dir, filename)
        # Create parent directories if they don't exist
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # AUTO-REGISTER with artifact pipeline
        try:
            from swarm_v2.core.artifact_pipeline import get_artifact_pipeline
            pipeline = get_artifact_pipeline()
            pipeline.register_artifact(filename, created_by="Agent")
        except Exception as e:
            pass  # Don't fail if pipeline unavailable
        
        return f"[OK] File written: {filename} ({len(content):,} bytes) -> {self.base_dir}/"

    def read_file(self, filename: str) -> str:
        """Read a file by name or relative subpath."""
        filename = filename.replace("\\", "/")
        path = os.path.join(self.base_dir, filename)
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return f"[FAIL] File not found: {filename}"

    def list_artifacts(self) -> list:
        """List all files recursively, returning relative paths."""
        results = []
        for root, dirs, files in os.walk(self.base_dir):
            # Skip hidden/cache dirs
            dirs[:] = [d for d in dirs if not d.startswith('.', '__')]
            for fname in files:
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, self.base_dir).replace("\\", "/")
                results.append(rel_path)
        return sorted(results)

    def delete_file(self, filename: str) -> str:
        filename = filename.replace("\\", "/")
        path = os.path.join(self.base_dir, filename)
        if os.path.exists(path):
            os.remove(path)
            return f"[DELETE] Deleted: {filename}"
        return f"[FAIL] File not found: {filename}"

    def make_dir(self, dirpath: str) -> str:
        """Create a directory (and parents) inside the artifacts workspace."""
        dirpath = dirpath.replace("\\", "/")
        full_path = os.path.join(self.base_dir, dirpath)
        os.makedirs(full_path, exist_ok=True)
        return f"[DIR] Directory created: {dirpath}/"


class ShellSkill:
    """Run safe shell commands (read-only or build commands)."""
    skill_name = "ShellSkill"
    description = "Execute safe shell commands for build, test, and inspection tasks."
    ALLOWED = ["dir", "ls", "echo", "python --version", "node --version", "npm --version", "git log", "git status"]

    def run(self, command: str) -> str:
        if not any(command.strip().startswith(a) for a in self.ALLOWED):
            return f"[DENY] Command not in allowlist: '{command}'"
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout or result.stderr or "(no output)"
        except Exception as e:
            return f"[FAIL] Error: {e}"


try:
    from swarm_v2.skills.web_search_skill import WebSearchSkill
except ImportError:
    class WebSearchSkill:
        """Simulate web search (stub for real integration)."""
        skill_name = "WebSearchSkill"
        description = "Search the web for information and return summarized results."

        def search(self, query: str) -> str:
            return (
                f"🔍 Search results for: '{query}'\n"
                f"(WebSearchSkill import failed. Using stub.)"
            )


class CodeAnalysisSkill:
    """Analyze code files for issues and patterns."""
    skill_name = "CodeAnalysisSkill"
    description = "Analyze Python/JS code files for quality, patterns, and issues."

    def analyze(self, filename: str, base_dir: str = "swarm_v2_artifacts") -> str:
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            return f"[FAIL] File not found: {filename}"
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.split("\n")
        issues = []
        for i, line in enumerate(lines, 1):
            if "TODO" in line: issues.append(f"  Line {i}: TODO found")
            if len(line) > 120: issues.append(f"  Line {i}: Line too long ({len(line)} chars)")
            if "print(" in line and filename.endswith(".py"): issues.append(f"  Line {i}: Debug print statement")
        report = f"[REPORT] Analysis of {filename} ({len(lines)} lines):\n"
        report += "\n".join(issues) if issues else "  [OK] No issues found."
        return report


class DataSkill:
    """Process and summarize data."""
    skill_name = "DataSkill"
    description = "Process CSV/JSON data and generate summaries and statistics."

    def summarize_json(self, data: dict) -> str:
        keys = list(data.keys())
        return f"[JSON] JSON Summary: {len(keys)} top-level keys: {', '.join(keys[:10])}"

    def count_words(self, text: str) -> str:
        words = text.split()
        return f"[WORDS] Word count: {len(words)} words, {len(text)} characters"


class DocSkill:
    """Generate documentation from code or descriptions."""
    skill_name = "DocSkill"
    description = "Generate markdown documentation, READMEs, and API docs."

    def generate_readme(self, project_name: str, description: str, features: list) -> str:
        features_md = "\n".join(f"- {f}" for f in features)
        return (
            f"# {project_name}\n\n"
            f"{description}\n\n"
            f"## Features\n{features_md}\n\n"
            f"## Installation\n```bash\npip install -r requirements.txt\n```\n\n"
            f"## Usage\n```python\n# Add usage example here\n```\n"
        )
