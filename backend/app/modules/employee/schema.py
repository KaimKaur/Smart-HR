from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.schemas import PaginatedResponse, PaginationMeta


class DepartmentRef(BaseModel):
    id: UUID
    name: str


class DesignationRef(BaseModel):
    id: UUID
    title: str


class ManagerRef(BaseModel):
    id: UUID
    name: str
    employee_code: str


class EmploymentStatusRef(BaseModel):
    id: UUID
    name: str


class CreateEmployeeRequest(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    department_id: UUID
    designation_id: UUID
    employment_status_id: UUID
    manager_id: UUID | None = None
    salary: Decimal | None = Field(default=None, ge=0)
    join_date: date
    user_id: UUID | None = None

    @field_validator("employee_code")
    @classmethod
    def strip_employee_code(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("employee_code must not be empty")
        return stripped


class UpdateEmployeeRequest(BaseModel):
    employee_code: str | None = Field(default=None, min_length=1, max_length=50)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    department_id: UUID | None = None
    designation_id: UUID | None = None
    employment_status_id: UUID | None = None
    manager_id: UUID | None = None
    salary: Decimal | None = Field(default=None, ge=0)
    join_date: date | None = None

    @field_validator("employee_code")
    @classmethod
    def strip_employee_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("employee_code must not be empty")
        return stripped


class EmployeeSelfUpdateRequest(BaseModel):
    phone: str | None = Field(default=None, max_length=30)


class EmployeeResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    employee_code: str
    first_name: str
    last_name: str
    full_name: str
    email: EmailStr
    phone: str | None
    department: DepartmentRef
    designation: DesignationRef
    employment_status: EmploymentStatusRef
    manager: ManagerRef | None
    salary: Decimal | None = None
    join_date: date
    created_at: datetime
    updated_at: datetime


class CreateEmployeeResponse(EmployeeResponse):
    password_reset_token: str | None = None


class EmployeeProfileResponse(EmployeeResponse):
    pass


class EmployeeListResponse(PaginatedResponse[EmployeeResponse]):
    pass


class EmployeeSearchItem(BaseModel):
    id: UUID
    full_name: str
    employee_code: str
    department: DepartmentRef


class EmployeeSearchResponse(BaseModel):
    items: list[EmployeeSearchItem]


class ManagerDetailResponse(BaseModel):
    id: UUID
    full_name: str
    employee_code: str
    designation: DesignationRef
    department: DepartmentRef


class DirectReportsResponse(PaginatedResponse[EmployeeResponse]):
    pass


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
