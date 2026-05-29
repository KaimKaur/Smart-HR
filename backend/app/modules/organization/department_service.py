import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employee.model import Department
from app.modules.organization.department_repository import DepartmentRepository
from app.modules.organization.department_schema import (
    CreateDepartmentRequest,
    DepartmentListResponse,
    DepartmentResponse,
    UpdateDepartmentRequest,
    build_pagination,
)
from app.modules.organization.errors import OrganizationError


class DepartmentService:
    def __init__(
        self,
        session: AsyncSession,
        repository: DepartmentRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or DepartmentRepository(session)

    async def create_department(
        self,
        body: CreateDepartmentRequest,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> DepartmentResponse:
        existing = await self._repository.get_department_by_name(body.name)
        if existing is not None:
            raise OrganizationError("Department name already exists", 409)

        department = await self._repository.create_department(
            name=body.name,
            description=body.description,
        )
        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="department_create",
            resource_id=department.id,
            ip_address=ip_address,
            after_state=self._audit_snapshot(department),
        )
        await self._session.commit()

        return self._to_response(department, employee_count=0)

    async def list_departments(
        self,
        *,
        page: int,
        page_size: int,
    ) -> DepartmentListResponse:
        rows, total = await self._repository.list_departments(
            page=page,
            page_size=page_size,
        )
        return DepartmentListResponse(
            items=[self._to_response(dept, count) for dept, count in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_department(self, department_id: uuid.UUID) -> DepartmentResponse:
        row = await self._repository.get_department_with_count(department_id)
        if row is None:
            raise OrganizationError("Department not found", 404)
        department, count = row
        return self._to_response(department, count)

    async def update_department(
        self,
        department_id: uuid.UUID,
        body: UpdateDepartmentRequest,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> DepartmentResponse:
        department = await self._repository.get_department_by_id(department_id)
        if department is None:
            raise OrganizationError("Department not found", 404)

        payload = body.model_dump(exclude_unset=True)
        if not payload:
            raise OrganizationError("No fields to update", 400)

        new_name = payload.get("name")
        if new_name is not None and new_name != department.name:
            duplicate = await self._repository.get_department_by_name(new_name)
            if duplicate is not None and duplicate.id != department_id:
                raise OrganizationError("Department name already exists", 409)

        before_state = self._audit_snapshot(department)
        updated = await self._repository.update_department(department_id, **payload)
        if updated is None:
            raise OrganizationError("Department not found", 404)

        count = await self._repository.count_active_employees(department_id)
        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="department_update",
            resource_id=department_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=self._audit_snapshot(updated),
        )
        await self._session.commit()

        return self._to_response(updated, count)

    async def delete_department(
        self,
        department_id: uuid.UUID,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> None:
        department = await self._repository.get_department_by_id(department_id)
        if department is None:
            raise OrganizationError("Department not found", 404)

        employee_count = await self._repository.count_active_employees(department_id)
        if employee_count > 0:
            raise OrganizationError(
                "Cannot delete department with assigned employees",
                409,
            )

        before_state = self._audit_snapshot(department)
        deleted = await self._repository.delete_department(department_id)
        if not deleted:
            raise OrganizationError("Department not found", 404)

        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="department_delete",
            resource_id=department_id,
            ip_address=ip_address,
            before_state=before_state,
        )
        await self._session.commit()

    def _audit_snapshot(self, department: Department) -> dict:
        return {
            "name": department.name,
            "description": department.description,
        }

    def _to_response(self, department: Department, employee_count: int) -> DepartmentResponse:
        return DepartmentResponse(
            id=department.id,
            name=department.name,
            description=department.description,
            employee_count=employee_count,
            created_at=department.created_at,
            updated_at=department.updated_at,
        )
