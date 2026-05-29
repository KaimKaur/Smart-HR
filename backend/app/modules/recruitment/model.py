from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.database.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.employee.model import Department, Employee
    from app.modules.user.model import User

JOB_STATUS_CHECK = "status IN ('draft','published','closed')"
AI_SCORE_CHECK = "ai_score BETWEEN 0 AND 100"
APPLICATION_STATUS_CHECK = (
    "application_status IN ("
    "'applied','screening','shortlisted',"
    "'interview_scheduled','interviewed',"
    "'offered','rejected','withdrawn'"
    ")"
)
CANDIDATE_STATUS_CHECK = (
    "current_status IN ("
    "'applied','screening','shortlisted',"
    "'interview_scheduled','interviewed',"
    "'offered','rejected','withdrawn'"
    ") OR current_status IS NULL"
)
ANALYSIS_STATUS_CHECK = (
    "analysis_status IN ('pending','processing','complete','failed')"
)
RESUME_SCORE_CHECK = "score BETWEEN 0 AND 100"
INTERVIEW_STATUS_CHECK = (
    "status IN ('scheduled','completed','cancelled','no_show')"
)


class Job(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (CheckConstraint(JOB_STATUS_CHECK, name="chk_job_status"),)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id")
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    department: Mapped[Department | None] = relationship()
    creator: Mapped[User | None] = relationship()
    skills: Mapped[list[JobSkill]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
    applications: Mapped[list[CandidateApplication]] = relationship(
        back_populates="job",
    )


class JobSkill(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "job_skills"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(150), nullable=False)

    job: Mapped[Job] = relationship(back_populates="skills")


class Candidate(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "candidates"
    __table_args__ = (
        CheckConstraint(CANDIDATE_STATUS_CHECK, name="chk_candidate_current_status"),
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    current_status: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    applications: Mapped[list[CandidateApplication]] = relationship(
        back_populates="candidate",
    )
    resume_files: Mapped[list[ResumeFile]] = relationship(back_populates="candidate")
    resume_analyses: Mapped[list[ResumeAnalysis]] = relationship(
        back_populates="candidate",
    )
    notes: Mapped[list[CandidateNote]] = relationship(back_populates="candidate")


class CandidateApplication(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "candidate_applications"
    __table_args__ = (
        CheckConstraint(AI_SCORE_CHECK, name="chk_ai_score"),
        CheckConstraint(APPLICATION_STATUS_CHECK, name="chk_application_status"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False
    )
    ai_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    ranking: Mapped[int | None] = mapped_column(Integer)
    recommendation: Mapped[str | None] = mapped_column(String(50))
    recruiter_override: Mapped[bool] = mapped_column(
        Boolean, server_default=false(), nullable=False
    )
    application_status: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    candidate: Mapped[Candidate] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(back_populates="applications")
    status_history: Mapped[list[CandidateStatusHistory]] = relationship(
        back_populates="application",
    )
    resume_analyses: Mapped[list[ResumeAnalysis]] = relationship(
        back_populates="application",
    )
    interviews: Mapped[list[Interview]] = relationship(back_populates="application")


class CandidateStatusHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "candidate_status_history"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_applications.id"),
        nullable=False,
    )
    old_status: Mapped[str | None] = mapped_column(String(100))
    new_status: Mapped[str] = mapped_column(String(100), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    application: Mapped[CandidateApplication] = relationship(
        back_populates="status_history",
    )
    changed_by_user: Mapped[User | None] = relationship()


class ResumeFile(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "resume_files"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    candidate: Mapped[Candidate] = relationship(back_populates="resume_files")


class ResumeAnalysis(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "resume_analysis"
    __table_args__ = (
        CheckConstraint(ANALYSIS_STATUS_CHECK, name="chk_analysis_status"),
        CheckConstraint(RESUME_SCORE_CHECK, name="chk_resume_score"),
    )

    analysis_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="pending"
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_applications.id"),
        nullable=False,
    )
    extracted_skills: Mapped[dict] = mapped_column(JSONB, nullable=False)
    matched_skills: Mapped[dict] = mapped_column(JSONB, nullable=False)
    missing_skills: Mapped[dict] = mapped_column(JSONB, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    recommendation: Mapped[str | None] = mapped_column(String(50))
    explanation: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    candidate: Mapped[Candidate] = relationship(back_populates="resume_analyses")
    application: Mapped[CandidateApplication] = relationship(
        back_populates="resume_analyses",
    )


class CandidateNote(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "candidate_notes"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    candidate: Mapped[Candidate] = relationship(back_populates="notes")
    author: Mapped[User | None] = relationship()


class Interview(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "interviews"
    __table_args__ = (
        CheckConstraint(INTERVIEW_STATUS_CHECK, name="chk_interview_status"),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_applications.id"),
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id")
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="scheduled"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    application: Mapped[CandidateApplication] = relationship(back_populates="interviews")
    interviewer: Mapped[Employee | None] = relationship()
    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by])
