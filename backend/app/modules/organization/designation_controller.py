from uuid import UUID

from fastapi import Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.organization.designation_schema import (
    CreateDesignationRequest,
    DesignationListResponse,
    DesignationResponse,
    UpdateDesignationRequest,
)
from app.modules.organization.designation_service import DesignationService
from app.modules.organization.errors import OrganizationError
from app.modules.organization.http import organization_http_exception


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


class DesignationController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = DesignationService(session)

    async def create_designation(
        self,
        body: CreateDesignationRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[DesignationResponse]:
        try:
            data = await self._service.create_designation(
                body,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return SuccessResponse(message="Designation created", data=data)

    async def list_designations(
        self,
        *,
        page: int,
        page_size: int,
    ) -> SuccessResponse[DesignationListResponse]:
        try:
            data = await self._service.list_designations(page=page, page_size=page_size)
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_designation(
        self,
        designation_id: UUID,
    ) -> SuccessResponse[DesignationResponse]:
        try:
            data = await self._service.get_designation(designation_id)
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def update_designation(
        self,
        designation_id: UUID,
        body: UpdateDesignationRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[DesignationResponse]:
        try:
            data = await self._service.update_designation(
                designation_id,
                body,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return SuccessResponse(message="Designation updated", data=data)

    async def delete_designation(
        self,
        designation_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> Response:
        try:
            await self._service.delete_designation(
                designation_id,
                actor_user_id=current_user.id,
                ip_address=_client_ip(request),
            )
        except OrganizationError as exc:
            raise organization_http_exception(exc) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)
