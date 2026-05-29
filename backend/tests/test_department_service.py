import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.organization.department_schema import CreateDepartmentRequest, UpdateDepartmentRequest
from app.modules.organization.department_service import DepartmentService
from app.modules.organization.errors import OrganizationError


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def service(mock_session: AsyncMock, mock_repository: AsyncMock) -> DepartmentService:
    return DepartmentService(mock_session, repository=mock_repository)


def _department_mock(**kwargs) -> MagicMock:
    dept = MagicMock()
    dept.id = kwargs.get("id", uuid.uuid4())
    dept.name = kwargs.get("name", "Engineering")
    dept.description = kwargs.get("description", "Eng dept")
    dept.created_at = datetime.now()
    dept.updated_at = datetime.now()
    return dept


@pytest.mark.asyncio
async def test_create_department_duplicate_name(
    service: DepartmentService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_department_by_name.return_value = _department_mock()
    with pytest.raises(OrganizationError) as exc_info:
        await service.create_department(
            CreateDepartmentRequest(name="Engineering"),
            actor_user_id=uuid.uuid4(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_create_department_success_audit(
    service: DepartmentService,
    mock_repository: AsyncMock,
) -> None:
    created = _department_mock(name="HR")
    mock_repository.get_department_by_name.return_value = None
    mock_repository.create_department.return_value = created

    result = await service.create_department(
        CreateDepartmentRequest(name="HR"),
        actor_user_id=uuid.uuid4(),
        ip_address="127.0.0.1",
    )

    assert result.name == "HR"
    assert result.employee_count == 0
    mock_repository.create_audit_log.assert_awaited()


@pytest.mark.asyncio
async def test_delete_department_with_employees(
    service: DepartmentService,
    mock_repository: AsyncMock,
) -> None:
    dept = _department_mock()
    mock_repository.get_department_by_id.return_value = dept
    mock_repository.count_active_employees.return_value = 3

    with pytest.raises(OrganizationError) as exc_info:
        await service.delete_department(
            dept.id,
            actor_user_id=uuid.uuid4(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_get_department_not_found(
    service: DepartmentService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_department_with_count.return_value = None
    with pytest.raises(OrganizationError) as exc_info:
        await service.get_department(uuid.uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_list_departments_includes_count(
    service: DepartmentService,
    mock_repository: AsyncMock,
) -> None:
    dept = _department_mock()
    mock_repository.list_departments.return_value = ([(dept, 5)], 1)

    result = await service.list_departments(page=1, page_size=20)

    assert result.items[0].employee_count == 5


@pytest.mark.asyncio
async def test_update_department_duplicate_name(
    service: DepartmentService,
    mock_repository: AsyncMock,
) -> None:
    dept_id = uuid.uuid4()
    dept = _department_mock(id=dept_id, name="Old")
    other = _department_mock(name="Taken")
    mock_repository.get_department_by_id.return_value = dept
    mock_repository.get_department_by_name.return_value = other

    with pytest.raises(OrganizationError) as exc_info:
        await service.update_department(
            dept_id,
            UpdateDepartmentRequest(name="Taken"),
            actor_user_id=uuid.uuid4(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409
