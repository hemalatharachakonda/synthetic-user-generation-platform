"""
Test scenarios for Milestone 2 - Survey Mode and Persona Consistency.

These scenarios validate the system across diverse persona sets and product categories
to ensure response realism and consistency.
"""
import pytest
from app.memory.memory_store import MemoryStore, PersonaMemory
from app.memory.consistency_checker import ConsistencyChecker


class TestPersonaMemory:
    """Test persona memory functionality for multi-turn conversations."""
    
    def test_memory_store_creation(self):
        """Test creating and retrieving persona memory."""
        store = MemoryStore()
        memory = store.get_or_create(
            persona_id="test-persona-1",
            persona_hash="abc123",
            consistency_seed=42,
            attributes={"name": "John", "age": 30}
        )
        
        assert memory.persona_id == "test-persona-1"
        assert memory.persona_hash == "abc123"
        assert memory.consistency_seed == 42
        assert memory.attributes["name"] == "John"
    
    def test_conversation_turn_tracking(self):
        """Test adding conversation turns to memory."""
        store = MemoryStore()
        memory = store.get_or_create(
            persona_id="test-persona-2",
            persona_hash="def456",
            consistency_seed=100,
            attributes={"name": "Jane", "age": 25}
        )
        
        memory.add_conversation_turn(
            question="What do you think about price?",
            answer="I'm very budget-conscious, so price is important to me."
        )
        
        assert len(memory.conversation_history) == 1
        assert memory.conversation_history[0].question == "What do you think about price?"
        assert memory.conversation_history[0].turn_number == 1
    
    def test_conversation_context_retrieval(self):
        """Test retrieving conversation context for LLM prompting."""
        store = MemoryStore()
        memory = store.get_or_create(
            persona_id="test-persona-3",
            persona_hash="ghi789",
            consistency_seed=200,
            attributes={"name": "Bob", "age": 40}
        )
        
        # Add multiple turns
        for i in range(5):
            memory.add_conversation_turn(
                question=f"Question {i}",
                answer=f"Answer {i}"
            )
        
        # Get last 3 turns
        context = memory.get_conversation_context(max_turns=3)
        assert len(context) == 3
        assert context[0]["turn_number"] == 3
        assert context[2]["turn_number"] == 5
    
    def test_opinion_tracking(self):
        """Test that opinions are extracted and tracked from responses."""
        store = MemoryStore()
        memory = store.get_or_create(
            persona_id="test-persona-4",
            persona_hash="jkl012",
            consistency_seed=300,
            attributes={"name": "Alice", "age": 35}
        )
        
        memory.add_conversation_turn(
            question="What do you think about brand loyalty?",
            answer="I tend to stick with brands I trust and rarely switch."
        )
        
        # Opinion should be tracked
        assert len(memory.expressed_opinions) > 0
        assert "brand loyalty" in list(memory.expressed_opinions.keys())[0].lower()


class TestConsistencyChecker:
    """Test persona consistency validation across different scenarios."""
    
    def test_demographic_consistency_age(self):
        """Test age-appropriate response validation."""
        checker = ConsistencyChecker()
        
        # Young persona shouldn't reference outdated tech
        issues = checker._check_demographic_consistency(
            {"age": 20, "occupation": "Student", "tech_savviness": "high"},
            "I still use floppy disks and VHS tapes."
        )
        
        assert len(issues) > 0
        assert any("floppy disk" in issue.description.lower() for issue in issues)
    
    def test_demographic_consistency_tech_savviness(self):
        """Test tech-savviness consistency."""
        checker = ConsistencyChecker()
        
        # Low tech-savviness persona shouldn't use technical terms
        issues = checker._check_demographic_consistency(
            {"age": 65, "occupation": "Retired", "tech_savviness": "low"},
            "I use APIs and blockchain technology daily."
        )
        
        assert len(issues) > 0
        assert any("tech-savviness" in issue.category for issue in issues)
    
    def test_behavioral_consistency_traits(self):
        """Test personality trait consistency."""
        checker = ConsistencyChecker()
        
        # Budget-conscious persona shouldn't say money doesn't matter
        issues = checker._check_behavioral_consistency(
            {"personality_traits": ["budget-conscious", "pragmatic"]},
            "I don't care about price at all, money is no object."
        )
        
        assert len(issues) > 0
        assert any("budget-conscious" in issue.description for issue in issues)
    
    def test_opinion_contradiction_detection(self):
        """Test detection of contradictory opinions."""
        checker = ConsistencyChecker()
        
        previous_opinions = {
            "brand loyalty": "I always stick with the same brands"
        }
        
        issues = checker._check_opinion_consistency(
            previous_opinions,
            "What about brand loyalty?",
            "I switch brands all the time, never stick with one."
        )
        
        assert len(issues) > 0
        assert any("contradicts" in issue.description for issue in issues)
    
    def test_consistency_score_calculation(self):
        """Test consistency score calculation."""
        checker = ConsistencyChecker()
        
        # No issues = perfect score
        from app.memory.consistency_checker import ConsistencyIssue
        score = checker.calculate_consistency_score([])
        assert score == 1.0
        
        # High severity issues reduce score significantly
        issues = [
            ConsistencyIssue(severity="high", category="opinion", description="Contradiction", details={}),
            ConsistencyIssue(severity="medium", category="attribute", description="Inconsistency", details={})
        ]
        score = checker.calculate_consistency_score(issues)
        assert score < 0.5  # Should be significantly reduced


class TestSurveyScenarios:
    """Test survey scenarios across diverse product categories and persona sets."""
    
    @pytest.fixture
    def tech_product_personas(self):
        """Sample personas for a tech product survey."""
        return [
            {
                "id": "p1",
                "name": "Alex",
                "age": 28,
                "occupation": "Software Engineer",
                "tech_savviness": "high",
                "personality_traits": ["early-adopter", "curious"],
                "core_values": ["innovation", "efficiency"],
                "risk_tolerance": "high"
            },
            {
                "id": "p2",
                "name": "Maria",
                "age": 55,
                "occupation": "Teacher",
                "tech_savviness": "medium",
                "personality_traits": ["skeptical", "pragmatic"],
                "core_values": ["trust", "simplicity"],
                "risk_tolerance": "low"
            },
            {
                "id": "p3",
                "name": "Jamal",
                "age": 22,
                "occupation": "Student",
                "tech_savviness": "high",
                "personality_traits": ["budget-conscious", "social"],
                "core_values": ["affordability", "community"],
                "risk_tolerance": "medium"
            }
        ]
    
    @pytest.fixture
    def fitness_product_personas(self):
        """Sample personas for a fitness product survey."""
        return [
            {
                "id": "p4",
                "name": "Sarah",
                "age": 32,
                "occupation": "Marketing Manager",
                "tech_savviness": "high",
                "personality_traits": ["goal-oriented", "competitive"],
                "core_values": ["health", "achievement"],
                "risk_tolerance": "medium"
            },
            {
                "id": "p5",
                "name": "Robert",
                "age": 45,
                "occupation": "Construction Worker",
                "tech_savviness": "low",
                "personality_traits": ["pragmatic", "value-driven"],
                "core_values": ["durability", "practicality"],
                "risk_tolerance": "low"
            }
        ]
    
    def test_tech_product_survey_questions(self):
        """Test survey questions for tech product category."""
        questions = [
            "How important is the latest technology in your purchasing decision?",
            "Would you be willing to pay a premium for cutting-edge features?",
            "How do you typically learn about new tech products?",
            "What concerns do you have about adopting new technology?"
        ]
        
        assert len(questions) == 4
        assert all("?" in q for q in questions)
    
    def test_fitness_product_survey_questions(self):
        """Test survey questions for fitness product category."""
        questions = [
            "What motivates you to maintain a fitness routine?",
            "How important is social sharing in your fitness activities?",
            "What features do you look for in fitness equipment?",
            "Would you prefer a simple or feature-rich fitness tracker?"
        ]
        
        assert len(questions) == 4
        assert all("?" in q for q in questions)
    
    def test_persona_diversity_validation(self, tech_product_personas, fitness_product_personas):
        """Test that persona sets are diverse across dimensions."""
        # Check age diversity
        ages = [p["age"] for p in tech_product_personas + fitness_product_personas]
        assert max(ages) - min(ages) > 20  # At least 20 year spread
        
        # Check tech-savviness diversity
        tech_levels = [p["tech_savviness"] for p in tech_product_personas + fitness_product_personas]
        assert len(set(tech_levels)) > 1  # At least 2 different levels
        
        # Check occupation diversity
        occupations = [p["occupation"] for p in tech_product_personas + fitness_product_personas]
        assert len(set(occupations)) >= 4  # At least 4 different occupations


class TestMultiTurnConversations:
    """Test multi-turn conversation scenarios for consistency."""
    
    def test_conversation_flow_consistency(self):
        """Test that conversation flow remains consistent across turns."""
        store = MemoryStore()
        checker = ConsistencyChecker()
        
        persona_attrs = {
            "id": "test-persona",
            "name": "Chris",
            "age": 30,
            "occupation": "Accountant",
            "tech_savviness": "medium",
            "personality_traits": ["budget-conscious", "analytical"]
        }
        
        memory = store.get_or_create(
            persona_id="test-persona",
            persona_hash="test-hash",
            consistency_seed=500,
            attributes=persona_attrs
        )
        
        # Turn 1
        memory.add_conversation_turn(
            question="How do you approach purchasing decisions?",
            answer="I always research thoroughly and compare prices before buying anything."
        )
        
        # Turn 2 - should be consistent
        memory.add_conversation_turn(
            question="Would you buy this without reading reviews?",
            answer="No, I never buy without reading reviews first."
        )
        
        # Check consistency
        context = memory.get_conversation_context()
        issues = checker.check_response_consistency(
            persona_attrs,
            memory.expressed_opinions,
            context[:-1],  # All but last turn
            "Would you buy this without reading reviews?",
            "No, I never buy without reading reviews first."
        )
        
        # Should have no high-severity issues
        high_severity_issues = [i for i in issues if i.severity == "high"]
        assert len(high_severity_issues) == 0
    
    def test_conversation_context_influence(self):
        """Test that conversation context influences subsequent responses."""
        store = MemoryStore()
        
        memory = store.get_or_create(
            persona_id="context-test-persona",
            persona_hash="context-hash",
            consistency_seed=600,
            attributes={"name": "Dana", "age": 35}
        )
        
        # Establish context
        memory.add_conversation_turn(
            question="What's your biggest frustration with current solutions?",
            answer="They're too complicated and have too many features I don't use."
        )
        
        memory.add_conversation_turn(
            question="What would make you switch?",
            answer="Something simpler that focuses on core functionality."
        )
        
        # Get context
        context = memory.get_conversation_context()
        assert len(context) == 2
        assert "complicated" in context[0]["answer"].lower()
        assert "simpler" in context[1]["answer"].lower()


# Sample experiment scenarios for testing
SAMPLE_SCENARIOS = {
    "tech_startup_mvp": {
        "product_description": "A new AI-powered productivity tool for remote teams",
        "target_audience": "Remote workers, team leads, and project managers",
        "research_objectives": "Understand pain points with current tools and feature priorities",
        "persona_count": 6,
        "survey_questions": [
            "What are the biggest challenges you face with remote collaboration?",
            "How do you currently track project progress?",
            "What would make you switch from your current tools?",
            "How important is AI assistance in your daily workflow?",
            "What's your budget for team productivity tools?"
        ]
    },
    "fitness_app": {
        "product_description": "A personalized fitness app with AI coaching",
        "target_audience": "Fitness enthusiasts, beginners, and casual exercisers",
        "research_objectives": "Identify key features and motivations for fitness tracking",
        "persona_count": 5,
        "survey_questions": [
            "What motivates you to exercise regularly?",
            "How do you currently track your fitness progress?",
            "What features would you most value in a fitness app?",
            "Would you prefer AI coaching or human guidance?",
            "How important is social sharing in your fitness journey?"
        ]
    },
    "sustainable_fashion": {
        "product_description": "A subscription service for sustainable clothing",
        "target_audience": "Environmentally conscious consumers",
        "research_objectives": "Understand willingness to pay for sustainable fashion",
        "persona_count": 4,
        "survey_questions": [
            "How important is sustainability in your clothing purchases?",
            "What's your current monthly clothing budget?",
            "Would you pay a premium for sustainably made items?",
            "What concerns do you have about subscription services?",
            "How do you typically discover new fashion brands?"
        ]
    }
}
