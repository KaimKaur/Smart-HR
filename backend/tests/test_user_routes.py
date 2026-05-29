import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.constants import EMPLOYEE, SYSTEM_ADMINISTRATOR
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.user.controller import UserController
from app.modules.user.routes import _controller
from app.modules.user.schema import CreateUserResponse, UserListResponse, UserResponse, build_pagination


@pytest.fixture
def mock_controller() -> MagicMock:
    controller = MagicMock(spec=UserController)
    controller.create_user = AsyncMock(
        return_value=SuccessResponse(
            message="User created",
            data=CreateUserResponse(
                id=uuid.uuid4(),
                email="new@example.com",
                is_active=False,
                roles=["employee"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                password_reset_token="setup-token",
            ),
        )
    )
    controller.list_users = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=UserListResponse(
                items=[],
                pagination=build_pagination(1, 20, 0),
            ),
        )
    )
    return controller


@pytest.fixture
def admin_client(mock_controller: MagicMock):
    async def _admin() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="admin@smarthr.dev",
            roles=[SYSTEM_ADMINISTRATOR],
        )

    app.dependency_overrides[_controller] = lambda: mock_controller
    app.dependency_overrides[get_current_user] = _admin
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def employee_client(mock_controller: MagicMock):
    async def _employee() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="employee@example.com",
            roles=[EMPLOYEE],
        )

    app.dependency_overrides[_controller] = lambda: mock_controller
    app.dependency_overrides[get_current_user] = _employee
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_user_admin_success(admin_client: MagicMock) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/users",
            json={"email": "new@example.com", "roles": ["employee"]},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["password_reset_token"] == "setup-token"
    assert "password_hash" not in body["data"]


@pytest.mark.asyncio
async def test_create_user_non_admin_forbidden(employee_client: MagicMock) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/users",
            json={"email": "new@example.com", "roles": ["employee"]},
        )

    assert response.status_code == 403
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_list_users_hr_allowed(mock_controller: MagicMock) -> None:
    from app.core.constants import HR_MANAGER

    async def _hr() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="hr@example.com",
            roles=[HR_MANAGER],
        )

    app.dependency_overrides[_controller] = lambda: mock_controller
    app.dependency_overrides[get_current_user] = _hr
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["pagination"]["page"] == 1
