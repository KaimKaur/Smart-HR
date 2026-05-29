from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import PaginationMeta
from app.modules.performance.schema import EmployeeSummary


class DepartmentAverageRatingRow(BaseModel):
    department_id: UUID
    department_name: str
    average_rating: float | None = None


class TopPerformerRow(BaseModel):
    employee: EmployeeSummary
    average_rating: float | None = None


class ScoreDistributionBucketRow(BaseModel):
    bucket: str
    count: int
    percentage: float


class PerformanceReportEmployeeRow(BaseModel):
    employee: EmployeeSummary
    average_rating: float | None = None
    average_score: float | None = None


class PerformanceReportResponse(BaseModel):
    average_rating_per_department: list[DepartmentAverageRatingRow]
    top_performers: list[TopPerformerRow]
    score_distribution: list[ScoreDistributionBucketRow]
    employees: list[PerformanceReportEmployeeRow]
    pagination: PaginationMeta


class EmployeeReportRow(BaseModel):
    employee_id: UUID
    employee_code: str
    full_name: str
    email: str
    department_name: str
    designation_title: str
    employment_status: str
    join_date: date


class EmployeeReportResponse(BaseModel):
    items: list[EmployeeReportRow]
    pagination: PaginationMeta


class AttendanceReportRow(BaseModel):
    record_id: UUID
    employee_id: UUID
    employee_code: str
    full_name: str
    department_name: str
    attendance_date: date
    status_name: str
    check_in_time: datetime | None
    check_out_time: datetime | None
    work_duration_minutes: int | None


class AttendanceReportResponse(BaseModel):
    items: list[AttendanceReportRow]
    pagination: PaginationMeta

