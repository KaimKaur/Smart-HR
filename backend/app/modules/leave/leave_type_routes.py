from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.leave.controller import LeaveTypeController
from app.modules.leave.schema import (
    CreateLeaveTypeRequest,
    LeaveTypeListResponse,
    LeaveTypeResponse,
    UpdateLeaveTypeRequest,
)

router = APIRouter()

_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)


def _controller(session: AsyncSession = Depends(get_db)) -> LeaveTypeController:
    return LeaveTypeController(session)


@router.get("", response_model=SuccessResponse[LeaveTypeListResponse])
async def list_leave_types(
    current_user: CurrentUser = Depends(get_current_user),
    controller: LeaveTypeController = Depends(_controller),
) -> SuccessResponse[LeaveTypeListResponse]:
    return await controller.list_leave_types()


@router.post(
    "",
    response_model=SuccessResponse[LeaveTypeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_leave_type(
    body: CreateLeaveTypeRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: LeaveTypeController = Depends(_controller),
) -> SuccessResponse[LeaveTypeResponse]:
    return await controller.create_leave_type(body, current_user, request)


@router.get("/{leave_type_id}", response_model=SuccessResponse[LeaveTypeResponse])
async def get_leave_type(
    leave_type_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: LeaveTypeController = Depends(_controller),
) -> SuccessResponse[LeaveTypeResponse]:
    return await controller.get_leave_type(leave_type_id)


@router.patch("/{leave_type_id}", response_model=SuccessResponse[LeaveTypeResponse])
async def update_leave_type(
    leave_type_id: UUID,
    body: UpdateLeaveTypeRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: LeaveTypeController = Depends(_controller),
) -> SuccessResponse[LeaveTypeResponse]:
    return await controller.update_leave_type(
        leave_type_id,
        body,
        current_user,
        request,
    )


@router.delete("/{leave_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_leave_type(
    leave_type_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: LeaveTypeController = Depends(_controller),
) -> Response:
    await controller.delete_leave_type(leave_type_id, current_user, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
