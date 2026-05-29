import uuid
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.employee.model import (
    Department,
    Designation,
    Employee,
    EmploymentStatus,
)
from app.modules.notifications.model import AuditLog

SortOrder = Literal["asc", "desc"]

_EMPLOYEE_LOAD_OPTIONS = (
    selectinload(Employee.department),
    selectinload(Employee.designation),
    selectinload(Employee.employment_status),
    selectinload(Employee.manager).selectinload(Employee.department),
    selectinload(Employee.manager).selectinload(Employee.designation),
)

_SORT_COLUMNS = {
    "first_name": Employee.first_name,
    "last_name": Employee.last_name,
    "employee_code": Employee.employee_code,
    "join_date": Employee.join_date,
    "created_at": Employee.created_at,
}


class EmployeeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self, *, include_deleted: bool = False):
        query = select(Employee).options(*_EMPLOYEE_LOAD_OPTIONS)
        if not include_deleted:
            query = query.where(Employee.deleted_at.is_(None))
        return query

    async def create_employee(
        self,
        *,
        user_id: uuid.UUID | None,
        employee_code: str,
        first_name: str,
        last_name: str,
        email: str,
        phone: str | None,
        department_id: uuid.UUID,
        designation_id: uuid.UUID,
        employment_status_id: uuid.UUID,
        manager_id: uuid.UUID | None,
        salary,
        join_date,
    ) -> Employee:
        employee = Employee(
            user_id=user_id,
            employee_code=employee_code,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            department_id=department_id,
            designation_id=designation_id,
            employment_status_id=employment_status_id,
            manager_id=manager_id,
            salary=salary,
            join_date=join_date,
        )
        self._session.add(employee)
        await self._session.flush()
        return await self.get_employee_by_id(employee.id)  # type: ignore[return-value]

    async def get_employee_by_id(
        self,
        employee_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> Employee | None:
        query = self._base_query(include_deleted=include_deleted).where(
            Employee.id == employee_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_employee_by_code(
        self,
        employee_code: str,
        *,
        include_deleted: bool = False,
    ) -> Employee | None:
        query = self._base_query(include_deleted=include_deleted).where(
            Employee.employee_code == employee_code,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_employee_by_email(
        self,
        email: str,
        *,
        include_deleted: bool = False,
    ) -> Employee | None:
        query = self._base_query(include_deleted=include_deleted).where(
            Employee.email == email,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_employee_by_user_id(
        self,
        user_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> Employee | None:
        query = self._base_query(include_deleted=include_deleted).where(
            Employee.user_id == user_id,
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_employees(
        self,
        *,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
        designation_id: uuid.UUID | None = None,
        employment_status_id: uuid.UUID | None = None,
        manager_id: uuid.UUID | None = None,
        sort_by: str = "created_at",
        sort_order: SortOrder = "desc",
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False,
    ) -> tuple[list[Employee], int]:
        query = self._base_query(include_deleted=include_deleted)
        count_query = select(func.count()).select_from(Employee)

        if not include_deleted:
            count_query = count_query.where(Employee.deleted_at.is_(None))

        if department_id is not None:
            query = query.where(Employee.department_id == department_id)
            count_query = count_query.where(Employee.department_id == department_id)

        if designation_id is not None:
            query = query.where(Employee.designation_id == designation_id)
            count_query = count_query.where(Employee.designation_id == designation_id)

        if employment_status_id is not None:
            query = query.where(Employee.employment_status_id == employment_status_id)
            count_query = count_query.where(
                Employee.employment_status_id == employment_status_id,
            )

        if manager_id is not None:
            query = query.where(Employee.manager_id == manager_id)
            count_query = count_query.where(Employee.manager_id == manager_id)

        if search:
            pattern = f"%{search.strip()}%"
            search_filter = or_(
                Employee.first_name.ilike(pattern),
                Employee.last_name.ilike(pattern),
                Employee.email.ilike(pattern),
                Employee.employee_code.ilike(pattern),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        sort_column = _SORT_COLUMNS.get(sort_by, Employee.created_at)
        order_expr = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        offset = (page - 1) * page_size
        query = query.order_by(order_expr).offset(offset).limit(page_size)

        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    async def search_employees(
        self,
        query_text: str,
        *,
        limit: int = 20,
        department_id: uuid.UUID | None = None,
    ) -> list[Employee]:
        pattern = f"%{query_text.strip()}%"
        query = (
            self._base_query()
            .where(
                or_(
                    Employee.first_name.ilike(pattern),
                    Employee.last_name.ilike(pattern),
                    Employee.email.ilike(pattern),
                    Employee.employee_code.ilike(pattern),
                ),
            )
            .order_by(Employee.last_name.asc(), Employee.first_name.asc())
            .limit(limit)
        )
        if department_id is not None:
            query = query.where(Employee.department_id == department_id)

        result = await self._session.execute(query)
        return list(result.scalars().unique().all())

    async def update_employee(
        self,
        employee_id: uuid.UUID,
        **fields,
    ) -> Employee | None:
        if not fields:
            return await self.get_employee_by_id(employee_id)

        fields["updated_at"] = datetime.now(UTC)
        await self._session.execute(
            update(Employee)
            .where(Employee.id == employee_id, Employee.deleted_at.is_(None))
            .values(**fields),
        )
        return await self.get_employee_by_id(employee_id)

    async def soft_delete_employee(self, employee_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            update(Employee)
            .where(Employee.id == employee_id, Employee.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        )
        return result.rowcount > 0

    async def get_direct_reports(
        self,
        manager_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Employee], int]:
        return await self.list_employees(
            manager_id=manager_id,
            page=page,
            page_size=page_size,
            sort_by="last_name",
            sort_order="asc",
        )

    async def get_department_by_id(self, department_id: uuid.UUID) -> Department | None:
        result = await self._session.execute(
            select(Department).where(Department.id == department_id),
        )
        return result.scalar_one_or_none()

    async def get_designation_by_id(
        self,
        designation_id: uuid.UUID,
    ) -> Designation | None:
        result = await self._session.execute(
            select(Designation).where(Designation.id == designation_id),
        )
        return result.scalar_one_or_none()

    async def get_employment_status_by_id(
        self,
        status_id: uuid.UUID,
    ) -> EmploymentStatus | None:
        result = await self._session.execute(
            select(EmploymentStatus).where(EmploymentStatus.id == status_id),
        )
        return result.scalar_one_or_none()

    async def get_active_employment_status_id(self) -> uuid.UUID | None:
        result = await self._session.execute(
            select(EmploymentStatus.id).where(EmploymentStatus.name == "active"),
        )
        return result.scalar_one_or_none()

    async def is_manager_active(self, manager_id: uuid.UUID) -> bool:
        active_status_id = await self.get_active_employment_status_id()
        if active_status_id is None:
            return False

        result = await self._session.execute(
            select(Employee.id).where(
                Employee.id == manager_id,
                Employee.deleted_at.is_(None),
                Employee.employment_status_id == active_status_id,
            ),
        )
        return result.scalar_one_or_none() is not None

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
            resource_type="employee",
            resource_id=resource_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=after_state,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
