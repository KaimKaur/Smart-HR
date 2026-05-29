import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from app.core.config import Settings
from app.core.security import create_access_token, create_refresh_token, decode_token


@pytest.fixture
def settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        JWT_SECRET_KEY="a" * 32,
        JWT_REFRESH_SECRET_KEY="b" * 32,
        ACCESS_TOKEN_EXPIRE_MINUTES=15,
        REFRESH_TOKEN_EXPIRE_DAYS=7,
    )


def test_create_access_token_payload(settings: Settings) -> None:
    user_id = str(uuid.uuid4())
    token = create_access_token(
        {"sub": user_id, "email": "user@example.com", "roles": ["employee"]},
        settings=settings,
    )
    payload = decode_token(token, settings)
    assert payload["sub"] == user_id
    assert payload["roles"] == ["employee"]
    assert payload["token_type"] == "access"
    assert "exp" in payload


def test_create_refresh_token_payload(settings: Settings) -> None:
    user_id = str(uuid.uuid4())
    token = create_refresh_token(
        {"sub": user_id, "roles": ["employee"]},
        settings=settings,
    )
    payload = decode_token(token, settings)
    assert payload["sub"] == user_id
    assert payload["token_type"] == "refresh"


def test_expired_token_raises_401(settings: Settings) -> None:
    expired = datetime.now(UTC) - timedelta(minutes=1)
    payload = {
        "sub": str(uuid.uuid4()),
        "roles": [],
        "token_type": "access",
        "exp": expired,
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token, settings)
    assert exc_info.value.status_code == 401


def test_tampered_token_raises_401(settings: Settings) -> None:
    token = create_access_token({"sub": str(uuid.uuid4()), "roles": []}, settings=settings)
    tampered = f"{token}invalid"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(tampered, settings)
    assert exc_info.value.status_code == 401
