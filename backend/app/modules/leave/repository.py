from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.employee.model import Employee
from app.modules.leave.model import LeaveApproval, LeaveBalance, LeaveRequest, LeaveType
from app.modules.notifications.model import AuditLog, Notification
from app.modules.user.model import User

ACTIVE_LEAVE_STATUSES = ("pending", "approved")


class LeaveRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- Leave types ---

    async def get_leave_type_by_id(self, leave_type_id: uuid.UUID) -> LeaveType | None:
        result = await self._session.execute(
            select(LeaveType).where(LeaveType.id == leave_type_id),
        )
        return result.scalar_one_or_none()

    async def get_leave_type_by_name(self, name: str) -> LeaveType | None:
        result = await self._session.execute(
            select(LeaveType).where(LeaveType.name == name),
        )
        return result.scalar_one_or_none()

    async def list_leave_types(self) -> list[LeaveType]:
        result = await self._session.execute(
            select(LeaveType).order_by(LeaveType.name.asc()),
        )
        return list(result.scalars().all())

    async def create_leave_type(self, *, name: str, annual_allocation: int) -> LeaveType:
        leave_type = LeaveType(name=name, annual_allocation=annual_allocation)
        self._session.add(leave_type)
        await self._session.flush()
        return leave_type

    async def update_leave_type(
        self,
        leave_type_id: uuid.UUID,
        *,
        name: str | None = None,
        annual_allocation: int | None = None,
    ) -> LeaveType | None:
        values: dict = {}
        if name is not None:
            values["name"] = name
        if annual_allocation is not None:
            values["annual_allocation"] = annual_allocation
        if not values:
            return await self.get_leave_type_by_id(leave_type_id)

        await self._session.execute(
            update(LeaveType).where(LeaveType.id == leave_type_id).values(**values),
        )
        return await self.get_leave_type_by_id(leave_type_id)

    async def delete_leave_type(self, leave_type_id: uuid.UUID) -> bool:
        leave_type = await self.get_leave_type_by_id(leave_type_id)
        if leave_type is None:
            return False
        await self._session.delete(leave_type)
        await self._session.flush()
        return True

    async def count_balances_for_leave_type(self, leave_type_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(LeaveBalance)
            .where(LeaveBalance.leave_type_id == leave_type_id),
        )
        return int(result.scalar_one())

    # --- Leave balances ---

    async def get_leave_balance(
        self,
        employee_id: uuid.UUID,
        leave_type_id: uuid.UUID,
    ) -> LeaveBalance | None:
        result = await self._session.execute(
            select(LeaveBalance)
            .where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
            )
            .options(selectinload(LeaveBalance.leave_type)),
        )
        return result.scalar_one_or_none()

    async def list_leave_balances_for_employee(
        self,
        employee_id: uuid.UUID,
    ) -> list[LeaveBalance]:
        result = await self._session.execute(
            select(LeaveBalance)
            .where(LeaveBalance.employee_id == employee_id)
            .options(selectinload(LeaveBalance.leave_type))
            .order_by(LeaveType.name.asc())
            .join(LeaveType, LeaveType.id == LeaveBalance.leave_type_id),
        )
        return list(result.scalars().unique().all())

    async def list_all_leave_types_with_balances(
        self,
        employee_id: uuid.UUID,
    ) -> list[tuple[LeaveType, LeaveBalance | None]]:
        types_result = await self._session.execute(
            select(LeaveType).order_by(LeaveType.name.asc()),
        )
        leave_types = list(types_result.scalars().all())
        balances_result = await self._session.execute(
            select(LeaveBalance).where(LeaveBalance.employee_id == employee_id),
        )
        balance_by_type = {
            balance.leave_type_id: balance for balance in balances_result.scalars().all()
        }
        return [(lt, balance_by_type.get(lt.id)) for lt in leave_types]

    async def create_leave_balance(
        self,
        *,
        employee_id: uuid.UUID,
        leave_type_id: uuid.UUID,
        balance: Decimal,
        created_by: uuid.UUID | None,
    ) -> LeaveBalance:
        record = LeaveBalance(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            balance=balance,
            created_by=created_by,
            updated_by=created_by,
        )
        self._session.add(record)
        await self._session.flush()
        return await self.get_leave_balance(employee_id, leave_type_id)  # type: ignore[return-value]

    async def update_leave_balance(
        self,
        balance_id: uuid.UUID,
        *,
        balance: Decimal,
        updated_by: uuid.UUID | None,
    ) -> LeaveBalance | None:
        await self._session.execute(
            update(LeaveBalance)
            .where(LeaveBalance.id == balance_id)
            .values(balance=balance, updated_by=updated_by),
        )
        result = await self._session.execute(
            select(LeaveBalance)
            .where(LeaveBalance.id == balance_id)
            .options(selectinload(LeaveBalance.leave_type)),
        )
        return result.scalar_one_or_none()

    async def list_active_employee_ids(self) -> list[uuid.UUID]:
        from app.modules.employee.model import EmploymentStatus

        result = await self._session.execute(
            select(Employee.id)
            .join(EmploymentStatus, EmploymentStatus.id == Employee.employment_status_id)
            .where(
                Employee.deleted_at.is_(None),
                EmploymentStatus.name == "active",
            ),
        )
        return list(result.scalars().all())

    # --- Leave requests ---

    async def create_leave_request(
        self,
        *,
        employee_id: uuid.UUID,
        leave_type_id: uuid.UUID,
        start_date: date,
        end_date: date,
        reason: str | None,
        created_by: uuid.UUID | None,
    ) -> LeaveRequest:
        request = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status="pending",
            created_by=created_by,
        )
        self._session.add(request)
        await self._session.flush()
        return await self.get_leave_request_by_id(request.id)  # type: ignore[return-value]

    async def get_leave_request_by_id(
        self,
        request_id: uuid.UUID,
    ) -> LeaveRequest | None:
        result = await self._session.execute(
            select(LeaveRequest)
            .where(
                LeaveRequest.id == request_id,
                LeaveRequest.deleted_at.is_(None),
            )
            .options(
                selectinload(LeaveRequest.leave_type),
                selectinload(LeaveRequest.employee),
                selectinload(LeaveRequest.approvals).selectinload(LeaveApproval.approver),
            ),
        )
        return result.scalar_one_or_none()

    async def update_leave_status(
        self,
        request_id: uuid.UUID,
        *,
        status: str,
        updated_by: uuid.UUID | None,
    ) -> LeaveRequest | None:
        await self._session.execute(
            update(LeaveRequest)
            .where(LeaveRequest.id == request_id)
            .values(status=status, updated_by=updated_by),
        )
        return await self.get_leave_request_by_id(request_id)

    async def list_leave_requests(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        status: str | None = None,
        leave_type_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        department_id: uuid.UUID | None = None,
        manager_id: uuid.UUID | None = None,
        direct_report_ids: list[uuid.UUID] | None = None,
        page: int = 1,
        page_size: int = 20,
        order_asc: bool = False,
    ) -> tuple[list[LeaveRequest], int]:
        query = (
            select(LeaveRequest)
            .where(LeaveRequest.deleted_at.is_(None))
            .options(
                selectinload(LeaveRequest.leave_type),
                selectinload(LeaveRequest.employee),
                selectinload(LeaveRequest.approvals).selectinload(LeaveApproval.approver),
            )
        )
        count_query = (
            select(func.count())
            .select_from(LeaveRequest)
            .where(LeaveRequest.deleted_at.is_(None))
        )

        if employee_id is not None:
            query = query.where(LeaveRequest.employee_id == employee_id)
            count_query = count_query.where(LeaveRequest.employee_id == employee_id)

        if status is not None:
            query = query.where(LeaveRequest.status == status)
            count_query = count_query.where(LeaveRequest.status == status)

        if leave_type_id is not None:
            query = query.where(LeaveRequest.leave_type_id == leave_type_id)
            count_query = count_query.where(LeaveRequest.leave_type_id == leave_type_id)

        if date_from is not None:
            query = query.where(LeaveRequest.end_date >= date_from)
            count_query = count_query.where(LeaveRequest.end_date >= date_from)

        if date_to is not None:
            query = query.where(LeaveRequest.start_date <= date_to)
            count_query = count_query.where(LeaveRequest.start_date <= date_to)

        if department_id is not None or manager_id is not None or direct_report_ids is not None:
            query = query.join(Employee, Employee.id == LeaveRequest.employee_id)
            count_query = count_query.join(Employee, Employee.id == LeaveRequest.employee_id)

        if department_id is not None:
            query = query.where(Employee.department_id == department_id)
            count_query = count_query.where(Employee.department_id == department_id)

        if manager_id is not None:
            query = query.where(Employee.manager_id == manager_id)
            count_query = count_query.where(Employee.manager_id == manager_id)

        if direct_report_ids is not None:
            query = query.where(LeaveRequest.employee_id.in_(direct_report_ids))
            count_query = count_query.where(LeaveRequest.employee_id.in_(direct_report_ids))

        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        order_clause = (
            LeaveRequest.created_at.asc() if order_asc else LeaveRequest.created_at.desc()
        )
        offset = (page - 1) * page_size
        query = query.order_by(order_clause).offset(offset).limit(page_size)

        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    async def list_pending_approvals(
        self,
        *,
        department_id: uuid.UUID | None = None,
        manager_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LeaveRequest], int]:
        return await self.list_leave_requests(
            status="pending",
            department_id=department_id,
            manager_id=manager_id,
            page=page,
            page_size=page_size,
            order_asc=True,
        )

    async def get_leave_history(
        self,
        *,
        employee_id: uuid.UUID,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LeaveRequest], int]:
        return await self.list_leave_requests(
            employee_id=employee_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
            order_asc=False,
        )

    async def has_overlapping_leave(
        self,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
        *,
        exclude_request_id: uuid.UUID | None = None,
    ) -> bool:
        conditions = [
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.deleted_at.is_(None),
            LeaveRequest.status.in_(ACTIVE_LEAVE_STATUSES),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        ]
        if exclude_request_id is not None:
            conditions.append(LeaveRequest.id != exclude_request_id)

        result = await self._session.execute(
            select(func.count()).select_from(LeaveRequest).where(and_(*conditions)),
        )
        return int(result.scalar_one()) > 0

    # --- Leave approvals ---

    async def create_leave_approval(
        self,
        *,
        leave_request_id: uuid.UUID,
        approver_id: uuid.UUID,
        approval_level: int,
        status: str,
        remarks: str | None,
    ) -> LeaveApproval:
        approval = LeaveApproval(
            leave_request_id=leave_request_id,
            approver_id=approver_id,
            approval_level=approval_level,
            status=status,
            remarks=remarks,
            approved_at=datetime.now(UTC),
        )
        self._session.add(approval)
        await self._session.flush()
        return approval

    async def count_approvals_for_request(self, leave_request_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(LeaveApproval)
            .where(LeaveApproval.leave_request_id == leave_request_id),
        )
        return int(result.scalar_one())

    # --- Employee helpers ---

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
            .where(Employee.user_id == user_id, Employee.deleted_at.is_(None)),
        )
        return result.scalar_one_or_none()

    async def get_direct_report_ids(self, manager_employee_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(Employee.id).where(
                Employee.manager_id == manager_employee_id,
                Employee.deleted_at.is_(None),
            ),
        )
        return list(result.scalars().all())

    async def get_user_display_name(self, user_id: uuid.UUID) -> str | None:
        result = await self._session.execute(
            select(User.email).where(User.id == user_id),
        )
        return result.scalar_one_or_none()

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

    # --- Audit ---

    async def create_audit_log(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        resource_id: uuid.UUID | None = None,
        ip_address: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
        resource_type: str = "leave_requests",
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=after_state,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
