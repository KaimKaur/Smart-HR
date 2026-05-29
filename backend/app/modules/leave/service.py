from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEPARTMENT_MANAGER,
    EMPLOYEE,
    HR_MANAGER,
    SYSTEM_ADMINISTRATOR,
)
from app.core.security import CurrentUser
from app.modules.employee.model import Employee
from app.modules.leave.errors import LeaveError
from app.modules.leave.model import LeaveApproval, LeaveBalance, LeaveRequest, LeaveType
from app.modules.leave.repository import LeaveRepository
from app.modules.leave.schema import (
    CreateLeaveRequest,
    CreateLeaveTypeRequest,
    InitializeBalanceRequest,
    InitializeBalanceResponse,
    InitializedBalanceRecord,
    LeaveApprovalRequest,
    LeaveBalanceItem,
    LeaveBalanceResponse,
    LeaveListResponse,
    LeaveRequestResponse,
    LeaveTypeListResponse,
    LeaveTypeResponse,
    UpdateLeaveTypeRequest,
    build_pagination,
)


class LeaveService:
    def __init__(
        self,
        session: AsyncSession,
        repository: LeaveRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or LeaveRepository(session)

    # --- Leave requests ---

    async def create_leave_request(
        self,
        body: CreateLeaveRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
        employee_id: uuid.UUID | None = None,
    ) -> LeaveRequestResponse:
        target_employee_id = await self._resolve_target_employee_id(actor, employee_id)

        leave_type = await self._repository.get_leave_type_by_id(body.leave_type_id)
        if leave_type is None:
            raise LeaveError("Leave type not found", 404)

        days = self._calendar_days(body.start_date, body.end_date)

        balance_row = await self._repository.get_leave_balance(
            target_employee_id,
            body.leave_type_id,
        )
        if balance_row is None:
            raise LeaveError(
                "Leave balance is not initialized for this leave type",
                400,
                errors=[
                    {
                        "field": "current_balance",
                        "message": "0",
                    },
                ],
            )

        current_balance = balance_row.balance
        if current_balance < Decimal(days):
            raise LeaveError(
                "Insufficient leave balance",
                400,
                errors=[
                    {
                        "field": "current_balance",
                        "message": str(current_balance),
                    },
                ],
            )

        if await self._repository.has_overlapping_leave(
            target_employee_id,
            body.start_date,
            body.end_date,
        ):
            raise LeaveError("Leave dates overlap with an existing request", 409)

        request = await self._repository.create_leave_request(
            employee_id=target_employee_id,
            leave_type_id=body.leave_type_id,
            start_date=body.start_date,
            end_date=body.end_date,
            reason=body.reason,
            created_by=actor.id,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="leave_request_submit",
            resource_id=request.id,
            ip_address=ip_address,
            after_state=self._request_snapshot(request),
        )
        await self._notify_manager_of_request(request)
        await self._session.commit()

        return self._to_request_response(request)

    async def approve_leave(
        self,
        leave_request_id: uuid.UUID,
        body: LeaveApprovalRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> LeaveRequestResponse:
        request = await self._get_request_or_404(leave_request_id)
        before = self._request_snapshot(request)

        await self._ensure_can_approve_request(actor, request)

        if request.status != "pending":
            raise LeaveError("Only pending leave requests can be approved", 400)

        days = self._calendar_days(request.start_date, request.end_date)
        balance_row = await self._repository.get_leave_balance(
            request.employee_id,
            request.leave_type_id,
        )
        if balance_row is None:
            raise LeaveError("Leave balance not found", 400)

        new_balance = balance_row.balance - Decimal(days)
        if new_balance < 0:
            raise LeaveError(
                "Insufficient leave balance for approval",
                400,
                errors=[
                    {
                        "field": "current_balance",
                        "message": str(balance_row.balance),
                    },
                ],
            )

        balance_before = self._balance_snapshot(balance_row)
        updated_balance = await self._repository.update_leave_balance(
            balance_row.id,
            balance=new_balance,
            updated_by=actor.id,
        )
        assert updated_balance is not None

        approval_level = await self._repository.count_approvals_for_request(request.id) + 1
        await self._repository.create_leave_approval(
            leave_request_id=request.id,
            approver_id=actor.id,
            approval_level=approval_level,
            status="approved",
            remarks=body.remarks,
        )

        updated = await self._repository.update_leave_status(
            request.id,
            status="approved",
            updated_by=actor.id,
        )
        assert updated is not None

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="leave_request_approve",
            resource_id=request.id,
            ip_address=ip_address,
            before_state=before,
            after_state=self._request_snapshot(updated),
        )
        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="leave_balance_update",
            resource_id=balance_row.id,
            ip_address=ip_address,
            before_state=balance_before,
            after_state=self._balance_snapshot(updated_balance),
            resource_type="leave_balances",
        )
        await self._notify_employee_of_decision(updated, "approved")
        await self._session.commit()

        refreshed = await self._repository.get_leave_request_by_id(request.id)
        assert refreshed is not None
        return self._to_request_response(refreshed)

    async def reject_leave(
        self,
        leave_request_id: uuid.UUID,
        body: LeaveApprovalRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> LeaveRequestResponse:
        request = await self._get_request_or_404(leave_request_id)
        before = self._request_snapshot(request)

        await self._ensure_can_approve_request(actor, request)

        if request.status != "pending":
            raise LeaveError("Only pending leave requests can be rejected", 400)

        approval_level = await self._repository.count_approvals_for_request(request.id) + 1
        await self._repository.create_leave_approval(
            leave_request_id=request.id,
            approver_id=actor.id,
            approval_level=approval_level,
            status="rejected",
            remarks=body.remarks,
        )

        updated = await self._repository.update_leave_status(
            request.id,
            status="rejected",
            updated_by=actor.id,
        )
        assert updated is not None

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="leave_request_reject",
            resource_id=request.id,
            ip_address=ip_address,
            before_state=before,
            after_state=self._request_snapshot(updated),
        )
        await self._notify_employee_of_decision(updated, "rejected")
        await self._session.commit()

        refreshed = await self._repository.get_leave_request_by_id(request.id)
        assert refreshed is not None
        return self._to_request_response(refreshed)

    async def cancel_leave(
        self,
        leave_request_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> LeaveRequestResponse:
        request = await self._get_request_or_404(leave_request_id)
        before = self._request_snapshot(request)

        if request.status not in ("pending", "approved"):
            raise LeaveError("Only pending or approved requests can be cancelled", 400)

        is_hr = self._is_hr_or_admin(actor)
        is_owner = await self._is_request_owner(actor, request)

        if request.status == "approved":
            if not is_hr:
                raise LeaveError("Only HR can cancel approved leave requests", 403)
        elif not is_hr and not is_owner:
            raise LeaveError("Insufficient permissions", 403)

        if request.status == "approved":
            days = self._calendar_days(request.start_date, request.end_date)
            balance_row = await self._repository.get_leave_balance(
                request.employee_id,
                request.leave_type_id,
            )
            if balance_row is not None:
                balance_before = self._balance_snapshot(balance_row)
                restored = balance_row.balance + Decimal(days)
                updated_balance = await self._repository.update_leave_balance(
                    balance_row.id,
                    balance=restored,
                    updated_by=actor.id,
                )
                assert updated_balance is not None
                await self._repository.create_audit_log(
                    actor_user_id=actor.id,
                    action="leave_balance_update",
                    resource_id=balance_row.id,
                    ip_address=ip_address,
                    before_state=balance_before,
                    after_state=self._balance_snapshot(updated_balance),
                    resource_type="leave_balances",
                )

        updated = await self._repository.update_leave_status(
            request.id,
            status="cancelled",
            updated_by=actor.id,
        )
        assert updated is not None

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="leave_request_cancel",
            resource_id=request.id,
            ip_address=ip_address,
            before_state=before,
            after_state=self._request_snapshot(updated),
        )
        await self._notify_employee_of_decision(updated, "cancelled")
        await self._session.commit()

        refreshed = await self._repository.get_leave_request_by_id(request.id)
        assert refreshed is not None
        return self._to_request_response(refreshed)

    async def get_leave_request(
        self,
        leave_request_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> LeaveRequestResponse:
        request = await self._get_request_or_404(leave_request_id)
        await self._ensure_can_read_request(actor, request)
        return self._to_request_response(request)

    async def list_leave_requests(
        self,
        *,
        actor: CurrentUser,
        employee_id: uuid.UUID | None = None,
        status: str | None = None,
        leave_type_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> LeaveListResponse:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise LeaveError("date_from must be on or before date_to", 400)

        filters = await self._list_scope_filters(actor, employee_id)

        rows, total = await self._repository.list_leave_requests(
            employee_id=filters.get("employee_id"),
            status=status,
            leave_type_id=leave_type_id,
            date_from=date_from,
            date_to=date_to,
            department_id=filters.get("department_id"),
            page=page,
            page_size=page_size,
        )
        return LeaveListResponse(
            items=[self._to_request_response(row) for row in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def list_pending_approvals(
        self,
        *,
        actor: CurrentUser,
        page: int = 1,
        page_size: int = 20,
    ) -> LeaveListResponse:
        if not self._can_approve_role(actor):
            raise LeaveError("Insufficient permissions", 403)

        manager_id: uuid.UUID | None = None
        department_id: uuid.UUID | None = None

        if self._is_hr_or_admin(actor):
            pass
        elif DEPARTMENT_MANAGER in actor.roles:
            manager = await self._repository.get_employee_by_user_id(actor.id)
            if manager is None:
                raise LeaveError("Manager employee profile not found", 404)
            manager_id = manager.id
        else:
            raise LeaveError("Insufficient permissions", 403)

        rows, total = await self._repository.list_pending_approvals(
            department_id=department_id,
            manager_id=manager_id,
            page=page,
            page_size=page_size,
        )
        return LeaveListResponse(
            items=[self._to_request_response(row) for row in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_leave_history(
        self,
        *,
        actor: CurrentUser,
        employee_id: uuid.UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> LeaveListResponse:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise LeaveError("date_from must be on or before date_to", 400)

        target_id = await self._resolve_history_employee_id(actor, employee_id)

        rows, total = await self._repository.get_leave_history(
            employee_id=target_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
        return LeaveListResponse(
            items=[self._to_request_response(row) for row in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_leave_balance(
        self,
        *,
        actor: CurrentUser,
        employee_id: uuid.UUID | None = None,
    ) -> LeaveBalanceResponse:
        target_id = await self._resolve_balance_employee_id(actor, employee_id)
        employee = await self._repository.get_employee_by_id(target_id)
        if employee is None:
            raise LeaveError("Employee not found", 404)

        rows = await self._repository.list_all_leave_types_with_balances(target_id)
        items = [
            LeaveBalanceItem(
                leave_type_id=leave_type.id,
                leave_type=leave_type.name,
                annual_allocation=leave_type.annual_allocation,
                current_balance=balance.balance if balance is not None else Decimal("0"),
            )
            for leave_type, balance in rows
        ]
        return LeaveBalanceResponse(employee_id=target_id, balances=items)

    async def initialize_balances(
        self,
        body: InitializeBalanceRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> InitializeBalanceResponse:
        self._require_hr_or_admin(actor)

        leave_types = await self._repository.list_leave_types()
        if not leave_types:
            raise LeaveError("No leave types configured", 400)

        employee_ids: list[uuid.UUID]
        if body.all_employees:
            employee_ids = await self._repository.list_active_employee_ids()
        else:
            assert body.employee_id is not None
            employee = await self._repository.get_employee_by_id(body.employee_id)
            if employee is None:
                raise LeaveError("Employee not found", 404)
            employee_ids = [body.employee_id]

        created: list[InitializedBalanceRecord] = []

        for emp_id in employee_ids:
            for leave_type in leave_types:
                existing = await self._repository.get_leave_balance(emp_id, leave_type.id)
                if existing is not None:
                    continue

                balance = await self._repository.create_leave_balance(
                    employee_id=emp_id,
                    leave_type_id=leave_type.id,
                    balance=Decimal(leave_type.annual_allocation),
                    created_by=actor.id,
                )

                await self._repository.create_audit_log(
                    actor_user_id=actor.id,
                    action="leave_balance_update",
                    resource_id=balance.id,
                    ip_address=ip_address,
                    after_state=self._balance_snapshot(balance),
                    resource_type="leave_balances",
                )
                created.append(
                    InitializedBalanceRecord(
                        id=balance.id,
                        employee_id=balance.employee_id,
                        leave_type_id=balance.leave_type_id,
                        leave_type_name=leave_type.name,
                        balance=balance.balance,
                    ),
                )

        await self._session.commit()
        return InitializeBalanceResponse(created=created)

    # --- Leave types ---

    async def list_leave_types(self) -> LeaveTypeListResponse:
        rows = await self._repository.list_leave_types()
        return LeaveTypeListResponse(
            items=[self._to_leave_type_response(row) for row in rows],
        )

    async def create_leave_type(
        self,
        body: CreateLeaveTypeRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> LeaveTypeResponse:
        self._require_hr_or_admin(actor)

        existing = await self._repository.get_leave_type_by_name(body.name)
        if existing is not None:
            raise LeaveError("Leave type name already exists", 409)

        leave_type = await self._repository.create_leave_type(
            name=body.name,
            annual_allocation=body.annual_allocation,
        )
        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="leave_type_create",
            resource_id=leave_type.id,
            ip_address=ip_address,
            after_state=self._leave_type_snapshot(leave_type),
            resource_type="leave_types",
        )
        await self._session.commit()
        return self._to_leave_type_response(leave_type)

    async def get_leave_type(self, leave_type_id: uuid.UUID) -> LeaveTypeResponse:
        leave_type = await self._repository.get_leave_type_by_id(leave_type_id)
        if leave_type is None:
            raise LeaveError("Leave type not found", 404)
        return self._to_leave_type_response(leave_type)

    async def update_leave_type(
        self,
        leave_type_id: uuid.UUID,
        body: UpdateLeaveTypeRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> LeaveTypeResponse:
        self._require_hr_or_admin(actor)

        leave_type = await self._repository.get_leave_type_by_id(leave_type_id)
        if leave_type is None:
            raise LeaveError("Leave type not found", 404)

        before = self._leave_type_snapshot(leave_type)

        if body.name is not None and body.name != leave_type.name:
            conflict = await self._repository.get_leave_type_by_name(body.name)
            if conflict is not None:
                raise LeaveError("Leave type name already exists", 409)

        updated = await self._repository.update_leave_type(
            leave_type_id,
            name=body.name,
            annual_allocation=body.annual_allocation,
        )
        assert updated is not None

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="leave_type_update",
            resource_id=leave_type_id,
            ip_address=ip_address,
            before_state=before,
            after_state=self._leave_type_snapshot(updated),
            resource_type="leave_types",
        )
        await self._session.commit()
        return self._to_leave_type_response(updated)

    async def delete_leave_type(
        self,
        leave_type_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> None:
        self._require_hr_or_admin(actor)

        leave_type = await self._repository.get_leave_type_by_id(leave_type_id)
        if leave_type is None:
            raise LeaveError("Leave type not found", 404)

        if await self._repository.count_balances_for_leave_type(leave_type_id) > 0:
            raise LeaveError(
                "Cannot delete leave type with existing employee balances",
                409,
            )

        before = self._leave_type_snapshot(leave_type)
        await self._repository.delete_leave_type(leave_type_id)
        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="leave_type_delete",
            resource_id=leave_type_id,
            ip_address=ip_address,
            before_state=before,
            resource_type="leave_types",
        )
        await self._session.commit()

    async def resolve_actor_employee_id(self, actor: CurrentUser) -> uuid.UUID:
        employee = await self._repository.get_employee_by_user_id(actor.id)
        if employee is None:
            raise LeaveError("Employee profile not found for current user", 404)
        return employee.id

    # --- Helpers ---

    async def _get_request_or_404(self, request_id: uuid.UUID) -> LeaveRequest:
        request = await self._repository.get_leave_request_by_id(request_id)
        if request is None:
            raise LeaveError("Leave request not found", 404)
        return request

    async def _resolve_target_employee_id(
        self,
        actor: CurrentUser,
        employee_id: uuid.UUID | None,
    ) -> uuid.UUID:
        if employee_id is not None:
            if not self._is_hr_or_admin(actor):
                raise LeaveError("Insufficient permissions", 403)
            employee = await self._repository.get_employee_by_id(employee_id)
            if employee is None:
                raise LeaveError("Employee not found", 404)
            return employee_id

        return await self.resolve_actor_employee_id(actor)

    async def _resolve_balance_employee_id(
        self,
        actor: CurrentUser,
        employee_id: uuid.UUID | None,
    ) -> uuid.UUID:
        if employee_id is None:
            return await self.resolve_actor_employee_id(actor)

        if self._is_hr_or_admin(actor):
            return employee_id

        own_id = await self.resolve_actor_employee_id(actor)
        if employee_id != own_id:
            raise LeaveError("Insufficient permissions", 403)
        return employee_id

    async def _resolve_history_employee_id(
        self,
        actor: CurrentUser,
        employee_id: uuid.UUID | None,
    ) -> uuid.UUID:
        if self._is_hr_or_admin(actor):
            if employee_id is not None:
                return employee_id
            return await self.resolve_actor_employee_id(actor)

        return await self.resolve_actor_employee_id(actor)

    async def _list_scope_filters(
        self,
        actor: CurrentUser,
        employee_id: uuid.UUID | None,
    ) -> dict[str, uuid.UUID | None]:
        if self._is_hr_or_admin(actor):
            return {"employee_id": employee_id, "department_id": None}

        if DEPARTMENT_MANAGER in actor.roles:
            manager = await self._repository.get_employee_by_user_id(actor.id)
            if manager is None:
                raise LeaveError("Manager employee profile not found", 404)
            if employee_id is not None:
                employee = await self._repository.get_employee_by_id(employee_id)
                if employee is None:
                    raise LeaveError("Employee not found", 404)
                if employee.department_id != manager.department_id:
                    raise LeaveError("Insufficient permissions", 403)
                return {"employee_id": employee_id, "department_id": None}
            return {"employee_id": None, "department_id": manager.department_id}

        own_id = await self.resolve_actor_employee_id(actor)
        if employee_id is not None and employee_id != own_id:
            raise LeaveError("Insufficient permissions", 403)
        return {"employee_id": own_id, "department_id": None}

    async def _ensure_can_read_request(
        self,
        actor: CurrentUser,
        request: LeaveRequest,
    ) -> None:
        if self._is_hr_or_admin(actor):
            return

        employee = request.employee
        if self._is_self(actor, employee):
            return

        if DEPARTMENT_MANAGER in actor.roles:
            manager = await self._repository.get_employee_by_user_id(actor.id)
            if manager is not None and manager.department_id == employee.department_id:
                return

        raise LeaveError("Insufficient permissions", 403)

    async def _ensure_can_approve_request(
        self,
        actor: CurrentUser,
        request: LeaveRequest,
    ) -> None:
        if not self._can_approve_role(actor):
            raise LeaveError("Insufficient permissions", 403)

        employee = request.employee
        if self._is_self(actor, employee):
            raise LeaveError("Cannot approve or reject your own leave request", 400)

        if self._is_hr_or_admin(actor):
            return

        if DEPARTMENT_MANAGER in actor.roles:
            manager = await self._repository.get_employee_by_user_id(actor.id)
            if manager is None:
                raise LeaveError("Manager employee profile not found", 404)
            report_ids = await self._repository.get_direct_report_ids(manager.id)
            if request.employee_id not in report_ids:
                raise LeaveError("Insufficient permissions", 403)
            return

        raise LeaveError("Insufficient permissions", 403)

    async def _is_request_owner(
        self,
        actor: CurrentUser,
        request: LeaveRequest,
    ) -> bool:
        return self._is_self(actor, request.employee)

    async def _notify_manager_of_request(self, request: LeaveRequest) -> None:
        employee = request.employee
        if employee.manager_id is None:
            return
        manager = await self._repository.get_employee_by_id(employee.manager_id)
        if manager is None or manager.user_id is None:
            return
        await self._repository.create_notification(
            user_id=manager.user_id,
            title="Leave request submitted",
            message=(
                f"{employee.first_name} {employee.last_name} submitted a leave request "
                f"from {request.start_date} to {request.end_date}."
            ),
        )

    async def _notify_employee_of_decision(
        self,
        request: LeaveRequest,
        decision: str,
    ) -> None:
        employee = request.employee
        if employee.user_id is None:
            return
        leave_type_name = (
            request.leave_type.name
            if getattr(request, "leave_type", None) is not None
            else "leave"
        )
        await self._repository.create_notification(
            user_id=employee.user_id,
            title=f"Leave request {decision}",
            message=(
                f"Your {leave_type_name} request from {request.start_date} to {request.end_date} "
                f"was {decision}."
            ),
        )

    def _calendar_days(self, start_date: date, end_date: date) -> int:
        return (end_date - start_date).days + 1

    def _is_hr_or_admin(self, actor: CurrentUser) -> bool:
        return bool({HR_MANAGER, SYSTEM_ADMINISTRATOR}.intersection(actor.roles))

    def _can_approve_role(self, actor: CurrentUser) -> bool:
        return bool(
            {HR_MANAGER, SYSTEM_ADMINISTRATOR, DEPARTMENT_MANAGER}.intersection(actor.roles),
        )

    def _require_hr_or_admin(self, actor: CurrentUser) -> None:
        if not self._is_hr_or_admin(actor):
            raise LeaveError("Insufficient permissions", 403)

    def _is_self(self, actor: CurrentUser, employee: Employee) -> bool:
        return employee.user_id is not None and employee.user_id == actor.id

    def _full_name(self, employee: Employee) -> str:
        return f"{employee.first_name} {employee.last_name}".strip()

    def _latest_approval(self, request: LeaveRequest) -> LeaveApproval | None:
        if not request.approvals:
            return None
        return max(request.approvals, key=lambda a: a.approval_level)

    def _approver_display_name(self, approval: LeaveApproval | None) -> str | None:
        if approval is None:
            return None
        if approval.approver is not None:
            return approval.approver.email
        return None

    def _request_snapshot(self, request: LeaveRequest) -> dict[str, Any]:
        return {
            "id": str(request.id),
            "employee_id": str(request.employee_id),
            "leave_type_id": str(request.leave_type_id),
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "status": request.status,
        }

    def _balance_snapshot(self, balance: LeaveBalance) -> dict[str, Any]:
        return {
            "id": str(balance.id),
            "employee_id": str(balance.employee_id),
            "leave_type_id": str(balance.leave_type_id),
            "balance": str(balance.balance),
        }

    def _leave_type_snapshot(self, leave_type: LeaveType) -> dict[str, Any]:
        return {
            "id": str(leave_type.id),
            "name": leave_type.name,
            "annual_allocation": leave_type.annual_allocation,
        }

    def _to_request_response(self, request: LeaveRequest) -> LeaveRequestResponse:
        approval = self._latest_approval(request)
        return LeaveRequestResponse(
            id=request.id,
            employee_id=request.employee_id,
            employee_name=self._full_name(request.employee),
            leave_type_id=request.leave_type_id,
            leave_type_name=request.leave_type.name,
            start_date=request.start_date,
            end_date=request.end_date,
            reason=request.reason,
            status=request.status,  # type: ignore[arg-type]
            created_at=request.created_at,
            approver_name=self._approver_display_name(approval),
            approval_level=approval.approval_level if approval else None,
            approval_remarks=approval.remarks if approval else None,
        )

    def _to_leave_type_response(self, leave_type: LeaveType) -> LeaveTypeResponse:
        return LeaveTypeResponse(
            id=leave_type.id,
            name=leave_type.name,
            annual_allocation=leave_type.annual_allocation,
        )
