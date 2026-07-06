"""
Persona Memory Store - maintains consistent attributes, opinions, and conversation
context across multi-turn interactions for each persona.
"""
from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ConversationTurn:
    """Single turn in a conversation with a persona."""
    question: str
    answer: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    turn_number: int = 0


@dataclass
class PersonaMemory:
    """
    In-memory representation of a persona's state across interactions.
    Maintains consistency by tracking:
    - Static attributes (from persona profile)
    - Opinion consistency (expressed views on topics)
    - Conversation history (for context-aware responses)
    """
    persona_id: str
    persona_hash: str
    consistency_seed: int
    
    # Static persona attributes (immutable)
    attributes: dict[str, Any] = field(default_factory=dict)
    
    # Opinion tracking (what the persona has expressed about topics)
    expressed_opinions: dict[str, str] = field(default_factory=dict)
    
    # Conversation history
    conversation_history: list[ConversationTurn] = field(default_factory=list)
    
    # Session metadata
    session_start: datetime = field(default_factory=datetime.utcnow)
    last_interaction: datetime = field(default_factory=datetime.utcnow)
    
    def add_conversation_turn(self, question: str, answer: str, metadata: dict[str, Any] | None = None) -> None:
        """Add a new conversation turn to memory."""
        turn_number = len(self.conversation_history) + 1
        turn = ConversationTurn(
            question=question,
            answer=answer,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            turn_number=turn_number
        )
        self.conversation_history.append(turn)
        self.last_interaction = datetime.utcnow()
        
        # Extract and track opinions from the answer
        self._extract_opinions(question, answer)
    
    def _extract_opinions(self, question: str, answer: str) -> None:
        """
        Simple opinion extraction - in production this would use NLP.
        For now, we store the question-answer pair as an opinion entry.
        """
        # Create a simple key from the question topic
        topic_key = self._normalize_topic(question)
        if topic_key:
            self.expressed_opinions[topic_key] = answer
    
    def _normalize_topic(self, question: str) -> str:
        """Extract a simple topic key from a question."""
        # Remove common question words and lowercase
        question = question.lower()
        for word in ["what", "how", "why", "do", "does", "is", "are", "would", "could", "should", "?"]:
            question = question.replace(word, "")
        return question.strip()[:50]  # First 50 chars as topic key
    
    def get_conversation_context(self, max_turns: int = 5) -> list[dict[str, Any]]:
        """
        Get recent conversation context for generating consistent responses.
        Returns the last N turns formatted for LLM prompting.
        """
        recent_turns = self.conversation_history[-max_turns:]
        return [
            {
                "turn_number": turn.turn_number,
                "question": turn.question,
                "answer": turn.answer,
                "timestamp": turn.timestamp.isoformat()
            }
            for turn in recent_turns
        ]
    
    def get_opinion_on_topic(self, topic: str) -> str | None:
        """Get previously expressed opinion on a topic."""
        normalized = self._normalize_topic(topic)
        return self.expressed_opinions.get(normalized)
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize memory to dictionary for storage/transmission."""
        return {
            "persona_id": self.persona_id,
            "persona_hash": self.persona_hash,
            "consistency_seed": self.consistency_seed,
            "attributes": self.attributes,
            "expressed_opinions": self.expressed_opinions,
            "conversation_history": [
                {
                    "question": turn.question,
                    "answer": turn.answer,
                    "timestamp": turn.timestamp.isoformat(),
                    "metadata": turn.metadata,
                    "turn_number": turn.turn_number
                }
                for turn in self.conversation_history
            ],
            "session_start": self.session_start.isoformat(),
            "last_interaction": self.last_interaction.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PersonaMemory:
        """Deserialize memory from dictionary."""
        conversation_history = [
            ConversationTurn(
                question=turn["question"],
                answer=turn["answer"],
                timestamp=datetime.fromisoformat(turn["timestamp"]),
                metadata=turn.get("metadata", {}),
                turn_number=turn.get("turn_number", 0)
            )
            for turn in data.get("conversation_history", [])
        ]
        
        return cls(
            persona_id=data["persona_id"],
            persona_hash=data["persona_hash"],
            consistency_seed=data["consistency_seed"],
            attributes=data.get("attributes", {}),
            expressed_opinions=data.get("expressed_opinions", {}),
            conversation_history=conversation_history,
            session_start=datetime.fromisoformat(data["session_start"]),
            last_interaction=datetime.fromisoformat(data["last_interaction"])
        )


class MemoryStore:
    """
    Central store for persona memories. In production, this would use Redis
    or a database for persistence. For now, we use an in-memory store.
    """
    def __init__(self) -> None:
        self._memories: dict[str, PersonaMemory] = {}
    
    def get_or_create(self, persona_id: str, persona_hash: str, consistency_seed: int, 
                     attributes: dict[str, Any] | None = None) -> PersonaMemory:
        """Get existing memory or create new one for a persona."""
        if persona_id not in self._memories:
            self._memories[persona_id] = PersonaMemory(
                persona_id=persona_id,
                persona_hash=persona_hash,
                consistency_seed=consistency_seed,
                attributes=attributes or {}
            )
        return self._memories[persona_id]
    
    def get(self, persona_id: str) -> PersonaMemory | None:
        """Get memory for a persona if it exists."""
        return self._memories.get(persona_id)
    
    def update(self, memory: PersonaMemory) -> None:
        """Update memory for a persona."""
        self._memories[memory.persona_id] = memory
    
    def clear(self, persona_id: str) -> None:
        """Clear memory for a persona."""
        if persona_id in self._memories:
            del self._memories[persona_id]
    
    def clear_all(self) -> None:
        """Clear all memories (useful for testing)."""
        self._memories.clear()


# Global memory store instance
_memory_store = MemoryStore()


def get_memory_store() -> MemoryStore:
    """Get the global memory store instance."""
    return _memory_store
