from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.constants import HR_MANAGER
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.reporting.routes import _reporting_controller as reporting_controller_dep


@pytest.fixture
def mock_reporting_controller() -> MagicMock:
    controller = MagicMock()
    controller.employee_report = AsyncMock(
        return_value={
            "success": True,
            "message": "Employee report retrieved",
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
    controller.attendance_report = AsyncMock(
        return_value={
            "success": True,
            "message": "Attendance report retrieved",
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
    return controller


async def _user_with_roles(*roles: str) -> CurrentUser:
    return CurrentUser(id=uuid.uuid4(), email="hr@example.com", roles=list(roles))


@pytest.mark.asyncio
async def test_employee_report_route_hr_access(
    mock_reporting_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles(HR_MANAGER)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[reporting_controller_dep] = lambda: mock_reporting_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/reports/employees")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_attendance_report_route_hr_access(
    mock_reporting_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles(HR_MANAGER)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[reporting_controller_dep] = lambda: mock_reporting_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/reports/attendance",
                params={"date_from": date(2024, 1, 1), "date_to": date(2024, 1, 31)},
            )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_employee_report_route_forbidden_for_employee(
    mock_reporting_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles("employee")

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[reporting_controller_dep] = lambda: mock_reporting_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/reports/employees")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
