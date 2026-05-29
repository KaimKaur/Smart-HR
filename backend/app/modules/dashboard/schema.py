from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class HRDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_employees: int
    active_employees: int
    new_hires_last_30_days: int
    departments_count: int
    attendance_rate_today: float = Field(
        ...,
        description=(
            "Attendance percentage for today in the range 0–100, "
            "computed as present employees divided by total active employees."
        ),
    )
    pending_leave_requests_count: int
    open_job_postings: int
    candidates_this_month: int


class RecruitmentJobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: str
    title: str
    open_applications: int
    shortlisted_applications: int
    rejected_applications: int
    pending_screening_applications: int
    average_ai_score: float | None
    top_candidates: list["RecruitmentTopCandidate"] = []


class RecruitmentTopCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    application_id: str
    candidate_id: str
    full_name: str
    email: str
    ai_score: float


class RecruitmentDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    open_jobs: int
    total_candidates: int
    shortlisted_candidates: int
    rejected_candidates: int
    pending_screening_candidates: int
    average_ai_score: float | None
    jobs: list[RecruitmentJobSummary] = []


class AttendanceTrendPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: date
    present_count: int
    absent_count: int


class AttendanceTopAbsentDepartment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    department_id: str
    department_name: str
    absent_count: int


class AttendanceDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    today_date: date
    present_count: int
    absent_count: int
    late_count: int
    attendance_rate_today: float
    weekly_trend: list[AttendanceTrendPoint] = []
    top_absent_departments: list[AttendanceTopAbsentDepartment] = []


class PerformanceTopPerformer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    employee_id: str
    employee_code: str
    full_name: str
    department_name: str | None = None
    rating: float


class PerformanceDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    active_cycle_id: str | None = None
    active_cycle_name: str | None = None
    average_rating: float | None = None
    top_performers: list[PerformanceTopPerformer] = []
    employees_without_review: int = 0


class EmployeeMonthlyAttendanceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    present_days: int
    total_hours: float


class EmployeeLeaveBalanceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    leave_type_id: str
    leave_type_name: str
    balance: float


class EmployeeDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    attendance_this_month: EmployeeMonthlyAttendanceSummary | None = None
    leave_balances: list[EmployeeLeaveBalanceItem] = []
    latest_performance_rating: float | None = None
    unread_notifications_count: int
    upcoming_interviews: list[dict[str, Any]] = []

