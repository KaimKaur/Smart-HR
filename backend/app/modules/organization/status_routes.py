from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user
from app.modules.organization.status_controller import StatusController
from app.modules.organization.status_schema import (
    AttendanceStatusListResponse,
    EmploymentStatusListResponse,
)

employment_router = APIRouter()
attendance_router = APIRouter()


def _controller(session: AsyncSession = Depends(get_db)) -> StatusController:
    return StatusController(session)


@employment_router.get(
    "",
    response_model=SuccessResponse[EmploymentStatusListResponse],
)
async def list_employment_statuses(
    current_user: CurrentUser = Depends(get_current_user),
    controller: StatusController = Depends(_controller),
) -> SuccessResponse[EmploymentStatusListResponse]:
    return await controller.list_employment_statuses()


@attendance_router.get(
    "",
    response_model=SuccessResponse[AttendanceStatusListResponse],
)
async def list_attendance_statuses(
    current_user: CurrentUser = Depends(get_current_user),
    controller: StatusController = Depends(_controller),
) -> SuccessResponse[AttendanceStatusListResponse]:
    return await controller.list_attendance_statuses()
