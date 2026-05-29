import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.organization.designation_schema import CreateDesignationRequest
from app.modules.organization.designation_service import DesignationService
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
def service(mock_session: AsyncMock, mock_repository: AsyncMock) -> DesignationService:
    return DesignationService(mock_session, repository=mock_repository)


def _designation_mock(**kwargs) -> MagicMock:
    item = MagicMock()
    item.id = kwargs.get("id", uuid.uuid4())
    item.title = kwargs.get("title", "Developer")
    item.description = kwargs.get("description")
    item.created_at = datetime.now()
    item.updated_at = datetime.now()
    return item


@pytest.mark.asyncio
async def test_create_designation_duplicate_title(
    service: DesignationService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_designation_by_title.return_value = _designation_mock()
    with pytest.raises(OrganizationError) as exc_info:
        await service.create_designation(
            CreateDesignationRequest(title="Developer"),
            actor_user_id=uuid.uuid4(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_delete_designation_with_employees(
    service: DesignationService,
    mock_repository: AsyncMock,
) -> None:
    item = _designation_mock()
    mock_repository.get_designation_by_id.return_value = item
    mock_repository.count_active_employees.return_value = 2

    with pytest.raises(OrganizationError) as exc_info:
        await service.delete_designation(
            item.id,
            actor_user_id=uuid.uuid4(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409
