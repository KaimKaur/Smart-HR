import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employee.model import Designation, Employee
from app.modules.notifications.model import AuditLog


class DesignationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _employee_count_subquery(self):
        return (
            select(func.count(Employee.id))
            .where(
                Employee.designation_id == Designation.id,
                Employee.deleted_at.is_(None),
            )
            .correlate(Designation)
            .scalar_subquery()
        )

    async def create_designation(
        self,
        *,
        title: str,
        description: str | None,
    ) -> Designation:
        designation = Designation(title=title, description=description)
        self._session.add(designation)
        await self._session.flush()
        return designation

    async def get_designation_by_id(
        self,
        designation_id: uuid.UUID,
    ) -> Designation | None:
        result = await self._session.execute(
            select(Designation).where(Designation.id == designation_id),
        )
        return result.scalar_one_or_none()

    async def get_designation_by_title(self, title: str) -> Designation | None:
        result = await self._session.execute(
            select(Designation).where(Designation.title == title),
        )
        return result.scalar_one_or_none()

    async def list_designations(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[Designation, int]], int]:
        employee_count = self._employee_count_subquery()
        count_query = select(func.count()).select_from(Designation)
        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        query = (
            select(Designation, employee_count.label("employee_count"))
            .order_by(Designation.title.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        rows = [(row[0], int(row[1])) for row in result.all()]
        return rows, total_items

    async def get_designation_with_count(
        self,
        designation_id: uuid.UUID,
    ) -> tuple[Designation, int] | None:
        employee_count = self._employee_count_subquery()
        result = await self._session.execute(
            select(Designation, employee_count.label("employee_count")).where(
                Designation.id == designation_id,
            ),
        )
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], int(row[1])

    async def count_active_employees(self, designation_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(Employee.id)).where(
                Employee.designation_id == designation_id,
                Employee.deleted_at.is_(None),
            ),
        )
        return int(result.scalar_one())

    async def update_designation(
        self,
        designation_id: uuid.UUID,
        *,
        title: str | None = None,
        description: str | None = None,
    ) -> Designation | None:
        values: dict = {"updated_at": datetime.now(UTC)}
        if title is not None:
            values["title"] = title
        if description is not None:
            values["description"] = description

        await self._session.execute(
            update(Designation).where(Designation.id == designation_id).values(**values),
        )
        return await self.get_designation_by_id(designation_id)

    async def delete_designation(self, designation_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(Designation).where(Designation.id == designation_id),
        )
        return result.rowcount > 0

    async def create_audit_log(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        resource_id: uuid.UUID | None = None,
        ip_address: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type="designation",
            resource_id=resource_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=after_state,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
