import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.modules.auth.errors import AuthError
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schema import (
    ForgotPasswordData,
    LoginResponse,
    MeResponse,
    RefreshResponse,
    TokenData,
)
from app.modules.user.model import User


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        repository: AuthRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or AuthRepository(session)
        self._settings = settings or get_settings()

    async def login(
        self,
        email: str,
        password: str,
        *,
        ip_address: str | None = None,
    ) -> LoginResponse:
        user = await self._repository.get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthError("Invalid credentials", 401)

        if not user.is_active:
            raise AuthError("Account is inactive", 401)

        tokens = await self._issue_token_pair(user, ip_address=ip_address)
        await self._repository.create_audit_log(
            actor_user_id=user.id,
            action="login",
            ip_address=ip_address or "0.0.0.0",
        )
        await self._session.commit()
        return LoginResponse(**tokens.model_dump())

    async def refresh_tokens(
        self,
        refresh_token: str,
        *,
        ip_address: str | None = None,
    ) -> RefreshResponse:
        payload = decode_token(refresh_token, self._settings)
        if payload.get("token_type") != "refresh":
            raise AuthError("Invalid or expired token", 401)

        token_hash = hash_token(refresh_token)
        stored = await self._repository.get_refresh_token_by_hash(token_hash)
        if stored is None:
            raise AuthError("Invalid or expired token", 401)

        now = datetime.now(UTC)
        if stored.revoked_at is not None:
            await self._repository.revoke_all_refresh_tokens_for_user(stored.user_id)
            await self._session.commit()
            raise AuthError("Invalid or expired token", 401)

        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            raise AuthError("Invalid or expired token", 401)

        user = await self._repository.get_user_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise AuthError("Invalid or expired token", 401)

        await self._repository.revoke_refresh_token(stored.id)
        tokens = await self._issue_token_pair(user, ip_address=ip_address)
        await self._session.commit()
        return RefreshResponse(**tokens.model_dump())

    async def logout(
        self,
        user_id: uuid.UUID,
        *,
        ip_address: str | None = None,
    ) -> None:
        await self._repository.revoke_all_refresh_tokens_for_user(user_id)
        await self._repository.create_audit_log(
            actor_user_id=user_id,
            action="logout",
            ip_address=ip_address or "0.0.0.0",
        )
        await self._session.commit()

    async def forgot_password_with_token(self, email: str) -> ForgotPasswordData:
        """MVP helper — returns reset token in data when user exists."""
        user = await self._repository.get_user_by_email(email)
        if user is None:
            return ForgotPasswordData(reset_token=None)

        raw_token = generate_opaque_token()
        expires_at = datetime.now(UTC) + timedelta(
            hours=self._settings.password_reset_expire_hours,
        )
        await self._repository.invalidate_unused_password_resets(user.id)
        await self._repository.create_password_reset_token(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )
        await self._session.commit()
        return ForgotPasswordData(reset_token=raw_token)

    async def reset_password(self, token: str, new_password: str) -> None:
        token_hash = hash_token(token)
        reset_row = await self._repository.get_password_reset_by_hash(token_hash)
        if reset_row is None:
            raise AuthError("Invalid or expired reset token", 400)

        now = datetime.now(UTC)
        expires_at = reset_row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if reset_row.used_at is not None or expires_at <= now:
            raise AuthError("Invalid or expired reset token", 400)

        user = await self._repository.get_user_by_id(reset_row.user_id)
        if user is None:
            raise AuthError("Invalid or expired reset token", 400)

        await self._repository.update_password_hash(
            user.id,
            hash_password(new_password),
        )
        await self._repository.mark_password_reset_used(reset_row.id)
        await self._repository.revoke_all_refresh_tokens_for_user(user.id)
        await self._session.commit()

    async def get_me(self, user_id: uuid.UUID) -> MeResponse:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise AuthError("User not found or inactive", 401)

        if not user.is_active:
            raise AuthError("Account is inactive", 401)

        roles = await self._repository.get_user_roles(user.id)
        return MeResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            roles=roles,
            created_at=user.created_at,
        )

    async def _issue_token_pair(
        self,
        user: User,
        *,
        ip_address: str | None,
    ) -> TokenData:
        roles = await self._repository.get_user_roles(user.id)
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "roles": roles,
        }
        access_token = create_access_token(token_data, self._settings)
        refresh_token = create_refresh_token(
            {"sub": str(user.id), "roles": roles},
            self._settings,
        )

        expires_at = datetime.now(UTC) + timedelta(
            days=self._settings.refresh_token_expire_days,
        )
        await self._repository.create_refresh_token(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
            ip_address=ip_address,
        )

        return TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
