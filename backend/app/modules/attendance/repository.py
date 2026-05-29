import uuid
from calendar import monthrange
from datetime import UTC, date, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.attendance.model import (
    AttendanceCorrection,
    AttendanceRecord,
    AttendanceStatus,
)
from app.modules.auth.model import Role, UserRole
from app.modules.employee.model import Department, Employee, EmploymentStatus
from app.modules.notifications.model import AuditLog
from app.modules.notifications.model import Notification


class AttendanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_status_by_name(self, name: str) -> AttendanceStatus | None:
        result = await self._session.execute(
            select(AttendanceStatus).where(AttendanceStatus.name == name),
        )
        return result.scalar_one_or_none()

    async def get_status_id_by_name(self, name: str) -> uuid.UUID | None:
        result = await self._session.execute(
            select(AttendanceStatus.id).where(AttendanceStatus.name == name),
        )
        return result.scalar_one_or_none()

    async def get_record_by_id(self, record_id: uuid.UUID) -> AttendanceRecord | None:
        result = await self._session.execute(
            select(AttendanceRecord)
            .where(AttendanceRecord.id == record_id)
            .options(selectinload(AttendanceRecord.status)),
        )
        return result.scalar_one_or_none()

    async def get_record_by_employee_date(
        self,
        employee_id: uuid.UUID,
        attendance_date: date,
    ) -> AttendanceRecord | None:
        result = await self._session.execute(
            select(AttendanceRecord)
            .where(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.attendance_date == attendance_date,
            )
            .options(selectinload(AttendanceRecord.status)),
        )
        return result.scalar_one_or_none()

    async def create_check_in(
        self,
        *,
        employee_id: uuid.UUID,
        attendance_date: date,
        check_in_time: datetime,
        attendance_status_id: uuid.UUID,
        created_by: uuid.UUID | None,
    ) -> AttendanceRecord:
        record = AttendanceRecord(
            employee_id=employee_id,
            attendance_date=attendance_date,
            check_in_time=check_in_time,
            attendance_status_id=attendance_status_id,
            created_by=created_by,
        )
        self._session.add(record)
        await self._session.flush()
        return await self.get_record_by_id(record.id)  # type: ignore[return-value]

    async def update_check_out(
        self,
        record_id: uuid.UUID,
        *,
        check_out_time: datetime,
        work_duration_minutes: int,
        updated_by: uuid.UUID | None,
    ) -> AttendanceRecord | None:
        await self._session.execute(
            update(AttendanceRecord)
            .where(AttendanceRecord.id == record_id)
            .values(
                check_out_time=check_out_time,
                work_duration_minutes=work_duration_minutes,
                updated_by=updated_by,
            ),
        )
        return await self.get_record_by_id(record_id)

    async def update_record_times(
        self,
        record_id: uuid.UUID,
        *,
        check_in_time: datetime | None = None,
        check_out_time: datetime | None = None,
        work_duration_minutes: int | None = None,
        attendance_status_id: uuid.UUID | None = None,
        updated_by: uuid.UUID | None = None,
    ) -> AttendanceRecord | None:
        values: dict = {}
        if check_in_time is not None:
            values["check_in_time"] = check_in_time
        if check_out_time is not None:
            values["check_out_time"] = check_out_time
        if work_duration_minutes is not None:
            values["work_duration_minutes"] = work_duration_minutes
        if attendance_status_id is not None:
            values["attendance_status_id"] = attendance_status_id
        if updated_by is not None:
            values["updated_by"] = updated_by

        if not values:
            return await self.get_record_by_id(record_id)

        await self._session.execute(
            update(AttendanceRecord).where(AttendanceRecord.id == record_id).values(**values),
        )
        return await self.get_record_by_id(record_id)

    async def list_records(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        department_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AttendanceRecord], int]:
        query = select(AttendanceRecord).options(
            selectinload(AttendanceRecord.status),
            selectinload(AttendanceRecord.employee).selectinload(Employee.department),
        )
        count_query = select(func.count()).select_from(AttendanceRecord)

        if employee_id is not None:
            query = query.where(AttendanceRecord.employee_id == employee_id)
            count_query = count_query.where(AttendanceRecord.employee_id == employee_id)

        if department_id is not None:
            query = query.join(Employee).where(Employee.department_id == department_id)
            count_query = count_query.join(Employee).where(
                Employee.department_id == department_id,
            )

        if date_from is not None:
            query = query.where(AttendanceRecord.attendance_date >= date_from)
            count_query = count_query.where(AttendanceRecord.attendance_date >= date_from)

        if date_to is not None:
            query = query.where(AttendanceRecord.attendance_date <= date_to)
            count_query = count_query.where(AttendanceRecord.attendance_date <= date_to)

        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        query = (
            query.order_by(
                AttendanceRecord.attendance_date.desc(),
                AttendanceRecord.created_at.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    async def get_monthly_summary(
        self,
        employee_id: uuid.UUID,
        year: int,
        month: int,
    ) -> dict[str, int | float]:
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])

        status_counts_result = await self._session.execute(
            select(AttendanceStatus.name, func.count(AttendanceRecord.id))
            .join(
                AttendanceRecord,
                AttendanceRecord.attendance_status_id == AttendanceStatus.id,
            )
            .where(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.attendance_date >= start,
                AttendanceRecord.attendance_date <= end,
            )
            .group_by(AttendanceStatus.name),
        )
        status_counts = {name: int(count) for name, count in status_counts_result.all()}

        minutes_result = await self._session.execute(
            select(func.coalesce(func.sum(AttendanceRecord.work_duration_minutes), 0)).where(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.attendance_date >= start,
                AttendanceRecord.attendance_date <= end,
            ),
        )
        total_minutes = int(minutes_result.scalar_one())

        present = status_counts.get("present", 0)
        absent = status_counts.get("absent", 0)
        late = status_counts.get("late", 0)
        half_days = status_counts.get("half_day", 0)
        total_working_days = sum(status_counts.values())

        return {
            "present_days": present,
            "absent_days": absent,
            "late_days": late,
            "half_days": half_days,
            "total_working_days": total_working_days,
            "total_hours": round(total_minutes / 60, 2),
        }

    async def list_active_employees(
        self,
        *,
        department_id: uuid.UUID | None = None,
    ) -> list[Employee]:
        active_status_id = await self._session.execute(
            select(EmploymentStatus.id).where(EmploymentStatus.name == "active"),
        )
        active_id = active_status_id.scalar_one_or_none()
        if active_id is None:
            return []

        query = (
            select(Employee)
            .where(
                Employee.deleted_at.is_(None),
                Employee.employment_status_id == active_id,
            )
            .options(selectinload(Employee.department))
            .order_by(Employee.last_name.asc(), Employee.first_name.asc())
        )
        if department_id is not None:
            query = query.where(Employee.department_id == department_id)

        result = await self._session.execute(query)
        return list(result.scalars().unique().all())

    async def list_records_for_date(
        self,
        attendance_date: date,
        *,
        department_id: uuid.UUID | None = None,
    ) -> list[AttendanceRecord]:
        query = (
            select(AttendanceRecord)
            .where(AttendanceRecord.attendance_date == attendance_date)
            .options(
                selectinload(AttendanceRecord.status),
                selectinload(AttendanceRecord.employee).selectinload(Employee.department),
            )
        )
        if department_id is not None:
            query = query.join(Employee).where(Employee.department_id == department_id)

        result = await self._session.execute(query)
        return list(result.scalars().unique().all())

    async def list_attendance_report(
        self,
        *,
        department_id: uuid.UUID | None = None,
        status_id: uuid.UUID | None = None,
        date_from: date,
        date_to: date,
        page: int,
        page_size: int,
    ) -> tuple[list[AttendanceRecord], int]:
        query = (
            select(AttendanceRecord)
            .join(Employee)
            .join(Department, Department.id == Employee.department_id)
            .options(
                selectinload(AttendanceRecord.status),
                selectinload(AttendanceRecord.employee).selectinload(Employee.department),
            )
            .where(
                AttendanceRecord.attendance_date >= date_from,
                AttendanceRecord.attendance_date <= date_to,
                Employee.deleted_at.is_(None),
            )
        )
        count_query = (
            select(func.count())
            .select_from(AttendanceRecord)
            .join(Employee)
            .where(
                AttendanceRecord.attendance_date >= date_from,
                AttendanceRecord.attendance_date <= date_to,
                Employee.deleted_at.is_(None),
            )
        )

        if department_id is not None:
            query = query.where(Employee.department_id == department_id)
            count_query = count_query.where(Employee.department_id == department_id)

        if status_id is not None:
            query = query.where(AttendanceRecord.attendance_status_id == status_id)
            count_query = count_query.where(
                AttendanceRecord.attendance_status_id == status_id,
            )

        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        query = (
            query.order_by(
                AttendanceRecord.attendance_date.desc(),
                Employee.last_name.asc(),
            )
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    async def create_correction(
        self,
        *,
        attendance_record_id: uuid.UUID,
        requested_by: uuid.UUID,
        reason: str,
    ) -> AttendanceCorrection:
        correction = AttendanceCorrection(
            attendance_record_id=attendance_record_id,
            requested_by=requested_by,
            reason=reason,
            correction_status="pending",
        )
        self._session.add(correction)
        await self._session.flush()
        return await self.get_correction_by_id(correction.id)  # type: ignore[return-value]

    async def get_correction_by_id(
        self,
        correction_id: uuid.UUID,
    ) -> AttendanceCorrection | None:
        result = await self._session.execute(
            select(AttendanceCorrection)
            .where(AttendanceCorrection.id == correction_id)
            .options(
                selectinload(AttendanceCorrection.attendance_record).selectinload(
                    AttendanceRecord.status,
                ),
            ),
        )
        return result.scalar_one_or_none()

    async def get_pending_correction_for_record(
        self,
        attendance_record_id: uuid.UUID,
    ) -> AttendanceCorrection | None:
        result = await self._session.execute(
            select(AttendanceCorrection).where(
                AttendanceCorrection.attendance_record_id == attendance_record_id,
                AttendanceCorrection.correction_status == "pending",
            ),
        )
        return result.scalar_one_or_none()

    async def list_corrections(
        self,
        attendance_record_id: uuid.UUID,
    ) -> list[AttendanceCorrection]:
        result = await self._session.execute(
            select(AttendanceCorrection)
            .where(AttendanceCorrection.attendance_record_id == attendance_record_id)
            .order_by(AttendanceCorrection.created_at.desc()),
        )
        return list(result.scalars().all())

    async def update_correction_status(
        self,
        correction_id: uuid.UUID,
        *,
        correction_status: str,
        reviewed_by: uuid.UUID,
        reviewed_at: datetime,
    ) -> AttendanceCorrection | None:
        await self._session.execute(
            update(AttendanceCorrection)
            .where(AttendanceCorrection.id == correction_id)
            .values(
                correction_status=correction_status,
                reviewed_by=reviewed_by,
                reviewed_at=reviewed_at,
            ),
        )
        return await self.get_correction_by_id(correction_id)

    async def get_employee_by_id(self, employee_id: uuid.UUID) -> Employee | None:
        result = await self._session.execute(
            select(Employee)
            .where(Employee.id == employee_id, Employee.deleted_at.is_(None))
            .options(selectinload(Employee.department)),
        )
        return result.scalar_one_or_none()

    async def get_employee_by_user_id(self, user_id: uuid.UUID) -> Employee | None:
        result = await self._session.execute(
            select(Employee)
            .where(Employee.user_id == user_id, Employee.deleted_at.is_(None))
            .options(selectinload(Employee.department)),
        )
        return result.scalar_one_or_none()

    async def is_employee_active(self, employee_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Employee.id)
            .join(EmploymentStatus, EmploymentStatus.id == Employee.employment_status_id)
            .where(
                Employee.id == employee_id,
                Employee.deleted_at.is_(None),
                EmploymentStatus.name == "active",
            ),
        )
        return result.scalar_one_or_none() is not None

    async def create_audit_log(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        resource_id: uuid.UUID | None = None,
        ip_address: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type="attendance_records",
            resource_id=resource_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=after_state,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    # --- Notifications ---

    async def create_notification(
        self,
        *,
        user_id: uuid.UUID,
        title: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            is_read=False,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def list_user_ids_for_role(self, role_slug: str) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(UserRole.user_id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.name == role_slug)
            .distinct(),
        )
        return list(result.scalars().all())
