from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import EMPLOYEE, HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.employee.controller import EmployeeController
from app.modules.employee.schema import (
    CreateEmployeeRequest,
    CreateEmployeeResponse,
    DirectReportsResponse,
    EmployeeListResponse,
    EmployeeProfileResponse,
    EmployeeResponse,
    EmployeeSearchResponse,
    EmployeeSelfUpdateRequest,
    ManagerDetailResponse,
    UpdateEmployeeRequest,
)

router = APIRouter()

_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)
_admin_only = require_roles(SYSTEM_ADMINISTRATOR)


def _controller(session: AsyncSession = Depends(get_db)) -> EmployeeController:
    return EmployeeController(session)


@router.get("/search", response_model=SuccessResponse[EmployeeSearchResponse])
async def search_employees(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: EmployeeController = Depends(_controller),
) -> SuccessResponse[EmployeeSearchResponse]:
    return await controller.search_employees(q, current_user, limit=limit)


@router.post(
    "",
    response_model=SuccessResponse[CreateEmployeeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    body: CreateEmployeeRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: EmployeeController = Depends(_controller),
) -> SuccessResponse[CreateEmployeeResponse]:
    return await controller.create_employee(body, current_user, request)


@router.get("", response_model=SuccessResponse[EmployeeListResponse])
async def list_employees(
    search: str | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    designation_id: UUID | None = Query(default=None),
    status: UUID | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: EmployeeController = Depends(_controller),
) -> SuccessResponse[EmployeeListResponse]:
    return await controller.list_employees(
        current_user=current_user,
        search=search,
        department_id=department_id,
        designation_id=designation_id,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/{employee_id}", response_model=SuccessResponse[EmployeeResponse])
async def get_employee(
    employee_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: EmployeeController = Depends(_controller),
) -> SuccessResponse[EmployeeResponse]:
    return await controller.get_employee(employee_id, current_user)


@router.patch("/{employee_id}", response_model=SuccessResponse[EmployeeResponse])
async def update_employee(
    employee_id: UUID,
    body: UpdateEmployeeRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    controller: EmployeeController = Depends(_controller),
) -> SuccessResponse[EmployeeResponse]:
    is_employee_only = EMPLOYEE in current_user.roles and not (
        {HR_MANAGER, SYSTEM_ADMINISTRATOR} & set(current_user.roles)
    )
    if is_employee_only:
        payload = body.model_dump(exclude_unset=True)
        disallowed = set(payload.keys()) - {"phone"}
        if disallowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Employees may only update phone",
                    "errors": [],
                },
            )
        return await controller.update_own_profile(
            employee_id,
            EmployeeSelfUpdateRequest(phone=body.phone),
            current_user,
            request,
        )
    return await controller.update_employee(
        employee_id,
        body,
        current_user,
        request,
    )


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_employee(
    employee_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_admin_only),
    controller: EmployeeController = Depends(_controller),
) -> Response:
    return await controller.deactivate_employee(employee_id, current_user, request)


@router.get(
    "/{employee_id}/profile",
    response_model=SuccessResponse[EmployeeProfileResponse],
)
async def get_employee_profile(
    employee_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: EmployeeController = Depends(_controller),
) -> SuccessResponse[EmployeeProfileResponse]:
    return await controller.get_profile(employee_id, current_user)


@router.get(
    "/{employee_id}/manager",
    response_model=SuccessResponse[ManagerDetailResponse | None],
)
async def get_employee_manager(
    employee_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: EmployeeController = Depends(_controller),
) -> SuccessResponse[ManagerDetailResponse | None]:
    return await controller.get_manager(employee_id, current_user)


@router.get(
    "/{employee_id}/reports",
    response_model=SuccessResponse[DirectReportsResponse],
)
async def get_employee_reports(
    employee_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: EmployeeController = Depends(_controller),
) -> SuccessResponse[DirectReportsResponse]:
    return await controller.get_direct_reports(
        employee_id,
        current_user=current_user,
        page=page,
        page_size=page_size,
    )
