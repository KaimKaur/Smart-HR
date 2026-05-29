from __future__ import annotations

from datetime import datetime
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


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    is_read: bool
    created_at: datetime


class NotificationListResponse(PaginatedResponse[NotificationResponse]):
    pass


class NotificationPreferenceResponse(BaseModel):
    in_app_enabled: bool


class UpdatePreferenceRequest(BaseModel):
    in_app_enabled: bool = Field(...)


class UnreadCountResponse(BaseModel):
    unread_count: int

