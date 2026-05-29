from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.attendance.controller import AttendanceController
from app.modules.attendance.schema import (
    AttendanceRecordListResponse,
    AttendanceRecordResponse,
    AttendanceReportResponse,
    CheckInRequest,
    CheckOutRequest,
    CorrectionListResponse,
    CorrectionRequest,
    CorrectionResponse,
    DailyAttendanceResponse,
    MonthlySummaryResponse,
    ReviewCorrectionRequest,
)

router = APIRouter()

_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)


def _controller(session: AsyncSession = Depends(get_db)) -> AttendanceController:
    return AttendanceController(session)


@router.post("/check-in", response_model=SuccessResponse[AttendanceRecordResponse])
async def check_in(
    body: CheckInRequest,
    request: Request,
    employee_id: UUID | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    controller: AttendanceController = Depends(_controller),
) -> SuccessResponse[AttendanceRecordResponse]:
    return await controller.check_in(
        body,
        current_user,
        request,
        employee_id=employee_id,
    )


@router.post("/check-out", response_model=SuccessResponse[AttendanceRecordResponse])
async def check_out(
    body: CheckOutRequest,
    request: Request,
    employee_id: UUID | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
    controller: AttendanceController = Depends(_controller),
) -> SuccessResponse[AttendanceRecordResponse]:
    return await controller.check_out(
        body,
        current_user,
        request,
        employee_id=employee_id,
    )


@router.get("/daily", response_model=SuccessResponse[DailyAttendanceResponse])
async def daily_attendance(
    attendance_date: date = Query(alias="date"),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: AttendanceController = Depends(_controller),
) -> SuccessResponse[DailyAttendanceResponse]:
    return await controller.daily_attendance(attendance_date, current_user)


@router.get("/monthly", response_model=SuccessResponse[MonthlySummaryResponse])
async def monthly_summary(
    employee_id: UUID = Query(),
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    current_user: CurrentUser = Depends(get_current_user),
    controller: AttendanceController = Depends(_controller),
) -> SuccessResponse[MonthlySummaryResponse]:
    return await controller.monthly_summary(
        current_user=current_user,
        employee_id=employee_id,
        year=year,
        month=month,
    )


@router.get("/report", response_model=SuccessResponse[AttendanceReportResponse])
async def attendance_report(
    date_from: date = Query(),
    date_to: date = Query(),
    department_id: UUID | None = Query(default=None),
    status: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: AttendanceController = Depends(_controller),
) -> SuccessResponse[AttendanceReportResponse]:
    return await controller.attendance_report(
        current_user=current_user,
        department_id=department_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/corrections/{correction_id}",
    response_model=SuccessResponse[CorrectionResponse],
)
async def review_correction(
    correction_id: UUID,
    body: ReviewCorrectionRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: AttendanceController = Depends(_controller),
) -> SuccessResponse[CorrectionResponse]:
    return await controller.review_correction(
        correction_id,
        body,
        current_user,
        request,
    )


@router.get(
    "/{record_id}/corrections",
    response_model=SuccessResponse[CorrectionListResponse],
)
async def list_corrections(
    record_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: AttendanceController = Depends(_controller),
) -> SuccessResponse[CorrectionListResponse]:
    return await controller.list_corrections(record_id, current_user)


@router.post(
    "/{record_id}/corrections",
    response_model=SuccessResponse[CorrectionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def request_correction(
    record_id: UUID,
    body: CorrectionRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    controller: AttendanceController = Depends(_controller),
) -> SuccessResponse[CorrectionResponse]:
    return await controller.request_correction(
        record_id,
        body,
        current_user,
        request,
    )


@router.get("", response_model=SuccessResponse[AttendanceRecordListResponse])
async def list_attendance(
    employee_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: AttendanceController = Depends(_controller),
) -> SuccessResponse[AttendanceRecordListResponse]:
    return await controller.list_attendance(
        current_user=current_user,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
