import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.constants import DEPARTMENT_MANAGER, EMPLOYEE, HR_MANAGER
from app.core.security import CurrentUser
from app.modules.leave.errors import LeaveError
from app.modules.leave.schema import CreateLeaveRequest, LeaveApprovalRequest
from app.modules.leave.service import LeaveService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def service(mock_session: AsyncMock, mock_repository: AsyncMock) -> LeaveService:
    return LeaveService(mock_session, repository=mock_repository)


def _actor(**kwargs) -> CurrentUser:
    return CurrentUser(
        id=kwargs.get("user_id", uuid.uuid4()),
        email="user@example.com",
        roles=kwargs.get("roles", [EMPLOYEE]),
    )


def _employee_mock(**kwargs) -> MagicMock:
    employee = MagicMock()
    employee.id = kwargs.get("id", uuid.uuid4())
    employee.user_id = kwargs.get("user_id", uuid.uuid4())
    employee.first_name = "Jane"
    employee.last_name = "Doe"
    employee.manager_id = kwargs.get("manager_id")
    employee.department_id = kwargs.get("department_id", uuid.uuid4())
    return employee


def _leave_type_mock(**kwargs) -> MagicMock:
    leave_type = MagicMock()
    leave_type.id = kwargs.get("id", uuid.uuid4())
    leave_type.name = kwargs.get("name", "annual")
    leave_type.annual_allocation = kwargs.get("annual_allocation", 20)
    return leave_type


def _balance_mock(**kwargs) -> MagicMock:
    balance = MagicMock()
    balance.id = kwargs.get("id", uuid.uuid4())
    balance.employee_id = kwargs.get("employee_id", uuid.uuid4())
    balance.leave_type_id = kwargs.get("leave_type_id", uuid.uuid4())
    balance.balance = kwargs.get("balance", Decimal("10"))
    return balance


def _request_mock(**kwargs) -> MagicMock:
    request = MagicMock()
    request.id = kwargs.get("id", uuid.uuid4())
    request.employee_id = kwargs.get("employee_id", uuid.uuid4())
    request.leave_type_id = kwargs.get("leave_type_id", uuid.uuid4())
    request.start_date = kwargs.get("start_date", date(2026, 6, 1))
    request.end_date = kwargs.get("end_date", date(2026, 6, 3))
    request.reason = "vacation"
    request.status = kwargs.get("status", "pending")
    request.created_at = datetime.now()
    request.approvals = kwargs.get("approvals", [])
    request.employee = kwargs.get(
        "employee",
        _employee_mock(id=request.employee_id),
    )
    request.leave_type = kwargs.get(
        "leave_type",
        _leave_type_mock(id=request.leave_type_id),
    )
    return request


@pytest.mark.asyncio
async def test_create_leave_insufficient_balance(
    service: LeaveService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    leave_type_id = uuid.uuid4()

    mock_repository.get_employee_by_user_id.return_value = _employee_mock(
        id=employee_id,
        user_id=user_id,
    )
    mock_repository.get_leave_type_by_id.return_value = _leave_type_mock(id=leave_type_id)
    mock_repository.get_leave_balance.return_value = _balance_mock(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        balance=Decimal("1"),
    )

    with pytest.raises(LeaveError) as exc_info:
        await service.create_leave_request(
            CreateLeaveRequest(
                leave_type_id=leave_type_id,
                start_date=date(2026, 6, 1),
                end_date=date(2026, 6, 5),
            ),
            actor=_actor(user_id=user_id),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 400
    assert any(e.get("field") == "current_balance" for e in exc_info.value.errors)


@pytest.mark.asyncio
async def test_create_leave_overlap(
    service: LeaveService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    leave_type_id = uuid.uuid4()

    mock_repository.get_employee_by_user_id.return_value = _employee_mock(
        id=employee_id,
        user_id=user_id,
    )
    mock_repository.get_leave_type_by_id.return_value = _leave_type_mock(id=leave_type_id)
    mock_repository.get_leave_balance.return_value = _balance_mock(
        balance=Decimal("20"),
    )
    mock_repository.has_overlapping_leave.return_value = True

    with pytest.raises(LeaveError) as exc_info:
        await service.create_leave_request(
            CreateLeaveRequest(
                leave_type_id=leave_type_id,
                start_date=date(2026, 6, 1),
                end_date=date(2026, 6, 2),
            ),
            actor=_actor(user_id=user_id),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_create_leave_success(
    service: LeaveService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    leave_type_id = uuid.uuid4()
    created = _request_mock(employee_id=employee_id, leave_type_id=leave_type_id)

    manager_id = uuid.uuid4()
    employee = _employee_mock(id=employee_id, user_id=user_id, manager_id=manager_id)
    manager = _employee_mock(id=manager_id, user_id=uuid.uuid4())

    mock_repository.get_employee_by_user_id.return_value = employee
    mock_repository.get_employee_by_id.return_value = manager
    mock_repository.get_leave_type_by_id.return_value = _leave_type_mock(id=leave_type_id)
    mock_repository.get_leave_balance.return_value = _balance_mock(balance=Decimal("20"))
    mock_repository.has_overlapping_leave.return_value = False
    mock_repository.create_leave_request.return_value = created
    created.employee = employee

    result = await service.create_leave_request(
        CreateLeaveRequest(
            leave_type_id=leave_type_id,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 2),
        ),
        actor=_actor(user_id=user_id),
        ip_address="127.0.0.1",
    )

    assert result.status == "pending"
    mock_repository.create_audit_log.assert_awaited()
    mock_repository.create_notification.assert_awaited()


@pytest.mark.asyncio
async def test_approve_deducts_balance(
    service: LeaveService,
    mock_repository: AsyncMock,
) -> None:
    approver_id = uuid.uuid4()
    request = _request_mock(status="pending")
    balance = _balance_mock(
        employee_id=request.employee_id,
        leave_type_id=request.leave_type_id,
        balance=Decimal("10"),
    )
    updated_balance = _balance_mock(balance=Decimal("7"))
    approved = _request_mock(status="approved")

    mock_repository.get_leave_request_by_id.side_effect = [request, approved]
    mock_repository.get_leave_balance.return_value = balance
    mock_repository.update_leave_balance.return_value = updated_balance
    mock_repository.count_approvals_for_request.return_value = 0
    mock_repository.update_leave_status.return_value = approved

    result = await service.approve_leave(
        request.id,
        LeaveApprovalRequest(remarks="ok"),
        actor=_actor(user_id=approver_id, roles=[HR_MANAGER]),
        ip_address="127.0.0.1",
    )

    assert result.status == "approved"
    mock_repository.update_leave_balance.assert_awaited_once()
    assert mock_repository.create_audit_log.await_count >= 2


@pytest.mark.asyncio
async def test_approve_own_request_blocked(
    service: LeaveService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee = _employee_mock(user_id=user_id)
    request = _request_mock(status="pending", employee=employee)

    mock_repository.get_leave_request_by_id.return_value = request

    with pytest.raises(LeaveError) as exc_info:
        await service.approve_leave(
            request.id,
            LeaveApprovalRequest(),
            actor=_actor(user_id=user_id, roles=[DEPARTMENT_MANAGER]),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_cancel_approved_by_employee_blocked(
    service: LeaveService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee = _employee_mock(user_id=user_id)
    request = _request_mock(status="approved", employee=employee)

    mock_repository.get_leave_request_by_id.return_value = request

    with pytest.raises(LeaveError) as exc_info:
        await service.cancel_leave(
            request.id,
            actor=_actor(user_id=user_id),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_cancel_approved_restores_balance(
    service: LeaveService,
    mock_repository: AsyncMock,
) -> None:
    request = _request_mock(status="approved")
    balance = _balance_mock(
        employee_id=request.employee_id,
        leave_type_id=request.leave_type_id,
        balance=Decimal("5"),
    )
    restored = _balance_mock(balance=Decimal("8"))
    cancelled = _request_mock(status="cancelled")

    mock_repository.get_leave_request_by_id.side_effect = [request, cancelled]
    mock_repository.get_leave_balance.return_value = balance
    mock_repository.update_leave_balance.return_value = restored
    mock_repository.update_leave_status.return_value = cancelled

    result = await service.cancel_leave(
        request.id,
        actor=_actor(roles=[HR_MANAGER]),
        ip_address="127.0.0.1",
    )

    assert result.status == "cancelled"
    mock_repository.update_leave_balance.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_pending_by_owner(
    service: LeaveService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee = _employee_mock(user_id=user_id)
    request = _request_mock(status="pending", employee=employee)
    cancelled = _request_mock(status="cancelled", employee=employee)

    mock_repository.get_leave_request_by_id.side_effect = [request, cancelled]
    mock_repository.update_leave_status.return_value = cancelled

    result = await service.cancel_leave(
        request.id,
        actor=_actor(user_id=user_id),
        ip_address="127.0.0.1",
    )

    assert result.status == "cancelled"
    mock_repository.update_leave_balance.assert_not_awaited()
