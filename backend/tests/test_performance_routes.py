import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.core.constants import DEPARTMENT_MANAGER, EMPLOYEE, HR_MANAGER
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.performance.routes import _controller as performance_controller_dep
from app.modules.performance.routes import _employee_or_hr_or_admin


@pytest.fixture
def mock_controller() -> MagicMock:
    controller = MagicMock()
    controller.create_review = AsyncMock()
    controller.create_cycle = AsyncMock()
    controller.performance_report = AsyncMock()
    return controller


@pytest.mark.asyncio
async def test_create_review_rating_out_of_range_returns_422(
    mock_controller: MagicMock,
) -> None:
    actor_user_id = uuid.uuid4()
    cycle_id = uuid.uuid4()
    employee_id = uuid.uuid4()

    async def _employee() -> CurrentUser:
        return CurrentUser(
            id=actor_user_id,
            email="employee@example.com",
            roles=[EMPLOYEE],
        )

    app.dependency_overrides[get_current_user] = _employee
    app.dependency_overrides[performance_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/performance/reviews",
                json={
                    "cycle_id": str(cycle_id),
                    "employee_id": str(employee_id),
                    "rating": 0.5,
                    "comments": "bad",
                },
            )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_review_duplicate_returns_409_via_controller(
    mock_controller: MagicMock,
) -> None:
    actor_user_id = uuid.uuid4()
    cycle_id = uuid.uuid4()
    employee_id = uuid.uuid4()

    async def _hr() -> CurrentUser:
        return CurrentUser(
            id=actor_user_id,
            email="hr@example.com",
            roles=[HR_MANAGER],
        )

    mock_controller.create_review = AsyncMock(
        side_effect=HTTPException(
            status_code=409,
            detail={"message": "Duplicate performance review", "errors": []},
        )
    )

    app.dependency_overrides[get_current_user] = _hr
    app.dependency_overrides[performance_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/performance/reviews",
                json={
                    "cycle_id": str(cycle_id),
                    "employee_id": str(employee_id),
                    "rating": 4.0,
                    "comments": "ok",
                },
            )

        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_cycle_employee_forbidden(
    mock_controller: MagicMock,
) -> None:
    actor_user_id = uuid.uuid4()

    async def _employee() -> CurrentUser:
        return CurrentUser(
            id=actor_user_id,
            email="employee@example.com",
            roles=[EMPLOYEE],
        )

    app.dependency_overrides[get_current_user] = _employee
    app.dependency_overrides[performance_controller_dep] = lambda: mock_controller
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/performance/cycles",
                json={
                    "name": "Cycle 1",
                    "start_date": "2026-06-01",
                    "end_date": "2026-06-10",
                },
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()

