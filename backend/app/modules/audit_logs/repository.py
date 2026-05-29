from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.model import AuditLog


class AuditLogsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_audit_logs(
        self,
        *,
        actor_user_id: uuid.UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)

        if actor_user_id is not None:
            query = query.where(AuditLog.actor_user_id == actor_user_id)
            count_query = count_query.where(AuditLog.actor_user_id == actor_user_id)
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
            count_query = count_query.where(AuditLog.resource_type == resource_type)
        if date_from is not None:
            from_dt = datetime.combine(date_from, time.min, tzinfo=UTC)
            query = query.where(AuditLog.created_at >= from_dt)
            count_query = count_query.where(AuditLog.created_at >= from_dt)
        if date_to is not None:
            to_dt = datetime.combine(date_to, time.max, tzinfo=UTC)
            query = query.where(AuditLog.created_at <= to_dt)
            count_query = count_query.where(AuditLog.created_at <= to_dt)
        if search:
            pattern = f"%{search.strip()}%"
            search_filter = or_(
                AuditLog.action.ilike(pattern),
                AuditLog.resource_type.ilike(pattern),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total_items = int((await self._session.execute(count_query)).scalar_one())
        offset = (page - 1) * page_size
        rows = await self._session.execute(
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size),
        )
        return list(rows.scalars().all()), total_items

    async def get_audit_log_by_id(self, audit_log_id: uuid.UUID) -> AuditLog | None:
        result = await self._session.execute(
            select(AuditLog).where(AuditLog.id == audit_log_id),
        )
        return result.scalar_one_or_none()

    async def get_user_activity(
        self,
        *,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        return await self.list_audit_logs(
            actor_user_id=user_id,
            page=page,
            page_size=page_size,
        )

    async def get_resource_activity(
        self,
        *,
        resource_type: str,
        resource_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog).where(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        )
        count_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.resource_type == resource_type, AuditLog.resource_id == resource_id)
        )
        total_items = int((await self._session.execute(count_query)).scalar_one())
        offset = (page - 1) * page_size
        rows = await self._session.execute(
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size),
        )
        return list(rows.scalars().all()), total_items
