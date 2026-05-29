import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employee.model import Department, Employee
from app.modules.notifications.model import AuditLog


class DepartmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _employee_count_subquery(self):
        return (
            select(func.count(Employee.id))
            .where(
                Employee.department_id == Department.id,
                Employee.deleted_at.is_(None),
            )
            .correlate(Department)
            .scalar_subquery()
        )

    async def create_department(
        self,
        *,
        name: str,
        description: str | None,
    ) -> Department:
        department = Department(name=name, description=description)
        self._session.add(department)
        await self._session.flush()
        return department

    async def get_department_by_id(self, department_id: uuid.UUID) -> Department | None:
        result = await self._session.execute(
            select(Department).where(Department.id == department_id),
        )
        return result.scalar_one_or_none()

    async def get_department_by_name(self, name: str) -> Department | None:
        result = await self._session.execute(
            select(Department).where(Department.name == name),
        )
        return result.scalar_one_or_none()

    async def list_departments(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[Department, int]], int]:
        employee_count = self._employee_count_subquery()
        count_query = select(func.count()).select_from(Department)
        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        query = (
            select(Department, employee_count.label("employee_count"))
            .order_by(Department.name.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        rows = [(row[0], int(row[1])) for row in result.all()]
        return rows, total_items

    async def get_department_with_count(
        self,
        department_id: uuid.UUID,
    ) -> tuple[Department, int] | None:
        employee_count = self._employee_count_subquery()
        result = await self._session.execute(
            select(Department, employee_count.label("employee_count")).where(
                Department.id == department_id,
            ),
        )
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], int(row[1])

    async def count_active_employees(self, department_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(Employee.id)).where(
                Employee.department_id == department_id,
                Employee.deleted_at.is_(None),
            ),
        )
        return int(result.scalar_one())

    async def update_department(
        self,
        department_id: uuid.UUID,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Department | None:
        values: dict = {"updated_at": datetime.now(UTC)}
        if name is not None:
            values["name"] = name
        if description is not None:
            values["description"] = description

        await self._session.execute(
            update(Department).where(Department.id == department_id).values(**values),
        )
        return await self.get_department_by_id(department_id)

    async def delete_department(self, department_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(Department).where(Department.id == department_id),
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
            resource_type="department",
            resource_id=resource_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=after_state,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
