import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.constants import EMPLOYEE, HR_MANAGER
from app.core.security import CurrentUser
from app.modules.attendance.errors import AttendanceError
from app.modules.attendance.schema import (
    CheckInRequest,
    CheckOutRequest,
    CorrectionRequest,
    ReviewCorrectionRequest,
)
from app.modules.attendance.service import AttendanceService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def service(mock_session: AsyncMock, mock_repository: AsyncMock) -> AttendanceService:
    return AttendanceService(mock_session, repository=mock_repository)


def _employee_mock(**kwargs) -> MagicMock:
    employee = MagicMock()
    employee.id = kwargs.get("id", uuid.uuid4())
    employee.user_id = kwargs.get("user_id", uuid.uuid4())
    employee.first_name = "Jane"
    employee.last_name = "Doe"
    employee.employee_code = "EMP001"
    employee.department_id = kwargs.get("department_id", uuid.uuid4())
    employee.department = MagicMock(name="Engineering")
    return employee


def _record_mock(**kwargs) -> MagicMock:
    record = MagicMock()
    record.id = kwargs.get("id", uuid.uuid4())
    record.employee_id = kwargs.get("employee_id", uuid.uuid4())
    record.attendance_date = kwargs.get("attendance_date", date.today())
    record.check_in_time = kwargs.get("check_in_time", datetime.now(UTC))
    record.check_out_time = kwargs.get("check_out_time")
    record.work_duration_minutes = kwargs.get("work_duration_minutes")
    record.attendance_status_id = kwargs.get("attendance_status_id", uuid.uuid4())
    record.created_at = datetime.now(UTC)
    status = MagicMock()
    status.name = kwargs.get("status_name", "present")
    status.id = record.attendance_status_id
    record.status = status
    return record


def _actor(**kwargs) -> CurrentUser:
    return CurrentUser(
        id=kwargs.get("user_id", uuid.uuid4()),
        email="user@example.com",
        roles=kwargs.get("roles", [EMPLOYEE]),
    )


@pytest.mark.asyncio
async def test_check_in_duplicate(
    service: AttendanceService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    mock_repository.is_employee_active.return_value = True
    mock_repository.get_employee_by_id.return_value = _employee_mock(
        id=employee_id,
        user_id=user_id,
    )
    mock_repository.get_record_by_employee_date.return_value = _record_mock(
        employee_id=employee_id,
    )

    with pytest.raises(AttendanceError) as exc_info:
        await service.check_in(
            employee_id,
            CheckInRequest(),
            actor=_actor(user_id=user_id),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_check_in_success(
    service: AttendanceService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    present = MagicMock(id=uuid.uuid4())
    created = _record_mock(employee_id=employee_id)

    mock_repository.is_employee_active.return_value = True
    mock_repository.get_employee_by_id.return_value = _employee_mock(
        id=employee_id,
        user_id=user_id,
    )
    mock_repository.get_record_by_employee_date.return_value = None
    mock_repository.get_status_by_name.return_value = present
    mock_repository.create_check_in.return_value = created

    result = await service.check_in(
        employee_id,
        CheckInRequest(),
        actor=_actor(user_id=user_id),
        ip_address="127.0.0.1",
    )

    assert result.status_name == "present"
    mock_repository.create_audit_log.assert_awaited()


@pytest.mark.asyncio
async def test_check_out_without_check_in(
    service: AttendanceService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    mock_repository.get_employee_by_id.return_value = _employee_mock(
        id=employee_id,
        user_id=user_id,
    )
    mock_repository.get_record_by_employee_date.return_value = None

    with pytest.raises(AttendanceError) as exc_info:
        await service.check_out(
            employee_id,
            CheckOutRequest(),
            actor=_actor(user_id=user_id),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_check_out_twice(
    service: AttendanceService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    mock_repository.get_employee_by_id.return_value = _employee_mock(
        id=employee_id,
        user_id=user_id,
    )
    mock_repository.get_record_by_employee_date.return_value = _record_mock(
        employee_id=employee_id,
        check_out_time=datetime.now(UTC),
    )

    with pytest.raises(AttendanceError) as exc_info:
        await service.check_out(
            employee_id,
            CheckOutRequest(),
            actor=_actor(user_id=user_id),
            ip_address="127.0.0.1",
        )
    assert "Already checked out" in exc_info.value.message


@pytest.mark.asyncio
async def test_history_invalid_date_range(
    service: AttendanceService,
) -> None:
    with pytest.raises(AttendanceError) as exc_info:
        await service.get_attendance_history(
            actor=CurrentUser(
                id=uuid.uuid4(),
                email="hr@example.com",
                roles=[HR_MANAGER],
            ),
            employee_id=None,
            date_from=date(2026, 5, 10),
            date_to=date(2026, 5, 1),
            page=1,
            page_size=20,
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_request_correction_duplicate_pending(
    service: AttendanceService,
    mock_repository: AsyncMock,
) -> None:
    user_id = uuid.uuid4()
    employee = _employee_mock(user_id=user_id)
    record = _record_mock(employee_id=employee.id)

    mock_repository.get_record_by_id.return_value = record
    mock_repository.get_employee_by_id.return_value = employee
    mock_repository.get_pending_correction_for_record.return_value = MagicMock()

    with pytest.raises(AttendanceError) as exc_info:
        await service.request_correction(
            record.id,
            CorrectionRequest(reason="Forgot to check in"),
            actor=_actor(user_id=user_id),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_review_correction_approve(
    service: AttendanceService,
    mock_repository: AsyncMock,
) -> None:
    record = _record_mock()
    correction = MagicMock()
    correction.id = uuid.uuid4()
    correction.correction_status = "pending"
    correction.attendance_record = record
    correction.attendance_record_id = record.id
    correction.requested_by = uuid.uuid4()
    correction.reason = "Fix"
    correction.reviewed_by = None
    correction.reviewed_at = None
    correction.created_at = datetime.now(UTC)

    updated_record = _record_mock(
        check_out_time=datetime.now(UTC),
        work_duration_minutes=480,
    )
    updated_correction = MagicMock()
    updated_correction.id = correction.id
    updated_correction.attendance_record_id = record.id
    updated_correction.requested_by = correction.requested_by
    updated_correction.reason = correction.reason
    updated_correction.correction_status = "approved"
    updated_correction.reviewed_by = uuid.uuid4()
    updated_correction.reviewed_at = datetime.now(UTC)
    updated_correction.created_at = correction.created_at

    mock_repository.get_correction_by_id.return_value = correction
    mock_repository.update_record_times.return_value = updated_record
    mock_repository.update_correction_status.return_value = updated_correction

    check_in = datetime(2026, 5, 26, 9, 0, tzinfo=UTC)
    check_out = datetime(2026, 5, 26, 17, 0, tzinfo=UTC)

    result = await service.review_correction(
        correction.id,
        ReviewCorrectionRequest(
            status="approved",
            check_in_time=check_in,
            check_out_time=check_out,
        ),
        actor=CurrentUser(
            id=uuid.uuid4(),
            email="hr@example.com",
            roles=[HR_MANAGER],
        ),
        ip_address="127.0.0.1",
    )

    assert result.correction_status == "approved"
    mock_repository.create_audit_log.assert_awaited()
