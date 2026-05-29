from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import PaginatedResponse, PaginationMeta


class AuditLogResponse(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    action: str
    resource_type: str
    resource_id: UUID | None
    ip_address: str
    before_state: dict | None
    after_state: dict | None
    created_at: datetime


class AuditLogListResponse(PaginatedResponse[AuditLogResponse]):
    pass


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
