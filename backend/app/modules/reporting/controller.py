from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.reporting.repository import ReportingRepository
from app.modules.reporting.schema import (
    AttendanceReportResponse,
    EmployeeReportResponse,
)
from app.modules.reporting.service import ReportingError, ReportingService


class ReportingController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = ReportingService(ReportingRepository(session))

    async def employee_report(
        self,
        *,
        actor: CurrentUser,
        department_id: UUID | None = None,
        designation_id: UUID | None = None,
        employment_status_id: UUID | None = None,
        date_from: date | None = None,
        sort_by: str = "join_date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[EmployeeReportResponse]:
        try:
            data = await self._service.employee_report(
                actor=actor,
                department_id=department_id,
                designation_id=designation_id,
                employment_status_id=employment_status_id,
                date_from=date_from,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )
        except ReportingError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
        return SuccessResponse(message="Employee report retrieved", data=data)

    async def attendance_report(
        self,
        *,
        actor: CurrentUser,
        employee_id: UUID | None = None,
        department_id: UUID | None = None,
        date_from: date,
        date_to: date,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[AttendanceReportResponse]:
        try:
            data = await self._service.attendance_report(
                actor=actor,
                employee_id=employee_id,
                department_id=department_id,
                date_from=date_from,
                date_to=date_to,
                status=status,
                page=page,
                page_size=page_size,
            )
        except ReportingError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
        return SuccessResponse(message="Attendance report retrieved", data=data)

    async def export_employee_report(
        self,
        *,
        actor: CurrentUser,
        department_id: UUID | None = None,
        designation_id: UUID | None = None,
        employment_status_id: UUID | None = None,
        date_from: date | None = None,
        sort_by: str = "join_date",
        sort_order: str = "desc",
    ) -> StreamingResponse:
        try:
            return await self._service.export_employee_report(
                actor=actor,
                department_id=department_id,
                designation_id=designation_id,
                employment_status_id=employment_status_id,
                date_from=date_from,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        except ReportingError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    async def export_attendance_report(
        self,
        *,
        actor: CurrentUser,
        employee_id: UUID | None = None,
        department_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: str | None = None,
    ) -> StreamingResponse:
        try:
            return await self._service.export_attendance_report(
                actor=actor,
                employee_id=employee_id,
                department_id=department_id,
                date_from=date_from,
                date_to=date_to,
                status=status,
            )
        except ReportingError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    async def export_recruitment_report(
        self,
        *,
        actor: CurrentUser,
        job_id: UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> StreamingResponse:
        try:
            return await self._service.export_recruitment_report(
                actor=actor,
                job_id=job_id,
                status=status,
                date_from=date_from,
                date_to=date_to,
            )
        except ReportingError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    async def export_performance_report(
        self,
        *,
        actor: CurrentUser,
        cycle_id: UUID | None = None,
        department_id: UUID | None = None,
        date_from: date,
        date_to: date,
    ) -> StreamingResponse:
        try:
            return await self._service.export_performance_report(
                actor=actor,
                cycle_id=cycle_id,
                department_id=department_id,
                date_from=date_from,
                date_to=date_to,
            )
        except ReportingError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
