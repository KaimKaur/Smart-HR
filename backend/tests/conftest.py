import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory
from app.core.security import create_access_token
from app.main import app

# Required settings for app import and tests (no live database for unit tests).
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://smart_hr:smart_hr_dev@localhost:5432/smart_hr_test",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-min-32-chars-long")
os.environ.setdefault(
    "JWT_REFRESH_SECRET_KEY",
    "test-jwt-refresh-secret-key-min-32-chars",
)
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def test_db_session() -> AsyncSession:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


@pytest.fixture
async def test_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def admin_token() -> str:
    return create_access_token(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "email": "admin@example.com",
            "roles": ["system_administrator"],
        }
    )


@pytest.fixture
def hr_manager_token() -> str:
    return create_access_token(
        {
            "sub": "00000000-0000-0000-0000-000000000002",
            "email": "hr@example.com",
            "roles": ["hr_manager"],
        }
    )


@pytest.fixture
def employee_token() -> str:
    return create_access_token(
        {
            "sub": "00000000-0000-0000-0000-000000000003",
            "email": "employee@example.com",
            "roles": ["employee"],
        }
    )
