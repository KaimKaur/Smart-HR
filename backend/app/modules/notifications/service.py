from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.modules.notifications.errors import NotificationsError
from app.modules.notifications.model import Notification, NotificationPreference
from app.modules.notifications.repository import NotificationsRepository
from app.modules.notifications.schema import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationResponse,
    UnreadCountResponse,
    UpdatePreferenceRequest,
    build_pagination,
)


class NotificationsService:
    def __init__(
        self,
        session: AsyncSession,
        repository: NotificationsRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or NotificationsRepository(session)

    def _to_notification_response(self, n: Notification) -> NotificationResponse:
        return NotificationResponse(
            id=n.id,
            title=n.title,
            message=n.message,
            is_read=bool(n.is_read),
            created_at=n.created_at,
        )

    async def list_notifications(
        self,
        *,
        actor: CurrentUser,
        is_read: bool | None,
        page: int,
        page_size: int,
    ) -> NotificationListResponse:
        items, total = await self._repository.list_notifications(
            user_id=actor.id,
            is_read=is_read,
            page=page,
            page_size=page_size,
        )
        return NotificationListResponse(
            items=[self._to_notification_response(n) for n in items],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_notification(
        self,
        notification_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> NotificationResponse:
        n = await self._repository.get_notification_by_id(notification_id)
        if n is None:
            raise NotificationsError("Notification not found", 404)
        if n.user_id != actor.id:
            raise NotificationsError("Insufficient permissions", 403)
        return self._to_notification_response(n)

    async def mark_read(
        self,
        notification_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> None:
        exists = await self._repository.get_notification_by_id(notification_id)
        if exists is None:
            raise NotificationsError("Notification not found", 404)
        if exists.user_id != actor.id:
            raise NotificationsError("Insufficient permissions", 403)

        updated = await self._repository.mark_read(
            notification_id=notification_id,
            user_id=actor.id,
        )
        if not updated:
            raise NotificationsError("Notification not found", 404)
        await self._session.commit()

    async def mark_all_read(self, *, actor: CurrentUser) -> int:
        updated = await self._repository.mark_all_read(user_id=actor.id)
        await self._session.commit()
        return updated

    async def unread_count(self, *, actor: CurrentUser) -> UnreadCountResponse:
        count = await self._repository.get_unread_count(user_id=actor.id)
        return UnreadCountResponse(unread_count=int(count))

    async def get_preferences(self, *, actor: CurrentUser) -> NotificationPreferenceResponse:
        pref = await self._repository.get_preferences(user_id=actor.id)
        if pref is None:
            # Default behavior per spec: enabled if no preference row exists.
            return NotificationPreferenceResponse(in_app_enabled=True)
        return NotificationPreferenceResponse(in_app_enabled=bool(pref.in_app_enabled))

    async def update_preferences(
        self,
        body: UpdatePreferenceRequest,
        *,
        actor: CurrentUser,
    ) -> NotificationPreferenceResponse:
        pref = await self._repository.upsert_preferences(
            user_id=actor.id,
            in_app_enabled=body.in_app_enabled,
        )
        await self._session.commit()
        return NotificationPreferenceResponse(in_app_enabled=bool(pref.in_app_enabled))
