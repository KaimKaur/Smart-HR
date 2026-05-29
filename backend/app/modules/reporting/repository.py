from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.filtering import apply_filters
from app.core.pagination import paginate
from app.core.sorting import apply_sorting
from app.modules.attendance.model import AttendanceRecord, AttendanceStatus
from app.modules.employee.model import Department, Designation, Employee, EmploymentStatus
from app.modules.performance.model import EmployeeMetricScore, PerformanceCycle, PerformanceReview
from app.modules.recruitment.model import CandidateApplication, Job


class ReportingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_employee_report(
        self,
        *,
        department_id: UUID | None = None,
        designation_id: UUID | None = None,
        employment_status_id: UUID | None = None,
        date_from: date | None = None,
        sort_by: str = "join_date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        query = (
            select(
                Employee.id.label("employee_id"),
                Employee.employee_code,
                Employee.first_name,
                Employee.last_name,
                Employee.email,
                Department.name.label("department_name"),
                Designation.title.label("designation_title"),
                EmploymentStatus.name.label("employment_status"),
                Employee.join_date,
            )
            .select_from(Employee)
            .join(Department, Department.id == Employee.department_id)
            .join(Designation, Designation.id == Employee.designation_id)
            .join(EmploymentStatus, EmploymentStatus.id == Employee.employment_status_id)
            .where(Employee.deleted_at.is_(None))
        )

        query = apply_filters(
            query,
            date_column=Employee.join_date,
            date_from=date_from,
            exact_filters={
                Employee.department_id: department_id,
                Employee.designation_id: designation_id,
                Employee.employment_status_id: employment_status_id,
            },
        )
        query = apply_sorting(query, Employee, sort_by=sort_by, sort_order=sort_order)

        paginated = await paginate(self._session, query, page=page, page_size=page_size)
        rows = [
            {
                "employee_id": row.employee_id,
                "employee_code": row.employee_code,
                "full_name": f"{row.first_name} {row.last_name}".strip(),
                "email": row.email,
                "department_name": row.department_name,
                "designation_title": row.designation_title,
                "employment_status": row.employment_status,
                "join_date": row.join_date,
            }
            for row in paginated.items
        ]
        return rows, paginated.total_items

    async def list_attendance_report(
        self,
        *,
        employee_id: UUID | None = None,
        department_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        query = (
            select(
                AttendanceRecord.id.label("record_id"),
                Employee.id.label("employee_id"),
                Employee.employee_code,
                Employee.first_name,
                Employee.last_name,
                Department.name.label("department_name"),
                AttendanceRecord.attendance_date,
                AttendanceStatus.name.label("status_name"),
                AttendanceRecord.check_in_time,
                AttendanceRecord.check_out_time,
                AttendanceRecord.work_duration_minutes,
            )
            .select_from(AttendanceRecord)
            .join(Employee, Employee.id == AttendanceRecord.employee_id)
            .join(Department, Department.id == Employee.department_id)
            .join(AttendanceStatus, AttendanceStatus.id == AttendanceRecord.attendance_status_id)
            .where(Employee.deleted_at.is_(None))
        )

        query = apply_filters(
            query,
            date_column=AttendanceRecord.attendance_date,
            date_from=date_from,
            date_to=date_to,
            exact_filters={
                Employee.id: employee_id,
                Employee.department_id: department_id,
                AttendanceStatus.name: status,
            },
        )
        query = query.order_by(AttendanceRecord.attendance_date.desc(), Employee.last_name.asc())

        paginated = await paginate(self._session, query, page=page, page_size=page_size)
        rows = [
            {
                "record_id": row.record_id,
                "employee_id": row.employee_id,
                "employee_code": row.employee_code,
                "full_name": f"{row.first_name} {row.last_name}".strip(),
                "department_name": row.department_name,
                "attendance_date": row.attendance_date,
                "status_name": row.status_name,
                "check_in_time": row.check_in_time,
                "check_out_time": row.check_out_time,
                "work_duration_minutes": row.work_duration_minutes,
            }
            for row in paginated.items
        ]
        return rows, paginated.total_items

    async def recruitment_report_rows(
        self,
        *,
        job_id: UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict]:
        query: Select = (
            select(
                Job.id.label("job_id"),
                Job.title.label("job_title"),
                func.count(CandidateApplication.id).label("total_candidates"),
                func.sum(
                    case((CandidateApplication.application_status == "shortlisted", 1), else_=0),
                ).label("shortlisted"),
                func.sum(
                    case((CandidateApplication.application_status == "rejected", 1), else_=0),
                ).label("rejected"),
                func.sum(
                    case(
                        (
                            CandidateApplication.application_status.in_(
                                ["applied", "screening"],
                            ),
                            1,
                        ),
                        else_=0,
                    ),
                ).label("pending"),
                func.avg(CandidateApplication.ai_score)
                .filter(CandidateApplication.ai_score.is_not(None))
                .label("average_ai_score"),
            )
            .select_from(Job)
            .outerjoin(
                CandidateApplication,
                (CandidateApplication.job_id == Job.id)
                & CandidateApplication.deleted_at.is_(None),
            )
            .where(Job.deleted_at.is_(None))
            .group_by(Job.id, Job.title)
            .order_by(Job.title.asc())
        )

        if job_id is not None:
            query = query.where(Job.id == job_id)
        if status is not None:
            query = query.where(CandidateApplication.application_status == status)
        if date_from is not None:
            query = query.where(func.date(CandidateApplication.created_at) >= date_from)
        if date_to is not None:
            query = query.where(func.date(CandidateApplication.created_at) <= date_to)

        result = (await self._session.execute(query)).all()
        return [
            {
                "job_id": row.job_id,
                "job_title": row.job_title,
                "total_candidates": int(row.total_candidates or 0),
                "shortlisted": int(row.shortlisted or 0),
                "rejected": int(row.rejected or 0),
                "pending": int(row.pending or 0),
                "average_ai_score": float(row.average_ai_score)
                if row.average_ai_score is not None
                else None,
            }
            for row in result
        ]

    async def performance_export_rows(
        self,
        *,
        cycle_id: UUID | None = None,
        department_id: UUID | None = None,
        date_from: date,
        date_to: date,
    ) -> list[dict]:
        avg_scores_subq = (
            select(
                EmployeeMetricScore.review_id.label("review_id"),
                func.avg(EmployeeMetricScore.score).label("average_score"),
            )
            .group_by(EmployeeMetricScore.review_id)
            .subquery()
        )
        query = (
            select(
                Employee.first_name,
                Employee.last_name,
                Department.name.label("department_name"),
                PerformanceCycle.name.label("cycle_name"),
                PerformanceReview.rating,
                avg_scores_subq.c.average_score,
            )
            .select_from(PerformanceReview)
            .join(Employee, Employee.id == PerformanceReview.employee_id)
            .join(Department, Department.id == Employee.department_id)
            .join(PerformanceCycle, PerformanceCycle.id == PerformanceReview.cycle_id)
            .outerjoin(avg_scores_subq, avg_scores_subq.c.review_id == PerformanceReview.id)
            .where(
                PerformanceCycle.start_date >= date_from,
                PerformanceCycle.start_date <= date_to,
            )
            .order_by(Employee.last_name.asc(), Employee.first_name.asc())
        )
        if cycle_id is not None:
            query = query.where(PerformanceReview.cycle_id == cycle_id)
        if department_id is not None:
            query = query.where(Employee.department_id == department_id)

        result = (await self._session.execute(query)).all()
        return [
            {
                "employee_name": f"{row.first_name} {row.last_name}".strip(),
                "cycle_name": row.cycle_name,
                "rating": float(row.rating),
                "average_score": float(row.average_score)
                if row.average_score is not None
                else None,
                "department_name": row.department_name,
            }
            for row in result
        ]
