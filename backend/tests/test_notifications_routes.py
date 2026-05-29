import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.notifications.routes import _controller as notifications_controller_dep
from app.modules.notifications.schema import (
    NotificationPreferenceResponse,
    UnreadCountResponse,
)


@pytest.fixture
def mock_controller() -> MagicMock:
    controller = MagicMock()
    controller.unread_count = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=UnreadCountResponse(unread_count=3),
        )
    )
    controller.mark_all_read = AsyncMock(
        return_value=SuccessResponse(message="OK", data={"updated": 2})
    )
    controller.get_preferences = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=NotificationPreferenceResponse(in_app_enabled=True),
        )
    )
    return controller


@pytest.mark.asyncio
async def test_unread_count_endpoint_returns_number(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="user@example.com",
            roles=["employee"],
        )

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[notifications_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/notifications/count")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["unread_count"] == 3
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_mark_all_read_updates(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="user@example.com",
            roles=["employee"],
        )

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[notifications_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/notifications/read-all")

        assert response.status_code == 200
        assert response.json()["data"]["updated"] == 2
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_preferences_default_enabled_shape(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="user@example.com",
            roles=["employee"],
        )

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[notifications_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/notifications/preferences")

        assert response.status_code == 200
        assert response.json()["data"]["in_app_enabled"] is True
    finally:
        app.dependency_overrides.clear()

