"""
Survey Response Agent - generates persona responses to survey questions
while maintaining consistency with persona attributes and conversation history.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from app.ai.llm_client import LLMClient
from app.ai.prompt_manager import PromptManager
from app.memory.consistency_checker import ConsistencyChecker, ConsistencyIssue
from app.memory.memory_store import MemoryStore, get_memory_store


class PersonaResponse(BaseModel):
    """Structured response from a persona to a survey question."""
    persona_id: str
    question: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str | None = None


class SurveyResponseAgent:
    """
    Generates consistent persona responses to survey questions.
    Uses the memory store to maintain conversation context and the
    consistency checker to validate responses.
    """
    
    def __init__(self) -> None:
        self.llm_client = LLMClient()
        self.memory_store: MemoryStore = get_memory_store()
        self.consistency_checker = ConsistencyChecker()
    
    async def generate_response(
        self,
        persona_attributes: dict[str, Any],
        question: str,
        conversation_history: list[dict[str, Any]] | None = None,
        previous_opinions: dict[str, str] | None = None
    ) -> PersonaResponse:
        """
        Generate a response from a persona to a question.
        
        Args:
            persona_attributes: The persona's demographic and behavioral attributes
            question: The survey question to answer
            conversation_history: Previous conversation turns for context
            previous_opinions: Previously expressed opinions for consistency
        
        Returns:
            PersonaResponse with the answer and metadata
        """
        # Build the system prompt with persona context
        system_prompt = self._build_system_prompt(persona_attributes, conversation_history)
        
        # Build the user prompt with the question
        user_prompt = self._build_user_prompt(question, previous_opinions)
        
        try:
            # Generate response using LLM
            result = await self.llm_client.generate_json(system_prompt, user_prompt)
            
            answer = result.get("answer", "")
            confidence = result.get("confidence", 0.8)
            reasoning = result.get("reasoning")
            
            return PersonaResponse(
                persona_id=persona_attributes.get("id", ""),
                question=question,
                answer=answer,
                confidence=confidence,
                reasoning=reasoning
            )
        except Exception as e:
            # Fallback to simple response if LLM fails
            return PersonaResponse(
                persona_id=persona_attributes.get("id", ""),
                question=question,
                answer=self._generate_fallback_response(persona_attributes, question),
                confidence=0.5,
                reasoning="LLM unavailable, using fallback"
            )
    
    def _build_system_prompt(
        self, persona_attributes: dict[str, Any], conversation_history: list[dict[str, Any]] | None
    ) -> str:
        """Build system prompt with persona context and conversation history."""
        prompt = PromptManager.load("survey/system.txt")
        
        # Format persona information
        persona_info = f"""
Name: {persona_attributes.get('name', 'Anonymous')}
Age: {persona_attributes.get('age', 30)}
Occupation: {persona_attributes.get('occupation', 'Unknown')}
Location: {persona_attributes.get('location', 'Unknown')}
Tech Savviness: {persona_attributes.get('tech_savviness', 'medium')}
Personality Traits: {', '.join(persona_attributes.get('personality_traits', []))}
Core Values: {', '.join(persona_attributes.get('core_values', []))}
Bio: {persona_attributes.get('bio', '')}
"""
        
        # Add conversation history if available
        context_section = ""
        if conversation_history:
            context_section = "\n\nPrevious conversation:\n"
            for turn in conversation_history[-3:]:  # Last 3 turns
                context_section += f"Q: {turn.get('question', '')}\n"
                context_section += f"A: {turn.get('answer', '')}\n\n"
        
        return prompt.format(persona_info=persona_info, conversation_context=context_section)
    
    def _build_user_prompt(self, question: str, previous_opinions: dict[str, str] | None) -> str:
        """Build user prompt with the question and any relevant previous opinions."""
        prompt = PromptManager.load("survey/user.txt")
        
        opinions_section = ""
        if previous_opinions:
            # Find relevant previous opinions
            relevant_opinions = {
                k: v for k, v in previous_opinions.items()
                if any(word in question.lower() for word in k.lower().split())
            }
            if relevant_opinions:
                opinions_section = "\n\nYour previous opinions on related topics:\n"
                for topic, opinion in relevant_opinions.items():
                    opinions_section += f"- {topic}: {opinion}\n"
        
        return prompt.format(question=question, previous_opinions=opinions_section)
    
    def _generate_fallback_response(self, persona_attributes: dict[str, Any], question: str) -> str:
        """Generate a simple fallback response when LLM is unavailable."""
        traits = persona_attributes.get('personality_traits', [])
        name = persona_attributes.get('name', 'I')
        
        if 'budget-conscious' in traits:
            return f"As someone who watches their spending carefully, {name} would consider the price carefully before making a decision about this."
        elif 'skeptical' in traits:
            return f"{name} would need to see more evidence and reviews before forming a strong opinion on this."
        elif 'early-adopter' in traits:
            return f"{name} is usually excited to try new things and would be interested in learning more."
        else:
            return f"{name} would consider this carefully based on their needs and circumstances."
    
    async def generate_batch_responses(
        self,
        personas: list[dict[str, Any]],
        questions: list[str]
    ) -> dict[str, list[PersonaResponse]]:
        """
        Generate responses from all personas to all questions.
        
        Args:
            personas: List of persona attribute dictionaries
            questions: List of survey questions
        
        Returns:
            Dictionary mapping persona_id to list of responses
        """
        results: dict[str, list[PersonaResponse]] = {}
        
        for persona in personas:
            persona_id = persona.get("id", "")
            results[persona_id] = []
            
            # Get or create memory for this persona
            memory = self.memory_store.get_or_create(
                persona_id=persona_id,
                persona_hash=persona.get("persona_hash", ""),
                consistency_seed=persona.get("consistency_seed", 0),
                attributes=persona
            )
            
            for question in questions:
                # Get conversation context
                conversation_context = memory.get_conversation_context(max_turns=3)
                previous_opinions = memory.expressed_opinions
                
                # Generate response
                response = await self.generate_response(
                    persona_attributes=persona,
                    question=question,
                    conversation_history=conversation_context,
                    previous_opinions=previous_opinions
                )
                
                # Update memory with this interaction
                memory.add_conversation_turn(
                    question=question,
                    answer=response.answer,
                    metadata={"confidence": response.confidence}
                )
                
                # Check consistency
                issues = self.consistency_checker.check_response_consistency(
                    persona_attributes=persona,
                    previous_opinions=previous_opinions,
                    conversation_history=conversation_context,
                    new_question=question,
                    new_answer=response.answer
                )
                
                # Store consistency info in response metadata
                response.reasoning = response.reasoning or ""
                if issues:
                    response.reasoning += f" | Consistency issues: {len(issues)}"
                
                results[persona_id].append(response)
            
            # Update memory store
            self.memory_store.update(memory)
        
        return results
    
    def validate_response_consistency(
        self,
        persona_attributes: dict[str, Any],
        conversation_history: list[dict[str, Any]],
        new_question: str,
        new_answer: str
    ) -> tuple[float, list[ConsistencyIssue]]:
        """
        Validate a response for consistency and return score with issues.
        
        Returns:
            Tuple of (consistency_score, list_of_issues)
        """
        # Get previous opinions from conversation history
        previous_opinions: dict[str, str] = {}
        for turn in conversation_history:
            topic = turn.get("question", "")[:50]  # Simple topic extraction
            previous_opinions[topic] = turn.get("answer", "")
        
        issues = self.consistency_checker.check_response_consistency(
            persona_attributes=persona_attributes,
            previous_opinions=previous_opinions,
            conversation_history=conversation_history,
            new_question=new_question,
            new_answer=new_answer
        )
        
        score = self.consistency_checker.calculate_consistency_score(issues)
        
        return score, issues
