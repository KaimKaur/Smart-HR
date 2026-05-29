import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.model import Permission, Role, RolePermission, UserRole
from app.modules.notifications.model import AuditLog
from app.modules.user.model import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        is_active: bool = False,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            is_active=is_active,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_user_by_id(
        self,
        user_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> User | None:
        query = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
        )
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        email: str,
        *,
        include_deleted: bool = False,
    ) -> User | None:
        query = (
            select(User)
            .where(User.email == email)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
        )
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        *,
        search: str | None,
        page: int,
        page_size: int,
        include_deleted: bool = False,
    ) -> tuple[list[User], int]:
        query = select(User).options(
            selectinload(User.user_roles).selectinload(UserRole.role),
        )
        count_query = select(func.count()).select_from(User)

        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
            count_query = count_query.where(User.deleted_at.is_(None))

        if search:
            pattern = f"%{search.strip()}%"
            filter_clause = User.email.ilike(pattern)
            query = query.where(filter_clause)
            count_query = count_query.where(filter_clause)

        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    async def update_user(
        self,
        user_id: uuid.UUID,
        *,
        email: str | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        values: dict = {"updated_at": datetime.now(UTC)}
        if email is not None:
            values["email"] = email
        if is_active is not None:
            values["is_active"] = is_active

        await self._session.execute(
            update(User).where(User.id == user_id, User.deleted_at.is_(None)).values(**values)
        )
        return await self.get_user_by_id(user_id)

    async def soft_delete_user(self, user_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            update(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), is_active=False, updated_at=datetime.now(UTC))
        )
        return result.rowcount > 0

    async def get_role_by_id(self, role_id: uuid.UUID) -> Role | None:
        result = await self._session.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_role_by_name(self, role_name: str) -> Role | None:
        result = await self._session.execute(select(Role).where(Role.name == role_name))
        return result.scalar_one_or_none()

    async def assign_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> UserRole:
        assignment = UserRole(user_id=user_id, role_id=role_id)
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def get_user_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> UserRole | None:
        result = await self._session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        return result.scalar_one_or_none()

    async def remove_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        assignment = await self.get_user_role(user_id, role_id)
        if assignment is None:
            return False
        await self._session.delete(assignment)
        await self._session.flush()
        return True

    async def get_user_role_names(self, user_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_user_permissions(self, user_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .distinct()
            .order_by(Permission.name)
        )
        return list(result.scalars().all())

    async def create_audit_log(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        resource_type: str = "user",
        resource_id: uuid.UUID | None = None,
        ip_address: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=after_state,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
