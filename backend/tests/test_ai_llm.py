import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.ai.llm_client import LLMClient, LLMClientError
from app.ai.schemas import LLMScreeningResult
from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        JWT_SECRET_KEY="test-jwt-secret-key-min-32-chars-long",
        JWT_REFRESH_SECRET_KEY="test-jwt-refresh-secret-key-min-32-chars",
        AI_API_KEY="test-key",
        AI_MODEL="gpt-4o-mini",
    )


@pytest.mark.asyncio
async def test_llm_not_configured() -> None:
    client = LLMClient(
        Settings(
            DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
            JWT_SECRET_KEY="test-jwt-secret-key-min-32-chars-long",
            JWT_REFRESH_SECRET_KEY="test-jwt-refresh-secret-key-min-32-chars",
        ),
    )
    assert not client.is_configured


@pytest.mark.asyncio
async def test_llm_complete_json_success(settings: Settings) -> None:
    payload = {
        "score": 82,
        "summary": "Strong fit",
        "strengths": ["Python"],
        "weaknesses": ["DevOps"],
        "recommendation": "proceed",
    }
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps(payload))),
    ]

    client = LLMClient(settings)
    with patch.object(
        client._client.chat.completions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await client.complete_json(
            system_prompt="sys",
            user_prompt="user",
        )
    validated = LLMScreeningResult.model_validate(result)
    assert validated.score == 82
    assert validated.recommendation == "proceed"


@pytest.mark.asyncio
async def test_llm_invalid_json(settings: Settings) -> None:
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="not json"))]

    client = LLMClient(settings)
    with patch.object(
        client._client.chat.completions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with pytest.raises(LLMClientError):
            await client.complete_json(system_prompt="s", user_prompt="u")


def test_screening_result_validation() -> None:
    with pytest.raises(ValidationError):
        LLMScreeningResult.model_validate(
            {
                "score": 150,
                "summary": "x",
                "strengths": [],
                "weaknesses": [],
                "recommendation": "proceed",
            },
        )
