import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.core.security import CurrentUser
from app.modules.dashboard.errors import DashboardError
from app.modules.dashboard.schema import (
    AttendanceDashboardResponse,
    EmployeeDashboardResponse,
    HRDashboardResponse,
    PerformanceDashboardResponse,
    RecruitmentDashboardResponse,
)
from app.modules.dashboard.service import DashboardService


def _actor(roles: list[str]) -> CurrentUser:
    return CurrentUser(
        id=uuid.uuid4(),
        email="user@example.com",
        roles=roles,
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    return session


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


@pytest.mark.asyncio
async def test_hr_dashboard_requires_hr_or_admin(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["employee"])

    with pytest.raises(DashboardError) as exc_info:
        await service.get_hr_dashboard(actor=actor, today=date(2024, 1, 1))

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_hr_dashboard_returns_snapshot(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["hr_manager"])

    mock_repository.get_hr_snapshot.return_value = {
        "total_employees": 10,
        "active_employees": 8,
        "new_hires_last_30_days": 2,
        "departments_count": 3,
        "attendance_rate_today": 75.0,
        "pending_leave_requests_count": 1,
        "open_job_postings": 2,
        "candidates_this_month": 5,
    }

    result = await service.get_hr_dashboard(actor=actor, today=date(2024, 1, 1))

    assert isinstance(result, HRDashboardResponse)
    assert result.total_employees == 10
    assert result.active_employees == 8
    assert result.attendance_rate_today == 75.0


@pytest.mark.asyncio
async def test_recruitment_dashboard_requires_recruitment_roles(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["department_manager"])

    with pytest.raises(DashboardError) as exc_info:
        await service.get_recruitment_dashboard(actor=actor, today=date(2024, 1, 1))

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_recruitment_dashboard_returns_snapshot(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["recruiter"])

    mock_repository.get_recruitment_snapshot.return_value = {
        "open_jobs": 2,
        "total_candidates": 10,
        "shortlisted_candidates": 3,
        "rejected_candidates": 1,
        "pending_screening_candidates": 2,
        "average_ai_score": 78.5,
        "jobs": [
            {
                "job_id": str(uuid.uuid4()),
                "title": "Software Engineer",
                "open_applications": 5,
                "shortlisted_applications": 1,
                "rejected_applications": 1,
                "pending_screening_applications": 2,
                "average_ai_score": 80.0,
                "top_candidates": [
                    {
                        "application_id": str(uuid.uuid4()),
                        "candidate_id": str(uuid.uuid4()),
                        "full_name": "Jane Doe",
                        "email": "jane@example.com",
                        "ai_score": 95.0,
                    }
                ],
            }
        ],
    }

    result = await service.get_recruitment_dashboard(actor=actor, today=date(2024, 1, 1))

    assert isinstance(result, RecruitmentDashboardResponse)
    assert result.open_jobs == 2
    assert result.average_ai_score == 78.5
    assert len(result.jobs) == 1


@pytest.mark.asyncio
async def test_attendance_dashboard_requires_hr_or_admin(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["recruiter"])

    with pytest.raises(DashboardError) as exc_info:
        await service.get_attendance_dashboard(actor=actor, today=date(2024, 1, 1))

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_attendance_dashboard_returns_snapshot(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["system_administrator"])

    mock_repository.get_attendance_snapshot.return_value = {
        "today_date": date(2024, 1, 1),
        "present_count": 8,
        "absent_count": 2,
        "late_count": 1,
        "attendance_rate_today": 80.0,
        "weekly_trend": [
            {"date": date(2023, 12, 26), "present_count": 5, "absent_count": 1},
        ],
        "top_absent_departments": [
            {"department_id": str(uuid.uuid4()), "department_name": "HR", "absent_count": 2},
        ],
    }

    result = await service.get_attendance_dashboard(actor=actor, today=date(2024, 1, 1))
    assert isinstance(result, AttendanceDashboardResponse)
    assert result.present_count == 8


@pytest.mark.asyncio
async def test_performance_dashboard_requires_hr_or_admin(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["employee"])

    with pytest.raises(DashboardError) as exc_info:
        await service.get_performance_dashboard(actor=actor, today=date(2024, 1, 1))

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_performance_dashboard_returns_snapshot(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["hr_manager"])

    mock_repository.get_performance_snapshot.return_value = {
        "active_cycle_id": str(uuid.uuid4()),
        "active_cycle_name": "Q1 2024",
        "average_rating": 4.2,
        "top_performers": [],
        "employees_without_review": 3,
    }

    result = await service.get_performance_dashboard(actor=actor, today=date(2024, 1, 1))
    assert isinstance(result, PerformanceDashboardResponse)
    assert result.active_cycle_name == "Q1 2024"


@pytest.mark.asyncio
async def test_employee_dashboard_requires_employee_or_manager(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["recruiter"])

    with pytest.raises(DashboardError) as exc_info:
        await service.get_employee_dashboard(actor=actor, today=date(2024, 1, 1))

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_employee_dashboard_returns_snapshot(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = DashboardService(mock_session, repository=mock_repository)
    actor = _actor(["employee"])

    mock_repository.get_employee_snapshot.return_value = {
        "attendance_this_month": {"present_days": 5, "total_hours": 40.0},
        "leave_balances": [],
        "latest_performance_rating": None,
        "unread_notifications_count": 2,
        "upcoming_interviews": [],
    }

    result = await service.get_employee_dashboard(actor=actor, today=date(2024, 1, 1))
    assert isinstance(result, EmployeeDashboardResponse)
    assert result.unread_notifications_count == 2

