from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SYSTEM_ADMINISTRATOR
from app.core.security import CurrentUser
from app.modules.audit_logs.errors import AuditLogsError
from app.modules.audit_logs.repository import AuditLogsRepository
from app.modules.audit_logs.schema import AuditLogListResponse, AuditLogResponse, build_pagination


class AuditLogsService:
    def __init__(
        self,
        session: AsyncSession,
        repository: AuditLogsRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or AuditLogsRepository(session)

    def _require_admin(self, actor: CurrentUser) -> None:
        if SYSTEM_ADMINISTRATOR not in actor.roles:
            raise AuditLogsError("Insufficient permissions", 403)

    @staticmethod
    def _to_response(item) -> AuditLogResponse:
        return AuditLogResponse(
            id=item.id,
            actor_user_id=item.actor_user_id,
            action=item.action,
            resource_type=item.resource_type,
            resource_id=item.resource_id,
            ip_address=item.ip_address,
            before_state=item.before_state,
            after_state=item.after_state,
            created_at=item.created_at,
        )

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
    ) -> AuditLogListResponse:
        self._require_admin(actor)
        if date_from and date_to and date_from > date_to:
            raise AuditLogsError("date_from must be on or before date_to", 400)

        items, total = await self._repository.list_audit_logs(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            date_from=date_from,
            date_to=date_to,
            search=search,
            page=page,
            page_size=page_size,
        )
        return AuditLogListResponse(
            items=[self._to_response(item) for item in items],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_audit_log(
        self,
        audit_log_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> AuditLogResponse:
        self._require_admin(actor)
        item = await self._repository.get_audit_log_by_id(audit_log_id)
        if item is None:
            raise AuditLogsError("Audit log not found", 404)
        return self._to_response(item)

    async def get_user_activity(
        self,
        user_id: uuid.UUID,
        *,
        actor: CurrentUser,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditLogListResponse:
        self._require_admin(actor)
        items, total = await self._repository.get_user_activity(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        return AuditLogListResponse(
            items=[self._to_response(item) for item in items],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_resource_activity(
        self,
        *,
        resource_type: str,
        resource_id: uuid.UUID,
        actor: CurrentUser,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditLogListResponse:
        self._require_admin(actor)
        items, total = await self._repository.get_resource_activity(
            resource_type=resource_type,
            resource_id=resource_id,
            page=page,
            page_size=page_size,
        )
        return AuditLogListResponse(
            items=[self._to_response(item) for item in items],
            pagination=build_pagination(page, page_size, total),
        )
