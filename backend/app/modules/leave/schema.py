from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.schemas import PaginatedResponse, PaginationMeta

LeaveRequestStatus = Literal["pending", "approved", "rejected", "cancelled"]


class CreateLeaveRequest(BaseModel):
    leave_type_id: UUID
    start_date: date
    end_date: date
    reason: str | None = None

    @model_validator(mode="after")
    def end_on_or_after_start(self) -> "CreateLeaveRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class LeaveApprovalRequest(BaseModel):
    remarks: str | None = None


class LeaveRequestResponse(BaseModel):
    id: UUID
    employee_id: UUID
    employee_name: str
    leave_type_id: UUID
    leave_type_name: str
    start_date: date
    end_date: date
    reason: str | None
    status: LeaveRequestStatus
    created_at: datetime
    approver_name: str | None = None
    approval_level: int | None = None
    approval_remarks: str | None = None


class LeaveListResponse(PaginatedResponse[LeaveRequestResponse]):
    pass


class LeaveBalanceItem(BaseModel):
    leave_type_id: UUID
    leave_type: str
    annual_allocation: int
    current_balance: Decimal


class LeaveBalanceResponse(BaseModel):
    employee_id: UUID
    balances: list[LeaveBalanceItem]


class InitializeBalanceRequest(BaseModel):
    employee_id: UUID | None = None
    all_employees: bool = False

    @model_validator(mode="after")
    def employee_or_all(self) -> "InitializeBalanceRequest":
        if not self.all_employees and self.employee_id is None:
            raise ValueError("employee_id is required when all_employees is false")
        if self.all_employees and self.employee_id is not None:
            raise ValueError("Provide employee_id or all_employees, not both")
        return self


class InitializedBalanceRecord(BaseModel):
    id: UUID
    employee_id: UUID
    leave_type_id: UUID
    leave_type_name: str
    balance: Decimal


class InitializeBalanceResponse(BaseModel):
    created: list[InitializedBalanceRecord]


class CreateLeaveTypeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    annual_allocation: int = Field(gt=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be empty")
        return stripped


class UpdateLeaveTypeRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    annual_allocation: int | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be empty")
        return stripped


class LeaveTypeResponse(BaseModel):
    id: UUID
    name: str
    annual_allocation: int


class LeaveTypeListResponse(BaseModel):
    items: list[LeaveTypeResponse]


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
