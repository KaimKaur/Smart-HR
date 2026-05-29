import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.core.constants import EMPLOYEE, HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.organization.department_controller import DepartmentController
from app.modules.organization.department_routes import _controller as department_controller_dep
from app.modules.organization.department_schema import (
    DepartmentListResponse,
    DepartmentResponse,
    build_pagination,
)
from app.modules.organization.designation_routes import _controller as designation_controller_dep
from app.modules.organization.status_routes import _controller as status_controller_dep
from app.modules.organization.status_controller import StatusController
from app.modules.organization.status_schema import EmploymentStatusListResponse, EmploymentStatusResponse


def _department_response() -> DepartmentResponse:
    return DepartmentResponse(
        id=uuid.uuid4(),
        name="Engineering",
        description=None,
        employee_count=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_department_controller() -> MagicMock:
    controller = MagicMock(spec=DepartmentController)
    controller.list_departments = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=DepartmentListResponse(
                items=[_department_response()],
                pagination=build_pagination(1, 20, 1),
            ),
        )
    )
    controller.create_department = AsyncMock(
        return_value=SuccessResponse(
            message="Department created",
            data=_department_response(),
        )
    )
    controller.delete_department = AsyncMock(return_value=None)
    return controller


@pytest.fixture
def employee_client(mock_department_controller: MagicMock):
    async def _employee() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="employee@example.com",
            roles=[EMPLOYEE],
        )

    app.dependency_overrides[department_controller_dep] = lambda: mock_department_controller
    app.dependency_overrides[get_current_user] = _employee
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def hr_client(mock_department_controller: MagicMock):
    async def _hr() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="hr@example.com",
            roles=[HR_MANAGER],
        )

    app.dependency_overrides[department_controller_dep] = lambda: mock_department_controller
    app.dependency_overrides[get_current_user] = _hr
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_departments_authenticated_employee(
    employee_client: MagicMock,
    mock_department_controller: MagicMock,
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/departments")

    assert response.status_code == 200
    mock_department_controller.list_departments.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_department_employee_forbidden(
    employee_client: MagicMock,
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/departments",
            json={"name": "New Dept"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_department_hr_success(hr_client: MagicMock) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/departments",
            json={"name": "New Dept"},
        )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_delete_department_in_use_returns_409(
    hr_client: MagicMock,
    mock_department_controller: MagicMock,
) -> None:
    mock_department_controller.delete_department = AsyncMock(
        side_effect=HTTPException(
            status_code=409,
            detail={
                "message": "Cannot delete department with assigned employees",
                "errors": [],
            },
        ),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(f"/api/v1/departments/{uuid.uuid4()}")

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_department_not_found(hr_client: MagicMock) -> None:
    controller = MagicMock(spec=DepartmentController)
    controller.get_department = AsyncMock(
        side_effect=HTTPException(
            status_code=404,
            detail={"message": "Department not found", "errors": []},
        ),
    )
    app.dependency_overrides[department_controller_dep] = lambda: controller

    async def _hr() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="hr@example.com",
            roles=[HR_MANAGER],
        )

    app.dependency_overrides[get_current_user] = _hr
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/departments/{uuid.uuid4()}")

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_employment_statuses() -> None:
    controller = MagicMock(spec=StatusController)
    controller.list_employment_statuses = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=EmploymentStatusListResponse(
                items=[
                    EmploymentStatusResponse(
                        id=uuid.uuid4(),
                        name="active",
                    ),
                ],
            ),
        ),
    )

    async def _user() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="user@example.com",
            roles=[EMPLOYEE],
        )

    app.dependency_overrides[status_controller_dep] = lambda: controller
    app.dependency_overrides[get_current_user] = _user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/employment-statuses")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]["items"]) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_attendance_statuses() -> None:
    controller = MagicMock(spec=StatusController)
    from app.modules.organization.status_schema import (
        AttendanceStatusListResponse,
        AttendanceStatusResponse,
    )

    controller.list_attendance_statuses = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=AttendanceStatusListResponse(
                items=[AttendanceStatusResponse(id=uuid.uuid4(), name="present")],
            ),
        ),
    )

    async def _user() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="user@example.com",
            roles=[EMPLOYEE],
        )

    app.dependency_overrides[status_controller_dep] = lambda: controller
    app.dependency_overrides[get_current_user] = _user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/attendance-statuses")

        assert response.status_code == 200
        assert response.json()["data"]["items"][0]["name"] == "present"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_designation_non_hr_forbidden(
    mock_department_controller: MagicMock,
) -> None:
    async def _employee() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="employee@example.com",
            roles=[EMPLOYEE],
        )

    app.dependency_overrides[designation_controller_dep] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = _employee
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/designations",
                json={"title": "Lead"},
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
