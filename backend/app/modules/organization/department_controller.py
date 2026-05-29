from uuid import UUID

from fastapi import Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.organization.department_schema import (
    CreateDepartmentRequest,
    DepartmentListResponse,
    DepartmentResponse,
    UpdateDepartmentRequest,
)
from app.modules.organization.department_service import DepartmentService
from app.modules.organization.errors import OrganizationError
from app.modules.organization.http import organization_http_exception


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


class DepartmentController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = DepartmentService(session)

    async def create_department(
        self,
        body: CreateDepartmentRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[DepartmentResponse]:
        try:
            data = await self._service.create_department(
                body,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return SuccessResponse(message="Department created", data=data)

    async def list_departments(
        self,
        *,
        page: int,
        page_size: int,
    ) -> SuccessResponse[DepartmentListResponse]:
        try:
            data = await self._service.list_departments(page=page, page_size=page_size)
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_department(
        self,
        department_id: UUID,
    ) -> SuccessResponse[DepartmentResponse]:
        try:
            data = await self._service.get_department(department_id)
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def update_department(
        self,
        department_id: UUID,
        body: UpdateDepartmentRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[DepartmentResponse]:
        try:
            data = await self._service.update_department(
                department_id,
                body,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return SuccessResponse(message="Department updated", data=data)

    async def delete_department(
        self,
        department_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> Response:
        try:
            await self._service.delete_department(
                department_id,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)