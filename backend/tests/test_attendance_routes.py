import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.core.constants import EMPLOYEE, HR_MANAGER
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.attendance.controller import AttendanceController
from app.modules.attendance.routes import _controller
from app.modules.attendance.schema import (
    AttendanceRecordResponse,
    DailyAttendanceResponse,
)


def _record_response() -> AttendanceRecordResponse:
    return AttendanceRecordResponse(
        id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        attendance_date=date.today(),
        check_in_time=datetime.now(),
        check_out_time=None,
        work_duration_minutes=None,
        attendance_status_id=uuid.uuid4(),
        status_name="present",
        created_at=datetime.now(),
    )


@pytest.fixture
def mock_controller() -> MagicMock:
    controller = MagicMock(spec=AttendanceController)
    controller.check_in = AsyncMock(
        return_value=SuccessResponse(message="Checked in", data=_record_response()),
    )
    controller.daily_attendance = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=DailyAttendanceResponse(
                date=date.today(),
                present_count=1,
                absent_count=0,
                late_count=0,
                employees=[],
            ),
        ),
    )
    return controller


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


@pytest.fixture
def hr_client(mock_controller: MagicMock):
    async def _hr() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="hr@example.com",
            roles=[HR_MANAGER],
        )

    app.dependency_overrides[_controller] = lambda: mock_controller
    app.dependency_overrides[get_current_user] = _hr
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_check_in_success(employee_client: MagicMock) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/attendance/check-in", json={})

    assert response.status_code == 200
    assert response.json()["data"]["status_name"] == "present"


@pytest.mark.asyncio
async def test_daily_attendance_employee_forbidden(employee_client: MagicMock) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/attendance/daily",
            params={"date": date.today().isoformat()},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_daily_attendance_hr_allowed(hr_client: MagicMock) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/attendance/daily",
            params={"date": date.today().isoformat()},
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_check_in_duplicate_via_controller(hr_client: MagicMock) -> None:
    mock_controller = MagicMock(spec=AttendanceController)
    mock_controller.check_in = AsyncMock(
        side_effect=HTTPException(
            status_code=409,
            detail={"message": "Attendance record already exists for today", "errors": []},
        ),
    )

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
            response = await client.post("/api/v1/attendance/check-in", json={})

        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()
