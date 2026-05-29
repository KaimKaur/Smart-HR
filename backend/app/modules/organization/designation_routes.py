from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.organization.designation_controller import DesignationController
from app.modules.organization.designation_schema import (
    CreateDesignationRequest,
    DesignationListResponse,
    DesignationResponse,
    UpdateDesignationRequest,
)

router = APIRouter()

_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)


def _controller(session: AsyncSession = Depends(get_db)) -> DesignationController:
    return DesignationController(session)


@router.post(
    "",
    response_model=SuccessResponse[DesignationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_designation(
    body: CreateDesignationRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: DesignationController = Depends(_controller),
) -> SuccessResponse[DesignationResponse]:
    return await controller.create_designation(body, current_user, request)


@router.get("", response_model=SuccessResponse[DesignationListResponse])
async def list_designations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: DesignationController = Depends(_controller),
) -> SuccessResponse[DesignationListResponse]:
    return await controller.list_designations(page=page, page_size=page_size)


@router.get("/{designation_id}", response_model=SuccessResponse[DesignationResponse])
async def get_designation(
    designation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: DesignationController = Depends(_controller),
) -> SuccessResponse[DesignationResponse]:
    return await controller.get_designation(designation_id)


@router.patch("/{designation_id}", response_model=SuccessResponse[DesignationResponse])
async def update_designation(
    designation_id: UUID,
    body: UpdateDesignationRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: DesignationController = Depends(_controller),
) -> SuccessResponse[DesignationResponse]:
    return await controller.update_designation(
        designation_id,
        body,
        current_user,
        request,
    )


@router.delete("/{designation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_designation(
    designation_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: DesignationController = Depends(_controller),
) -> Response:
    return await controller.delete_designation(designation_id, current_user, request)
