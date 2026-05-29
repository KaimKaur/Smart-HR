from datetime import date
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.attendance.errors import AttendanceError
from app.modules.attendance.http import attendance_http_exception
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
from app.modules.attendance.service import AttendanceService


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


class AttendanceController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = AttendanceService(session)

    async def check_in(
        self,
        body: CheckInRequest,
        current_user: CurrentUser,
        request: Request,
        *,
        employee_id: UUID | None = None,
    ) -> SuccessResponse[AttendanceRecordResponse]:
        try:
            target_id = employee_id or await self._service.resolve_actor_employee_id(
                current_user,
            )
            data = await self._service.check_in(
                target_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except AttendanceError as exc:
            raise attendance_http_exception(exc) from exc
        return SuccessResponse(message="Checked in", data=data)

    async def check_out(
        self,
        body: CheckOutRequest,
        current_user: CurrentUser,
        request: Request,
        *,
        employee_id: UUID | None = None,
    ) -> SuccessResponse[AttendanceRecordResponse]:
        try:
            target_id = employee_id or await self._service.resolve_actor_employee_id(
                current_user,
            )
            data = await self._service.check_out(
                target_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except AttendanceError as exc:
            raise attendance_http_exception(exc) from exc
        return SuccessResponse(message="Checked out", data=data)

    async def list_attendance(
        self,
        *,
        current_user: CurrentUser,
        employee_id: UUID | None,
        date_from: date | None,
        date_to: date | None,
        page: int,
        page_size: int,
    ) -> SuccessResponse[AttendanceRecordListResponse]:
        try:
            data = await self._service.get_attendance_history(
                actor=current_user,
                employee_id=employee_id,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=page_size,
            )
        except AttendanceError as exc:
            raise attendance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def daily_attendance(
        self,
        attendance_date: date,
        current_user: CurrentUser,
    ) -> SuccessResponse[DailyAttendanceResponse]:
        try:
            data = await self._service.get_daily_attendance(
                attendance_date,
                actor=current_user,
            )
        except AttendanceError as exc:
            raise attendance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def monthly_summary(
        self,
        *,
        current_user: CurrentUser,
        employee_id: UUID,
        year: int,
        month: int,
    ) -> SuccessResponse[MonthlySummaryResponse]:
        try:
            data = await self._service.get_monthly_summary(
                actor=current_user,
                employee_id=employee_id,
                year=year,
                month=month,
            )
        except AttendanceError as exc:
            raise attendance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def attendance_report(
        self,
        *,
        current_user: CurrentUser,
        department_id: UUID | None,
        status: UUID | None,
        date_from: date,
        date_to: date,
        page: int,
        page_size: int,
    ) -> SuccessResponse[AttendanceReportResponse]:
        try:
            data = await self._service.get_attendance_report(
                actor=current_user,
                department_id=department_id,
                status=status,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=page_size,
            )
        except AttendanceError as exc:
            raise attendance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def list_corrections(
        self,
        record_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[CorrectionListResponse]:
        try:
            data = await self._service.list_corrections(record_id, actor=current_user)
        except AttendanceError as exc:
            raise attendance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def request_correction(
        self,
        record_id: UUID,
        body: CorrectionRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[CorrectionResponse]:
        try:
            data = await self._service.request_correction(
                record_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except AttendanceError as exc:
            raise attendance_http_exception(exc) from exc
        return SuccessResponse(message="Correction requested", data=data)

    async def review_correction(
        self,
        correction_id: UUID,
        body: ReviewCorrectionRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[CorrectionResponse]:
        try:
            data = await self._service.review_correction(
                correction_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except AttendanceError as exc:
            raise attendance_http_exception(exc) from exc
        return SuccessResponse(message="Correction reviewed", data=data)
