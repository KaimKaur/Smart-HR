from __future__ import annotations

from sqlalchemy import Select


def apply_sorting(
    query: Select,
    model,
    *,
    sort_by: str | None,
    sort_order: str = "desc",
) -> Select:
    normalized_order = sort_order.lower()
    if normalized_order not in {"asc", "desc"}:
        raise ValueError("sort_order must be 'asc' or 'desc'")

    column_name = sort_by or "created_at"
    if not hasattr(model, column_name):
        raise ValueError(f"Invalid sort_by field: {column_name}")

    column = getattr(model, column_name)
    return query.order_by(column.asc() if normalized_order == "asc" else column.desc())
