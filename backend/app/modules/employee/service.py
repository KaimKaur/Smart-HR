import secrets
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import (
    DEPARTMENT_MANAGER,
    EMPLOYEE,
    HR_MANAGER,
    SYSTEM_ADMINISTRATOR,
)
from app.core.security import CurrentUser, generate_opaque_token, hash_password, hash_token
from app.modules.auth.repository import AuthRepository
from app.modules.employee.errors import EmployeeError
from app.modules.employee.model import Employee
from app.modules.employee.repository import EmployeeRepository, SortOrder
from app.modules.employee.schema import (
    CreateEmployeeRequest,
    CreateEmployeeResponse,
    DepartmentRef,
    DesignationRef,
    DirectReportsResponse,
    EmployeeListResponse,
    EmployeeProfileResponse,
    EmployeeResponse,
    EmployeeSearchItem,
    EmployeeSearchResponse,
    EmployeeSelfUpdateRequest,
    EmploymentStatusRef,
    ManagerDetailResponse,
    ManagerRef,
    UpdateEmployeeRequest,
    build_pagination,
)
from app.modules.user.repository import UserRepository


class EmployeeService:
    def __init__(
        self,
        session: AsyncSession,
        repository: EmployeeRepository | None = None,
        user_repository: UserRepository | None = None,
        auth_repository: AuthRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or EmployeeRepository(session)
        self._user_repository = user_repository or UserRepository(session)
        self._auth_repository = auth_repository or AuthRepository(session)
        self._settings = settings or get_settings()

    async def create_employee(
        self,
        body: CreateEmployeeRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> CreateEmployeeResponse:
        self._require_hr_or_admin(actor)

        if body.join_date > date.today():
            raise EmployeeError("join_date cannot be in the future", 400)

        await self._validate_unique_code(body.employee_code)
        await self._validate_unique_email(body.email)
        await self._validate_foreign_keys(
            department_id=body.department_id,
            designation_id=body.designation_id,
            employment_status_id=body.employment_status_id,
            manager_id=body.manager_id,
        )

        reset_token: str | None = None
        user_id = body.user_id

        if user_id is not None:
            user = await self._user_repository.get_user_by_id(user_id)
            if user is None:
                raise EmployeeError("Linked user not found", 400)
            existing_link = await self._repository.get_employee_by_user_id(user_id)
            if existing_link is not None:
                raise EmployeeError("User is already linked to an employee", 409)
        else:
            existing_user = await self._user_repository.get_user_by_email(
                body.email,
                include_deleted=True,
            )
            if existing_user is not None:
                raise EmployeeError("Email already used by a user account", 409)

            placeholder_password = hash_password(secrets.token_urlsafe(32))
            user = await self._user_repository.create_user(
                email=body.email,
                password_hash=placeholder_password,
                is_active=False,
            )
            role = await self._user_repository.get_role_by_name(EMPLOYEE)
            if role is None:
                raise EmployeeError("Employee role is not configured", 500)
            await self._user_repository.assign_role(user.id, role.id)
            user_id = user.id
            reset_token = await self._create_password_reset_token(user.id)

        employee = await self._repository.create_employee(
            user_id=user_id,
            employee_code=body.employee_code,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            phone=body.phone,
            department_id=body.department_id,
            designation_id=body.designation_id,
            employment_status_id=body.employment_status_id,
            manager_id=body.manager_id,
            salary=body.salary,
            join_date=body.join_date,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="employee_create",
            resource_id=employee.id,
            ip_address=ip_address,
            after_state=self._audit_snapshot(employee),
        )
        await self._session.commit()

        return self._to_create_response(
            employee,
            reset_token,
            include_salary=True,
        )

    async def list_employees(
        self,
        *,
        actor: CurrentUser,
        search: str | None,
        department_id: uuid.UUID | None,
        designation_id: uuid.UUID | None,
        employment_status_id: uuid.UUID | None,
        sort_by: str,
        sort_order: SortOrder,
        page: int,
        page_size: int,
    ) -> EmployeeListResponse:
        scope, scoped_department_id = await self._resolve_list_scope(actor)

        if scope == "own":
            own = await self._repository.get_employee_by_user_id(actor.id)
            if own is None:
                raise EmployeeError("Employee profile not found", 404)
            items = [self._to_response(own, include_salary=False)]
            return EmployeeListResponse(
                items=items,
                pagination=build_pagination(1, page_size, 1),
            )

        if scope == "department":
            if (
                department_id is not None
                and department_id != scoped_department_id
            ):
                raise EmployeeError("Cannot filter outside your department", 403)
            department_id = scoped_department_id

        employees, total = await self._repository.list_employees(
            search=search,
            department_id=department_id,
            designation_id=designation_id,
            employment_status_id=employment_status_id,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )
        include_salary = self._can_view_salary(actor.roles)
        return EmployeeListResponse(
            items=[
                self._to_response(employee, include_salary=include_salary)
                for employee in employees
            ],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_employee(
        self,
        employee_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> EmployeeResponse:
        employee = await self._get_employee_or_404(employee_id)
        await self._ensure_can_read(actor, employee)
        return self._to_response(
            employee,
            include_salary=self._can_view_salary(actor.roles),
        )

    async def update_employee(
        self,
        employee_id: uuid.UUID,
        body: UpdateEmployeeRequest | EmployeeSelfUpdateRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> EmployeeResponse:
        employee = await self._get_employee_or_404(employee_id)
        await self._ensure_can_read(actor, employee)

        if isinstance(body, EmployeeSelfUpdateRequest):
            if not self._is_self(actor, employee):
                raise EmployeeError("Insufficient permissions", 403)
            if body.phone is None:
                raise EmployeeError("No fields to update", 400)
            update_fields: dict[str, Any] = {"phone": body.phone}
        else:
            self._require_hr_or_admin(actor)
            update_fields = body.model_dump(exclude_unset=True)
            if not update_fields:
                raise EmployeeError("No fields to update", 400)

            if "join_date" in update_fields and update_fields["join_date"] > date.today():
                raise EmployeeError("join_date cannot be in the future", 400)

            new_code = update_fields.get("employee_code")
            if new_code is not None and new_code != employee.employee_code:
                await self._validate_unique_code(new_code, exclude_id=employee_id)

            new_email = update_fields.get("email")
            if new_email is not None and new_email != employee.email:
                await self._validate_unique_email(new_email, exclude_id=employee_id)

            department_id = update_fields.get("department_id", employee.department_id)
            designation_id = update_fields.get("designation_id", employee.designation_id)
            status_id = update_fields.get(
                "employment_status_id",
                employee.employment_status_id,
            )
            manager_id = update_fields.get("manager_id", employee.manager_id)
            await self._validate_foreign_keys(
                department_id=department_id,
                designation_id=designation_id,
                employment_status_id=status_id,
                manager_id=manager_id,
                employee_id=employee_id,
            )

        before_state = self._audit_snapshot(employee)
        updated = await self._repository.update_employee(employee_id, **update_fields)
        if updated is None:
            raise EmployeeError("Employee not found", 404)

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="employee_update",
            resource_id=employee_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=self._audit_snapshot(updated),
        )
        await self._session.commit()

        return self._to_response(
            updated,
            include_salary=self._can_view_salary(actor.roles),
        )

    async def deactivate_employee(
        self,
        employee_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> None:
        if SYSTEM_ADMINISTRATOR not in actor.roles:
            raise EmployeeError("Insufficient permissions", 403)

        employee = await self._get_employee_or_404(employee_id)
        before_state = self._audit_snapshot(employee)

        deleted = await self._repository.soft_delete_employee(employee_id)
        if not deleted:
            raise EmployeeError("Employee not found", 404)

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="employee_deactivate",
            resource_id=employee_id,
            ip_address=ip_address,
            before_state=before_state,
        )
        await self._session.commit()

    async def get_profile(
        self,
        employee_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> EmployeeProfileResponse:
        employee = await self._get_employee_or_404(employee_id)
        if not (
            self._is_self(actor, employee)
            or self._is_hr_or_admin(actor)
        ):
            raise EmployeeError("Insufficient permissions", 403)

        return EmployeeProfileResponse(
            **self._to_response(
                employee,
                include_salary=self._can_view_salary(actor.roles),
            ).model_dump(),
        )

    async def get_manager(
        self,
        employee_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> ManagerDetailResponse | None:
        employee = await self._get_employee_or_404(employee_id)
        await self._ensure_can_read(actor, employee)

        if employee.manager is None:
            return None

        manager = employee.manager
        return ManagerDetailResponse(
            id=manager.id,
            full_name=self._full_name(manager),
            employee_code=manager.employee_code,
            designation=DesignationRef(
                id=manager.designation.id,
                title=manager.designation.title,
            ),
            department=DepartmentRef(
                id=manager.department.id,
                name=manager.department.name,
            ),
        )

    async def get_direct_reports(
        self,
        employee_id: uuid.UUID,
        *,
        actor: CurrentUser,
        page: int,
        page_size: int,
    ) -> DirectReportsResponse:
        employee = await self._get_employee_or_404(employee_id)
        await self._ensure_can_read(actor, employee)

        reports, total = await self._repository.get_direct_reports(
            employee_id,
            page=page,
            page_size=page_size,
        )
        include_salary = self._can_view_salary(actor.roles)
        return DirectReportsResponse(
            items=[
                self._to_response(report, include_salary=include_salary)
                for report in reports
            ],
            pagination=build_pagination(page, page_size, total),
        )

    async def search_employees(
        self,
        query: str,
        *,
        actor: CurrentUser,
        limit: int = 20,
    ) -> EmployeeSearchResponse:
        if not query.strip():
            raise EmployeeError("Search query is required", 400)

        if not (
            self._is_hr_or_admin(actor) or DEPARTMENT_MANAGER in actor.roles
        ):
            raise EmployeeError("Insufficient permissions", 403)

        department_filter: uuid.UUID | None = None
        if DEPARTMENT_MANAGER in actor.roles and not self._is_hr_or_admin(actor):
            manager_record = await self._repository.get_employee_by_user_id(actor.id)
            if manager_record is None:
                raise EmployeeError("Employee profile not found", 404)
            department_filter = manager_record.department_id

        employees = await self._repository.search_employees(
            query,
            limit=limit,
            department_id=department_filter,
        )
        return EmployeeSearchResponse(
            items=[
                EmployeeSearchItem(
                    id=employee.id,
                    full_name=self._full_name(employee),
                    employee_code=employee.employee_code,
                    department=DepartmentRef(
                        id=employee.department.id,
                        name=employee.department.name,
                    ),
                )
                for employee in employees
            ],
        )

    async def _resolve_list_scope(
        self,
        actor: CurrentUser,
    ) -> tuple[str, uuid.UUID | None]:
        if self._is_hr_or_admin(actor):
            return "all", None
        if DEPARTMENT_MANAGER in actor.roles:
            manager_record = await self._repository.get_employee_by_user_id(actor.id)
            if manager_record is None:
                raise EmployeeError("Employee profile not found", 404)
            return "department", manager_record.department_id
        if EMPLOYEE in actor.roles:
            return "own", None
        raise EmployeeError("Insufficient permissions", 403)

    async def _validate_unique_code(
        self,
        employee_code: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        existing = await self._repository.get_employee_by_code(employee_code)
        if existing is not None and existing.id != exclude_id:
            raise EmployeeError("Employee code already exists", 409)

    async def _validate_unique_email(
        self,
        email: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        existing = await self._repository.get_employee_by_email(email)
        if existing is not None and existing.id != exclude_id:
            raise EmployeeError("Employee email already exists", 409)

    async def _validate_foreign_keys(
        self,
        *,
        department_id: uuid.UUID,
        designation_id: uuid.UUID,
        employment_status_id: uuid.UUID,
        manager_id: uuid.UUID | None,
        employee_id: uuid.UUID | None = None,
    ) -> None:
        if await self._repository.get_department_by_id(department_id) is None:
            raise EmployeeError("Invalid department_id", 400)

        if await self._repository.get_designation_by_id(designation_id) is None:
            raise EmployeeError("Invalid designation_id", 400)

        if (
            await self._repository.get_employment_status_by_id(employment_status_id)
            is None
        ):
            raise EmployeeError("Invalid employment_status_id", 400)

        if manager_id is None:
            return

        if employee_id is not None and manager_id == employee_id:
            raise EmployeeError("Employee cannot be their own manager", 400)

        manager = await self._repository.get_employee_by_id(manager_id)
        if manager is None:
            raise EmployeeError("Invalid manager_id", 400)

        if not await self._repository.is_manager_active(manager_id):
            raise EmployeeError("Manager must be an active employee", 400)

    async def _get_employee_or_404(self, employee_id: uuid.UUID) -> Employee:
        employee = await self._repository.get_employee_by_id(employee_id)
        if employee is None:
            raise EmployeeError("Employee not found", 404)
        return employee

    async def _ensure_can_read(self, actor: CurrentUser, employee: Employee) -> None:
        if self._is_hr_or_admin(actor):
            return
        if self._is_self(actor, employee):
            return
        if DEPARTMENT_MANAGER in actor.roles:
            manager_record = await self._repository.get_employee_by_user_id(actor.id)
            if (
                manager_record is not None
                and manager_record.department_id == employee.department_id
            ):
                return
        raise EmployeeError("Insufficient permissions", 403)

    async def _create_password_reset_token(self, user_id: uuid.UUID) -> str:
        raw_token = generate_opaque_token()
        expires_at = datetime.now(UTC) + timedelta(
            hours=self._settings.password_reset_expire_hours,
        )
        await self._auth_repository.invalidate_unused_password_resets(user_id)
        await self._auth_repository.create_password_reset_token(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )
        return raw_token

    def _full_name(self, employee: Employee) -> str:
        return f"{employee.first_name} {employee.last_name}".strip()

    def _can_view_salary(self, roles: list[str]) -> bool:
        return bool({HR_MANAGER, SYSTEM_ADMINISTRATOR}.intersection(roles))

    def _is_hr_or_admin(self, actor: CurrentUser) -> bool:
        return bool({HR_MANAGER, SYSTEM_ADMINISTRATOR}.intersection(actor.roles))

    def _require_hr_or_admin(self, actor: CurrentUser) -> None:
        if not self._is_hr_or_admin(actor):
            raise EmployeeError("Insufficient permissions", 403)

    def _is_self(self, actor: CurrentUser, employee: Employee) -> bool:
        return employee.user_id is not None and employee.user_id == actor.id

    def _audit_snapshot(self, employee: Employee) -> dict[str, Any]:
        return {
            "employee_code": employee.employee_code,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "email": employee.email,
            "phone": employee.phone,
            "department_id": str(employee.department_id),
            "designation_id": str(employee.designation_id),
            "employment_status_id": str(employee.employment_status_id),
            "manager_id": str(employee.manager_id) if employee.manager_id else None,
            "salary": str(employee.salary) if employee.salary is not None else None,
            "join_date": employee.join_date.isoformat(),
        }

    def _to_response(
        self,
        employee: Employee,
        *,
        include_salary: bool,
    ) -> EmployeeResponse:
        manager_ref = None
        if employee.manager is not None:
            manager_ref = ManagerRef(
                id=employee.manager.id,
                name=self._full_name(employee.manager),
                employee_code=employee.manager.employee_code,
            )

        return EmployeeResponse(
            id=employee.id,
            user_id=employee.user_id,
            employee_code=employee.employee_code,
            first_name=employee.first_name,
            last_name=employee.last_name,
            full_name=self._full_name(employee),
            email=employee.email,
            phone=employee.phone,
            department=DepartmentRef(
                id=employee.department.id,
                name=employee.department.name,
            ),
            designation=DesignationRef(
                id=employee.designation.id,
                title=employee.designation.title,
            ),
            employment_status=EmploymentStatusRef(
                id=employee.employment_status.id,
                name=employee.employment_status.name,
            ),
            manager=manager_ref,
            salary=employee.salary if include_salary else None,
            join_date=employee.join_date,
            created_at=employee.created_at,
            updated_at=employee.updated_at,
        )

    def _to_create_response(
        self,
        employee: Employee,
        reset_token: str | None,
        *,
        include_salary: bool,
    ) -> CreateEmployeeResponse:
        base = self._to_response(employee, include_salary=include_salary)
        return CreateEmployeeResponse(
            **base.model_dump(),
            password_reset_token=reset_token,
        )
