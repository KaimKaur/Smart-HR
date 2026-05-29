from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_refresh_secret_key: str = Field(..., alias="JWT_REFRESH_SECRET_KEY")
    access_token_expire_minutes: int = Field(15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    password_reset_expire_hours: int = Field(24, alias="PASSWORD_RESET_EXPIRE_HOURS")
    cors_origins: str = Field("http://localhost:3000", alias="CORS_ORIGINS")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    resume_upload_dir: str = Field(
        "uploads/resumes",
        alias="RESUME_UPLOAD_DIR",
    )
    max_resume_size_bytes: int = Field(
        10 * 1024 * 1024,
        alias="MAX_RESUME_SIZE_BYTES",
    )
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    ai_api_key: str | None = Field(default=None, alias="AI_API_KEY")
    ai_model: str = Field(default="gpt-4o-mini", alias="AI_MODEL")
    ai_base_url: str = Field(default="https://api.openai.com/v1", alias="AI_BASE_URL")
    ai_max_tokens: int = Field(default=1500, alias="AI_MAX_TOKENS")
    ai_temperature: float = Field(default=0.2, alias="AI_TEMPERATURE")
    ai_auto_screen_on_upload: bool = Field(default=False, alias="AI_AUTO_SCREEN_ON_UPLOAD")

    @property
    def resolved_ai_api_key(self) -> str | None:
        return self.ai_api_key or self.openai_api_key

    @field_validator("database_url", "jwt_secret_key", "jwt_refresh_secret_key")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
