"""
Digital DNA Repository (DDR) — Antibody System
Stores error patterns and their fixes. Acts as a codebase immune system
that prevents known errors from recurring.
"""

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("DDR_Antibody")

DDR_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "swarm_v2_artifacts", "DDR_ANTIBODIES.json"
)


class Antibody:
    """A single error antibody — records a known error and its fix."""

    def __init__(self, error_type: str, file_pattern: str, line_pattern: str,
                 fix_description: str, severity: str = "medium",
                 recorded_by: str = "system"):
        self.antibody_id = f"ab-{int(datetime.now().timestamp())}-{hash(error_type) & 0xFFFF:04x}"
        self.error_type = error_type
        self.file_pattern = file_pattern  # glob or regex for matching files
        self.line_pattern = line_pattern  # regex for matching problematic code
        self.fix_description = fix_description
        self.severity = severity  # low, medium, high, critical
        self.recorded_by = recorded_by
        self.created_at = datetime.now().isoformat()
        self.matches_prevented = 0

    def to_dict(self) -> Dict[str, Any]:
        return vars(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Antibody":
        ab = Antibody.__new__(Antibody)
        for k, v in d.items():
            setattr(ab, k, v)
        return ab


class DigitalDNARepository:
    """
    Digital DNA Repository (DDR) — Codebase Immune System.

    Records error patterns discovered during development and prevents
    them from recurring. Integrates with NeuralWall for proactive scanning.
    """

    def __init__(self, path: str = DDR_PATH):
        self.path = os.path.abspath(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._antibodies: List[Antibody] = self._load()

    def _load(self) -> List[Antibody]:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return [Antibody.from_dict(d) for d in data]
            except Exception:
                return []
        return []

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([ab.to_dict() for ab in self._antibodies], f, indent=2)

    def record_error(self, file_path: str, line_number: int,
                     error_type: str, fix_description: str,
                     line_pattern: str = "", severity: str = "medium",
                     recorded_by: str = "system") -> str:
        """
        Record an error as a new antibody.

        Args:
            file_path: File where error occurred
            line_number: Line number
            error_type: Category (sql_injection, null_reference, race_condition, etc.)
            fix_description: How the error was fixed
            line_pattern: Regex pattern matching the problematic code
            severity: low/medium/high/critical
            recorded_by: Agent who discovered the error

        Returns:
            antibody_id
        """
        # Auto-derive file pattern from path
        ext = os.path.splitext(file_path)[1]
        file_pattern = f"*{ext}" if ext else "*"

        ab = Antibody(
            error_type=error_type,
            file_pattern=file_pattern,
            line_pattern=line_pattern,
            fix_description=fix_description,
            severity=severity,
            recorded_by=recorded_by,
        )

        self._antibodies.append(ab)
        self._save()

        logger.info(f"[DDR] Recorded antibody: {ab.antibody_id} ({error_type}) "
                    f"in {file_path}:{line_number}")
        return ab.antibody_id

    def check_antibodies(self, code: str, filename: str = "") -> List[Dict[str, Any]]:
        """
        Check code against all antibodies. Returns list of matches.

        Args:
            code: Source code to scan
            filename: Optional filename for file-pattern matching

        Returns:
            List of matched antibodies with details
        """
        matches = []
        for ab in self._antibodies:
            # Check file pattern
            if ab.file_pattern and filename:
                import fnmatch
                if not fnmatch.fnmatch(filename, ab.file_pattern):
                    continue

            # Check line pattern
            if ab.line_pattern:
                try:
                    if re.search(ab.line_pattern, code):
                        ab.matches_prevented += 1
                        matches.append({
                            "antibody_id": ab.antibody_id,
                            "error_type": ab.error_type,
                            "severity": ab.severity,
                            "fix": ab.fix_description,
                            "pattern": ab.line_pattern,
                        })
                except re.error:
                    pass

        if matches:
            self._save()  # Update prevention counts
            logger.warning(f"[DDR] {len(matches)} antibody matches in {filename or '(code)'}")

        return matches

    def match_patterns(self, code: str) -> List[str]:
        """Quick check — returns list of matched error types."""
        matches = self.check_antibodies(code)
        return [m["error_type"] for m in matches]

    def get_antibodies(self, error_type: str = None) -> List[Dict[str, Any]]:
        """List all (or filtered) antibodies."""
        antibodies = self._antibodies
        if error_type:
            antibodies = [ab for ab in antibodies if ab.error_type == error_type]
        return [ab.to_dict() for ab in antibodies]

    def get_prevention_stats(self) -> Dict[str, Any]:
        """Get prevention statistics."""
        total_prevented = sum(ab.matches_prevented for ab in self._antibodies)
        by_type = {}
        for ab in self._antibodies:
            by_type[ab.error_type] = by_type.get(ab.error_type, 0) + 1

        return {
            "total_antibodies": len(self._antibodies),
            "total_prevented": total_prevented,
            "by_type": by_type,
            "severity_breakdown": {
                sev: sum(1 for ab in self._antibodies if ab.severity == sev)
                for sev in ["low", "medium", "high", "critical"]
            },
        }

    # --- Built-in antibodies (common patterns) ---

    def install_default_antibodies(self):
        """Install a set of default antibodies for common vulnerability patterns."""
        defaults = [
            ("sql_injection", "*.py", r"f['\"].*SELECT.*{.*}",
             "Use parameterized queries instead of f-strings in SQL", "critical"),
            ("hardcoded_secret", "*.py", r"(SECRET_KEY|API_KEY|PASSWORD)\s*=\s*['\"]",
             "Move secrets to SecretsVault or environment variables", "high"),
            ("eval_usage", "*.py", r"\beval\s*\(",
             "Replace eval() with ast.literal_eval() or structured parsing", "high"),
            ("debug_print", "*.py", r"^\s*print\s*\(",
             "Replace debug print() with logger.debug()", "low"),
            ("bare_except", "*.py", r"except\s*:",
             "Catch specific exceptions instead of bare except", "medium"),
            ("path_traversal", "*.py", r"\.\./\.\.",
             "Validate paths against allowlist; use os.path.abspath()", "high"),
        ]

        for error_type, file_pat, line_pat, fix, severity in defaults:
            # Don't duplicate
            if any(ab.error_type == error_type and ab.line_pattern == line_pat
                   for ab in self._antibodies):
                continue
            ab = Antibody(error_type, file_pat, line_pat, fix, severity, "DDR_defaults")
            self._antibodies.append(ab)

        self._save()
        logger.info(f"[DDR] Installed default antibodies. Total: {len(self._antibodies)}")


# Singleton
_ddr: Optional[DigitalDNARepository] = None

def get_ddr() -> DigitalDNARepository:
    global _ddr
    if _ddr is None:
        _ddr = DigitalDNARepository()
    return _ddr
