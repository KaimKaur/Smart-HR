from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.model import Notification, NotificationPreference


class NotificationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_notification(
        self,
        *,
        user_id: uuid.UUID,
        title: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            is_read=False,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def get_notification_by_id(
        self,
        notification_id: uuid.UUID,
    ) -> Notification | None:
        result = await self._session.execute(
            select(Notification).where(Notification.id == notification_id),
        )
        return result.scalar_one_or_none()

    async def list_notifications(
        self,
        *,
        user_id: uuid.UUID,
        is_read: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Notification], int]:
        # Uses idx_notifications_user via (user_id, is_read) filters.
        query = select(Notification).where(Notification.user_id == user_id)
        count_query = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id
        )

        if is_read is not None:
            query = query.where(Notification.is_read.is_(is_read))
            count_query = count_query.where(Notification.is_read.is_(is_read))

        total_items = int((await self._session.execute(count_query)).scalar_one())
        offset = (page - 1) * page_size
        query = (
            query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_items

    async def mark_read(
        self,
        *,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        result = await self._session.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .values(is_read=True)
        )
        return (result.rowcount or 0) > 0

    async def mark_all_read(self, *, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        return int(result.rowcount or 0)

    async def get_unread_count(self, *, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        return int(result.scalar_one())

    async def get_preferences(
        self,
        *,
        user_id: uuid.UUID,
    ) -> NotificationPreference | None:
        result = await self._session.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def upsert_preferences(
        self,
        *,
        user_id: uuid.UUID,
        in_app_enabled: bool,
    ) -> NotificationPreference:
        existing = await self.get_preferences(user_id=user_id)
        if existing is None:
            pref = NotificationPreference(user_id=user_id, in_app_enabled=in_app_enabled)
            self._session.add(pref)
            await self._session.flush()
            return pref

        await self._session.execute(
            update(NotificationPreference)
            .where(NotificationPreference.id == existing.id)
            .values(in_app_enabled=in_app_enabled)
        )
        updated = await self.get_preferences(user_id=user_id)
        assert updated is not None
        return updated

