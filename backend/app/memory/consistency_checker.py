"""
Consistency Checker - validates that persona responses remain consistent
with their established attributes, opinions, and conversation history.
"""
from __future__ import annotations

from typing import Any
from dataclasses import dataclass
import re


@dataclass
class ConsistencyIssue:
    """Represents a consistency violation found during validation."""
    severity: str  # "low", "medium", "high"
    category: str  # "attribute", "opinion", "logic", "demographic"
    description: str
    details: dict[str, Any]


class ConsistencyChecker:
    """
    Validates persona responses for consistency with:
    - Demographic attributes (age, occupation, etc.)
    - Previously expressed opinions
    - Behavioral patterns and personality traits
    - Logical consistency in conversation flow
    """
    
    def __init__(self) -> None:
        # Patterns that might indicate inconsistency
        self.inconsistency_patterns = {
            "contradiction": [
                r"although.*however",
                r"but.*also",
                r"despite.*yet"
            ],
            "uncertainty": [
                r"i think.*maybe",
                r"not sure.*but",
                r"probably.*actually"
            ]
        }
    
    def check_response_consistency(
        self,
        persona_attributes: dict[str, Any],
        previous_opinions: dict[str, str],
        conversation_history: list[dict[str, Any]],
        new_question: str,
        new_answer: str
    ) -> list[ConsistencyIssue]:
        """
        Check a new response for consistency issues.
        Returns a list of ConsistencyIssue objects (empty if consistent).
        """
        issues: list[ConsistencyIssue] = []
        
        # Check demographic consistency
        issues.extend(self._check_demographic_consistency(persona_attributes, new_answer))
        
        # Check opinion consistency
        issues.extend(self._check_opinion_consistency(previous_opinions, new_question, new_answer))
        
        # Check behavioral consistency
        issues.extend(self._check_behavioral_consistency(persona_attributes, new_answer))
        
        # Check logical consistency
        issues.extend(self._check_logical_consistency(conversation_history, new_question, new_answer))
        
        return issues
    
    def _check_demographic_consistency(
        self, attributes: dict[str, Any], answer: str
    ) -> list[ConsistencyIssue]:
        """Check if answer aligns with demographic attributes."""
        issues: list[ConsistencyIssue] = []
        answer_lower = answer.lower()
        
        # Age-appropriate language and references
        age = attributes.get("age", 30)
        if age < 25:
            # Younger personas shouldn't reference outdated technology
            outdated_refs = ["floppy disk", "vhs", "dial-up", "pager"]
            for ref in outdated_refs:
                if ref in answer_lower:
                    issues.append(ConsistencyIssue(
                        severity="medium",
                        category="demographic",
                        description=f"Age-inappropriate reference: {ref}",
                        details={"age": age, "reference": ref}
                    ))
        elif age > 60:
            # Older personas might not use very current slang
            slang_terms = ["lit", "no cap", "bet", "slay", "rizz"]
            for slang in slang_terms:
                if slang in answer_lower:
                    issues.append(ConsistencyIssue(
                        severity="low",
                        category="demographic",
                        description=f"Age-inappropriate slang: {slang}",
                        details={"age": age, "slang": slang}
                    ))
        
        # Occupation-appropriate knowledge
        occupation = attributes.get("occupation", "").lower()
        if "teacher" in occupation or "professor" in occupation:
            # Should value education
            if "education is overrated" in answer_lower or "school is useless" in answer_lower:
                issues.append(ConsistencyIssue(
                    severity="high",
                    category="demographic",
                    description="Occupation-inconsistent view on education",
                    details={"occupation": occupation}
                ))
        
        # Tech savviness consistency
        tech_savviness = attributes.get("tech_savviness", "medium")
        if tech_savviness == "low":
            tech_terms = ["api", "blockchain", "cryptocurrency", "machine learning"]
            for term in tech_terms:
                if term in answer_lower:
                    issues.append(ConsistencyIssue(
                        severity="medium",
                        category="demographic",
                        description=f"Tech-savviness inconsistent: using technical term '{term}'",
                        details={"tech_savviness": tech_savviness, "term": term}
                    ))
        
        return issues
    
    def _check_opinion_consistency(
        self, previous_opinions: dict[str, str], new_question: str, new_answer: str
    ) -> list[ConsistencyIssue]:
        """Check if new answer contradicts previously expressed opinions."""
        issues: list[ConsistencyIssue] = []
        
        # Simple topic matching
        for topic, previous_answer in previous_opinions.items():
            if topic.lower() in new_question.lower():
                # Check for direct contradictions
                if self._are_contradictory(previous_answer, new_answer):
                    issues.append(ConsistencyIssue(
                        severity="high",
                        category="opinion",
                        description=f"Contradicts previous opinion on '{topic}'",
                        details={
                            "topic": topic,
                            "previous": previous_answer,
                            "new": new_answer
                        }
                    ))
        
        return issues
    
    def _check_behavioral_consistency(
        self, attributes: dict[str, Any], answer: str
    ) -> list[ConsistencyIssue]:
        """Check if answer aligns with behavioral patterns and personality traits."""
        issues: list[ConsistencyIssue] = []
        answer_lower = answer.lower()
        
        personality_traits = attributes.get("personality_traits", [])
        behavioral_patterns = attributes.get("behavioral_patterns", [])
        
        # Check for trait-consistent behavior
        if "budget-conscious" in personality_traits:
            if "i don't care about price" in answer_lower or "money is no object" in answer_lower:
                issues.append(ConsistencyIssue(
                    severity="medium",
                    category="attribute",
                    description="Contradicts 'budget-conscious' personality trait",
                    details={"trait": "budget-conscious"}
                ))
        
        if "skeptical" in personality_traits:
            if "i trust everything" in answer_lower or "never doubt" in answer_lower:
                issues.append(ConsistencyIssue(
                    severity="medium",
                    category="attribute",
                    description="Contradicts 'skeptical' personality trait",
                    details={"trait": "skeptical"}
                ))
        
        if "brand-loyal" in personality_traits:
            if "i always switch brands" in answer_lower or "brand doesn't matter" in answer_lower:
                issues.append(ConsistencyIssue(
                    severity="medium",
                    category="attribute",
                    description="Contradicts 'brand-loyal' personality trait",
                    details={"trait": "brand-loyal"}
                ))
        
        return issues
    
    def _check_logical_consistency(
        self, conversation_history: list[dict[str, Any]], new_question: str, new_answer: str
    ) -> list[ConsistencyIssue]:
        """Check for logical consistency within conversation flow."""
        issues: list[ConsistencyIssue] = []
        
        if not conversation_history:
            return issues
        
        # Check for immediate contradictions with the last response
        last_turn = conversation_history[-1]
        last_answer = last_turn.get("answer", "")
        
        if self._are_contradictory(last_answer, new_answer):
            issues.append(ConsistencyIssue(
                severity="high",
                category="logic",
                description="Contradicts immediately preceding statement",
                details={"previous": last_answer, "new": new_answer}
            ))
        
        # Check for contradiction patterns
        for pattern_type, patterns in self.inconsistency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, new_answer, re.IGNORECASE):
                    # This might be fine, but flag it for review
                    issues.append(ConsistencyIssue(
                        severity="low",
                        category="logic",
                        description=f"Contains potential contradiction pattern: {pattern}",
                        details={"pattern": pattern, "pattern_type": pattern_type}
                    ))
        
        return issues
    
    def _are_contradictory(self, statement1: str, statement2: str) -> bool:
        """
        Simple contradiction detection.
        In production, this would use NLP/embeddings for semantic comparison.
        """
        s1_lower = statement1.lower()
        s2_lower = statement2.lower()
        
        # Direct negation pairs
        contradiction_pairs = [
            ("yes", "no"),
            ("always", "never"),
            ("love", "hate"),
            ("good", "bad"),
            ("important", "unimportant"),
            ("would", "wouldn't"),
            ("will", "won't"),
            ("agree", "disagree")
        ]
        
        for word1, word2 in contradiction_pairs:
            if word1 in s1_lower and word2 in s2_lower:
                return True
            if word2 in s1_lower and word1 in s2_lower:
                return True
        
        return False
    
    def calculate_consistency_score(self, issues: list[ConsistencyIssue]) -> float:
        """
        Calculate an overall consistency score (0.0 to 1.0).
        Higher is better.
        """
        if not issues:
            return 1.0
        
        # Weight issues by severity
        severity_weights = {"low": 0.1, "medium": 0.3, "high": 0.6}
        total_penalty = sum(severity_weights.get(issue.severity, 0.3) for issue in issues)
        
        # Cap penalty at 1.0
        total_penalty = min(total_penalty, 1.0)
        
        return max(0.0, 1.0 - total_penalty)
