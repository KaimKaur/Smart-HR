from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.model import AuditLog


async def write_audit_log(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None = None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog | None:
    # Non-blocking audit write: failures should not break parent flow.
    try:
        async with db.begin_nested():
            entry = AuditLog(
                actor_user_id=actor_user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                before_state=before_state,
                after_state=after_state,
                ip_address=ip_address or "0.0.0.0",
            )
            db.add(entry)
            await db.flush()
            return entry
    except Exception:
        return None
