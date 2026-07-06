from pydantic import BaseModel, Field


class SurveyCreateRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment to create survey for")
    title: str = Field(..., min_length=1, max_length=200, description="Survey title")
    description: str | None = Field(None, description="Optional survey description")
    questions:list[str] = Field(..., min_items=1, max_items=20, description="Survey questions")


class SurveyUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = Field(None, description="Survey status: draft, active, completed, archived")


class SurveyExecuteRequest(BaseModel):
    survey_id: str = Field(..., description="Survey to execute")
    regenerate: bool = Field(default=False, description="Regenerate responses if they exist")
