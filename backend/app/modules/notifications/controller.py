import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.notifications.errors import NotificationsError
from app.modules.notifications.http import notifications_http_exception
from app.modules.notifications.schema import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationResponse,
    UnreadCountResponse,
    UpdatePreferenceRequest,
)
from app.modules.notifications.service import NotificationsService


class NotificationsController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = NotificationsService(session)

    async def list_notifications(
        self,
        *,
        actor: CurrentUser,
        is_read: bool | None,
        page: int,
        page_size: int,
    ) -> SuccessResponse[NotificationListResponse]:
        try:
            data = await self._service.list_notifications(
                actor=actor,
                is_read=is_read,
                page=page,
                page_size=page_size,
            )
        except NotificationsError as exc:
            raise notifications_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_notification(
        self,
        notification_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[NotificationResponse]:
        try:
            data = await self._service.get_notification(notification_id, actor=actor)
        except NotificationsError as exc:
            raise notifications_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def mark_read(
        self,
        notification_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[None]:
        try:
            await self._service.mark_read(notification_id, actor=actor)
        except NotificationsError as exc:
            raise notifications_http_exception(exc) from exc
        return SuccessResponse(message="Marked as read", data=None)

    async def mark_all_read(
        self,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[dict]:
        try:
            updated = await self._service.mark_all_read(actor=actor)
        except NotificationsError as exc:
            raise notifications_http_exception(exc) from exc
        return SuccessResponse(message="OK", data={"updated": updated})

    async def unread_count(
        self,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[UnreadCountResponse]:
        try:
            data = await self._service.unread_count(actor=actor)
        except NotificationsError as exc:
            raise notifications_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_preferences(
        self,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[NotificationPreferenceResponse]:
        try:
            data = await self._service.get_preferences(actor=actor)
        except NotificationsError as exc:
            raise notifications_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def update_preferences(
        self,
        body: UpdatePreferenceRequest,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[NotificationPreferenceResponse]:
        try:
            data = await self._service.update_preferences(body, actor=actor)
        except NotificationsError as exc:
            raise notifications_http_exception(exc) from exc
        return SuccessResponse(message="Preferences updated", data=data)
