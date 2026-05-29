from __future__ import annotations

from collections import defaultdict
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Date, and_, cast, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attendance.model import AttendanceRecord, AttendanceStatus
from app.modules.employee.model import Department, Employee, EmploymentStatus
from app.modules.leave.model import LeaveBalance, LeaveRequest, LeaveType
from app.modules.notifications.model import Notification
from app.modules.performance.model import PerformanceCycle, PerformanceReview
from app.modules.recruitment.model import Candidate, CandidateApplication, Interview, Job


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- HR dashboard ---

    async def get_hr_snapshot(self, today: date) -> dict:
        thirty_days_ago = today - timedelta(days=30)
        month_start = date(today.year, today.month, 1)

        # Total and active employees.
        total_employees_query = select(func.count()).select_from(Employee).where(
            Employee.deleted_at.is_(None),
        )

        active_status_subq = (
            select(EmploymentStatus.id)
            .where(EmploymentStatus.name == "Active")
            .scalar_subquery()
        )
        active_employees_query = select(func.count()).select_from(Employee).where(
            Employee.deleted_at.is_(None),
            Employee.employment_status_id == active_status_subq,
        )

        # New hires.
        new_hires_query = select(func.count()).select_from(Employee).where(
            Employee.deleted_at.is_(None),
            Employee.join_date >= thirty_days_ago,
        )

        # Departments.
        departments_query = select(func.count(func.distinct(Department.id))).select_from(
            Department,
        )

        # Attendance rate today: present / active employees.
        present_status_subq = (
            select(AttendanceStatus.id)
            .where(AttendanceStatus.name == "present")
            .scalar_subquery()
        )
        today_present_query = select(func.count()).select_from(AttendanceRecord).where(
            AttendanceRecord.attendance_date == today,
            AttendanceRecord.attendance_status_id == present_status_subq,
        )

        # Pending leave requests.
        pending_leave_query = select(func.count()).select_from(LeaveRequest).where(
            LeaveRequest.status == "pending",
            LeaveRequest.deleted_at.is_(None),
        )

        # Open job postings.
        open_jobs_query = select(func.count()).select_from(Job).where(
            Job.status == "published",
            Job.deleted_at.is_(None),
        )

        # Candidates created this month.
        candidates_month_query = select(func.count()).select_from(Candidate).where(
            Candidate.deleted_at.is_(None),
            cast(Candidate.created_at, Date) >= month_start,
            cast(Candidate.created_at, Date) <= today,
        )

        (
            total_employees_result,
            active_employees_result,
            new_hires_result,
            departments_result,
            todays_present_result,
            pending_leave_result,
            open_jobs_result,
            candidates_month_result,
        ) = await self._session.execute(
            total_employees_query
        ), await self._session.execute(
            active_employees_query
        ), await self._session.execute(
            new_hires_query
        ), await self._session.execute(
            departments_query
        ), await self._session.execute(
            today_present_query
        ), await self._session.execute(
            pending_leave_query
        ), await self._session.execute(
            open_jobs_query
        ), await self._session.execute(candidates_month_query)

        total_employees = int(total_employees_result.scalar_one())
        active_employees = int(active_employees_result.scalar_one())
        new_hires_last_30_days = int(new_hires_result.scalar_one())
        departments_count = int(departments_result.scalar_one())
        todays_present = int(todays_present_result.scalar_one())
        pending_leave_requests_count = int(pending_leave_result.scalar_one())
        open_job_postings = int(open_jobs_result.scalar_one())
        candidates_this_month = int(candidates_month_result.scalar_one())

        attendance_rate_today = (
            float(todays_present) * 100 / active_employees if active_employees else 0.0
        )

        return {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "new_hires_last_30_days": new_hires_last_30_days,
            "departments_count": departments_count,
            "attendance_rate_today": round(attendance_rate_today, 2),
            "pending_leave_requests_count": pending_leave_requests_count,
            "open_job_postings": open_job_postings,
            "candidates_this_month": candidates_this_month,
        }

    # --- Recruitment dashboard ---

    async def get_recruitment_snapshot(self, today: date, *, top_n_per_job: int = 3) -> dict:
        month_start = date(today.year, today.month, 1)

        open_jobs_query = select(func.count()).select_from(Job).where(
            Job.status == "published",
            Job.deleted_at.is_(None),
        )

        total_candidates_query = select(func.count()).select_from(Candidate).where(
            Candidate.deleted_at.is_(None),
        )

        shortlisted_candidates_query = select(func.count()).select_from(Candidate).where(
            Candidate.deleted_at.is_(None),
            Candidate.current_status == "shortlisted",
        )

        rejected_candidates_query = select(func.count()).select_from(Candidate).where(
            Candidate.deleted_at.is_(None),
            Candidate.current_status == "rejected",
        )

        pending_screening_candidates_query = select(func.count()).select_from(Candidate).where(
            Candidate.deleted_at.is_(None),
            Candidate.current_status == "screening",
        )

        average_ai_score_query = select(func.avg(CandidateApplication.ai_score)).select_from(
            CandidateApplication
        ).where(
            CandidateApplication.deleted_at.is_(None),
            CandidateApplication.ai_score.is_not(None),
        )

        # Per-job breakdown for published jobs.
        open_apps = func.count(CandidateApplication.id)
        shortlisted_apps = func.sum(
            case((CandidateApplication.application_status == "shortlisted", 1), else_=0)
        )
        rejected_apps = func.sum(
            case((CandidateApplication.application_status == "rejected", 1), else_=0)
        )
        pending_screening_apps = func.sum(
            case((CandidateApplication.application_status == "screening", 1), else_=0)
        )

        per_job_query = (
            select(
                Job.id,
                Job.title,
                open_apps.label("open_applications"),
                shortlisted_apps.label("shortlisted_applications"),
                rejected_apps.label("rejected_applications"),
                pending_screening_apps.label("pending_screening_applications"),
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
            .where(Job.status == "published", Job.deleted_at.is_(None))
            .group_by(Job.id, Job.title)
            .order_by(Job.title.asc())
        )

        # Top candidates per job by ai_score (deterministic).
        rn = func.row_number().over(
            partition_by=CandidateApplication.job_id,
            order_by=(
                CandidateApplication.ai_score.desc().nullslast(),
                CandidateApplication.created_at.desc(),
            ),
        ).label("rn")

        top_candidates_query = (
            select(
                CandidateApplication.job_id,
                CandidateApplication.id.label("application_id"),
                Candidate.id.label("candidate_id"),
                Candidate.full_name,
                Candidate.email,
                CandidateApplication.ai_score,
                rn,
            )
            .select_from(CandidateApplication)
            .join(Job, Job.id == CandidateApplication.job_id)
            .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
            .where(
                Job.status == "published",
                Job.deleted_at.is_(None),
                Candidate.deleted_at.is_(None),
                CandidateApplication.deleted_at.is_(None),
                CandidateApplication.ai_score.is_not(None),
            )
        )

        (
            open_jobs_result,
            total_candidates_result,
            shortlisted_candidates_result,
            rejected_candidates_result,
            pending_screening_candidates_result,
            average_ai_score_result,
        ) = (
            await self._session.execute(open_jobs_query),
            await self._session.execute(total_candidates_query),
            await self._session.execute(shortlisted_candidates_query),
            await self._session.execute(rejected_candidates_query),
            await self._session.execute(pending_screening_candidates_query),
            await self._session.execute(average_ai_score_query),
        )

        per_job_rows = (await self._session.execute(per_job_query)).all()
        top_candidate_rows = (await self._session.execute(top_candidates_query)).all()

        top_by_job: dict[str, list[dict]] = defaultdict(list)
        for row in top_candidate_rows:
            if int(row.rn) <= top_n_per_job:
                top_by_job[str(row.job_id)].append(
                    {
                        "application_id": str(row.application_id),
                        "candidate_id": str(row.candidate_id),
                        "full_name": row.full_name,
                        "email": row.email,
                        "ai_score": float(row.ai_score),
                    }
                )

        jobs: list[dict] = []
        for row in per_job_rows:
            jobs.append(
                {
                    "job_id": str(row.id),
                    "title": row.title,
                    "open_applications": int(row.open_applications or 0),
                    "shortlisted_applications": int(row.shortlisted_applications or 0),
                    "rejected_applications": int(row.rejected_applications or 0),
                    "pending_screening_applications": int(
                        row.pending_screening_applications or 0
                    ),
                    "average_ai_score": float(row.average_ai_score)
                    if row.average_ai_score is not None
                    else None,
                    "top_candidates": top_by_job.get(str(row.id), []),
                }
            )

        avg_score = average_ai_score_result.scalar_one()

        return {
            "open_jobs": int(open_jobs_result.scalar_one()),
            "total_candidates": int(total_candidates_result.scalar_one()),
            "shortlisted_candidates": int(shortlisted_candidates_result.scalar_one()),
            "rejected_candidates": int(rejected_candidates_result.scalar_one()),
            "pending_screening_candidates": int(pending_screening_candidates_result.scalar_one()),
            "average_ai_score": float(avg_score) if avg_score is not None else None,
            "jobs": jobs,
        }

    # --- Attendance dashboard ---

    async def get_attendance_snapshot(self, today: date) -> dict:
        """
        Attendance dashboard snapshot.

        Notes / ambiguity resolved:
        - "Absent" is computed as active employees with either an explicit 'absent' status
          OR no attendance record for today (matching existing daily-attendance behavior).
        - "Late" is computed if an attendance status named 'late' exists; otherwise it is 0.
        """

        active_status_subq = (
            select(EmploymentStatus.id)
            .where(EmploymentStatus.name == "Active")
            .scalar_subquery()
        )

        # Active employees per department (used for absence-by-department).
        active_employees_cte = (
            select(
                Employee.id.label("employee_id"),
                Employee.department_id.label("department_id"),
            )
            .where(
                Employee.deleted_at.is_(None),
                Employee.employment_status_id == active_status_subq,
            )
            .cte("active_employees")
        )

        active_count_result = await self._session.execute(
            select(func.count()).select_from(active_employees_cte),
        )
        active_employees_count = int(active_count_result.scalar_one())

        present_status_id = await self._session.execute(
            select(AttendanceStatus.id).where(AttendanceStatus.name == "present"),
        )
        absent_status_id = await self._session.execute(
            select(AttendanceStatus.id).where(AttendanceStatus.name == "absent"),
        )
        late_status_id = await self._session.execute(
            select(AttendanceStatus.id).where(AttendanceStatus.name == "late"),
        )

        present_id = present_status_id.scalar_one_or_none()
        absent_id = absent_status_id.scalar_one_or_none()
        late_id = late_status_id.scalar_one_or_none()

        # Counts for today's records for active employees only.
        record_counts_query = (
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (AttendanceRecord.attendance_status_id == present_id, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("present_count"),
                func.coalesce(
                    func.sum(
                        case(
                            (AttendanceRecord.attendance_status_id == absent_id, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("explicit_absent_count"),
                func.coalesce(
                    func.sum(
                        case(
                            (AttendanceRecord.attendance_status_id == late_id, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("late_count"),
                func.count(AttendanceRecord.id).label("records_count"),
            )
            .select_from(active_employees_cte)
            .outerjoin(
                AttendanceRecord,
                and_(
                    AttendanceRecord.employee_id == active_employees_cte.c.employee_id,
                    AttendanceRecord.attendance_date == today,
                ),
            )
        )

        counts_row = (await self._session.execute(record_counts_query)).one()

        present_count = int(counts_row.present_count or 0)
        explicit_absent_count = int(counts_row.explicit_absent_count or 0)
        late_count = int(counts_row.late_count or 0)
        records_count = int(counts_row.records_count or 0)

        # Absent includes missing records for active employees.
        missing_records = max(active_employees_count - records_count, 0)
        absent_count = explicit_absent_count + missing_records

        attendance_rate_today = (
            float(present_count) * 100 / active_employees_count
            if active_employees_count
            else 0.0
        )

        # Weekly trend (last 7 days inclusive): record-based present/absent counts.
        start_date = today - timedelta(days=6)
        weekly_rows = (
            await self._session.execute(
                select(
                    AttendanceRecord.attendance_date.label("date"),
                    func.coalesce(
                        func.sum(
                            case(
                                (AttendanceRecord.attendance_status_id == present_id, 1),
                                else_=0,
                            )
                        ),
                        0,
                    ).label("present_count"),
                    func.coalesce(
                        func.sum(
                            case(
                                (AttendanceRecord.attendance_status_id == absent_id, 1),
                                else_=0,
                            )
                        ),
                        0,
                    ).label("absent_count"),
                )
                .select_from(AttendanceRecord)
                .join(
                    active_employees_cte,
                    active_employees_cte.c.employee_id == AttendanceRecord.employee_id,
                )
                .where(
                    AttendanceRecord.attendance_date >= start_date,
                    AttendanceRecord.attendance_date <= today,
                )
                .group_by(AttendanceRecord.attendance_date)
                .order_by(AttendanceRecord.attendance_date.asc()),
            )
        ).all()

        weekly_trend = []
        by_date = {r.date: r for r in weekly_rows}
        for i in range(7):
            d = start_date + timedelta(days=i)
            r = by_date.get(d)
            weekly_trend.append(
                {
                    "date": d,
                    "present_count": int(getattr(r, "present_count", 0) or 0),
                    "absent_count": int(getattr(r, "absent_count", 0) or 0),
                }
            )

        # Top absent departments (today), counting explicit absent + missing records.
        # 1) total active by department
        active_by_dept_rows = (
            await self._session.execute(
                select(
                    active_employees_cte.c.department_id.label("department_id"),
                    func.count(active_employees_cte.c.employee_id).label("active_count"),
                )
                .group_by(active_employees_cte.c.department_id),
            )
        ).all()
        active_by_dept = {r.department_id: int(r.active_count) for r in active_by_dept_rows}

        # 2) present/late/explicit absent records by department
        dept_record_counts = (
            await self._session.execute(
                select(
                    active_employees_cte.c.department_id.label("department_id"),
                    func.count(AttendanceRecord.id).label("records_count"),
                    func.coalesce(
                        func.sum(
                            case(
                                (AttendanceRecord.attendance_status_id == absent_id, 1),
                                else_=0,
                            )
                        ),
                        0,
                    ).label("explicit_absent_count"),
                )
                .select_from(active_employees_cte)
                .outerjoin(
                    AttendanceRecord,
                    and_(
                        AttendanceRecord.employee_id == active_employees_cte.c.employee_id,
                        AttendanceRecord.attendance_date == today,
                    ),
                )
                .group_by(active_employees_cte.c.department_id),
            )
        ).all()

        # 3) department names
        dept_names = (
            await self._session.execute(
                select(Department.id, Department.name).select_from(Department),
            )
        ).all()
        dept_name_by_id = {d.id: d.name for d in dept_names}

        top_absent_departments = []
        for r in dept_record_counts:
            dept_id = r.department_id
            dept_active = active_by_dept.get(dept_id, 0)
            dept_records = int(r.records_count or 0)
            dept_explicit_absent = int(r.explicit_absent_count or 0)
            dept_missing = max(dept_active - dept_records, 0)
            dept_absent = dept_explicit_absent + dept_missing
            if dept_absent > 0:
                top_absent_departments.append(
                    {
                        "department_id": str(dept_id),
                        "department_name": dept_name_by_id.get(dept_id) or "",
                        "absent_count": int(dept_absent),
                    }
                )

        top_absent_departments.sort(key=lambda x: (-x["absent_count"], x["department_name"]))
        top_absent_departments = top_absent_departments[:5]

        return {
            "today_date": today,
            "present_count": present_count,
            "absent_count": absent_count,
            "late_count": late_count,
            "attendance_rate_today": round(attendance_rate_today, 2),
            "weekly_trend": weekly_trend,
            "top_absent_departments": top_absent_departments,
        }

    # --- Performance dashboard ---

    async def get_performance_snapshot(self, today: date) -> dict:
        # Active cycle is derived from date range (cycle has no status column).
        active_cycle_row = (
            await self._session.execute(
                select(PerformanceCycle)
                .where(PerformanceCycle.start_date <= today, PerformanceCycle.end_date >= today)
                .order_by(PerformanceCycle.start_date.desc(), PerformanceCycle.id.desc())
                .limit(1),
            )
        ).scalar_one_or_none()

        if active_cycle_row is None:
            return {
                "active_cycle_id": None,
                "active_cycle_name": None,
                "average_rating": None,
                "top_performers": [],
                "employees_without_review": 0,
            }

        cycle_id = active_cycle_row.id

        avg_rating_result = await self._session.execute(
            select(func.avg(PerformanceReview.rating)).where(PerformanceReview.cycle_id == cycle_id),
        )
        avg_rating = avg_rating_result.scalar_one()

        top_rows = (
            await self._session.execute(
                select(
                    Employee.id.label("employee_id"),
                    Employee.employee_code.label("employee_code"),
                    Employee.first_name.label("first_name"),
                    Employee.last_name.label("last_name"),
                    Department.name.label("department_name"),
                    PerformanceReview.rating.label("rating"),
                )
                .select_from(PerformanceReview)
                .join(Employee, Employee.id == PerformanceReview.employee_id)
                .join(Department, Department.id == Employee.department_id)
                .where(
                    PerformanceReview.cycle_id == cycle_id,
                    PerformanceReview.rating >= 4.0,
                    Employee.deleted_at.is_(None),
                )
                .order_by(
                    PerformanceReview.rating.desc(),
                    Employee.last_name.asc(),
                    Employee.first_name.asc(),
                    PerformanceReview.id.desc(),
                )
                .limit(20),
            )
        ).all()

        top_performers = [
            {
                "employee_id": str(r.employee_id),
                "employee_code": r.employee_code,
                "full_name": f"{r.first_name} {r.last_name}".strip(),
                "department_name": r.department_name,
                "rating": float(r.rating),
            }
            for r in top_rows
        ]

        # Employees not yet reviewed in this cycle: active employees minus distinct reviewed employee ids.
        active_status_subq = (
            select(EmploymentStatus.id)
            .where(EmploymentStatus.name == "Active")
            .scalar_subquery()
        )
        active_employees_count_result = await self._session.execute(
            select(func.count()).select_from(Employee).where(
                Employee.deleted_at.is_(None),
                Employee.employment_status_id == active_status_subq,
            )
        )
        active_employees_count = int(active_employees_count_result.scalar_one())

        reviewed_distinct_result = await self._session.execute(
            select(func.count(func.distinct(PerformanceReview.employee_id))).where(
                PerformanceReview.cycle_id == cycle_id,
            )
        )
        reviewed_distinct = int(reviewed_distinct_result.scalar_one())

        employees_without_review = max(active_employees_count - reviewed_distinct, 0)

        return {
            "active_cycle_id": str(active_cycle_row.id),
            "active_cycle_name": active_cycle_row.name,
            "average_rating": float(avg_rating) if avg_rating is not None else None,
            "top_performers": top_performers,
            "employees_without_review": employees_without_review,
        }

    # --- Employee dashboard ---

    async def get_employee_snapshot(self, user_id: uuid.UUID, today: date) -> dict:
        month_start = date(today.year, today.month, 1)

        employee_row = (
            await self._session.execute(
                select(Employee).where(Employee.user_id == user_id, Employee.deleted_at.is_(None)),
            )
        ).scalar_one_or_none()

        if employee_row is None:
            # Mirror other modules: missing employee profile is a 404 in service.
            return {"_error": "employee_not_found"}

        employee_id = employee_row.id

        present_id = (
            await self._session.execute(
                select(AttendanceStatus.id).where(AttendanceStatus.name == "present"),
            )
        ).scalar_one_or_none()

        attendance_row = (
            await self._session.execute(
                select(
                    func.coalesce(
                        func.sum(case((AttendanceRecord.attendance_status_id == present_id, 1), else_=0)),
                        0,
                    ).label("present_days"),
                    func.coalesce(func.sum(AttendanceRecord.work_duration_minutes), 0).label(
                        "total_minutes"
                    ),
                )
                .select_from(AttendanceRecord)
                .where(
                    AttendanceRecord.employee_id == employee_id,
                    AttendanceRecord.attendance_date >= month_start,
                    AttendanceRecord.attendance_date <= today,
                ),
            )
        ).one()

        present_days = int(attendance_row.present_days or 0)
        total_minutes = int(attendance_row.total_minutes or 0)
        total_hours = round(total_minutes / 60, 2)

        balance_rows = (
            await self._session.execute(
                select(
                    LeaveBalance.leave_type_id,
                    LeaveType.name.label("leave_type_name"),
                    LeaveBalance.balance,
                )
                .select_from(LeaveBalance)
                .join(LeaveType, LeaveType.id == LeaveBalance.leave_type_id)
                .where(LeaveBalance.employee_id == employee_id)
                .order_by(LeaveType.name.asc()),
            )
        ).all()

        leave_balances = [
            {
                "leave_type_id": str(r.leave_type_id),
                "leave_type_name": r.leave_type_name,
                "balance": float(r.balance),
            }
            for r in balance_rows
        ]

        latest_rating_row = (
            await self._session.execute(
                select(PerformanceReview.rating)
                .where(PerformanceReview.employee_id == employee_id)
                .order_by(PerformanceReview.created_at.desc(), PerformanceReview.id.desc())
                .limit(1),
            )
        ).scalar_one_or_none()

        unread_count = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(Notification).where(
                        Notification.user_id == user_id,
                        Notification.is_read.is_(False),
                    ),
                )
            ).scalar_one()
        )

        return {
            "attendance_this_month": {
                "present_days": present_days,
                "total_hours": float(total_hours),
            },
            "leave_balances": leave_balances,
            "latest_performance_rating": float(latest_rating_row)
            if latest_rating_row is not None
            else None,
            "unread_notifications_count": unread_count,
            "upcoming_interviews": [],
        }

