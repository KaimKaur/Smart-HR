from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.dashboard.errors import DashboardError
from app.modules.dashboard.http import dashboard_http_exception
from app.modules.dashboard.schema import (
    AttendanceDashboardResponse,
    EmployeeDashboardResponse,
    HRDashboardResponse,
    PerformanceDashboardResponse,
    RecruitmentDashboardResponse,
)
from app.modules.dashboard.service import DashboardService


class DashboardController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = DashboardService(session)

    async def hr_dashboard(
        self,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[HRDashboardResponse]:
        try:
            data = await self._service.get_hr_dashboard(actor=actor)
        except DashboardError as exc:
            raise dashboard_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def recruitment_dashboard(
        self,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[RecruitmentDashboardResponse]:
        try:
            data = await self._service.get_recruitment_dashboard(actor=actor)
        except DashboardError as exc:
            raise dashboard_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def attendance_dashboard(
        self,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[AttendanceDashboardResponse]:
        try:
            data = await self._service.get_attendance_dashboard(actor=actor)
        except DashboardError as exc:
            raise dashboard_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def performance_dashboard(
        self,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[PerformanceDashboardResponse]:
        try:
            data = await self._service.get_performance_dashboard(actor=actor)
        except DashboardError as exc:
            raise dashboard_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def employee_dashboard(
        self,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[EmployeeDashboardResponse]:
        try:
            data = await self._service.get_employee_dashboard(actor=actor)
        except DashboardError as exc:
            raise dashboard_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

