import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, create_access_token, get_current_user
from app.main import app
from app.modules.auth.controller import AuthController
from app.modules.auth.routes import _controller
from app.modules.auth.schema import MeResponse, TokenData


@pytest.fixture
def mock_controller() -> MagicMock:
    controller = MagicMock(spec=AuthController)
    controller.login = AsyncMock(
        return_value=SuccessResponse(
            message="Login successful",
            data=TokenData(
                access_token="access",
                refresh_token="refresh",
                token_type="bearer",
            ),
        )
    )
    controller.refresh = AsyncMock(
        return_value=SuccessResponse(
            message="Token refreshed",
            data=TokenData(
                access_token="access2",
                refresh_token="refresh2",
                token_type="bearer",
            ),
        )
    )
    controller.logout = AsyncMock()
    from fastapi import Response

    controller.logout.return_value = Response(status_code=204)
    controller.forgot_password = AsyncMock(
        return_value=SuccessResponse(
            message="If an account exists for this email, password reset instructions have been sent.",
            data={"reset_token": None},
        )
    )
    controller.reset_password = AsyncMock(
        return_value=SuccessResponse(message="Password reset successful", data=None)
    )
    controller.me = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=MeResponse(
                id=uuid.uuid4(),
                email="user@example.com",
                is_active=True,
                roles=["employee"],
                created_at=datetime.now(),
            ),
        )
    )
    return controller


@pytest.fixture
def client(mock_controller: MagicMock):
    app.dependency_overrides[_controller] = lambda: mock_controller
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_route_returns_token_envelope(client: MagicMock) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        response = await http_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "password123"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["access_token"] == "access"
    assert body["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_me_requires_authentication() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        response = await http_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_me_with_valid_token(client: MagicMock) -> None:
    user_id = uuid.uuid4()

    async def _current_user() -> CurrentUser:
        return CurrentUser(
            id=user_id,
            email="user@example.com",
            roles=["employee"],
        )

    app.dependency_overrides[get_current_user] = _current_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            response = await http_client.get("/api/v1/auth/me")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_logout_returns_204(client: MagicMock) -> None:
    user_id = uuid.uuid4()

    async def _current_user() -> CurrentUser:
        return CurrentUser(
            id=user_id,
            email="user@example.com",
            roles=["employee"],
        )

    app.dependency_overrides[get_current_user] = _current_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            response = await http_client.post("/api/v1/auth/logout")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 204
