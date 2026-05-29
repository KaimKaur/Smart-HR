from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organization.status_repository import StatusRepository
from app.modules.organization.status_schema import (
    AttendanceStatusListResponse,
    AttendanceStatusResponse,
    EmploymentStatusListResponse,
    EmploymentStatusResponse,
)


class StatusService:
    def __init__(
        self,
        session: AsyncSession,
        repository: StatusRepository | None = None,
    ) -> None:
        self._repository = repository or StatusRepository(session)

    async def list_employment_statuses(self) -> EmploymentStatusListResponse:
        statuses = await self._repository.list_employment_statuses()
        return EmploymentStatusListResponse(
            items=[EmploymentStatusResponse.model_validate(s) for s in statuses],
        )

    async def list_attendance_statuses(self) -> AttendanceStatusListResponse:
        statuses = await self._repository.list_attendance_statuses()
        return AttendanceStatusListResponse(
            items=[AttendanceStatusResponse.model_validate(s) for s in statuses],
        )
