from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


@dataclass(slots=True)
class PaginatedResult(Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total_items: int
    total_pages: int


async def paginate(
    session: AsyncSession,
    query: Select,
    *,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResult:
    safe_page = max(page, 1)
    safe_page_size = min(max(page_size, 1), 100)

    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total_items = int((await session.execute(count_query)).scalar_one())
    total_pages = ceil(total_items / safe_page_size) if total_items else 0

    offset = (safe_page - 1) * safe_page_size
    result = await session.execute(query.offset(offset).limit(safe_page_size))
    items = result.all()

    return PaginatedResult(
        items=items,
        page=safe_page,
        page_size=safe_page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
