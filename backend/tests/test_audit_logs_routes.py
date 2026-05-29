from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.constants import SYSTEM_ADMINISTRATOR
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.audit_logs.routes import _controller as audit_controller_dep


@pytest.fixture
def mock_audit_controller() -> MagicMock:
    controller = MagicMock()
    controller.list_audit_logs = AsyncMock(
        return_value={
            "success": True,
            "message": "OK",
            "data": {
                "items": [],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 0,
                    "total_pages": 0,
                },
            },
        },
    )
    controller.get_audit_log = AsyncMock(
        return_value={
            "success": True,
            "message": "OK",
            "data": {
                "id": str(uuid.uuid4()),
                "actor_user_id": None,
                "action": "login",
                "resource_type": "auth",
                "resource_id": None,
                "ip_address": "127.0.0.1",
                "before_state": None,
                "after_state": None,
                "created_at": datetime.now().isoformat(),
            },
        },
    )
    controller.get_user_activity = AsyncMock(return_value=controller.list_audit_logs.return_value)
    controller.get_resource_activity = AsyncMock(
        return_value=controller.list_audit_logs.return_value
    )
    return controller


async def _user_with_roles(*roles: str) -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email="admin@example.com", roles=list(roles))


@pytest.mark.asyncio
async def test_audit_logs_list_admin_access(mock_audit_controller: MagicMock) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles(SYSTEM_ADMINISTRATOR)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[audit_controller_dep] = lambda: mock_audit_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/audit-logs")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_audit_logs_list_forbidden_non_admin(mock_audit_controller: MagicMock) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles("hr_manager")

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[audit_controller_dep] = lambda: mock_audit_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/audit-logs")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_audit_log_get_by_id_admin_access(mock_audit_controller: MagicMock) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles(SYSTEM_ADMINISTRATOR)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[audit_controller_dep] = lambda: mock_audit_controller
    try:
        audit_log_id = str(uuid.uuid4())
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/audit-logs/{audit_log_id}")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
