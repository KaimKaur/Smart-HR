from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.audit_logs.errors import AuditLogsError
from app.modules.audit_logs.http import audit_logs_http_exception
from app.modules.audit_logs.schema import AuditLogListResponse, AuditLogResponse
from app.modules.audit_logs.service import AuditLogsService


class AuditLogsController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = AuditLogsService(session)

    async def list_audit_logs(
        self,
        *,
        actor: CurrentUser,
        actor_user_id: uuid.UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[AuditLogListResponse]:
        try:
            data = await self._service.list_audit_logs(
                actor=actor,
                actor_user_id=actor_user_id,
                action=action,
                resource_type=resource_type,
                date_from=date_from,
                date_to=date_to,
                search=search,
                page=page,
                page_size=page_size,
            )
        except AuditLogsError as exc:
            raise audit_logs_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_audit_log(
        self,
        audit_log_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[AuditLogResponse]:
        try:
            data = await self._service.get_audit_log(audit_log_id, actor=actor)
        except AuditLogsError as exc:
            raise audit_logs_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_user_activity(
        self,
        user_id: uuid.UUID,
        *,
        actor: CurrentUser,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[AuditLogListResponse]:
        try:
            data = await self._service.get_user_activity(
                user_id,
                actor=actor,
                page=page,
                page_size=page_size,
            )
        except AuditLogsError as exc:
            raise audit_logs_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_resource_activity(
        self,
        *,
        resource_type: str,
        resource_id: uuid.UUID,
        actor: CurrentUser,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[AuditLogListResponse]:
        try:
            data = await self._service.get_resource_activity(
                resource_type=resource_type,
                resource_id=resource_id,
                actor=actor,
                page=page,
                page_size=page_size,
            )
        except AuditLogsError as exc:
            raise audit_logs_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)
