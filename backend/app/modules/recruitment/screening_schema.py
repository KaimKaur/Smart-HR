from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ScreeningResultResponse(BaseModel):
    analysis_id: UUID
    application_id: UUID
    candidate_id: UUID
    job_id: UUID
    analysis_status: str
    score: float
    ai_score: float | None
    recommendation: str | None
    matched_skills: list[str]
    missing_skills: list[str]
    extracted_skills: list[str]
    explanation: dict[str, Any]


class MatchExplanationResponse(BaseModel):
    application_id: UUID
    score: Decimal
    matched_skills: list[Any]
    missing_skills: list[Any]
    recommendation: str | None
    explanation: dict[str, Any]
