from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.schemas import PaginatedResponse, PaginationMeta


class CreateDesignationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be empty")
        return stripped


class UpdateDesignationRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be empty")
        return stripped


class DesignationResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    employee_count: int
    created_at: datetime
    updated_at: datetime


class DesignationListResponse(PaginatedResponse[DesignationResponse]):
    pass


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
