from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.organization.department_controller import DepartmentController
from app.modules.organization.department_schema import (
    CreateDepartmentRequest,
    DepartmentListResponse,
    DepartmentResponse,
    UpdateDepartmentRequest,
)

router = APIRouter()

_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)


def _controller(session: AsyncSession = Depends(get_db)) -> DepartmentController:
    return DepartmentController(session)


@router.post(
    "",
    response_model=SuccessResponse[DepartmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    body: CreateDepartmentRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: DepartmentController = Depends(_controller),
) -> SuccessResponse[DepartmentResponse]:
    return await controller.create_department(body, current_user, request)


@router.get("", response_model=SuccessResponse[DepartmentListResponse])
async def list_departments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: DepartmentController = Depends(_controller),
) -> SuccessResponse[DepartmentListResponse]:
    return await controller.list_departments(page=page, page_size=page_size)


@router.get("/{department_id}", response_model=SuccessResponse[DepartmentResponse])
async def get_department(
    department_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: DepartmentController = Depends(_controller),
) -> SuccessResponse[DepartmentResponse]:
    return await controller.get_department(department_id)


@router.patch("/{department_id}", response_model=SuccessResponse[DepartmentResponse])
async def update_department(
    department_id: UUID,
    body: UpdateDepartmentRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: DepartmentController = Depends(_controller),
) -> SuccessResponse[DepartmentResponse]:
    return await controller.update_department(
        department_id,
        body,
        current_user,
        request,
    )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: DepartmentController = Depends(_controller),
) -> Response:
    return await controller.delete_department(department_id, current_user, request)
