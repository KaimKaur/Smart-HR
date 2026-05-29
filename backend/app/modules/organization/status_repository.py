from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attendance.model import AttendanceStatus
from app.modules.employee.model import EmploymentStatus


class StatusRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_employment_statuses(self) -> list[EmploymentStatus]:
        result = await self._session.execute(
            select(EmploymentStatus).order_by(EmploymentStatus.name.asc()),
        )
        return list(result.scalars().all())

    async def list_attendance_statuses(self) -> list[AttendanceStatus]:
        result = await self._session.execute(
            select(AttendanceStatus).order_by(AttendanceStatus.name.asc()),
        )
        return list(result.scalars().all())
