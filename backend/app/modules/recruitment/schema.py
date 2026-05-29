from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.schemas import PaginatedResponse, PaginationMeta

JobStatus = Literal["draft", "published", "closed"]
ApplicationStatus = Literal[
    "applied",
    "screening",
    "shortlisted",
    "interview_scheduled",
    "interviewed",
    "offered",
    "rejected",
    "withdrawn",
]
InterviewStatus = Literal["scheduled", "completed", "cancelled", "no_show"]


class CreateJobRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    department_id: UUID | None = None
    description: str = Field(min_length=1)
    skills: list[str] = Field(default_factory=list)

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str]) -> list[str]:
        return [skill.strip() for skill in value if skill.strip()]


class UpdateJobRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    department_id: UUID | None = None
    description: str | None = Field(default=None, min_length=1)
    skills: list[str] | None = None

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [skill.strip() for skill in value if skill.strip()]


class JobResponse(BaseModel):
    id: UUID
    title: str
    department_id: UUID | None
    department_name: str | None = None
    description: str
    status: JobStatus
    skills: list[str]
    created_by: UUID | None
    created_by_name: str | None = None
    created_at: datetime
    updated_at: datetime


class JobListResponse(PaginatedResponse[JobResponse]):
    pass


class CreateCandidateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    job_id: UUID | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class CandidateResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None
    current_status: str | None
    created_at: datetime


class CandidateListResponse(PaginatedResponse[CandidateResponse]):
    pass


class CreateApplicationRequest(BaseModel):
    candidate_id: UUID
    job_id: UUID


class ApplicationResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    candidate_name: str
    candidate_email: str
    job_id: UUID
    job_title: str
    application_status: ApplicationStatus
    ai_score: Decimal | None = None
    ranking: int | None = None
    recommendation: str | None = None
    recruiter_override: bool
    created_at: datetime


class ApplicationListResponse(PaginatedResponse[ApplicationResponse]):
    pass


class CandidateStatusUpdateRequest(BaseModel):
    status: ApplicationStatus
    remarks: str | None = None


class CandidateTimelineItem(BaseModel):
    old_status: str | None
    new_status: str
    changed_at: datetime
    changed_by: UUID | None
    changed_by_name: str | None = None


class CandidateTimelineResponse(BaseModel):
    application_id: UUID
    items: list[CandidateTimelineItem]


class JobCandidateRow(BaseModel):
    application_id: UUID
    candidate_id: UUID
    full_name: str
    email: str
    application_status: ApplicationStatus
    ai_score: Decimal | None = None
    ranking: int | None = None
    recommendation: str | None = None
    matched_skills: list[Any] | None = None
    missing_skills: list[Any] | None = None


class JobCandidateListResponse(PaginatedResponse[JobCandidateRow]):
    pass


class CandidateRankingRow(JobCandidateRow):
    score: Decimal | None = None


class CandidateRankingResponse(PaginatedResponse[CandidateRankingRow]):
    pass


class ManualOverrideRequest(BaseModel):
    status: ApplicationStatus
    remarks: str | None = None


class ResumeUploadResponse(BaseModel):
    resume_file_id: UUID
    file_url: str
    file_name: str


class CreateNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=5000)


class NoteResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    note: str
    created_by: UUID | None
    created_by_name: str | None = None
    created_at: datetime


class NoteListResponse(BaseModel):
    items: list[NoteResponse]


class ResumeAnalysisResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    application_id: UUID
    analysis_status: str
    extracted_skills: list[Any] | dict
    matched_skills: list[Any] | dict
    missing_skills: list[Any] | dict
    score: Decimal
    recommendation: str | None
    explanation: dict | list | str | None = None
    created_at: datetime


class AnalysisResultRow(BaseModel):
    application_id: UUID
    candidate_id: UUID
    candidate_name: str
    application_status: ApplicationStatus
    ai_score: Decimal | None = None
    score: Decimal | None = None
    recommendation: str | None = None
    matched_skills: list[Any] | dict | None = None
    missing_skills: list[Any] | dict | None = None


class AnalysisResultsResponse(PaginatedResponse[AnalysisResultRow]):
    pass


class ScheduleInterviewRequest(BaseModel):
    application_id: UUID
    scheduled_at: datetime
    interviewer_id: UUID | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def scheduled_in_future(self) -> "ScheduleInterviewRequest":
        from datetime import UTC

        scheduled = self.scheduled_at
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=UTC)
        if scheduled <= datetime.now(UTC):
            raise ValueError("scheduled_at must be in the future")
        return self


class UpdateInterviewRequest(BaseModel):
    scheduled_at: datetime | None = None
    interviewer_id: UUID | None = None
    status: InterviewStatus | None = None
    notes: str | None = None


class InterviewResponse(BaseModel):
    id: UUID
    application_id: UUID
    candidate_name: str
    job_title: str
    scheduled_at: datetime
    interviewer_id: UUID | None
    interviewer_name: str | None = None
    status: InterviewStatus
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime


class InterviewListResponse(PaginatedResponse[InterviewResponse]):
    pass


class RecruitmentReportRow(BaseModel):
    job_id: UUID
    job_title: str
    total_candidates: int
    shortlisted: int
    rejected: int
    pending: int
    average_ai_score: float | None


class RecruitmentReportResponse(PaginatedResponse[RecruitmentReportRow]):
    pass


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
