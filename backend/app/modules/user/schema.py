from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.schemas import PaginatedResponse, PaginationMeta


class CreateUserRequest(BaseModel):
    email: EmailStr
    roles: list[str] = Field(default_factory=list)
    is_active: bool = False


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    roles: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateUserResponse(UserResponse):
    password_reset_token: str | None = None


class AssignRoleRequest(BaseModel):
    role: str = Field(description="Role slug, e.g. hr_manager")


class PermissionResponse(BaseModel):
    permissions: list[str]


class UserListResponse(PaginatedResponse[UserResponse]):
    pass


def build_pagination(page: int, page_size: int, total_items: int) -> PaginationMeta:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
