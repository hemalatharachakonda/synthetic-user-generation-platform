"""
Integration tests for Survey Mode and Memory Consistency (Milestone 2).

These tests validate the end-to-end flow of survey creation, execution,
and response generation with consistency checking.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.survey_agent import SurveyResponseAgent, PersonaResponse
from app.memory.memory_store import MemoryStore, get_memory_store
from app.memory.consistency_checker import ConsistencyChecker
from app.models.experiment import Experiment, ExperimentStatus
from app.models.persona import Persona
from app.models.survey import Survey, SurveyStatus
from app.services.survey_service import SurveyService
from app.services.persona_service import PersonaService


@pytest.mark.asyncio
class TestSurveyIntegration:
    """Integration tests for survey mode functionality."""
    
    async def test_create_survey_for_experiment(self, db_session: AsyncSession):
        """Test creating a survey for an experiment with personas."""
        # Create experiment
        from app.services.experiment_service import ExperimentService
        exp_service = ExperimentService(db_session)
        experiment = await exp_service.create(
            owner_id="test-user",
            payload={
                "title": "Test Experiment",
                "product_description": "Test product",
                "target_audience": "Test audience",
                "research_objectives": "Test objectives",
                "persona_count": 3
            }
        )
        
        # Generate personas
        persona_service = PersonaService(db_session)
        personas = await persona_service.generate_for_experiment(experiment.id, persona_count=3)
        
        # Update experiment status
        experiment.status = ExperimentStatus.PERSONAS_READY
        await exp_service.experiment_repo.commit()
        
        # Create survey
        survey_service = SurveyService(db_session)
        survey = await survey_service.create(
            experiment_id=experiment.id,
            title="Test Survey",
            questions=["Question 1", "Question 2"]
        )
        
        assert survey.id is not None
        assert survey.title == "Test Survey"
        assert survey.status == SurveyStatus.DRAFT
        assert survey.total_personas == 3
        assert len(survey.questions) == 2
    
    async def test_survey_response_generation(self, db_session: AsyncSession):
        """Test generating responses for a survey using the survey agent."""
        agent = SurveyResponseAgent()
        
        # Sample persona
        persona_attrs = {
            "id": "test-persona-1",
            "name": "Test User",
            "age": 30,
            "occupation": "Engineer",
            "location": "San Francisco",
            "income_bracket": "High",
            "education_level": "Master's Degree",
            "personality_traits": ["curious", "analytical"],
            "behavioral_patterns": ["researches before buying"],
            "tech_savviness": "high",
            "daily_habits": ["reads tech news"],
            "core_values": ["innovation", "efficiency"],
            "motivations": ["learning", "improvement"],
            "pain_points": ["complexity", "waste of time"],
            "risk_tolerance": "medium",
            "bio": "Test user bio",
            "persona_hash": "test-hash",
            "consistency_seed": 42
        }
        
        response = await agent.generate_response(
            persona_attributes=persona_attrs,
            question="What do you think about new technology?"
        )
        
        assert isinstance(response, PersonaResponse)
        assert response.answer is not None
        assert len(response.answer) > 0
        assert 0.0 <= response.confidence <= 1.0
    
    async def test_batch_response_generation(self, db_session: AsyncSession):
        """Test generating responses from multiple personas to multiple questions."""
        agent = SurveyResponseAgent()
        
        personas = [
            {
                "id": "p1",
                "name": "Alice",
                "age": 28,
                "occupation": "Designer",
                "tech_savviness": "high",
                "personality_traits": ["creative", "early-adopter"],
                "core_values": ["aesthetics", "innovation"],
                "risk_tolerance": "high",
                "bio": "Creative designer",
                "persona_hash": "hash1",
                "consistency_seed": 100
            },
            {
                "id": "p2",
                "name": "Bob",
                "age": 45,
                "occupation": "Accountant",
                "tech_savviness": "medium",
                "personality_traits": ["pragmatic", "budget-conscious"],
                "core_values": ["reliability", "value"],
                "risk_tolerance": "low",
                "bio": "Careful accountant",
                "persona_hash": "hash2",
                "consistency_seed": 200
            }
        ]
        
        questions = [
            "How do you approach new technology purchases?",
            "What factors influence your buying decisions?"
        ]
        
        responses = await agent.generate_batch_responses(personas, questions)
        
        assert len(responses) == 2  # 2 personas
        assert all(len(resp_list) == 2 for resp_list in responses.values())  # 2 questions each
        assert all(resp.answer for resp_list in responses.values() for resp in resp_list)
    
    async def test_memory_persistence_across_turns(self, db_session: AsyncSession):
        """Test that memory persists across multiple conversation turns."""
        store = MemoryStore()
        
        persona_attrs = {
            "id": "memory-test-persona",
            "name": "Memory Test",
            "age": 35,
            "occupation": "Tester",
            "tech_savviness": "medium",
            "personality_traits": ["analytical"],
            "core_values": ["accuracy"],
            "risk_tolerance": "medium",
            "bio": "Test persona for memory"
        }
        
        # Create memory
        memory = store.get_or_create(
            persona_id="memory-test-persona",
            persona_hash="memory-hash",
            consistency_seed=300,
            attributes=persona_attrs
        )
        
        # Add turns
        memory.add_conversation_turn("Q1", "A1")
        memory.add_conversation_turn("Q2", "A2")
        memory.add_conversation_turn("Q3", "A3")
        
        # Retrieve memory
        retrieved = store.get("memory-test-persona")
        assert retrieved is not None
        assert len(retrieved.conversation_history) == 3
        assert retrieved.conversation_history[0].question == "Q1"
        assert retrieved.conversation_history[2].question == "Q3"
    
    async def test_consistency_validation_integration(self, db_session: AsyncSession):
        """Test consistency validation in the context of survey responses."""
        checker = ConsistencyChecker()
        
        persona_attrs = {
            "age": 25,
            "occupation": "Software Developer",
            "tech_savviness": "high",
            "personality_traits": ["budget-conscious", "skeptical"]
        }
        
        conversation_history = [
            {"question": "How do you feel about price?", "answer": "Price is very important to me, I always compare options."}
        ]
        
        # Consistent response
        score1, issues1 = checker.validate_response_consistency(
            persona_attrs,
            conversation_history,
            "Would you pay more for premium features?",
            "It depends on the value, but I'd need to see clear benefits to justify the cost."
        )
        
        # Should have high consistency score
        assert score1 > 0.7
        
        # Inconsistent response
        score2, issues2 = checker.validate_response_consistency(
            persona_attrs,
            conversation_history,
            "Would you pay more for premium features?",
            "I don't care about price at all, money is no object to me."
        )
        
        # Should have lower consistency score due to contradiction
        assert score2 < score1
        assert len(issues2) > 0


@pytest.mark.asyncio
class TestSurveyAPIContract:
    """Test API contract for survey endpoints."""
    
    async def test_survey_create_request_validation(self):
        """Test that survey creation requests are properly validated."""
        from app.schemas.request.survey import SurveyCreateRequest
        from pydantic import ValidationError
        
        # Valid request
        valid_request = SurveyCreateRequest(
            experiment_id="test-exp-id",
            title="Test Survey",
            questions=["Q1", "Q2", "Q3"]
        )
        assert valid_request.experiment_id == "test-exp-id"
        assert len(valid_request.questions) == 3
        
        # Invalid: no questions
        with pytest.raises(ValidationError):
            SurveyCreateRequest(
                experiment_id="test-exp-id",
                title="Test Survey",
                questions=[]
            )
        
        # Invalid: too many questions
        with pytest.raises(ValidationError):
            SurveyCreateRequest(
                experiment_id="test-exp-id",
                title="Test Survey",
                questions=[f"Q{i}" for i in range(25)]
            )
    
    async def test_survey_response_schema_validation(self):
        """Test that survey response schemas are properly structured."""
        from app.schemas.response.survey import SurveyExecutionResponse, PersonaSurveyResponse
        
        persona_response = PersonaSurveyResponse(
            persona_id="p1",
            persona_name="Alice",
            responses=[
                {"question": "Q1", "answer": "A1", "confidence": 0.9},
                {"question": "Q2", "answer": "A2", "confidence": 0.8}
            ]
        )
        
        execution_response = SurveyExecutionResponse(
            survey_id="survey-1",
            total_personas=2,
            completed_responses=2,
            persona_responses=[persona_response]
        )
        
        assert execution_response.total_personas == 2
        assert len(execution_response.persona_responses) == 1
        assert len(execution_response.persona_responses[0].responses) == 2


@pytest.mark.asyncio
class TestSurveyEdgeCases:
    """Test edge cases and error handling in survey mode."""
    
    async def test_survey_creation_without_personas(self, db_session: AsyncSession):
        """Test that survey creation fails when experiment has no personas."""
        from app.services.experiment_service import ExperimentService
        from app.services.survey_service import SurveyService
        
        exp_service = ExperimentService(db_session)
        survey_service = SurveyService(db_session)
        
        # Create experiment without personas
        experiment = await exp_service.create(
            owner_id="test-user",
            payload={
                "title": "Test Experiment",
                "product_description": "Test product",
                "target_audience": "Test audience",
                "research_objectives": "Test objectives",
                "persona_count": 3
            }
        )
        
        # Try to create survey - should fail
        with pytest.raises(ValueError, match="No personas found"):
            await survey_service.create(
                experiment_id=experiment.id,
                title="Test Survey",
                questions=["Q1"]
            )
    
    async def test_survey_execution_with_llm_fallback(self, db_session: AsyncSession):
        """Test survey execution when LLM is unavailable (fallback mode)."""
        agent = SurveyResponseAgent()
        
        persona_attrs = {
            "id": "fallback-test",
            "name": "Fallback Test",
            "age": 30,
            "occupation": "Worker",
            "tech_savviness": "medium",
            "personality_traits": ["pragmatic"],
            "core_values": ["simplicity"],
            "risk_tolerance": "medium",
            "bio": "Test for fallback"
        }
        
        # This should work even if LLM fails (uses fallback)
        response = await agent.generate_response(
            persona_attributes=persona_attrs,
            question="What do you think?"
        )
        
        assert response is not None
        assert response.answer is not None
        assert len(response.answer) > 0
    
    async def test_memory_store_clear(self, db_session: AsyncSession):
        """Test clearing memory store."""
        store = MemoryStore()
        
        # Add some memories
        store.get_or_create("p1", "h1", 100, {"name": "P1"})
        store.get_or_create("p2", "h2", 200, {"name": "P2"})
        
        assert len(store._memories) == 2
        
        # Clear one
        store.clear("p1")
        assert len(store._memories) == 1
        assert "p1" not in store._memories
        
        # Clear all
        store.clear_all()
        assert len(store._memories) == 0
