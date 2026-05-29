from uuid import UUID

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.user.errors import UserError
from app.modules.user.schema import (
    AssignRoleRequest,
    CreateUserRequest,
    CreateUserResponse,
    PermissionResponse,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)
from app.modules.user.service import UserService


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


class UserController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = UserService(session)

    async def create_user(
        self,
        body: CreateUserRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[CreateUserResponse]:
        try:
            user = await self._service.create_user(
                body,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except UserError as exc:
            raise _user_http_exception(exc) from exc
        return SuccessResponse(message="User created", data=user)

    async def list_users(
        self,
        *,
        search: str | None,
        page: int,
        page_size: int,
    ) -> SuccessResponse[UserListResponse]:
        try:
            data = await self._service.list_users(
                search=search,
                page=page,
                page_size=page_size,
            )
        except UserError as exc:
            raise _user_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_user(self, user_id: UUID) -> SuccessResponse[UserResponse]:
        try:
            user = await self._service.get_user(user_id)
        except UserError as exc:
            raise _user_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=user)

    async def update_user(
        self,
        user_id: UUID,
        body: UpdateUserRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[UserResponse]:
        try:
            user = await self._service.update_user(
                user_id,
                body,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except UserError as exc:
            raise _user_http_exception(exc) from exc
        return SuccessResponse(message="User updated", data=user)

    async def delete_user(
        self,
        user_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> Response:
        try:
            await self._service.soft_delete_user(
                user_id,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except UserError as exc:
            raise _user_http_exception(exc) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def assign_role(
        self,
        user_id: UUID,
        body: AssignRoleRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[UserResponse]:
        try:
            user = await self._service.assign_role(
                user_id,
                body,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except UserError as exc:
            raise _user_http_exception(exc) from exc
        return SuccessResponse(message="Role assigned", data=user)

    async def remove_role(
        self,
        user_id: UUID,
        role_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[UserResponse]:
        try:
            user = await self._service.remove_role(
                user_id,
                role_id,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except UserError as exc:
            raise _user_http_exception(exc) from exc
        return SuccessResponse(message="Role removed", data=user)

    async def get_permissions(self, user_id: UUID) -> SuccessResponse[PermissionResponse]:
        try:
            permissions = await self._service.get_permissions(user_id)
        except UserError as exc:
            raise _user_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=permissions)


def _user_http_exception(exc: UserError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": []},
    )
