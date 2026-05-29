from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEPARTMENT_MANAGER,
    EMPLOYEE,
    HR_MANAGER,
    RECRUITER,
    SYSTEM_ADMINISTRATOR,
)
from app.core.security import CurrentUser
from app.modules.dashboard.errors import DashboardError
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schema import (
    AttendanceDashboardResponse,
    EmployeeDashboardResponse,
    HRDashboardResponse,
    PerformanceDashboardResponse,
    RecruitmentDashboardResponse,
)


class DashboardService:
    def __init__(
        self,
        session: AsyncSession,
        repository: DashboardRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or DashboardRepository(session)

    async def get_hr_dashboard(
        self,
        *,
        actor: CurrentUser,
        today: date | None = None,
    ) -> HRDashboardResponse:
        if not self._is_hr_or_admin(actor):
            raise DashboardError("Insufficient permissions", 403)

        today = today or date.today()
        snapshot = await self._repository.get_hr_snapshot(today)
        return HRDashboardResponse(**snapshot)

    async def get_recruitment_dashboard(
        self,
        *,
        actor: CurrentUser,
        today: date | None = None,
    ) -> RecruitmentDashboardResponse:
        if not self._is_recruitment_allowed(actor):
            raise DashboardError("Insufficient permissions", 403)

        today = today or date.today()
        snapshot = await self._repository.get_recruitment_snapshot(today)
        return RecruitmentDashboardResponse(**snapshot)

    async def get_attendance_dashboard(
        self,
        *,
        actor: CurrentUser,
        today: date | None = None,
    ) -> AttendanceDashboardResponse:
        if not self._is_hr_or_admin(actor):
            raise DashboardError("Insufficient permissions", 403)

        today = today or date.today()
        snapshot = await self._repository.get_attendance_snapshot(today)
        return AttendanceDashboardResponse(**snapshot)

    async def get_performance_dashboard(
        self,
        *,
        actor: CurrentUser,
        today: date | None = None,
    ) -> PerformanceDashboardResponse:
        if not self._is_hr_or_admin(actor):
            raise DashboardError("Insufficient permissions", 403)

        today = today or date.today()
        snapshot = await self._repository.get_performance_snapshot(today)
        return PerformanceDashboardResponse(**snapshot)

    async def get_employee_dashboard(
        self,
        *,
        actor: CurrentUser,
        today: date | None = None,
    ) -> EmployeeDashboardResponse:
        if not self._is_employee_allowed(actor):
            raise DashboardError("Insufficient permissions", 403)

        today = today or date.today()
        snapshot = await self._repository.get_employee_snapshot(actor.id, today)
        if snapshot.get("_error") == "employee_not_found":
            raise DashboardError("Employee profile not found", 404)
        return EmployeeDashboardResponse(**snapshot)

    def _is_hr_or_admin(self, actor: CurrentUser) -> bool:
        return bool({HR_MANAGER, SYSTEM_ADMINISTRATOR}.intersection(actor.roles))

    def _is_recruitment_allowed(self, actor: CurrentUser) -> bool:
        return bool({RECRUITER, HR_MANAGER, SYSTEM_ADMINISTRATOR}.intersection(actor.roles))

    def _is_employee_allowed(self, actor: CurrentUser) -> bool:
        return bool({EMPLOYEE, DEPARTMENT_MANAGER}.intersection(actor.roles))

