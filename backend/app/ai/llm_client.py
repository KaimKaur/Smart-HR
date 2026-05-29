from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from openai import APIStatusError, AsyncOpenAI

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = frozenset({429, 503})
MAX_RETRIES = 3


class LLMClientError(Exception):
    pass


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        api_key = self._settings.resolved_ai_api_key
        if not api_key:
            self._client: AsyncOpenAI | None = None
        else:
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=self._settings.ai_base_url or None,
            )

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        if self._client is None:
            raise LLMClientError("AI API key is not configured")

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.chat.completions.create(
                    model=self._settings.ai_model,
                    temperature=self._settings.ai_temperature,
                    max_tokens=self._settings.ai_max_tokens,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content
                if not content:
                    raise LLMClientError("Empty response from language model")
                return json.loads(content)
            except APIStatusError as exc:
                last_error = exc
                if exc.status_code not in RETRYABLE_STATUS_CODES:
                    raise LLMClientError(str(exc)) from exc
                delay = 2**attempt
                logger.warning(
                    "LLM transient error %s, retry in %ss",
                    exc.status_code,
                    delay,
                )
                await asyncio.sleep(delay)
            except json.JSONDecodeError as exc:
                raise LLMClientError("Invalid JSON in model response") from exc
            except LLMClientError:
                raise
            except Exception as exc:
                raise LLMClientError(str(exc)) from exc

        raise LLMClientError(str(last_error or "LLM request failed"))
