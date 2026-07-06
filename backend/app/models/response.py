from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
import uuid


class Response(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "responses"

    persona_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Survey/experiment context
    survey_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=True, index=True
    )
    
    # Question and answer
    question_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Conversation context for multi-turn interactions
    turn_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    conversation_context: Mapped[dict[str, any]] = mapped_column(JSON, default=list)
    
    # Consistency tracking
    consistency_score: Mapped[float | None] = mapped_column(Integer, nullable=True)
    consistency_issues: Mapped[dict[str, any]] = mapped_column(JSON, default=list)
    
    # Response metadata
    response_metadata: Mapped[dict[str, any]] = mapped_column(JSON, default={})
    
    # Relationships
    persona: Mapped["Persona"] = relationship(back_populates="responses")  # noqa: F821
    survey: Mapped["Survey"] = relationship(back_populates="responses")  # noqa: F821

    def __repr__(self):
        return f"<Response persona={self.persona_id} turn={self.turn_number} q={self.question_text[:30]}>"