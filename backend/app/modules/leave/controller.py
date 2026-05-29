from datetime import date
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.leave.errors import LeaveError
from app.modules.leave.http import leave_http_exception
from app.modules.leave.schema import (
    CreateLeaveRequest,
    CreateLeaveTypeRequest,
    InitializeBalanceRequest,
    InitializeBalanceResponse,
    LeaveApprovalRequest,
    LeaveBalanceResponse,
    LeaveListResponse,
    LeaveRequestResponse,
    LeaveTypeListResponse,
    LeaveTypeResponse,
    UpdateLeaveTypeRequest,
)
from app.modules.leave.service import LeaveService


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


class LeaveController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = LeaveService(session)

    async def create_leave_request(
        self,
        body: CreateLeaveRequest,
        current_user: CurrentUser,
        request: Request,
        *,
        employee_id: UUID | None = None,
    ) -> SuccessResponse[LeaveRequestResponse]:
        try:
            data = await self._service.create_leave_request(
                body,
                actor=current_user,
                ip_address=_client_ip(request),
                employee_id=employee_id,
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave request submitted", data=data)

    async def list_leave_requests(
        self,
        current_user: CurrentUser,
        *,
        employee_id: UUID | None = None,
        status: str | None = None,
        leave_type_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[LeaveListResponse]:
        try:
            data = await self._service.list_leave_requests(
                actor=current_user,
                employee_id=employee_id,
                status=status,
                leave_type_id=leave_type_id,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=page_size,
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave requests retrieved", data=data)

    async def get_leave_request(
        self,
        leave_request_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[LeaveRequestResponse]:
        try:
            data = await self._service.get_leave_request(
                leave_request_id,
                actor=current_user,
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave request retrieved", data=data)

    async def approve_leave(
        self,
        leave_request_id: UUID,
        body: LeaveApprovalRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[LeaveRequestResponse]:
        try:
            data = await self._service.approve_leave(
                leave_request_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave request approved", data=data)

    async def reject_leave(
        self,
        leave_request_id: UUID,
        body: LeaveApprovalRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[LeaveRequestResponse]:
        try:
            data = await self._service.reject_leave(
                leave_request_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave request rejected", data=data)

    async def cancel_leave(
        self,
        leave_request_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[LeaveRequestResponse]:
        try:
            data = await self._service.cancel_leave(
                leave_request_id,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave request cancelled", data=data)

    async def get_leave_balance(
        self,
        current_user: CurrentUser,
        *,
        employee_id: UUID | None = None,
    ) -> SuccessResponse[LeaveBalanceResponse]:
        try:
            data = await self._service.get_leave_balance(
                actor=current_user,
                employee_id=employee_id,
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave balance retrieved", data=data)

    async def list_pending_approvals(
        self,
        current_user: CurrentUser,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[LeaveListResponse]:
        try:
            data = await self._service.list_pending_approvals(
                actor=current_user,
                page=page,
                page_size=page_size,
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Pending approvals retrieved", data=data)

    async def get_leave_history(
        self,
        current_user: CurrentUser,
        *,
        employee_id: UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[LeaveListResponse]:
        try:
            data = await self._service.get_leave_history(
                actor=current_user,
                employee_id=employee_id,
                status=status,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=page_size,
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave history retrieved", data=data)

    async def initialize_balances(
        self,
        body: InitializeBalanceRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[InitializeBalanceResponse]:
        try:
            data = await self._service.initialize_balances(
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave balances initialized", data=data)


class LeaveTypeController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = LeaveService(session)

    async def list_leave_types(self) -> SuccessResponse[LeaveTypeListResponse]:
        data = await self._service.list_leave_types()
        return SuccessResponse(message="Leave types retrieved", data=data)

    async def create_leave_type(
        self,
        body: CreateLeaveTypeRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[LeaveTypeResponse]:
        try:
            data = await self._service.create_leave_type(
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave type created", data=data)

    async def get_leave_type(
        self,
        leave_type_id: UUID,
    ) -> SuccessResponse[LeaveTypeResponse]:
        try:
            data = await self._service.get_leave_type(leave_type_id)
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave type retrieved", data=data)

    async def update_leave_type(
        self,
        leave_type_id: UUID,
        body: UpdateLeaveTypeRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[LeaveTypeResponse]:
        try:
            data = await self._service.update_leave_type(
                leave_type_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave type updated", data=data)

    async def delete_leave_type(
        self,
        leave_type_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[None]:
        try:
            await self._service.delete_leave_type(
                leave_type_id,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except LeaveError as exc:
            raise leave_http_exception(exc) from exc
        return SuccessResponse(message="Leave type deleted", data=None)
