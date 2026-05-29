import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.modules.auth.errors import AuthError
from app.modules.auth.service import AuthService
from app.modules.user.model import User


@pytest.fixture
def settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        JWT_SECRET_KEY="a" * 32,
        JWT_REFRESH_SECRET_KEY="b" * 32,
        ACCESS_TOKEN_EXPIRE_MINUTES=15,
        REFRESH_TOKEN_EXPIRE_DAYS=7,
        PASSWORD_RESET_EXPIRE_HOURS=24,
    )


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def service(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
    settings: Settings,
) -> AuthService:
    return AuthService(mock_session, repository=mock_repository, settings=settings)


def _active_user(**overrides) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = overrides.get("id", uuid.uuid4())
    user.email = overrides.get("email", "user@example.com")
    user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$fake$fake"
    user.is_active = overrides.get("is_active", True)
    return user


@pytest.mark.asyncio
async def test_login_success(
    service: AuthService,
    mock_repository: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _active_user()
    mock_repository.get_user_by_email.return_value = user
    mock_repository.get_user_roles.return_value = ["employee"]
    mock_repository.create_refresh_token.return_value = MagicMock()

    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        lambda _plain, _hash: True,
    )
    result = await service.login("user@example.com", "password")

    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"
    mock_repository.create_audit_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_wrong_password(
    service: AuthService,
    mock_repository: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_repository.get_user_by_email.return_value = _active_user()
    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        lambda _plain, _hash: False,
    )
    with pytest.raises(AuthError) as exc_info:
        await service.login("user@example.com", "wrong")
    assert exc_info.value.message == "Invalid credentials"
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(
    service: AuthService,
    mock_repository: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_repository.get_user_by_email.return_value = _active_user(is_active=False)
    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        lambda _plain, _hash: True,
    )
    with pytest.raises(AuthError) as exc_info:
        await service.login("user@example.com", "password")
    assert exc_info.value.message == "Account is inactive"


@pytest.mark.asyncio
async def test_refresh_revoked_token_triggers_reuse_detection(
    service: AuthService,
    mock_repository: AsyncMock,
    settings: Settings,
) -> None:
    user = _active_user()
    from app.core.security import create_refresh_token, hash_token

    refresh = create_refresh_token({"sub": str(user.id), "roles": []}, settings=settings)
    stored = MagicMock()
    stored.id = uuid.uuid4()
    stored.user_id = user.id
    stored.token_hash = hash_token(refresh)
    stored.expires_at = datetime.now(UTC) + timedelta(days=1)
    stored.revoked_at = datetime.now(UTC)
    mock_repository.get_refresh_token_by_hash.return_value = stored

    with pytest.raises(AuthError):
        await service.refresh_tokens(refresh)

    mock_repository.revoke_all_refresh_tokens_for_user.assert_awaited_once_with(user.id)


@pytest.mark.asyncio
async def test_forgot_password_always_returns(
    service: AuthService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_user_by_email.return_value = None
    data = await service.forgot_password_with_token("missing@example.com")
    assert data.reset_token is None


@pytest.mark.asyncio
async def test_reset_password_invalid_token(
    service: AuthService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_password_reset_by_hash.return_value = None
    with pytest.raises(AuthError) as exc_info:
        await service.reset_password("bad-token", "NewPassword123!")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_logout_writes_audit(
    service: AuthService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    await service.logout(user_id, ip_address="127.0.0.1")
    mock_repository.revoke_all_refresh_tokens_for_user.assert_awaited_once_with(user_id)
    mock_repository.create_audit_log.assert_awaited_once()
