import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.security import CurrentUser
from app.modules.notifications.errors import NotificationsError
from app.modules.notifications.schema import UpdatePreferenceRequest
from app.modules.notifications.service import NotificationsService


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


def _actor(user_id: uuid.UUID | None = None) -> CurrentUser:
    return CurrentUser(
        id=user_id or uuid.uuid4(),
        email="user@example.com",
        roles=["employee"],
    )


@pytest.mark.asyncio
async def test_unread_count_returns_integer(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = NotificationsService(mock_session, repository=mock_repository)
    actor = _actor()
    mock_repository.get_unread_count.return_value = 5

    result = await service.unread_count(actor=actor)
    assert result.unread_count == 5


@pytest.mark.asyncio
async def test_preferences_default_enabled_when_missing(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = NotificationsService(mock_session, repository=mock_repository)
    actor = _actor()
    mock_repository.get_preferences.return_value = None

    result = await service.get_preferences(actor=actor)
    assert result.in_app_enabled is True


@pytest.mark.asyncio
async def test_mark_read_for_other_user_forbidden(
    mock_session: AsyncMock,
    mock_repository: AsyncMock,
) -> None:
    service = NotificationsService(mock_session, repository=mock_repository)
    actor = _actor()
    notification_id = uuid.uuid4()

    other = AsyncMock()
    other.id = notification_id
    other.user_id = uuid.uuid4()
    mock_repository.get_notification_by_id.return_value = other

    with pytest.raises(NotificationsError) as exc_info:
        await service.mark_read(notification_id, actor=actor)
    assert exc_info.value.status_code == 403

