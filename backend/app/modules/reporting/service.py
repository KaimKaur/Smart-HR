from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.responses import StreamingResponse

from app.core.constants import HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.export import generate_csv
from app.core.schemas import PaginationMeta
from app.core.security import CurrentUser
from app.modules.reporting.repository import ReportingRepository
from app.modules.reporting.schema import (
    AttendanceReportResponse,
    EmployeeReportResponse,
)


class ReportingError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ReportingService:
    def __init__(self, repository: ReportingRepository) -> None:
        self._repository = repository

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
    ) -> EmployeeReportResponse:
        self._require_hr_or_admin(actor)
        rows, total = await self._repository.list_employee_report(
            department_id=department_id,
            designation_id=designation_id,
            employment_status_id=employment_status_id,
            date_from=date_from,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )
        return EmployeeReportResponse(
            items=rows,
            pagination=self._build_pagination(page=page, page_size=page_size, total_items=total),
        )

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
    ) -> AttendanceReportResponse:
        self._require_hr_or_admin(actor)
        if date_from > date_to:
            raise ReportingError("date_from must be on or before date_to", 400)

        rows, total = await self._repository.list_attendance_report(
            employee_id=employee_id,
            department_id=department_id,
            date_from=date_from,
            date_to=date_to,
            status=status,
            page=page,
            page_size=page_size,
        )
        return AttendanceReportResponse(
            items=rows,
            pagination=self._build_pagination(page=page, page_size=page_size, total_items=total),
        )

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
        self._require_hr_or_admin(actor)
        rows, _ = await self._repository.list_employee_report(
            department_id=department_id,
            designation_id=designation_id,
            employment_status_id=employment_status_id,
            date_from=date_from,
            sort_by=sort_by,
            sort_order=sort_order,
            page=1,
            page_size=100_000,
        )
        csv_rows = [
            [
                row["employee_code"],
                row["full_name"],
                row["email"],
                row["department_name"],
                row["designation_title"],
                row["employment_status"],
                row["join_date"].isoformat(),
            ]
            for row in rows
        ]
        return generate_csv(
            headers=[
                "employee_code",
                "full_name",
                "email",
                "department_name",
                "designation_title",
                "employment_status",
                "join_date",
            ],
            rows=csv_rows,
            filename=f"employees_{self._today_stamp()}.csv",
        )

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
        self._require_hr_or_admin(actor)
        from_date = date_from or date.today()
        to_date = date_to or date.today()
        if from_date > to_date:
            raise ReportingError("date_from must be on or before date_to", 400)

        rows, _ = await self._repository.list_attendance_report(
            employee_id=employee_id,
            department_id=department_id,
            date_from=from_date,
            date_to=to_date,
            status=status,
            page=1,
            page_size=100_000,
        )
        csv_rows = [
            [
                row["attendance_date"].isoformat(),
                row["employee_code"],
                row["full_name"],
                row["department_name"],
                row["status_name"],
                row["check_in_time"].isoformat() if row["check_in_time"] else "",
                row["check_out_time"].isoformat() if row["check_out_time"] else "",
                row["work_duration_minutes"] if row["work_duration_minutes"] is not None else "",
            ]
            for row in rows
        ]
        return generate_csv(
            headers=[
                "attendance_date",
                "employee_code",
                "full_name",
                "department_name",
                "status_name",
                "check_in_time",
                "check_out_time",
                "work_duration_minutes",
            ],
            rows=csv_rows,
            filename=f"attendance_{self._today_stamp()}.csv",
        )

    async def export_recruitment_report(
        self,
        *,
        actor: CurrentUser,
        job_id: UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> StreamingResponse:
        self._require_hr_or_admin(actor)
        rows = await self._repository.recruitment_report_rows(
            job_id=job_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )
        csv_rows = [
            [
                row["job_title"],
                row["total_candidates"],
                row["shortlisted"],
                row["rejected"],
                row["pending"],
                row["average_ai_score"] if row["average_ai_score"] is not None else "",
            ]
            for row in rows
        ]
        return generate_csv(
            headers=[
                "job_title",
                "total_candidates",
                "shortlisted",
                "rejected",
                "pending",
                "average_ai_score",
            ],
            rows=csv_rows,
            filename=f"recruitment_{self._today_stamp()}.csv",
        )

    async def export_performance_report(
        self,
        *,
        actor: CurrentUser,
        cycle_id: UUID | None = None,
        department_id: UUID | None = None,
        date_from: date,
        date_to: date,
    ) -> StreamingResponse:
        self._require_hr_or_admin(actor)
        if date_from > date_to:
            raise ReportingError("date_from must be on or before date_to", 400)

        rows = await self._repository.performance_export_rows(
            cycle_id=cycle_id,
            department_id=department_id,
            date_from=date_from,
            date_to=date_to,
        )
        csv_rows = [
            [
                row["employee_name"],
                row["cycle_name"],
                row["rating"],
                row["average_score"] if row["average_score"] is not None else "",
                row["department_name"],
            ]
            for row in rows
        ]
        return generate_csv(
            headers=["employee_name", "cycle_name", "rating", "average_score", "department_name"],
            rows=csv_rows,
            filename=f"performance_{self._today_stamp()}.csv",
        )

    def _require_hr_or_admin(self, actor: CurrentUser) -> None:
        if not {HR_MANAGER, SYSTEM_ADMINISTRATOR}.intersection(actor.roles):
            raise ReportingError("Insufficient permissions", 403)

    def _build_pagination(self, *, page: int, page_size: int, total_items: int) -> PaginationMeta:
        total_pages = (total_items + page_size - 1) // page_size if page_size else 0
        return PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def _today_stamp(self) -> str:
        return datetime.now(UTC).date().isoformat()
