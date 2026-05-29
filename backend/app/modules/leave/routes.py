from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEPARTMENT_MANAGER,
    HR_MANAGER,
    SYSTEM_ADMINISTRATOR,
)
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.leave.controller import LeaveController
from app.modules.leave.schema import (
    CreateLeaveRequest,
    InitializeBalanceRequest,
    InitializeBalanceResponse,
    LeaveApprovalRequest,
    LeaveBalanceResponse,
    LeaveListResponse,
    LeaveRequestResponse,
)

router = APIRouter()

_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)
_approvers = require_roles(
    SYSTEM_ADMINISTRATOR,
    HR_MANAGER,
    DEPARTMENT_MANAGER,
)


def _controller(session: AsyncSession = Depends(get_db)) -> LeaveController:
    return LeaveController(session)


@router.get("/balance", response_model=SuccessResponse[LeaveBalanceResponse])
async def get_own_leave_balance(
    current_user: CurrentUser = Depends(get_current_user),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveBalanceResponse]:
    return await controller.get_leave_balance(current_user)


@router.get(
    "/balance/{employee_id}",
    response_model=SuccessResponse[LeaveBalanceResponse],
)
async def get_employee_leave_balance(
    employee_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveBalanceResponse]:
    return await controller.get_leave_balance(
        current_user,
        employee_id=employee_id,
    )


@router.post(
    "/balance/initialize",
    response_model=SuccessResponse[InitializeBalanceResponse],
    status_code=status.HTTP_201_CREATED,
)
async def initialize_leave_balances(
    body: InitializeBalanceRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[InitializeBalanceResponse]:
    return await controller.initialize_balances(body, current_user, request)


@router.get("/pending-approvals", response_model=SuccessResponse[LeaveListResponse])
async def list_pending_approvals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_approvers),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveListResponse]:
    return await controller.list_pending_approvals(
        current_user,
        page=page,
        page_size=page_size,
    )


@router.get("/history", response_model=SuccessResponse[LeaveListResponse])
async def get_leave_history(
    employee_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveListResponse]:
    return await controller.get_leave_history(
        current_user,
        employee_id=employee_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get("", response_model=SuccessResponse[LeaveListResponse])
async def list_leave_requests(
    employee_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    leave_type_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveListResponse]:
    return await controller.list_leave_requests(
        current_user,
        employee_id=employee_id,
        status=status,
        leave_type_id=leave_type_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=SuccessResponse[LeaveRequestResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_leave_request(
    body: CreateLeaveRequest,
    request: Request,
    employee_id: UUID | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveRequestResponse]:
    return await controller.create_leave_request(
        body,
        current_user,
        request,
        employee_id=employee_id,
    )


@router.get("/{leave_request_id}", response_model=SuccessResponse[LeaveRequestResponse])
async def get_leave_request(
    leave_request_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveRequestResponse]:
    return await controller.get_leave_request(leave_request_id, current_user)


@router.post(
    "/{leave_request_id}/approve",
    response_model=SuccessResponse[LeaveRequestResponse],
)
async def approve_leave_request(
    leave_request_id: UUID,
    body: LeaveApprovalRequest,
    request: Request,
    current_user: CurrentUser = Depends(_approvers),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveRequestResponse]:
    return await controller.approve_leave(
        leave_request_id,
        body,
        current_user,
        request,
    )


@router.post(
    "/{leave_request_id}/reject",
    response_model=SuccessResponse[LeaveRequestResponse],
)
async def reject_leave_request(
    leave_request_id: UUID,
    body: LeaveApprovalRequest,
    request: Request,
    current_user: CurrentUser = Depends(_approvers),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveRequestResponse]:
    return await controller.reject_leave(
        leave_request_id,
        body,
        current_user,
        request,
    )


@router.post(
    "/{leave_request_id}/cancel",
    response_model=SuccessResponse[LeaveRequestResponse],
)
async def cancel_leave_request(
    leave_request_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    controller: LeaveController = Depends(_controller),
) -> SuccessResponse[LeaveRequestResponse]:
    return await controller.cancel_leave(leave_request_id, current_user, request)
