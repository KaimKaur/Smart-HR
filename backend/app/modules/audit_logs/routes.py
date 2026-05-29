from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, require_roles
from app.modules.audit_logs.controller import AuditLogsController
from app.modules.audit_logs.schema import AuditLogListResponse, AuditLogResponse

router = APIRouter()

_admin_only = require_roles(SYSTEM_ADMINISTRATOR)


def _controller(session: AsyncSession = Depends(get_db)) -> AuditLogsController:
    return AuditLogsController(session)


@router.get("", response_model=SuccessResponse[AuditLogListResponse])
async def list_audit_logs(
    actor_user_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_admin_only),
    controller: AuditLogsController = Depends(_controller),
) -> SuccessResponse[AuditLogListResponse]:
    return await controller.list_audit_logs(
        actor=current_user,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}/activity", response_model=SuccessResponse[AuditLogListResponse])
async def get_user_activity(
    user_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_admin_only),
    controller: AuditLogsController = Depends(_controller),
) -> SuccessResponse[AuditLogListResponse]:
    return await controller.get_user_activity(
        user_id,
        actor=current_user,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/resources/{resource_type}/{resource_id}",
    response_model=SuccessResponse[AuditLogListResponse],
)
async def get_resource_activity(
    resource_type: str,
    resource_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_admin_only),
    controller: AuditLogsController = Depends(_controller),
) -> SuccessResponse[AuditLogListResponse]:
    return await controller.get_resource_activity(
        resource_type=resource_type,
        resource_id=resource_id,
        actor=current_user,
        page=page,
        page_size=page_size,
    )


@router.get("/{audit_log_id}", response_model=SuccessResponse[AuditLogResponse])
async def get_audit_log(
    audit_log_id: UUID,
    current_user: CurrentUser = Depends(_admin_only),
    controller: AuditLogsController = Depends(_controller),
) -> SuccessResponse[AuditLogResponse]:
    return await controller.get_audit_log(audit_log_id, actor=current_user)
