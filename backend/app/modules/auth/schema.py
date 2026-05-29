from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenData):
    pass


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(TokenData):
    pass


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordData(BaseModel):
    reset_token: str | None = None


class ForgotPasswordResponse(BaseModel):
    message: str = (
        "If an account exists for this email, password reset instructions have been sent."
    )


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class MeResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    roles: list[str]
    created_at: datetime
