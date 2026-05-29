from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.database.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

CYCLE_DATES_CHECK = "end_date >= start_date"
RATING_CHECK = "rating BETWEEN 1 AND 5"
METRIC_SCORE_CHECK = "score BETWEEN 0 AND 100"


class PerformanceCycle(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "performance_cycles"
    __table_args__ = (CheckConstraint(CYCLE_DATES_CHECK, name="chk_cycle_dates"),)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    reviews: Mapped[list[PerformanceReview]] = relationship(back_populates="cycle")
    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by])


class PerformanceReview(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "performance_reviews"
    __table_args__ = (
        CheckConstraint(RATING_CHECK, name="chk_rating"),
        UniqueConstraint(
            "cycle_id",
            "employee_id",
            "reviewer_id",
            name="uq_review_cycle_employee_reviewer",
        ),
    )

    cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("performance_cycles.id"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    rating: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    cycle: Mapped[PerformanceCycle] = relationship(back_populates="reviews")
    employee: Mapped[Employee] = relationship(foreign_keys=[employee_id])
    reviewer: Mapped[Employee] = relationship(foreign_keys=[reviewer_id])
    metric_scores: Mapped[list[EmployeeMetricScore]] = relationship(
        back_populates="review",
    )
    feedback_entries: Mapped[list[PerformanceFeedback]] = relationship(
        back_populates="review",
    )


class PerformanceMetric(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "performance_metrics"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    scores: Mapped[list[EmployeeMetricScore]] = relationship(back_populates="metric")
    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by])


class EmployeeMetricScore(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "employee_metric_scores"
    __table_args__ = (CheckConstraint(METRIC_SCORE_CHECK, name="chk_metric_score"),)

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("performance_reviews.id"), nullable=False
    )
    metric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("performance_metrics.id"), nullable=False
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    review: Mapped[PerformanceReview] = relationship(back_populates="metric_scores")
    metric: Mapped[PerformanceMetric] = relationship(back_populates="scores")
    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by])


class PerformanceFeedback(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "performance_feedback"

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("performance_reviews.id"), nullable=False
    )
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    review: Mapped[PerformanceReview] = relationship(back_populates="feedback_entries")
    author: Mapped[Employee] = relationship()
