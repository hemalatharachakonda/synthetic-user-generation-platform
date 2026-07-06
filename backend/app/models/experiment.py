"""
Experiment = one "workspace" a user creates to validate a product idea.
Holds the product description, target audience, and research objectives
that drive persona generation, survey/interview modes, and insight extraction.
"""
from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"                 # workspace created, personas not yet generated
    PERSONAS_READY = "personas_ready"  # persona generation complete
    RUNNING = "running"             # survey/interview in progress
    COMPLETED = "completed"         # insights + report generated
    ARCHIVED = "archived"


class Experiment(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "experiments"

    owner_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # --- Experiment Workspace fields (Milestone 1, item 3) ---
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    research_objectives: Mapped[str] = mapped_column(Text, nullable=False)

    persona_count: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), default=ExperimentStatus.DRAFT, nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="experiments")  # noqa: F821
    personas: Mapped[list["Persona"]] = relationship(  # noqa: F821
        back_populates="experiment", cascade="all, delete-orphan"
    )
    surveys: Mapped[list["Survey"]] = relationship(back_populates="experiment", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Experiment id={self.id} title={self.title!r} status={self.status}>"
