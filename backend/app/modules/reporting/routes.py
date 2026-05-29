from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, require_roles
from app.modules.reporting.controller import ReportingController
from app.modules.reporting.schema import AttendanceReportResponse, EmployeeReportResponse
from app.modules.performance.controller import PerformanceController
from app.modules.reporting.schema import PerformanceReportResponse

router = APIRouter()

_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)


def _controller(session: AsyncSession = Depends(get_db)) -> PerformanceController:
    return PerformanceController(session)


def _reporting_controller(session: AsyncSession = Depends(get_db)) -> ReportingController:
    return ReportingController(session)


@router.get(
    "/performance",
    response_model=SuccessResponse[PerformanceReportResponse],
)
async def performance_report(
    cycle_id: UUID | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    date_from: date = Query(),
    date_to: date = Query(),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[PerformanceReportResponse]:
    return await controller.performance_report(
        actor=current_user,
        cycle_id=cycle_id,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get("/employees", response_model=SuccessResponse[EmployeeReportResponse])
async def employee_report(
    department_id: UUID | None = Query(default=None),
    designation_id: UUID | None = Query(default=None),
    employment_status_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    sort_by: str = Query(default="join_date"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: ReportingController = Depends(_reporting_controller),
) -> SuccessResponse[EmployeeReportResponse]:
    return await controller.employee_report(
        actor=current_user,
        department_id=department_id,
        designation_id=designation_id,
        employment_status_id=employment_status_id,
        date_from=date_from,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/attendance", response_model=SuccessResponse[AttendanceReportResponse])
async def attendance_report(
    employee_id: UUID | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    date_from: date = Query(),
    date_to: date = Query(),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: ReportingController = Depends(_reporting_controller),
) -> SuccessResponse[AttendanceReportResponse]:
    return await controller.attendance_report(
        actor=current_user,
        employee_id=employee_id,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/employees/export", response_class=StreamingResponse)
async def export_employee_report(
    department_id: UUID | None = Query(default=None),
    designation_id: UUID | None = Query(default=None),
    employment_status_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    sort_by: str = Query(default="join_date"),
    sort_order: str = Query(default="desc"),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: ReportingController = Depends(_reporting_controller),
) -> StreamingResponse:
    return await controller.export_employee_report(
        actor=current_user,
        department_id=department_id,
        designation_id=designation_id,
        employment_status_id=employment_status_id,
        date_from=date_from,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/attendance/export", response_class=StreamingResponse)
async def export_attendance_report(
    employee_id: UUID | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    status: str | None = Query(default=None),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: ReportingController = Depends(_reporting_controller),
) -> StreamingResponse:
    return await controller.export_attendance_report(
        actor=current_user,
        employee_id=employee_id,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )


@router.get("/recruitment/export", response_class=StreamingResponse)
async def export_recruitment_report(
    job_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: ReportingController = Depends(_reporting_controller),
) -> StreamingResponse:
    return await controller.export_recruitment_report(
        actor=current_user,
        job_id=job_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/performance/export", response_class=StreamingResponse)
async def export_performance_report(
    cycle_id: UUID | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    date_from: date = Query(),
    date_to: date = Query(),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: ReportingController = Depends(_reporting_controller),
) -> StreamingResponse:
    return await controller.export_performance_report(
        actor=current_user,
        cycle_id=cycle_id,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
    )
