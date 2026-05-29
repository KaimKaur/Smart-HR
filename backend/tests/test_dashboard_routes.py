import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.constants import HR_MANAGER, RECRUITER, SYSTEM_ADMINISTRATOR
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.dashboard.routes import _controller as dashboard_controller_dep
from app.modules.dashboard.schema import (
    AttendanceDashboardResponse,
    EmployeeDashboardResponse,
    HRDashboardResponse,
    PerformanceDashboardResponse,
    RecruitmentDashboardResponse,
)


@pytest.fixture
def mock_controller() -> MagicMock:
    controller = MagicMock()
    controller.hr_dashboard = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=HRDashboardResponse(
                total_employees=10,
                active_employees=8,
                new_hires_last_30_days=2,
                departments_count=3,
                attendance_rate_today=80.0,
                pending_leave_requests_count=1,
                open_job_postings=2,
                candidates_this_month=4,
            ),
        )
    )
    controller.recruitment_dashboard = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=RecruitmentDashboardResponse(
                open_jobs=2,
                total_candidates=10,
                shortlisted_candidates=3,
                rejected_candidates=1,
                pending_screening_candidates=2,
                average_ai_score=78.5,
                jobs=[],
            ),
        )
    )
    controller.attendance_dashboard = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=AttendanceDashboardResponse(
                today_date=date(2024, 1, 1),
                present_count=8,
                absent_count=2,
                late_count=1,
                attendance_rate_today=80.0,
                weekly_trend=[],
                top_absent_departments=[],
            ),
        )
    )
    controller.performance_dashboard = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=PerformanceDashboardResponse(
                active_cycle_id=None,
                active_cycle_name=None,
                average_rating=None,
                top_performers=[],
                employees_without_review=0,
            ),
        )
    )
    controller.employee_dashboard = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=EmployeeDashboardResponse(
                attendance_this_month=None,
                leave_balances=[],
                latest_performance_rating=None,
                unread_notifications_count=2,
                upcoming_interviews=[],
            ),
        )
    )
    return controller


async def _user_with_roles(*roles: str) -> CurrentUser:
    return CurrentUser(
        id=uuid.uuid4(),
        email="user@example.com",
        roles=list(roles),
    )


@pytest.mark.asyncio
async def test_hr_dashboard_endpoint_allows_hr(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles(HR_MANAGER)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/hr")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total_employees"] == 10
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_hr_dashboard_endpoint_forbidden_for_employee(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        # Employee role only, should be forbidden by require_roles dependency.
        return await _user_with_roles("employee")

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/hr")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_recruitment_dashboard_allows_recruiter(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles(RECRUITER)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/recruitment")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["open_jobs"] == 2
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_recruitment_dashboard_forbidden_for_employee(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles("employee")

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/recruitment")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_attendance_dashboard_allows_hr(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles(HR_MANAGER)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/attendance")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["present_count"] == 8
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_attendance_dashboard_forbidden_for_employee(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles("employee")

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/attendance")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_performance_dashboard_allows_hr(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles(HR_MANAGER)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/performance")

        assert response.status_code == 200
        assert response.json()["success"] is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_performance_dashboard_forbidden_for_employee(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles("employee")

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/performance")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_employee_dashboard_allows_employee(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles("employee")

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/employee")

        assert response.status_code == 200
        assert response.json()["data"]["unread_notifications_count"] == 2
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_employee_dashboard_forbidden_for_recruiter(
    mock_controller: MagicMock,
) -> None:
    async def _user() -> CurrentUser:
        return await _user_with_roles(RECRUITER)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[dashboard_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard/employee")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()

