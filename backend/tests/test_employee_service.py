import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.constants import EMPLOYEE, HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.security import CurrentUser
from app.modules.employee.errors import EmployeeError
from app.modules.employee.schema import CreateEmployeeRequest, UpdateEmployeeRequest
from app.modules.employee.service import EmployeeService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_user_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_auth_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def service(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
    mock_user_repository: AsyncMock,
    mock_auth_repository: AsyncMock,
) -> EmployeeService:
    return EmployeeService(
        mock_session,
        repository=mock_repository,
        user_repository=mock_user_repository,
        auth_repository=mock_auth_repository,
    )


def _hr_actor() -> CurrentUser:
    return CurrentUser(
        id=uuid.uuid4(),
        email="hr@example.com",
        roles=[HR_MANAGER],
    )


def _employee_actor(user_id: uuid.UUID | None = None) -> CurrentUser:
    return CurrentUser(
        id=user_id or uuid.uuid4(),
        email="emp@example.com",
        roles=[EMPLOYEE],
    )


def _employee_mock(**kwargs) -> MagicMock:
    employee = MagicMock()
    employee.id = kwargs.get("id", uuid.uuid4())
    employee.user_id = kwargs.get("user_id", uuid.uuid4())
    employee.employee_code = kwargs.get("employee_code", "EMP001")
    employee.first_name = kwargs.get("first_name", "Jane")
    employee.last_name = kwargs.get("last_name", "Doe")
    employee.email = kwargs.get("email", "jane@example.com")
    employee.phone = kwargs.get("phone", "+10000000000")
    employee.department_id = kwargs.get("department_id", uuid.uuid4())
    employee.designation_id = kwargs.get("designation_id", uuid.uuid4())
    employee.employment_status_id = kwargs.get("employment_status_id", uuid.uuid4())
    employee.manager_id = kwargs.get("manager_id")
    employee.salary = kwargs.get("salary", Decimal("50000.00"))
    employee.join_date = kwargs.get("join_date", date.today())
    employee.created_at = datetime.now()
    employee.updated_at = datetime.now()
    employee.manager = kwargs.get("manager")

    department = MagicMock()
    department.id = employee.department_id
    department.name = "Engineering"
    employee.department = department

    designation = MagicMock()
    designation.id = employee.designation_id
    designation.title = "Developer"
    employee.designation = designation

    status = MagicMock()
    status.id = employee.employment_status_id
    status.name = "active"
    employee.employment_status = status

    return employee


@pytest.mark.asyncio
async def test_create_employee_duplicate_code(
    service: EmployeeService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_employee_by_code.return_value = _employee_mock()
    with pytest.raises(EmployeeError) as exc_info:
        await service.create_employee(
            CreateEmployeeRequest(
                employee_code="EMP001",
                first_name="Jane",
                last_name="Doe",
                email="jane@example.com",
                department_id=uuid.uuid4(),
                designation_id=uuid.uuid4(),
                employment_status_id=uuid.uuid4(),
                join_date=date.today(),
            ),
            actor=_hr_actor(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_create_employee_invalid_department(
    service: EmployeeService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_employee_by_code.return_value = None
    mock_repository.get_employee_by_email.return_value = None
    mock_repository.get_department_by_id.return_value = None
    dept_id = uuid.uuid4()
    with pytest.raises(EmployeeError) as exc_info:
        await service.create_employee(
            CreateEmployeeRequest(
                employee_code="EMP002",
                first_name="Jane",
                last_name="Doe",
                email="jane@example.com",
                department_id=dept_id,
                designation_id=uuid.uuid4(),
                employment_status_id=uuid.uuid4(),
                join_date=date.today(),
            ),
            actor=_hr_actor(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 400
    assert "department" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_update_employee_self_manager(
    service: EmployeeService,
    mock_repository: AsyncMock,
) -> None:
    employee_id = uuid.uuid4()
    employee = _employee_mock(id=employee_id)
    mock_repository.get_employee_by_id.return_value = employee
    mock_repository.get_department_by_id.return_value = MagicMock()
    mock_repository.get_designation_by_id.return_value = MagicMock()
    mock_repository.get_employment_status_by_id.return_value = MagicMock()

    with pytest.raises(EmployeeError) as exc_info:
        await service.update_employee(
            employee_id,
            UpdateEmployeeRequest(manager_id=employee_id),
            actor=_hr_actor(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 400
    assert "own manager" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_create_employee_success_writes_audit(
    service: EmployeeService,
    mock_repository: AsyncMock,
    mock_user_repository: AsyncMock,
    mock_auth_repository: AsyncMock,
) -> None:
    created = _employee_mock()
    mock_repository.get_employee_by_code.return_value = None
    mock_repository.get_employee_by_email.return_value = None
    mock_repository.get_department_by_id.return_value = MagicMock()
    mock_repository.get_designation_by_id.return_value = MagicMock()
    mock_repository.get_employment_status_by_id.return_value = MagicMock()
    mock_user_repository.get_user_by_email.return_value = None
    mock_user_repository.create_user.return_value = MagicMock(id=uuid.uuid4())
    mock_user_repository.get_role_by_name.return_value = MagicMock(id=uuid.uuid4())
    mock_repository.create_employee.return_value = created
    mock_auth_repository.invalidate_unused_password_resets = AsyncMock()
    mock_auth_repository.create_password_reset_token = AsyncMock()

    result = await service.create_employee(
        CreateEmployeeRequest(
            employee_code="EMP004",
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            department_id=uuid.uuid4(),
            designation_id=uuid.uuid4(),
            employment_status_id=uuid.uuid4(),
            join_date=date.today(),
        ),
        actor=_hr_actor(),
        ip_address="127.0.0.1",
    )

    assert result.password_reset_token is not None
    mock_repository.create_audit_log.assert_awaited()


@pytest.mark.asyncio
async def test_list_employees_employee_sees_only_self(
    service: EmployeeService,
    mock_repository: AsyncMock,
) -> None:
    actor = _employee_actor()
    own = _employee_mock(user_id=actor.id)
    mock_repository.get_employee_by_user_id.return_value = own

    result = await service.list_employees(
        actor=actor,
        search=None,
        department_id=None,
        designation_id=None,
        employment_status_id=None,
        sort_by="created_at",
        sort_order="desc",
        page=1,
        page_size=20,
    )

    assert len(result.items) == 1
    assert result.items[0].id == own.id
    assert result.items[0].salary is None
    mock_repository.list_employees.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_employee_employee_cannot_change_salary(
    service: EmployeeService,
    mock_repository: AsyncMock,
) -> None:
    actor = _employee_actor()
    employee = _employee_mock(user_id=actor.id)
    mock_repository.get_employee_by_id.return_value = employee

    from app.modules.employee.schema import EmployeeSelfUpdateRequest

    updated = _employee_mock(user_id=actor.id, phone="+19998887777")
    mock_repository.update_employee.return_value = updated

    await service.update_employee(
        employee.id,
        EmployeeSelfUpdateRequest(phone="+19998887777"),
        actor=actor,
        ip_address="127.0.0.1",
    )
    mock_repository.update_employee.assert_awaited_with(
        employee.id,
        phone="+19998887777",
    )


@pytest.mark.asyncio
async def test_deactivate_requires_admin(
    service: EmployeeService,
) -> None:
    actor = CurrentUser(
        id=uuid.uuid4(),
        email="hr@example.com",
        roles=[HR_MANAGER],
    )
    with pytest.raises(EmployeeError) as exc_info:
        await service.deactivate_employee(
            uuid.uuid4(),
            actor=actor,
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_manager_returns_none(
    service: EmployeeService,
    mock_repository: AsyncMock,
) -> None:
    employee = _employee_mock(manager=None)
    mock_repository.get_employee_by_id.return_value = employee

    result = await service.get_manager(
        employee.id,
        actor=CurrentUser(
            id=uuid.uuid4(),
            email="hr@example.com",
            roles=[SYSTEM_ADMINISTRATOR],
        ),
    )
    assert result is None
