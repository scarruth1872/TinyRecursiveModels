
from typing import List, Optional
# from swarm_v2.core.trm_brain import get_trm_brain

class TRMSkill:
    """Skill to access the Tiny Recursive Model for deep symbolic reasoning."""
    skill_name = "TRMReasoning"
    description = "Use the 7M Tiny Recursive Model to perform deep, multi-cycle symbolic reasoning. Best for abstract pattern matching and logical puzzles."

    def __init__(self):
        self.brain = None # get_trm_brain()

    def recursive_reason(self, pattern: str, cycles: int = 1) -> str:
        """
        Processes a symbolic pattern through the TRM engine.
        
        Args:
            pattern: A string of space-separated integers representing the symbolic input.
            cycles: Number of times to pass through the TRM brain.
        
        Returns:
            The refined pattern as a string of integers.
        """
        try:
            tokens = [int(t) for t in pattern.split() if t.isdigit()]
            if not tokens:
                return "Error: No symbolic tokens found in input."
            
            result_tokens = tokens
            for _ in range(cycles):
                result_tokens = self.brain.reason(result_tokens)
            
            # Map back to string
            # We only return the non-padded part (original input length)
            return " ".join(map(str, result_tokens[:len(tokens)]))
        except Exception as e:
            return f"TRM Error: {str(e)}"

    def analyze_arc_pattern(self, grid_json: str) -> str:
        """
        Analyzes an ARC-style grid pattern.
        """
        # Simplistic mapping for now: convert grid to tokens
        import json
        try:
            grid = json.loads(grid_json)
            # Flatten grid
            tokens = []
            for row in grid:
                tokens.extend(row)
            
            result = self.brain.reason(tokens)
            return f"Processed Pattern: {result[:len(tokens)]}"
        except Exception as e:
            return f"ARC Analysis Failed: {str(e)}"
