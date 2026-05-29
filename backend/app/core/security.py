import hashlib
import secrets
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import ALL_ROLES
from app.core.database import get_db
from app.modules.auth.model import Role, UserRole
from app.modules.user.model import User

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

bearer_scheme = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    sub: str
    email: str | None = None
    roles: list[str] = []
    token_type: str = "access"


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str
    roles: list[str]


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(32)


class UserRoleRepository:
    async def get_role_names_for_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[str]:
        result = await session.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return list(result.scalars().all())

    async def user_exists_and_active(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> bool:
        result = await session.execute(
            select(User.id).where(
                User.id == user_id,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None


def _build_expiry(
    settings: Settings,
    *,
    token_type: str,
    expires_delta: timedelta | None = None,
) -> datetime:
    if expires_delta is not None:
        return datetime.now(UTC) + expires_delta
    if token_type == "refresh":
        return datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    return datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)


def create_access_token(
    data: dict[str, Any],
    settings: Settings | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    settings = settings or get_settings()
    expire = _build_expiry(settings, token_type="access", expires_delta=expires_delta)
    payload = {
        **data,
        "token_type": "access",
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    data: dict[str, Any],
    settings: Settings | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    settings = settings or get_settings()
    expire = _build_expiry(settings, token_type="refresh", expires_delta=expires_delta)
    payload = {
        **data,
        "token_type": "refresh",
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.jwt_refresh_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    try:
        unverified = jwt.get_unverified_claims(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid or expired token"},
        ) from exc

    token_type = unverified.get("token_type", "access")
    secret = (
        settings.jwt_refresh_secret_key
        if token_type == "refresh"
        else settings.jwt_secret_key
    )

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid or expired token"},
        ) from exc

    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid token payload"},
        )

    return payload


def decode_access_token(
    token: str,
    settings: Settings | None = None,
) -> TokenPayload:
    payload = decode_token(token, settings)
    if payload.get("token_type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid token type"},
        )
    return TokenPayload(
        sub=str(payload["sub"]),
        email=str(payload.get("email", "")),
        roles=list(payload.get("roles", [])),
        token_type="access",
    )


async def resolve_current_user(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
    role_repository: UserRoleRepository | None = None,
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Not authenticated"},
        )

    token_payload = decode_access_token(credentials.credentials)
    try:
        user_id = uuid.UUID(token_payload.sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid token subject"},
        ) from exc

    repository = role_repository or UserRoleRepository()
    if not await repository.user_exists_and_active(session, user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "User not found or inactive"},
        )

    roles = await repository.get_role_names_for_user(session, user_id)
    return CurrentUser(id=user_id, email=token_payload.email or "", roles=roles)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> CurrentUser:
    return await resolve_current_user(credentials, session)


def require_roles(*required_roles: str) -> Callable[..., Any]:
    unknown = set(required_roles) - set(ALL_ROLES)
    if unknown:
        raise ValueError(f"Unknown roles: {', '.join(sorted(unknown))}")

    async def dependency(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not set(required_roles).intersection(current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Insufficient permissions"},
            )
        return current_user

    return dependency
