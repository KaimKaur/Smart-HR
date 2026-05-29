from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LLMScreeningResult(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendation: Literal["proceed", "reject", "review"]

    @field_validator("strengths", "weaknesses", mode="before")
    @classmethod
    def coerce_str_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return []


class MatchResult(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    score: float
