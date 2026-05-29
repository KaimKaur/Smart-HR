from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.schemas import PaginatedResponse, PaginationMeta


class CreateDepartmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be empty")
        return stripped


class UpdateDepartmentRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be empty")
        return stripped


class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    employee_count: int
    created_at: datetime
    updated_at: datetime


class DepartmentListResponse(PaginatedResponse[DepartmentResponse]):
    pass


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
