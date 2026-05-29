import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_not_found_returns_error_envelope() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert "message" in body
    assert isinstance(body["errors"], list)


@pytest.mark.asyncio
async def test_http_exception_detail_dict() -> None:
    from app.main import create_app

    test_app = create_app()

    @test_app.get("/api/v1/test-forbidden")
    async def forbidden() -> None:
        raise HTTPException(
            status_code=403,
            detail={"message": "Forbidden", "errors": []},
        )

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/test-forbidden")

    assert response.status_code == 403
    assert response.json()["success"] is False
