from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.modules.notifications.controller import NotificationsController
from app.modules.notifications.schema import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationResponse,
    UnreadCountResponse,
    UpdatePreferenceRequest,
)

router = APIRouter()


def _controller(session: AsyncSession = Depends(get_db)) -> NotificationsController:
    return NotificationsController(session)


@router.get("", response_model=SuccessResponse[NotificationListResponse])
async def list_notifications(
    is_read: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: NotificationsController = Depends(_controller),
) -> SuccessResponse[NotificationListResponse]:
    return await controller.list_notifications(
        actor=current_user,
        is_read=is_read,
        page=page,
        page_size=page_size,
    )


# Spec says POST /read-all; user notes mention PATCH /read-all.
@router.post("/read-all", response_model=SuccessResponse[dict])
async def mark_all_read_post(
    current_user: CurrentUser = Depends(get_current_user),
    controller: NotificationsController = Depends(_controller),
) -> SuccessResponse[dict]:
    return await controller.mark_all_read(actor=current_user)


@router.patch("/read-all", response_model=SuccessResponse[dict])
async def mark_all_read_patch(
    current_user: CurrentUser = Depends(get_current_user),
    controller: NotificationsController = Depends(_controller),
) -> SuccessResponse[dict]:
    return await controller.mark_all_read(actor=current_user)


# Spec says GET /count; user notes mention GET /unread-count.
@router.get("/count", response_model=SuccessResponse[UnreadCountResponse])
async def unread_count(
    current_user: CurrentUser = Depends(get_current_user),
    controller: NotificationsController = Depends(_controller),
) -> SuccessResponse[UnreadCountResponse]:
    return await controller.unread_count(actor=current_user)


@router.get("/unread-count", response_model=SuccessResponse[UnreadCountResponse])
async def unread_count_alias(
    current_user: CurrentUser = Depends(get_current_user),
    controller: NotificationsController = Depends(_controller),
) -> SuccessResponse[UnreadCountResponse]:
    return await controller.unread_count(actor=current_user)


@router.get("/preferences", response_model=SuccessResponse[NotificationPreferenceResponse])
async def get_preferences(
    current_user: CurrentUser = Depends(get_current_user),
    controller: NotificationsController = Depends(_controller),
) -> SuccessResponse[NotificationPreferenceResponse]:
    return await controller.get_preferences(actor=current_user)


@router.patch(
    "/preferences",
    response_model=SuccessResponse[NotificationPreferenceResponse],
)
async def update_preferences(
    body: UpdatePreferenceRequest,
    current_user: CurrentUser = Depends(get_current_user),
    controller: NotificationsController = Depends(_controller),
) -> SuccessResponse[NotificationPreferenceResponse]:
    return await controller.update_preferences(body, actor=current_user)


@router.get("/{notification_id}", response_model=SuccessResponse[NotificationResponse])
async def get_notification(
    notification_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: NotificationsController = Depends(_controller),
) -> SuccessResponse[NotificationResponse]:
    return await controller.get_notification(notification_id, actor=current_user)


@router.patch("/{notification_id}/read", response_model=SuccessResponse[None])
async def mark_read(
    notification_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: NotificationsController = Depends(_controller),
) -> SuccessResponse[None]:
    return await controller.mark_read(notification_id, actor=current_user)
