import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.constants import DEPARTMENT_MANAGER, EMPLOYEE
from app.core.security import CurrentUser
from app.modules.performance.errors import PerformanceError
from app.modules.performance.schema import FeedbackRequest, ReviewRequest
from app.modules.performance.service import PerformanceService


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


def _employee_mock(
    *,
    employee_id: uuid.UUID,
    user_id: uuid.UUID,
    department_name: str = "Engineering",
) -> MagicMock:
    employee = MagicMock()
    employee.id = employee_id
    employee.user_id = user_id
    employee.employee_code = "EMP001"
    employee.first_name = "Jane"
    employee.last_name = "Doe"
    employee.department = MagicMock(name=department_name)
    employee.department.name = department_name
    return employee


@pytest.mark.asyncio
async def test_duplicate_review_returns_409(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = PerformanceService(mock_session, repository=mock_repository)

    actor_user_id = uuid.uuid4()
    manager_employee_id = uuid.uuid4()
    target_employee_id = uuid.uuid4()
    cycle_id = uuid.uuid4()

    actor = CurrentUser(
        id=actor_user_id,
        email="manager@example.com",
        roles=[DEPARTMENT_MANAGER],
    )

    mock_repository.get_employee_by_user_id.return_value = _employee_mock(
        employee_id=manager_employee_id,
        user_id=actor_user_id,
    )
    mock_repository.get_direct_report_ids.return_value = [target_employee_id]
    mock_repository.get_cycle_by_id.return_value = MagicMock(id=cycle_id)
    mock_repository.get_employee_by_id.side_effect = [
        _employee_mock(employee_id=target_employee_id, user_id=uuid.uuid4()),
        _employee_mock(employee_id=manager_employee_id, user_id=actor_user_id),
    ]
    mock_repository.get_review_by_keys.return_value = MagicMock(id=uuid.uuid4())

    with pytest.raises(PerformanceError) as exc_info:
        await service.create_review(
            ReviewRequest(
                cycle_id=cycle_id,
                employee_id=target_employee_id,
                rating=4.0,
                comments="Great work",
            ),
            actor=actor,
            ip_address="127.0.0.1",
        )

    assert exc_info.value.status_code == 409


class _FeedbackAppendFakeRepository:
    def __init__(self, *, review: MagicMock, employee: MagicMock) -> None:
        self._review = review
        self._employee = employee
        self._entries: list[MagicMock] = []
        self._counter = 0

    async def get_employee_by_user_id(self, user_id: uuid.UUID) -> MagicMock:
        return self._employee

    async def get_employee_by_id(self, employee_id: uuid.UUID) -> MagicMock:
        return self._employee

    async def get_review_by_id(self, *, review_id: uuid.UUID) -> MagicMock:
        return self._review

    async def create_audit_log(self, **kwargs) -> MagicMock:
        return MagicMock(id=uuid.uuid4())

    async def create_feedback(
        self,
        *,
        review_id: uuid.UUID,
        feedback_text: str,
        created_by_employee_id: uuid.UUID,
    ) -> MagicMock:
        entry = MagicMock()
        entry.id = uuid.uuid4()
        entry.review_id = review_id
        entry.feedback_text = feedback_text
        entry.created_by = created_by_employee_id
        entry.created_at = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=self._counter)
        self._counter += 1
        entry.author = self._employee
        self._entries.append(entry)
        return entry

    async def list_feedback_for_review(self, review_id: uuid.UUID) -> list[MagicMock]:
        # Service expects `created_at DESC`.
        return sorted(self._entries, key=lambda e: e.created_at, reverse=True)


@pytest.mark.asyncio
async def test_feedback_is_appended_not_overwritten() -> None:
    actor_user_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    review_id = uuid.uuid4()

    employee = _employee_mock(
        employee_id=employee_id,
        user_id=actor_user_id,
        department_name="Engineering",
    )

    review = MagicMock()
    review.id = review_id
    review.review_id = review_id
    review.employee_id = employee_id
    review.reviewer_id = employee_id

    repo = _FeedbackAppendFakeRepository(review=review, employee=employee)
    session = AsyncMock()
    session.commit = AsyncMock()

    service = PerformanceService(session, repository=repo)  # type: ignore[arg-type]
    actor = CurrentUser(
        id=actor_user_id,
        email="employee@example.com",
        roles=[EMPLOYEE],
    )

    await service.add_feedback(
        review_id,
        FeedbackRequest(feedback_text="First note"),
        actor=actor,
        ip_address="127.0.0.1",
    )
    await service.add_feedback(
        review_id,
        FeedbackRequest(feedback_text="Second note"),
        actor=actor,
        ip_address="127.0.0.1",
    )

    entries = await service.list_feedback(
        review_id,
        actor=actor,
    )
    assert [e.feedback_text for e in entries] == ["Second note", "First note"]

