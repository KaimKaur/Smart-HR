from uuid import UUID

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.employee.errors import EmployeeError
from app.modules.employee.schema import (
    CreateEmployeeRequest,
    CreateEmployeeResponse,
    DirectReportsResponse,
    EmployeeListResponse,
    EmployeeProfileResponse,
    EmployeeResponse,
    EmployeeSearchResponse,
    EmployeeSelfUpdateRequest,
    ManagerDetailResponse,
    UpdateEmployeeRequest,
)
from app.modules.employee.service import EmployeeService


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


class EmployeeController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = EmployeeService(session)

    async def create_employee(
        self,
        body: CreateEmployeeRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[CreateEmployeeResponse]:
        try:
            data = await self._service.create_employee(
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return SuccessResponse(message="Employee created", data=data)

    async def list_employees(
        self,
        *,
        current_user: CurrentUser,
        search: str | None,
        department_id: UUID | None,
        designation_id: UUID | None,
        status: UUID | None,
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int,
    ) -> SuccessResponse[EmployeeListResponse]:
        try:
            data = await self._service.list_employees(
                actor=current_user,
                search=search,
                department_id=department_id,
                designation_id=designation_id,
                employment_status_id=status,
                sort_by=sort_by,
                sort_order=sort_order,  # type: ignore[arg-type]
                page=page,
                page_size=page_size,
            )
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_employee(
        self,
        employee_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[EmployeeResponse]:
        try:
            data = await self._service.get_employee(employee_id, actor=current_user)
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def update_employee(
        self,
        employee_id: UUID,
        body: UpdateEmployeeRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[EmployeeResponse]:
        try:
            data = await self._service.update_employee(
                employee_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return SuccessResponse(message="Employee updated", data=data)

    async def update_own_profile(
        self,
        employee_id: UUID,
        body: EmployeeSelfUpdateRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[EmployeeResponse]:
        try:
            data = await self._service.update_employee(
                employee_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return SuccessResponse(message="Employee updated", data=data)

    async def deactivate_employee(
        self,
        employee_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> Response:
        try:
            await self._service.deactivate_employee(
                employee_id,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def get_profile(
        self,
        employee_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[EmployeeProfileResponse]:
        try:
            data = await self._service.get_profile(employee_id, actor=current_user)
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_manager(
        self,
        employee_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[ManagerDetailResponse | None]:
        try:
            data = await self._service.get_manager(employee_id, actor=current_user)
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_direct_reports(
        self,
        employee_id: UUID,
        *,
        current_user: CurrentUser,
        page: int,
        page_size: int,
    ) -> SuccessResponse[DirectReportsResponse]:
        try:
            data = await self._service.get_direct_reports(
                employee_id,
                actor=current_user,
                page=page,
                page_size=page_size,
            )
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def search_employees(
        self,
        query: str,
        current_user: CurrentUser,
        *,
        limit: int,
    ) -> SuccessResponse[EmployeeSearchResponse]:
        try:
            data = await self._service.search_employees(
                query,
                actor=current_user,
                limit=limit,
            )
        except EmployeeError as exc:
            raise _employee_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)


def _employee_http_exception(exc: EmployeeError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": []},
    )
