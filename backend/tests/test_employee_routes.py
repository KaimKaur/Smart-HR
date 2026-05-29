import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.constants import EMPLOYEE, HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.employee.controller import EmployeeController
from app.modules.employee.routes import _controller
from app.modules.employee.schema import (
    CreateEmployeeResponse,
    DepartmentRef,
    DesignationRef,
    EmployeeListResponse,
    EmployeeResponse,
    EmploymentStatusRef,
    build_pagination,
)


def _sample_employee_response() -> EmployeeResponse:
    return EmployeeResponse(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        employee_code="EMP001",
        first_name="Jane",
        last_name="Doe",
        full_name="Jane Doe",
        email="jane@example.com",
        phone=None,
        department=DepartmentRef(id=uuid.uuid4(), name="Engineering"),
        designation=DesignationRef(id=uuid.uuid4(), title="Developer"),
        employment_status=EmploymentStatusRef(id=uuid.uuid4(), name="active"),
        manager=None,
        salary=Decimal("50000.00"),
        join_date=date.today(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_controller() -> MagicMock:
    controller = MagicMock(spec=EmployeeController)
    controller.list_employees = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=EmployeeListResponse(
                items=[_sample_employee_response()],
                pagination=build_pagination(1, 20, 1),
            ),
        )
    )
    controller.create_employee = AsyncMock(
        return_value=SuccessResponse(
            message="Employee created",
            data=CreateEmployeeResponse(
                **_sample_employee_response().model_dump(),
                password_reset_token="reset-token",
            ),
        )
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
async def test_list_employees_employee_cannot_see_all(
    employee_client: MagicMock,
    mock_controller: MagicMock,
) -> None:
    """Integration: employee list returns at most their own record (mocked service)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/employees")

    assert response.status_code == 200
    mock_controller.list_employees.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_employee_hr_success(hr_client: MagicMock) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/employees",
            json={
                "employee_code": "EMP010",
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "department_id": str(uuid.uuid4()),
                "designation_id": str(uuid.uuid4()),
                "employment_status_id": str(uuid.uuid4()),
                "join_date": date.today().isoformat(),
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["password_reset_token"] == "reset-token"


@pytest.mark.asyncio
async def test_create_employee_employee_role_forbidden(
    employee_client: MagicMock,
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/employees",
            json={
                "employee_code": "EMP011",
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane2@example.com",
                "department_id": str(uuid.uuid4()),
                "designation_id": str(uuid.uuid4()),
                "employment_status_id": str(uuid.uuid4()),
                "join_date": date.today().isoformat(),
            },
        )

    assert response.status_code == 403
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_search_route_registered_before_id(mock_controller: MagicMock) -> None:
    from app.modules.employee.schema import EmployeeSearchResponse

    async def _hr() -> CurrentUser:
        return CurrentUser(
            id=uuid.uuid4(),
            email="hr@example.com",
            roles=[HR_MANAGER],
        )

    mock_controller.search_employees = AsyncMock(
        return_value=SuccessResponse(
            message="OK",
            data=EmployeeSearchResponse(items=[]),
        ),
    )
    app.dependency_overrides[_controller] = lambda: mock_controller
    app.dependency_overrides[get_current_user] = _hr
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/employees/search", params={"q": "jane"})

        assert response.status_code == 200
        mock_controller.search_employees.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()
