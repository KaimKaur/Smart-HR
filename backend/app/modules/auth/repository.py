import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.model import PasswordResetToken, RefreshToken, Role, UserRole
from app.modules.notifications.model import AuditLog
from app.modules.user.model import User


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User)
            .where(
                User.email == email,
                User.deleted_at.is_(None),
            )
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(User)
            .where(
                User.id == user_id,
                User.deleted_at.is_(None),
            )
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
        )
        return result.scalar_one_or_none()

    async def get_user_roles(self, user_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_password_hash(self, user_id: uuid.UUID, password_hash: str) -> None:
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password_hash, updated_at=datetime.now(UTC))
        )

    async def create_refresh_token(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        ip_address: str | None,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_refresh_token_by_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_id: uuid.UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked_at=datetime.now(UTC))
        )

    async def revoke_all_refresh_tokens_for_user(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )

    async def create_password_reset_token(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_password_reset_by_hash(
        self,
        token_hash: str,
    ) -> PasswordResetToken | None:
        result = await self._session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
            )
        )
        return result.scalar_one_or_none()

    async def mark_password_reset_used(self, token_id: uuid.UUID) -> None:
        await self._session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used_at=datetime.now(UTC))
        )

    async def invalidate_unused_password_resets(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )

    async def create_audit_log(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        resource_type: str = "auth",
        resource_id: uuid.UUID | None = None,
        ip_address: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=after_state,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
