from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.modules.organization.status_schema import (
    AttendanceStatusListResponse,
    EmploymentStatusListResponse,
)
from app.modules.organization.status_service import StatusService


class StatusController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = StatusService(session)

    async def list_employment_statuses(
        self,
    ) -> SuccessResponse[EmploymentStatusListResponse]:
        data = await self._service.list_employment_statuses()
        return SuccessResponse(message="OK", data=data)

    async def list_attendance_statuses(
        self,
    ) -> SuccessResponse[AttendanceStatusListResponse]:
        data = await self._service.list_attendance_statuses()
        return SuccessResponse(message="OK", data=data)
