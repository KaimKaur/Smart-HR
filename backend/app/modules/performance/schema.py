from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import PaginatedResponse, PaginationMeta


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


class EmployeeSummary(BaseModel):
    id: UUID
    employee_code: str
    full_name: str
    department_name: str | None = None


class CycleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    start_date: date
    end_date: date


CycleStatus = Literal["draft", "active", "completed"]


class CycleResponse(BaseModel):
    id: UUID
    name: str
    start_date: date
    end_date: date
    status: CycleStatus


class ReviewRequest(BaseModel):
    cycle_id: UUID
    employee_id: UUID
    rating: float = Field(ge=1.0, le=5.0)
    comments: str | None = Field(default=None)


class ReviewResponse(BaseModel):
    id: UUID
    cycle: CycleResponse
    employee: EmployeeSummary
    reviewer: EmployeeSummary
    rating: float
    comments: str | None
    created_at: datetime
    average_metric_score: float | None
    metric_scores: list["MetricScoreResponse"] = []
    feedback_entries: list["FeedbackResponse"] = []


class PerformanceMetricRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None


class PerformanceMetricResponse(BaseModel):
    id: UUID
    name: str
    description: str | None


class PerformanceMetricListResponse(PaginatedResponse[PerformanceMetricResponse]):
    pass


class MetricScoreRequest(BaseModel):
    metric_id: UUID
    score: float = Field(ge=0.0, le=100.0)


class MetricScoreResponse(BaseModel):
    id: UUID
    review_id: UUID
    metric_id: UUID
    metric_name: str
    score: float


class FeedbackRequest(BaseModel):
    feedback_text: str = Field(min_length=1, max_length=5000)


class FeedbackResponse(BaseModel):
    id: UUID
    review_id: UUID
    feedback_text: str
    created_by: UUID
    author: EmployeeSummary | None = None
    created_at: datetime


class EmployeePerformanceSummary(BaseModel):
    review_id: UUID
    cycle: CycleResponse
    employee: EmployeeSummary
    reviewer: EmployeeSummary
    rating: float
    average_metric_score: float | None
    metric_scores: list[MetricScoreResponse] = []
    feedback_entries: list[FeedbackResponse] = []
    feedback_count: int = 0


class CycleListResponse(PaginatedResponse[CycleResponse]):
    pass


class ReviewListResponse(PaginatedResponse[ReviewResponse]):
    pass


class EmployeePerformanceSummaryListResponse(
    PaginatedResponse[EmployeePerformanceSummary]
):
    pass


class CreatePerformanceReportEmployeeRow(BaseModel):
    employee: EmployeeSummary
    average_rating: float | None = None
    average_score: float | None = None


