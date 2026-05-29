import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.user.errors import UserError
from app.modules.user.schema import AssignRoleRequest, CreateUserRequest, UpdateUserRequest
from app.modules.user.service import UserService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_auth_repository() -> AsyncMock:
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
    mock_auth_repository: AsyncMock,
) -> UserService:
    return UserService(
        mock_session,
        repository=mock_repository,
        auth_repository=mock_auth_repository,
    )


def _user_mock(**kwargs) -> MagicMock:
    user = MagicMock()
    user.id = kwargs.get("id", uuid.uuid4())
    user.email = kwargs.get("email", "new@example.com")
    user.is_active = kwargs.get("is_active", False)
    user.created_at = datetime.now()
    user.updated_at = datetime.now()
    role = MagicMock()
    role.name = kwargs.get("role_name", "employee")
    user_role = MagicMock()
    user_role.role = role
    user.user_roles = kwargs.get("user_roles", [user_role])
    return user


@pytest.mark.asyncio
async def test_create_user_duplicate_email(
    service: UserService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_user_by_email.return_value = _user_mock()
    with pytest.raises(UserError) as exc_info:
        await service.create_user(
            CreateUserRequest(email="dup@example.com"),
            actor_user_id=uuid.uuid4(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_create_user_success(
    service: UserService,
    mock_repository: AsyncMock,
    mock_auth_repository: AsyncMock,
) -> None:
    created = _user_mock()
    mock_repository.get_user_by_email.return_value = None
    mock_repository.create_user.return_value = created
    mock_repository.get_user_by_id.return_value = created
    mock_repository.get_role_by_name.return_value = MagicMock(id=uuid.uuid4())
    mock_auth_repository.invalidate_unused_password_resets = AsyncMock()
    mock_auth_repository.create_password_reset_token = AsyncMock()

    result = await service.create_user(
        CreateUserRequest(email="new@example.com", roles=["employee"]),
        actor_user_id=uuid.uuid4(),
        ip_address="127.0.0.1",
    )

    assert result.email == "new@example.com"
    assert result.password_reset_token
    mock_repository.create_audit_log.assert_awaited()


@pytest.mark.asyncio
async def test_update_user_cannot_deactivate_self(
    service: UserService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    mock_repository.get_user_by_id.return_value = _user_mock(id=user_id)
    with pytest.raises(UserError) as exc_info:
        await service.update_user(
            user_id,
            UpdateUserRequest(is_active=False),
            actor_user_id=user_id,
            ip_address="127.0.0.1",
        )
    assert "Cannot deactivate your own account" in exc_info.value.message


@pytest.mark.asyncio
async def test_assign_role_duplicate(
    service: UserService,
    mock_repository: AsyncMock,
) -> None:
    user = _user_mock()
    role_id = uuid.uuid4()
    mock_repository.get_user_by_id.return_value = user
    mock_repository.get_role_by_name.return_value = MagicMock(id=role_id)
    mock_repository.get_user_role.return_value = MagicMock()

    with pytest.raises(UserError) as exc_info:
        await service.assign_role(
            user.id,
            AssignRoleRequest(role="employee"),
            actor_user_id=uuid.uuid4(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_remove_role_not_assigned(
    service: UserService,
    mock_repository: AsyncMock,
) -> None:
    user = _user_mock()
    role_id = uuid.uuid4()
    mock_repository.get_user_by_id.return_value = user
    mock_repository.get_role_by_id.return_value = MagicMock(id=role_id, name="employee")
    mock_repository.remove_role.return_value = False

    with pytest.raises(UserError) as exc_info:
        await service.remove_role(
            user.id,
            role_id,
            actor_user_id=uuid.uuid4(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 404
