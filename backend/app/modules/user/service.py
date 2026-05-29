import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import SYSTEM_ADMINISTRATOR
from app.core.security import generate_opaque_token, hash_password, hash_token
from app.modules.auth.repository import AuthRepository
from app.modules.user.errors import UserError
from app.modules.user.repository import UserRepository
from app.modules.user.schema import (
    AssignRoleRequest,
    CreateUserRequest,
    CreateUserResponse,
    PermissionResponse,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
    build_pagination,
)


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        repository: UserRepository | None = None,
        auth_repository: AuthRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or UserRepository(session)
        self._auth_repository = auth_repository or AuthRepository(session)
        self._settings = settings or get_settings()

    async def create_user(
        self,
        body: CreateUserRequest,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> CreateUserResponse:
        existing = await self._repository.get_user_by_email(
            body.email,
            include_deleted=True,
        )
        if existing is not None:
            raise UserError("Email already exists", 409)

        placeholder_password = hash_password(secrets.token_urlsafe(32))
        user = await self._repository.create_user(
            email=body.email,
            password_hash=placeholder_password,
            is_active=body.is_active,
        )

        for role_name in body.roles:
            role = await self._repository.get_role_by_name(role_name)
            if role is None:
                raise UserError(f"Unknown role: {role_name}", 400)
            await self._repository.assign_role(user.id, role.id)

        reset_token = await self._create_password_reset_token(user.id)

        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="user_create",
            resource_id=user.id,
            ip_address=ip_address,
            after_state={"email": user.email, "roles": body.roles},
        )
        await self._session.commit()

        refreshed = await self._repository.get_user_by_id(user.id)
        assert refreshed is not None
        return self._to_create_response(refreshed, reset_token)

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise UserError("User not found", 404)
        return self._to_response(user)

    async def list_users(
        self,
        *,
        search: str | None,
        page: int,
        page_size: int,
        include_deleted: bool = False,
    ) -> UserListResponse:
        users, total_items = await self._repository.list_users(
            search=search,
            page=page,
            page_size=page_size,
            include_deleted=include_deleted,
        )
        return UserListResponse(
            items=[self._to_response(user) for user in users],
            pagination=build_pagination(page, page_size, total_items),
        )

    async def update_user(
        self,
        user_id: uuid.UUID,
        body: UpdateUserRequest,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> UserResponse:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise UserError("User not found", 404)

        if body.is_active is False and user_id == actor_user_id:
            raise UserError("Cannot deactivate your own account", 400)

        if body.email is not None and body.email != user.email:
            duplicate = await self._repository.get_user_by_email(
                body.email,
                include_deleted=True,
            )
            if duplicate is not None and duplicate.id != user_id:
                raise UserError("Email already exists", 409)

        before_state = {
            "email": user.email,
            "is_active": user.is_active,
        }
        updated = await self._repository.update_user(
            user_id,
            email=body.email,
            is_active=body.is_active,
        )
        if updated is None:
            raise UserError("User not found", 404)

        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="user_update",
            resource_id=user_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state={"email": updated.email, "is_active": updated.is_active},
        )
        await self._session.commit()
        return self._to_response(updated)

    async def soft_delete_user(
        self,
        user_id: uuid.UUID,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> None:
        if user_id == actor_user_id:
            raise UserError("Cannot deactivate your own account", 400)

        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise UserError("User not found", 404)

        deleted = await self._repository.soft_delete_user(user_id)
        if not deleted:
            raise UserError("User not found", 404)

        await self._auth_repository.revoke_all_refresh_tokens_for_user(user_id)
        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="user_deactivate",
            resource_id=user_id,
            ip_address=ip_address,
            before_state={"email": user.email},
        )
        await self._session.commit()

    async def assign_role(
        self,
        user_id: uuid.UUID,
        body: AssignRoleRequest,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> UserResponse:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise UserError("User not found", 404)

        role = await self._repository.get_role_by_name(body.role)
        if role is None:
            raise UserError(f"Unknown role: {body.role}", 400)

        existing = await self._repository.get_user_role(user_id, role.id)
        if existing is not None:
            raise UserError("Role already assigned to user", 409)

        await self._repository.assign_role(user_id, role.id)
        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="user_role_assign",
            resource_id=user_id,
            ip_address=ip_address,
            after_state={"role": body.role},
        )
        await self._session.commit()

        refreshed = await self._repository.get_user_by_id(user_id)
        assert refreshed is not None
        return self._to_response(refreshed)

    async def remove_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        *,
        actor_user_id: uuid.UUID,
        ip_address: str,
    ) -> UserResponse:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise UserError("User not found", 404)

        role = await self._repository.get_role_by_id(role_id)
        if role is None:
            raise UserError("Role not found", 404)

        if user_id == actor_user_id and role.name == SYSTEM_ADMINISTRATOR:
            raise UserError("Cannot remove your own administrator role", 400)

        removed = await self._repository.remove_role(user_id, role_id)
        if not removed:
            raise UserError("Role is not assigned to this user", 404)

        await self._repository.create_audit_log(
            actor_user_id=actor_user_id,
            action="user_role_remove",
            resource_id=user_id,
            ip_address=ip_address,
            after_state={"role": role.name},
        )
        await self._session.commit()

        refreshed = await self._repository.get_user_by_id(user_id)
        assert refreshed is not None
        return self._to_response(refreshed)

    async def get_permissions(self, user_id: uuid.UUID) -> PermissionResponse:
        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise UserError("User not found", 404)
        permissions = await self._repository.get_user_permissions(user_id)
        return PermissionResponse(permissions=permissions)

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

    def _role_names(self, user) -> list[str]:
        return [user_role.role.name for user_role in user.user_roles]

    def _to_response(self, user) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            roles=self._role_names(user),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _to_create_response(self, user, reset_token: str) -> CreateUserResponse:
        base = self._to_response(user)
        return CreateUserResponse(
            **base.model_dump(),
            password_reset_token=reset_token,
        )
