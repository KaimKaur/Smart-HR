from __future__ import annotations

from datetime import date

from sqlalchemy import Select, and_, or_


def apply_filters(
    query: Select,
    *,
    search: str | None = None,
    search_columns: list | None = None,
    date_column=None,
    date_from: date | None = None,
    date_to: date | None = None,
    exact_filters: dict | None = None,
) -> Select:
    next_query = query

    if search and search_columns:
        pattern = f"%{search.strip()}%"
        next_query = next_query.where(
            or_(*[column.ilike(pattern) for column in search_columns]),
        )

    if date_column is not None:
        date_conditions = []
        if date_from is not None:
            date_conditions.append(date_column >= date_from)
        if date_to is not None:
            date_conditions.append(date_column <= date_to)
        if date_conditions:
            next_query = next_query.where(and_(*date_conditions))

    if exact_filters:
        for column, value in exact_filters.items():
            if value is not None:
                next_query = next_query.where(column == value)

    return next_query
