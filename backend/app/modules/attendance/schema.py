from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.schemas import PaginatedResponse, PaginationMeta


class CheckInRequest(BaseModel):
    timestamp: datetime | None = None


class CheckOutRequest(BaseModel):
    timestamp: datetime | None = None


class AttendanceRecordResponse(BaseModel):
    id: UUID
    employee_id: UUID
    attendance_date: date
    check_in_time: datetime | None
    check_out_time: datetime | None
    work_duration_minutes: int | None
    attendance_status_id: UUID
    status_name: str
    created_at: datetime


class AttendanceRecordListResponse(PaginatedResponse[AttendanceRecordResponse]):
    pass


class MonthlySummaryResponse(BaseModel):
    employee_id: UUID
    year: int
    month: int
    present_days: int
    absent_days: int
    late_days: int
    half_days: int
    total_working_days: int
    total_hours: float


class DailyAttendanceEmployeeItem(BaseModel):
    employee_id: UUID
    employee_code: str
    full_name: str
    department_name: str
    status_name: str
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    record_id: UUID | None = None


class DailyAttendanceResponse(BaseModel):
    date: date
    present_count: int
    absent_count: int
    late_count: int
    employees: list[DailyAttendanceEmployeeItem]


class CorrectionRequest(BaseModel):
    reason: str = Field(min_length=1)


class ReviewCorrectionRequest(BaseModel):
    status: Literal["approved", "rejected"]
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None

    @model_validator(mode="after")
    def checkout_after_checkin(self) -> "ReviewCorrectionRequest":
        if (
            self.check_out_time is not None
            and self.check_in_time is not None
            and self.check_out_time <= self.check_in_time
        ):
            raise ValueError("check_out_time must be after check_in_time")
        return self


class CorrectionResponse(BaseModel):
    id: UUID
    attendance_record_id: UUID
    requested_by: UUID
    reason: str
    correction_status: str
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class CorrectionListResponse(BaseModel):
    items: list[CorrectionResponse]


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


class AttendanceReportResponse(PaginatedResponse[AttendanceReportRow]):
    pass


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
