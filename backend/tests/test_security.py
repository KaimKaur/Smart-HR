import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends, FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from app.core.constants import HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.security import (
    CurrentUser,
    UserRoleRepository,
    create_access_token,
    decode_access_token,
    require_roles,
    resolve_current_user,
)


def test_decode_access_token_valid() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(
        {
            "sub": str(user_id),
            "email": "user@example.com",
            "roles": ["employee"],
        },
    )
    payload = decode_access_token(token)
    assert payload.sub == str(user_id)
    assert payload.email == "user@example.com"


def test_decode_access_token_invalid_raises() -> None:
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not-a-valid-token")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_token() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await resolve_current_user(credentials=None, session=AsyncMock())
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_with_mock_repository() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(
        {
            "sub": str(user_id),
            "email": "admin@smarthr.dev",
            "roles": [SYSTEM_ADMINISTRATOR],
        },
    )
    repository = AsyncMock(spec=UserRoleRepository)
    repository.user_exists_and_active.return_value = True
    repository.get_role_names_for_user.return_value = [SYSTEM_ADMINISTRATOR]

    from fastapi.security import HTTPAuthorizationCredentials

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    session = AsyncMock()

    current_user = await resolve_current_user(
        credentials=credentials,
        session=session,
        role_repository=repository,
    )

    assert current_user.id == user_id
    assert current_user.roles == [SYSTEM_ADMINISTRATOR]
    repository.get_role_names_for_user.assert_awaited_once()


@pytest.mark.asyncio
async def test_require_roles_forbidden() -> None:
    checker = require_roles(HR_MANAGER)
    current_user = CurrentUser(
        id=uuid.uuid4(),
        email="employee@example.com",
        roles=["employee"],
    )

    with pytest.raises(HTTPException) as exc_info:
        await checker(current_user=current_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_protected_route_without_token_returns_401() -> None:
    test_app = FastAPI()

    @test_app.get("/protected")
    async def protected(
        user: CurrentUser = Depends(require_roles(SYSTEM_ADMINISTRATOR)),
    ) -> dict[str, str]:
        return {"id": str(user.id)}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/protected")

    assert response.status_code == 401
