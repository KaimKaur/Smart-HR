from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[ErrorDetail] = Field(default_factory=list)


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T | None = None


class PaginationMeta(BaseModel):
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationMeta
