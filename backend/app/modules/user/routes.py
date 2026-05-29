from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.user.controller import UserController
from app.modules.user.schema import (
    AssignRoleRequest,
    CreateUserRequest,
    CreateUserResponse,
    PermissionResponse,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)

router = APIRouter()

_admin_only = require_roles(SYSTEM_ADMINISTRATOR)
_admin_or_hr = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)


def _controller(session: AsyncSession = Depends(get_db)) -> UserController:
    return UserController(session)


@router.post(
    "",
    response_model=SuccessResponse[CreateUserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    body: CreateUserRequest,
    request: Request,
    current_user: CurrentUser = Depends(_admin_only),
    controller: UserController = Depends(_controller),
) -> SuccessResponse[CreateUserResponse]:
    return await controller.create_user(body, current_user, request)


@router.get("", response_model=SuccessResponse[UserListResponse])
async def list_users(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_admin_or_hr),
    controller: UserController = Depends(_controller),
) -> SuccessResponse[UserListResponse]:
    return await controller.list_users(
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: UUID,
    current_user: CurrentUser = Depends(_admin_or_hr),
    controller: UserController = Depends(_controller),
) -> SuccessResponse[UserResponse]:
    return await controller.get_user(user_id)


@router.patch("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user(
    user_id: UUID,
    body: UpdateUserRequest,
    request: Request,
    current_user: CurrentUser = Depends(_admin_only),
    controller: UserController = Depends(_controller),
) -> SuccessResponse[UserResponse]:
    return await controller.update_user(user_id, body, current_user, request)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_admin_only),
    controller: UserController = Depends(_controller),
) -> Response:
    return await controller.delete_user(user_id, current_user, request)


@router.post("/{user_id}/roles", response_model=SuccessResponse[UserResponse])
async def assign_role(
    user_id: UUID,
    body: AssignRoleRequest,
    request: Request,
    current_user: CurrentUser = Depends(_admin_only),
    controller: UserController = Depends(_controller),
) -> SuccessResponse[UserResponse]:
    return await controller.assign_role(user_id, body, current_user, request)


@router.delete("/{user_id}/roles/{role_id}", response_model=SuccessResponse[UserResponse])
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_admin_only),
    controller: UserController = Depends(_controller),
) -> SuccessResponse[UserResponse]:
    return await controller.remove_role(user_id, role_id, current_user, request)


@router.get("/{user_id}/permissions", response_model=SuccessResponse[PermissionResponse])
async def get_user_permissions(
    user_id: UUID,
    current_user: CurrentUser = Depends(_admin_only),
    controller: UserController = Depends(_controller),
) -> SuccessResponse[PermissionResponse]:
    return await controller.get_permissions(user_id)
