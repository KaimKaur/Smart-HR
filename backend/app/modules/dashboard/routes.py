from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEPARTMENT_MANAGER,
    EMPLOYEE,
    HR_MANAGER,
    RECRUITER,
    SYSTEM_ADMINISTRATOR,
)
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.dashboard.controller import DashboardController
from app.modules.dashboard.schema import (
    AttendanceDashboardResponse,
    EmployeeDashboardResponse,
    HRDashboardResponse,
    PerformanceDashboardResponse,
    RecruitmentDashboardResponse,
)

router = APIRouter()

_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)
_recruitment_allowed = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER, RECRUITER)
_employee_allowed = require_roles(EMPLOYEE, DEPARTMENT_MANAGER)


def _controller(session: AsyncSession = Depends(get_db)) -> DashboardController:
    return DashboardController(session)


@router.get("/hr", response_model=SuccessResponse[HRDashboardResponse])
async def get_hr_dashboard(
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: DashboardController = Depends(_controller),
) -> SuccessResponse[HRDashboardResponse]:
    return await controller.hr_dashboard(actor=current_user)


@router.get(
    "/recruitment",
    response_model=SuccessResponse[RecruitmentDashboardResponse],
)
async def get_recruitment_dashboard(
    current_user: CurrentUser = Depends(_recruitment_allowed),
    controller: DashboardController = Depends(_controller),
) -> SuccessResponse[RecruitmentDashboardResponse]:
    return await controller.recruitment_dashboard(actor=current_user)


@router.get(
    "/attendance",
    response_model=SuccessResponse[AttendanceDashboardResponse],
)
async def get_attendance_dashboard(
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: DashboardController = Depends(_controller),
) -> SuccessResponse[AttendanceDashboardResponse]:
    return await controller.attendance_dashboard(actor=current_user)


@router.get(
    "/performance",
    response_model=SuccessResponse[PerformanceDashboardResponse],
)
async def get_performance_dashboard(
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: DashboardController = Depends(_controller),
) -> SuccessResponse[PerformanceDashboardResponse]:
    return await controller.performance_dashboard(actor=current_user)


@router.get(
    "/employee",
    response_model=SuccessResponse[EmployeeDashboardResponse],
)
async def get_employee_dashboard(
    current_user: CurrentUser = Depends(_employee_allowed),
    controller: DashboardController = Depends(_controller),
) -> SuccessResponse[EmployeeDashboardResponse]:
    return await controller.employee_dashboard(actor=current_user)

