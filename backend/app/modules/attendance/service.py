import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEPARTMENT_MANAGER,
    EMPLOYEE,
    HR_MANAGER,
    SYSTEM_ADMINISTRATOR,
)
from app.core.security import CurrentUser
from app.modules.attendance.errors import AttendanceError
from app.modules.attendance.model import AttendanceCorrection, AttendanceRecord
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.schema import (
    AttendanceRecordListResponse,
    AttendanceRecordResponse,
    AttendanceReportResponse,
    AttendanceReportRow,
    CheckInRequest,
    CheckOutRequest,
    CorrectionListResponse,
    CorrectionRequest,
    CorrectionResponse,
    DailyAttendanceEmployeeItem,
    DailyAttendanceResponse,
    MonthlySummaryResponse,
    ReviewCorrectionRequest,
    build_pagination,
)
from app.modules.employee.model import Employee


class AttendanceService:
    def __init__(
        self,
        session: AsyncSession,
        repository: AttendanceRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or AttendanceRepository(session)

    async def check_in(
        self,
        employee_id: uuid.UUID,
        body: CheckInRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> AttendanceRecordResponse:
        await self._ensure_can_act_on_employee(actor, employee_id)

        if not await self._repository.is_employee_active(employee_id):
            raise AttendanceError("Employee is not active", 400)

        timestamp = self._resolve_timestamp(body.timestamp)
        attendance_date = timestamp.date()

        if attendance_date != date.today():
            raise AttendanceError("Check-in timestamp must be for today", 400)

        existing = await self._repository.get_record_by_employee_date(
            employee_id,
            attendance_date,
        )
        if existing is not None:
            raise AttendanceError("Attendance record already exists for today", 409)

        present_status = await self._repository.get_status_by_name("present")
        if present_status is None:
            raise AttendanceError("Present attendance status is not configured", 500)

        record = await self._repository.create_check_in(
            employee_id=employee_id,
            attendance_date=attendance_date,
            check_in_time=timestamp,
            attendance_status_id=present_status.id,
            created_by=actor.id,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="attendance_check_in",
            resource_id=record.id,
            ip_address=ip_address,
            after_state=self._record_snapshot(record),
        )
        await self._session.commit()

        return self._to_record_response(record)

    async def check_out(
        self,
        employee_id: uuid.UUID,
        body: CheckOutRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> AttendanceRecordResponse:
        await self._ensure_can_act_on_employee(actor, employee_id)

        timestamp = self._resolve_timestamp(body.timestamp)
        attendance_date = timestamp.date()

        if attendance_date != date.today():
            raise AttendanceError("Check-out timestamp must be for today", 400)

        record = await self._repository.get_record_by_employee_date(
            employee_id,
            attendance_date,
        )
        if record is None or record.check_in_time is None:
            raise AttendanceError("Check-in is required before check-out", 400)

        if record.check_out_time is not None:
            raise AttendanceError("Already checked out for today", 400)

        if timestamp <= record.check_in_time:
            raise AttendanceError("Check-out must be after check-in", 400)

        duration = int((timestamp - record.check_in_time).total_seconds() // 60)

        updated = await self._repository.update_check_out(
            record.id,
            check_out_time=timestamp,
            work_duration_minutes=duration,
            updated_by=actor.id,
        )
        assert updated is not None

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="attendance_check_out",
            resource_id=record.id,
            ip_address=ip_address,
            before_state=self._record_snapshot(record),
            after_state=self._record_snapshot(updated),
        )
        await self._session.commit()

        return self._to_record_response(updated)

    async def get_attendance_history(
        self,
        *,
        actor: CurrentUser,
        employee_id: uuid.UUID | None,
        date_from: date | None,
        date_to: date | None,
        page: int,
        page_size: int,
    ) -> AttendanceRecordListResponse:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise AttendanceError("start_date must be on or before end_date", 400)

        scoped_employee_id, scoped_department_id = await self._resolve_history_scope(
            actor,
            employee_id,
        )

        records, total = await self._repository.list_records(
            employee_id=scoped_employee_id,
            department_id=scoped_department_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
        return AttendanceRecordListResponse(
            items=[self._to_record_response(record) for record in records],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_daily_attendance(
        self,
        attendance_date: date,
        *,
        actor: CurrentUser,
    ) -> DailyAttendanceResponse:
        if not self._is_hr_or_admin(actor):
            raise AttendanceError("Insufficient permissions", 403)

        employees = await self._repository.list_active_employees()
        records = await self._repository.list_records_for_date(attendance_date)
        records_by_employee = {record.employee_id: record for record in records}

        present_count = 0
        absent_count = 0
        late_count = 0
        items: list[DailyAttendanceEmployeeItem] = []

        for employee in employees:
            record = records_by_employee.get(employee.id)
            if record is None:
                status_name = "absent"
                absent_count += 1
                items.append(self._daily_item(employee, status_name, None))
                continue

            status_name = record.status.name
            if status_name == "present":
                present_count += 1
            elif status_name == "late":
                late_count += 1
            elif status_name == "absent":
                absent_count += 1
            else:
                present_count += 1

            items.append(self._daily_item(employee, status_name, record))

        return DailyAttendanceResponse(
            date=attendance_date,
            present_count=present_count,
            absent_count=absent_count,
            late_count=late_count,
            employees=items,
        )

    async def get_monthly_summary(
        self,
        *,
        actor: CurrentUser,
        employee_id: uuid.UUID,
        year: int,
        month: int,
    ) -> MonthlySummaryResponse:
        if month < 1 or month > 12:
            raise AttendanceError("month must be between 1 and 12", 400)

        employee = await self._repository.get_employee_by_id(employee_id)
        if employee is None:
            raise AttendanceError("Employee not found", 404)

        await self._ensure_can_read_employee(actor, employee)

        totals = await self._repository.get_monthly_summary(employee_id, year, month)
        return MonthlySummaryResponse(
            employee_id=employee_id,
            year=year,
            month=month,
            present_days=int(totals["present_days"]),
            absent_days=int(totals["absent_days"]),
            late_days=int(totals["late_days"]),
            half_days=int(totals["half_days"]),
            total_working_days=int(totals["total_working_days"]),
            total_hours=float(totals["total_hours"]),
        )

    async def request_correction(
        self,
        record_id: uuid.UUID,
        body: CorrectionRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> CorrectionResponse:
        record = await self._repository.get_record_by_id(record_id)
        if record is None:
            raise AttendanceError("Attendance record not found", 404)

        employee = await self._repository.get_employee_by_id(record.employee_id)
        if employee is None or not self._is_self(actor, employee):
            raise AttendanceError("Only the record owner can request a correction", 403)

        pending = await self._repository.get_pending_correction_for_record(record_id)
        if pending is not None:
            raise AttendanceError("A pending correction already exists for this record", 409)

        correction = await self._repository.create_correction(
            attendance_record_id=record_id,
            requested_by=actor.id,
            reason=body.reason,
        )

        # Notify HR managers of new correction request.
        hr_user_ids = await self._repository.list_user_ids_for_role(HR_MANAGER)
        for user_id in hr_user_ids:
            await self._repository.create_notification(
                user_id=user_id,
                title="Attendance correction requested",
                message=(
                    f"{employee.first_name} {employee.last_name} requested an attendance correction "
                    f"for {record.attendance_date}."
                ),
            )
        await self._session.commit()

        return self._to_correction_response(correction)

    async def list_corrections(
        self,
        record_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> CorrectionListResponse:
        record = await self._repository.get_record_by_id(record_id)
        if record is None:
            raise AttendanceError("Attendance record not found", 404)

        employee = await self._repository.get_employee_by_id(record.employee_id)
        if employee is None:
            raise AttendanceError("Employee not found", 404)

        await self._ensure_can_read_employee(actor, employee)

        corrections = await self._repository.list_corrections(record_id)
        return CorrectionListResponse(
            items=[self._to_correction_response(item) for item in corrections],
        )

    async def review_correction(
        self,
        correction_id: uuid.UUID,
        body: ReviewCorrectionRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> CorrectionResponse:
        if not self._is_hr_or_admin(actor):
            raise AttendanceError("Insufficient permissions", 403)

        correction = await self._repository.get_correction_by_id(correction_id)
        if correction is None:
            raise AttendanceError("Correction not found", 404)

        if correction.correction_status != "pending":
            raise AttendanceError("Correction has already been reviewed", 400)

        record = correction.attendance_record
        before_record = self._record_snapshot(record)
        reviewed_at = datetime.now(UTC)

        if body.status == "approved":
            check_in = body.check_in_time or record.check_in_time
            check_out = body.check_out_time or record.check_out_time
            if check_in is not None and check_out is not None and check_out <= check_in:
                raise AttendanceError("Check-out must be after check-in", 400)

            duration = None
            if check_in is not None and check_out is not None:
                duration = int((check_out - check_in).total_seconds() // 60)

            updated_record = await self._repository.update_record_times(
                record.id,
                check_in_time=body.check_in_time,
                check_out_time=body.check_out_time,
                work_duration_minutes=duration,
                updated_by=actor.id,
            )
            audit_action = "attendance_correction_approve"
            after_record = (
                self._record_snapshot(updated_record) if updated_record else before_record
            )
        else:
            audit_action = "attendance_correction_reject"
            after_record = before_record

        updated_correction = await self._repository.update_correction_status(
            correction_id,
            correction_status=body.status,
            reviewed_by=actor.id,
            reviewed_at=reviewed_at,
        )
        assert updated_correction is not None

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action=audit_action,
            resource_id=record.id,
            ip_address=ip_address,
            before_state={"record": before_record, "correction_status": "pending"},
            after_state={
                "record": after_record,
                "correction_status": body.status,
            },
        )

        # Notify requesting employee when correction is reviewed.
        requester = await self._repository.get_employee_by_user_id(correction.requested_by)
        if requester is not None and requester.user_id is not None:
            await self._repository.create_notification(
                user_id=requester.user_id,
                title="Attendance correction reviewed",
                message=(
                    f"Your attendance correction request for {record.attendance_date} was {body.status}."
                ),
            )
        await self._session.commit()

        return self._to_correction_response(updated_correction)

    async def get_attendance_report(
        self,
        *,
        actor: CurrentUser,
        department_id: uuid.UUID | None,
        status: uuid.UUID | None,
        date_from: date,
        date_to: date,
        page: int,
        page_size: int,
    ) -> AttendanceReportResponse:
        if not self._is_hr_or_admin(actor):
            raise AttendanceError("Insufficient permissions", 403)

        if date_from > date_to:
            raise AttendanceError("start_date must be on or before end_date", 400)

        records, total = await self._repository.list_attendance_report(
            department_id=department_id,
            status_id=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )

        rows = []
        for record in records:
            employee = record.employee
            rows.append(
                AttendanceReportRow(
                    record_id=record.id,
                    employee_id=employee.id,
                    employee_code=employee.employee_code,
                    full_name=self._full_name(employee),
                    department_name=employee.department.name,
                    attendance_date=record.attendance_date,
                    status_name=record.status.name,
                    check_in_time=record.check_in_time,
                    check_out_time=record.check_out_time,
                    work_duration_minutes=record.work_duration_minutes,
                ),
            )

        return AttendanceReportResponse(
            items=rows,
            pagination=build_pagination(page, page_size, total),
        )

    async def resolve_actor_employee_id(self, actor: CurrentUser) -> uuid.UUID:
        employee = await self._repository.get_employee_by_user_id(actor.id)
        if employee is None:
            raise AttendanceError("Employee profile not found", 404)
        return employee.id

    async def _resolve_history_scope(
        self,
        actor: CurrentUser,
        employee_id: uuid.UUID | None,
    ) -> tuple[uuid.UUID | None, uuid.UUID | None]:
        if self._is_hr_or_admin(actor):
            return employee_id, None

        if DEPARTMENT_MANAGER in actor.roles:
            manager = await self._repository.get_employee_by_user_id(actor.id)
            if manager is None:
                raise AttendanceError("Employee profile not found", 404)
            if employee_id is not None:
                target = await self._repository.get_employee_by_id(employee_id)
                if target is None:
                    raise AttendanceError("Employee not found", 404)
                if target.department_id != manager.department_id:
                    raise AttendanceError("Insufficient permissions", 403)
                return employee_id, None
            return None, manager.department_id

        if EMPLOYEE in actor.roles:
            own_id = await self.resolve_actor_employee_id(actor)
            if employee_id is not None and employee_id != own_id:
                raise AttendanceError("Insufficient permissions", 403)
            return own_id, None

        raise AttendanceError("Insufficient permissions", 403)

    async def _ensure_can_act_on_employee(
        self,
        actor: CurrentUser,
        employee_id: uuid.UUID,
    ) -> None:
        if self._is_hr_or_admin(actor):
            return

        employee = await self._repository.get_employee_by_id(employee_id)
        if employee is None:
            raise AttendanceError("Employee not found", 404)

        if self._is_self(actor, employee):
            return

        if DEPARTMENT_MANAGER in actor.roles:
            manager = await self._repository.get_employee_by_user_id(actor.id)
            if (
                manager is not None
                and manager.department_id == employee.department_id
            ):
                return

        raise AttendanceError("Insufficient permissions", 403)

    async def _ensure_can_read_employee(
        self,
        actor: CurrentUser,
        employee: Employee,
    ) -> None:
        if self._is_hr_or_admin(actor):
            return
        if self._is_self(actor, employee):
            return
        if DEPARTMENT_MANAGER in actor.roles:
            manager = await self._repository.get_employee_by_user_id(actor.id)
            if (
                manager is not None
                and manager.department_id == employee.department_id
            ):
                return
        raise AttendanceError("Insufficient permissions", 403)

    def _resolve_timestamp(self, value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(UTC)
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _is_hr_or_admin(self, actor: CurrentUser) -> bool:
        return bool({HR_MANAGER, SYSTEM_ADMINISTRATOR}.intersection(actor.roles))

    def _is_self(self, actor: CurrentUser, employee: Employee) -> bool:
        return employee.user_id is not None and employee.user_id == actor.id

    def _full_name(self, employee: Employee) -> str:
        return f"{employee.first_name} {employee.last_name}".strip()

    def _record_snapshot(self, record: AttendanceRecord) -> dict[str, Any]:
        return {
            "employee_id": str(record.employee_id),
            "attendance_date": record.attendance_date.isoformat(),
            "check_in_time": record.check_in_time.isoformat()
            if record.check_in_time
            else None,
            "check_out_time": record.check_out_time.isoformat()
            if record.check_out_time
            else None,
            "work_duration_minutes": record.work_duration_minutes,
            "status_id": str(record.attendance_status_id),
        }

    def _to_record_response(self, record: AttendanceRecord) -> AttendanceRecordResponse:
        return AttendanceRecordResponse(
            id=record.id,
            employee_id=record.employee_id,
            attendance_date=record.attendance_date,
            check_in_time=record.check_in_time,
            check_out_time=record.check_out_time,
            work_duration_minutes=record.work_duration_minutes,
            attendance_status_id=record.attendance_status_id,
            status_name=record.status.name,
            created_at=record.created_at,
        )

    def _to_correction_response(
        self,
        correction: AttendanceCorrection,
    ) -> CorrectionResponse:
        return CorrectionResponse(
            id=correction.id,
            attendance_record_id=correction.attendance_record_id,
            requested_by=correction.requested_by,
            reason=correction.reason,
            correction_status=correction.correction_status,
            reviewed_by=correction.reviewed_by,
            reviewed_at=correction.reviewed_at,
            created_at=correction.created_at,
        )

    def _daily_item(
        self,
        employee: Employee,
        status_name: str,
        record: AttendanceRecord | None,
    ) -> DailyAttendanceEmployeeItem:
        return DailyAttendanceEmployeeItem(
            employee_id=employee.id,
            employee_code=employee.employee_code,
            full_name=self._full_name(employee),
            department_name=employee.department.name,
            status_name=status_name,
            check_in_time=record.check_in_time if record else None,
            check_out_time=record.check_out_time if record else None,
            record_id=record.id if record else None,
        )
