import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employee.model import Designation
from app.modules.organization.designation_repository import DesignationRepository
from app.modules.organization.designation_schema import (
    CreateDesignationRequest,
    DesignationListResponse,
    DesignationResponse,
    UpdateDesignationRequest,
    build_pagination,
)
from app.modules.organization.errors import OrganizationError


class DesignationService:
    def __init__(
        self,
        session: AsyncSession,
        repository: DesignationRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or DesignationRepository(session)

    async def create_designation(
        self,
        body: CreateDesignationRequest,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> DesignationResponse:
        existing = await self._repository.get_designation_by_title(body.title)
        if existing is not None:
            raise OrganizationError("Designation title already exists", 409)

        designation = await self._repository.create_designation(
            title=body.title,
            description=body.description,
        )
        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="designation_create",
            resource_id=designation.id,
            ip_address=ip_address,
            after_state=self._audit_snapshot(designation),
        )
        await self._session.commit()

        return self._to_response(designation, employee_count=0)

    async def list_designations(
        self,
        *,
        page: int,
        page_size: int,
    ) -> DesignationListResponse:
        rows, total = await self._repository.list_designations(
            page=page,
            page_size=page_size,
        )
        return DesignationListResponse(
            items=[self._to_response(item, count) for item, count in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_designation(self, designation_id: uuid.UUID) -> DesignationResponse:
        row = await self._repository.get_designation_with_count(designation_id)
        if row is None:
            raise OrganizationError("Designation not found", 404)
        designation, count = row
        return self._to_response(designation, count)

    async def update_designation(
        self,
        designation_id: uuid.UUID,
        body: UpdateDesignationRequest,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> DesignationResponse:
        designation = await self._repository.get_designation_by_id(designation_id)
        if designation is None:
            raise OrganizationError("Designation not found", 404)

        payload = body.model_dump(exclude_unset=True)
        if not payload:
            raise OrganizationError("No fields to update", 400)

        new_title = payload.get("title")
        if new_title is not None and new_title != designation.title:
            duplicate = await self._repository.get_designation_by_title(new_title)
            if duplicate is not None and duplicate.id != designation_id:
                raise OrganizationError("Designation title already exists", 409)

        before_state = self._audit_snapshot(designation)
        updated = await self._repository.update_designation(designation_id, **payload)
        if updated is None:
            raise OrganizationError("Designation not found", 404)

        count = await self._repository.count_active_employees(designation_id)
        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="designation_update",
            resource_id=designation_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=self._audit_snapshot(updated),
        )
        await self._session.commit()

        return self._to_response(updated, count)

    async def delete_designation(
        self,
        designation_id: uuid.UUID,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> None:
        designation = await self._repository.get_designation_by_id(designation_id)
        if designation is None:
            raise OrganizationError("Designation not found", 404)

        employee_count = await self._repository.count_active_employees(designation_id)
        if employee_count > 0:
            raise OrganizationError(
                "Cannot delete designation with assigned employees",
                409,
            )

        before_state = self._audit_snapshot(designation)
        deleted = await self._repository.delete_designation(designation_id)
        if not deleted:
            raise OrganizationError("Designation not found", 404)

        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="designation_delete",
            resource_id=designation_id,
            ip_address=ip_address,
            before_state=before_state,
        )
        await self._session.commit()

    def _audit_snapshot(self, designation: Designation) -> dict:
        return {
            "title": designation.title,
            "description": designation.description,
        }

    def _to_response(
        self,
        designation: Designation,
        employee_count: int,
    ) -> DesignationResponse:
        return DesignationResponse(
            id=designation.id,
            title=designation.title,
            description=designation.description,
            employee_count=employee_count,
            created_at=designation.created_at,
            updated_at=designation.updated_at,
        )
