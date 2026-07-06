from pydantic import BaseModel, ConfigDict
from typing import Any


class SurveyResponse(BaseModel):
    """Survey response for API clients."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_id: str
    title: str
    description: str | None
    questions: list[str]
    status: str
    total_personas: int
    completed_responses: int
    created_at: str
    updated_at: str


class SurveyListResponse(BaseModel):
    total: int
    experiment_id: str
    items: list[SurveyResponse]


class PersonaSurveyResponse(BaseModel):
    """Response from a single persona to survey questions."""
    persona_id: str
    persona_name: str
    responses: list[dict[str, Any]]


class SurveyExecutionResponse(BaseModel):
    """Result of executing a survey across all personas."""
    survey_id: str
    total_personas: int
    completed_responses: int
    persona_responses: list[PersonaSurveyResponse]
