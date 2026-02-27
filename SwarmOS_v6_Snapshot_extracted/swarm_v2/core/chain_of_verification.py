"""
Swarm V2 Chain-of-Verification (CoV)
Phase 5: Logic (Reasoning Engine) Upgrade

A self-audit system where Logic reviews its own reasoning steps for logical
fallacies before the final output is generated.

Implements a 3-stage verification process:
1. Reasoning Extraction - Parse reasoning steps from LLM output
2. Fallacy Detection - Check for common logical fallacies
3. Verification & Correction - Score reasoning, suggest fixes
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FallacyType(Enum):
    """Common logical fallacies that the CoV can detect."""
    CIRCULAR_REASONING = "circular_reasoning"
    FALSE_DICHOTOMY = "false_dichotomy"
    HASTY_GENERALIZATION = "hasty_generalization"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    SLIPPERY_SLOPE = "slippery_slope"
    STRAW_MAN = "straw_man"
    AD_HOMINEM = "ad_hominem"
    RED_HERRING = "red_herring"
    POST_HOC = "post_hoc"
    BEGGING_THE_QUESTION = "begging_the_question"
    EQUIVOCATION = "equivocation"
    APPEAL_TO_EMOTION = "appeal_to_emotion"
    NON_SEQUITUR = "non_sequitur"
    CONTRADICTION = "contradiction"
    INCOMPLETE_REASONING = "incomplete_reasoning"


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""
    step_number: int
    content: str
    premises: List[str] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 1.0


@dataclass
class FallacyDetection:
    """A detected fallacy in reasoning."""
    fallacy_type: FallacyType
    severity: str  # "low", "medium", "high", "critical"
    step_number: int
    description: str
    suggestion: str
    affected_text: str


@dataclass
class VerificationResult:
    """Result of the Chain-of-Verification process."""
    passed: bool
    score: float  # 0.0 to 1.0
    reasoning_steps: List[ReasoningStep]
    detected_fallacies: List[FallacyDetection]
    suggestions: List[str]
    corrected_reasoning: Optional[str] = None
    verification_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ═══════════════════════════════════════════════════════════════════════════
# FALLACY DETECTION PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

FALLACY_PATTERNS = {
    FallacyType.CIRCULAR_REASONING: [
        (r"(\w+)\s+(?:is|means|because)\s+\1", "Definition restates itself"),
        (r"because\s+it\s+is\s+(?:true|correct|right)", "Asserts conclusion as premise"),
        (r"this\s+is\s+(?:true|correct)\s+because\s+it\s+is", "Begs the question"),
    ],
    FallacyType.FALSE_DICHOTOMY: [
        (r"(?:either|only)\s+\w+\s+or\s+\w+(?:\.|,|\s+no\s+other)", "Presents only two options"),
        (r"if\s+not\s+\w+,\s+then\s+(?:must\s+be\s+)?\w+", "Forces binary choice"),
        (r"the\s+only\s+(?:way|option|choice)\s+is", "Eliminates alternatives"),
    ],
    FallacyType.HASTY_GENERALIZATION: [
        (r"(?:all|every|always)\s+\w+\s+(?:are|is|do|have)", "Overgeneralization from limited data"),
        (r"based\s+on\s+(?:this|one|a\s+single)", "Generalizing from single instance"),
        (r"clearly\s+all\s+", "Unjustified universal claim"),
    ],
    FallacyType.APPEAL_TO_AUTHORITY: [
        (r"(?:experts|scientists|studies)\s+says?\s+(?:it|this)\s+is\s+true", "Vague authority appeal"),
        (r"according\s+to\s+(?:an?\s+)?expert", "Unnamed authority"),
        (r"because\s+\w+\s+said\s+so", "Authority without evidence"),
    ],
    FallacyType.SLIPPERY_SLOPE: [
        (r"this\s+will\s+(?:inevitably|certainly|surely)\s+lead\s+to", "Unjustified causal chain"),
        (r"step\s+by\s+step\s+(?:leading|resulting)\s+in", "Inevitable decline claim"),
        (r"if\s+we\s+allow\s+this,\s+(?:then\s+)?eventually", "Domino effect assertion"),
    ],
    FallacyType.STRAW_MAN: [
        (r"(?:some\s+might\s+say|critics\s+claim|opponents\s+argue)\s+that\s+\w+\s+(?:just\s+)?wants?\s+to\s+destroy", "Exaggerated opponent position"),
        (r"obviously\s+wrong\s+to\s+suggest\s+that", "Attacking weakened argument"),
    ],
    FallacyType.AD_HOMINEM: [
        (r"\w+\s+is\s+(?:wrong|mistaken|lying)\s+because\s+(?:he|she|they)\s+(?:is|are|was|were)\s+an?", "Attacks person not argument"),
        (r"don't\s+trust\s+\w+\s+because\s+of\s+(?:their|his|her)", "Discredits source personally"),
        (r"coming\s+from\s+someone\s+who", "Dismisses based on source"),
    ],
    FallacyType.RED_HERRING: [
        (r"but\s+what\s+about\s+", "Deflects to unrelated topic"),
        (r"speaking\s+of\s+which,\s+(?:unrelated|different)", "Introduces irrelevant subject"),
        (r"this\s+reminds\s+me\s+of\s+(?:another|a\s+different)", "Changes subject"),
    ],
    FallacyType.POST_HOC: [
        (r"(?:after|since|following)\s+\w+,\s+then\s+\w+\s+(?:happened|occurred|resulted)", "Correlation implies causation"),
        (r"because\s+\w+\s+happened\s+first", "Temporal order fallacy"),
        (r"coincidence\??\s+I\s+think\s+not", "Unjustified causal claim"),
    ],
    FallacyType.CONTRADICTION: [
        (r"(\w+)\s+(?:is|are)\s+(\w+).+?(?:however|but|yet).+?\1\s+(?:is|are)\s+not\s+\2", "Direct contradiction"),
        (r"always\s+.+?\s+never", "Mutually exclusive claims"),
    ],
    FallacyType.INCOMPLETE_REASONING: [
        (r"therefore\s+\w+\s+is\s+(?:true|correct|the\s+answer)", "Conclusion without premises"),
        (r"simply\s+put,", "Oversimplification marker"),
        (r"it's\s+obvious\s+that", "Unexplained assertion"),
    ],
    FallacyType.NON_SEQUITUR: [
        (r"therefore\s+(?:we\s+should|it\s+follows)", "Non-logical conclusion"),
        (r"thus\s+\w+\s+must\s+be", "Invalid logical jump"),
    ],
    FallacyType.APPEAL_TO_EMOTION: [
        (r"(?:think\s+of\s+the|consider\s+the)\s+(?:children|poor|victims)", "Emotional manipulation"),
        (r"(?:terrifying|horrifying|shocking|disgusting)\s+to\s+think", "Fear-based appeal"),
        (r"any\s+(?:decent|right-thinking|moral)\s+person", "Moral pressure"),
    ],
}


class ChainOfVerification:
    """
    Chain-of-Verification system for logical self-audit.
    
    Usage:
        cov = ChainOfVerification()
        result = cov.verify(reasoning_text)
        if not result.passed:
            print(result.suggestions)
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.verification_history: List[VerificationResult] = []
    
    def verify(self, reasoning_text: str, auto_correct: bool = False) -> VerificationResult:
        """
        Main entry point: verify reasoning text for logical fallacies.
        
        Args:
            reasoning_text: The reasoning output from an LLM
            auto_correct: If True, attempt to generate corrected reasoning
            
        Returns:
            VerificationResult with pass/fail status and detected fallacies
        """
        # Step 1: Extract reasoning steps
        steps = self._extract_reasoning_steps(reasoning_text)
        
        # Step 2: Detect fallacies in each step
        fallacies = self._detect_fallacies(reasoning_text, steps)
        
        # Step 3: Calculate verification score
        score = self._calculate_score(len(steps), fallacies)
        
        # Step 4: Generate suggestions
        suggestions = self._generate_suggestions(fallacies)
        
        # Step 5: Auto-correct if requested
        corrected = None
        if auto_correct and fallacies:
            corrected = self._generate_corrected_reasoning(reasoning_text, fallacies)
        
        # Build result
        result = VerificationResult(
            passed=score >= self.confidence_threshold and not any(
                f.severity in ["high", "critical"] for f in fallacies
            ),
            score=score,
            reasoning_steps=steps,
            detected_fallacies=fallacies,
            suggestions=suggestions,
            corrected_reasoning=corrected
        )
        
        # Store in history
        self.verification_history.append(result)
        
        return result
    
    def _extract_reasoning_steps(self, text: str) -> List[ReasoningStep]:
        """Extract individual reasoning steps from the text."""
        steps = []
        
        # Pattern 1: Numbered steps (1., 2., etc.)
        numbered_pattern = re.compile(
            r'(?:^|\n)\s*(\d+)\.\s+([^\n]+(?:\n(?!\s*\d+\.)[^\n]*)*)',
            re.MULTILINE
        )
        
        for match in numbered_pattern.finditer(text):
            step_num = int(match.group(1))
            content = match.group(2).strip()
            steps.append(ReasoningStep(
                step_number=step_num,
                content=content,
                premises=self._extract_premises(content),
                conclusion=self._extract_conclusion(content)
            ))
        
        # Pattern 2: Bullet points or dashes
        if not steps:
            bullet_pattern = re.compile(
                r'(?:^|\n)\s*[-•]\s+([^\n]+)',
                re.MULTILINE
            )
            for i, match in enumerate(bullet_pattern.finditer(text), 1):
                content = match.group(1).strip()
                steps.append(ReasoningStep(
                    step_number=i,
                    content=content,
                    premises=self._extract_premises(content),
                    conclusion=self._extract_conclusion(content)
                ))
        
        # Pattern 3: Sentence-based (fallback)
        if not steps:
            sentences = re.split(r'[.!?]+', text)
            for i, sentence in enumerate(sentences, 1):
                sentence = sentence.strip()
                if len(sentence) > 20:  # Skip very short sentences
                    steps.append(ReasoningStep(
                        step_number=i,
                        content=sentence,
                        premises=self._extract_premises(sentence),
                        conclusion=self._extract_conclusion(sentence)
                    ))
        
        return steps
    
    def _extract_premises(self, text: str) -> List[str]:
        """Extract premises from a reasoning step."""
        premises = []
        
        # Look for explicit premise markers
        premise_markers = ["because", "since", "given that", "assuming", "if"]
        for marker in premise_markers:
            pattern = rf"{marker}\s+([^,\.]+)"
            matches = re.findall(pattern, text, re.IGNORECASE)
            premises.extend(matches)
        
        return premises
    
    def _extract_conclusion(self, text: str) -> str:
        """Extract the conclusion from a reasoning step."""
        # Look for conclusion markers
        conclusion_markers = ["therefore", "thus", "hence", "so", "consequently", "as a result"]
        for marker in conclusion_markers:
            pattern = rf"{marker}\s+([^,\.]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no marker, return the last sentence
        sentences = re.split(r'[,.]', text)
        if sentences:
            return sentences[-1].strip()
        
        return ""
    
    def _detect_fallacies(self, text: str, steps: List[ReasoningStep]) -> List[FallacyDetection]:
        """Detect logical fallacies in the reasoning."""
        fallacies = []
        text_lower = text.lower()
        
        for fallacy_type, patterns in FALLACY_PATTERNS.items():
            for pattern, description in patterns:
                for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                    # Determine severity based on fallacy type and context
                    severity = self._determine_severity(fallacy_type, match.group(0))
                    
                    # Find which step this fallacy belongs to
                    step_num = self._find_step_for_text(match.group(0), steps)
                    
                    fallacies.append(FallacyDetection(
                        fallacy_type=fallacy_type,
                        severity=severity,
                        step_number=step_num,
                        description=description,
                        suggestion=self._get_fallacy_suggestion(fallacy_type),
                        affected_text=match.group(0)
                    ))
        
        return fallacies
    
    def _determine_severity(self, fallacy_type: FallacyType, text: str) -> str:
        """Determine the severity of a detected fallacy."""
        critical_fallacies = [FallacyType.CIRCULAR_REASONING, FallacyType.CONTRADICTION]
        high_fallacies = [FallacyType.HASTY_GENERALIZATION, FallacyType.FALSE_DICHOTOMY]
        
        if fallacy_type in critical_fallacies:
            return "critical"
        elif fallacy_type in high_fallacies:
            return "high"
        elif "always" in text.lower() or "never" in text.lower():
            return "medium"
        else:
            return "low"
    
    def _find_step_for_text(self, text: str, steps: List[ReasoningStep]) -> int:
        """Find which reasoning step contains the given text."""
        text_lower = text.lower()
        for step in steps:
            if text_lower in step.content.lower():
                return step.step_number
        return 0
    
    def _get_fallacy_suggestion(self, fallacy_type: FallacyType) -> str:
        """Get a suggestion for fixing the fallacy."""
        suggestions = {
            FallacyType.CIRCULAR_REASONING: "Provide independent evidence or premises that don't assume the conclusion.",
            FallacyType.FALSE_DICHOTOMY: "Consider additional alternatives beyond the two presented.",
            FallacyType.HASTY_GENERALIZATION: "Gather more data before making universal claims.",
            FallacyType.APPEAL_TO_AUTHORITY: "Cite specific evidence or studies rather than vague authority.",
            FallacyType.SLIPPERY_SLOPE: "Demonstrate each causal link with evidence.",
            FallacyType.STRAW_MAN: "Address the strongest version of the opposing argument.",
            FallacyType.AD_HOMINEM: "Focus on the argument's merits rather than the source.",
            FallacyType.RED_HERRING: "Stay focused on the relevant issue at hand.",
            FallacyType.POST_HOC: "Establish a causal mechanism, not just temporal sequence.",
            FallacyType.BEGGING_THE_QUESTION: "Provide premises that don't presuppose the conclusion.",
            FallacyType.EQUIVOCATION: "Use terms consistently throughout the argument.",
            FallacyType.APPEAL_TO_EMOTION: "Rely on logical evidence rather than emotional appeals.",
            FallacyType.NON_SEQUITUR: "Ensure conclusions follow logically from premises.",
            FallacyType.CONTRADICTION: "Resolve inconsistent claims before proceeding.",
            FallacyType.INCOMPLETE_REASONING: "Make all premises and logical steps explicit.",
        }
        return suggestions.get(fallacy_type, "Review reasoning for logical consistency.")
    
    def _calculate_score(self, step_count: int, fallacies: List[FallacyDetection]) -> float:
        """Calculate a verification score based on reasoning quality."""
        if step_count == 0:
            return 0.5  # No reasoning detected
        
        # Base score from having structured reasoning
        base_score = min(1.0, step_count * 0.15 + 0.4)
        
        # Penalties for fallacies
        penalty = 0.0
        for fallacy in fallacies:
            if fallacy.severity == "critical":
                penalty += 0.25
            elif fallacy.severity == "high":
                penalty += 0.15
            elif fallacy.severity == "medium":
                penalty += 0.10
            else:
                penalty += 0.05
        
        return max(0.0, min(1.0, base_score - penalty))
    
    def _generate_suggestions(self, fallacies: List[FallacyDetection]) -> List[str]:
        """Generate actionable suggestions for improving reasoning."""
        suggestions = []
        
        # Group fallacies by type for consolidated suggestions
        fallacy_counts = {}
        for f in fallacies:
            if f.fallacy_type not in fallacy_counts:
                fallacy_counts[f.fallacy_type] = []
            fallacy_counts[f.fallacy_type].append(f)
        
        for fallacy_type, detections in fallacy_counts.items():
            suggestion = f"• [{fallacy_type.value}] {detections[0].suggestion}"
            if len(detections) > 1:
                suggestion += f" (found {len(detections)} instances)"
            suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_corrected_reasoning(self, original: str, fallacies: List[FallacyDetection]) -> str:
        """Generate a corrected version of the reasoning (placeholder for LLM integration)."""
        # This is a simplified correction - in production, this would call the LLM
        corrections = []
        for f in fallacies:
            corrections.append(f"Note: {f.description} in step {f.step_number}. {f.suggestion}")
        
        return f"{original}\n\n[VERIFICATION NOTES]\n" + "\n".join(corrections)
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get statistics about verification history."""
        if not self.verification_history:
            return {"total_verifications": 0}
        
        total = len(self.verification_history)
        passed = sum(1 for r in self.verification_history if r.passed)
        avg_score = sum(r.score for r in self.verification_history) / total
        
        # Count fallacy types
        fallacy_counts = {}
        for result in self.verification_history:
            for f in result.detected_fallacies:
                key = f.fallacy_type.value
                fallacy_counts[key] = fallacy_counts.get(key, 0) + 1
        
        return {
            "total_verifications": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "average_score": round(avg_score, 3),
            "most_common_fallacies": sorted(
                fallacy_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
        }


# Singleton instance
_cov_instance: Optional[ChainOfVerification] = None

def get_chain_of_verification() -> ChainOfVerification:
    """Get the singleton ChainOfVerification instance."""
    global _cov_instance
    if _cov_instance is None:
        _cov_instance = ChainOfVerification()
    return _cov_instance


async def verify_reasoning(text: str, auto_correct: bool = False) -> VerificationResult:
    """
    Convenience function to verify reasoning.
    
    Usage:
        result = await verify_reasoning(llm_output)
        if not result.passed:
            print("Reasoning issues detected:", result.suggestions)
    """
    cov = get_chain_of_verification()
    return cov.verify(text, auto_correct=auto_correct)