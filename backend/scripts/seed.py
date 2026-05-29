"""Idempotent database seed for Smart HR reference data and bootstrap admin."""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from passlib.context import CryptContext
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.constants import ALL_ROLES, SYSTEM_ADMINISTRATOR  # noqa: E402
from app.core.database import get_session_factory  # noqa: E402
from app.database.models import Role, User, UserRole  # noqa: E402

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ADMIN_EMAIL = "admin@smarthr.dev"
ADMIN_PASSWORD = "ChangeMe123!"

DEPARTMENTS = (
    ("Engineering", "Product engineering teams"),
    ("Human Resources", "People operations"),
    ("Sales", "Revenue and customer growth"),
)

DESIGNATIONS = (
    ("Software Engineer", "Builds product features"),
    ("HR Manager", "Leads HR operations"),
    ("Sales Executive", "Owns customer accounts"),
)

EMPLOYMENT_STATUSES = ("active", "inactive", "on_leave")
ATTENDANCE_STATUSES = ("present", "absent", "late", "half_day", "holiday")
LEAVE_TYPES = (("annual", 20), ("sick", 10), ("casual", 5))


async def seed_roles(session: AsyncSession) -> dict[str, uuid.UUID]:
    for role_name in ALL_ROLES:
        await session.execute(
            insert(Role)
            .values(
                id=uuid.uuid4(),
                name=role_name,
                description=f"{role_name.replace('_', ' ').title()} role",
            )
            .on_conflict_do_nothing(index_elements=[Role.name])
        )

    result = await session.execute(select(Role.id, Role.name).where(Role.name.in_(ALL_ROLES)))
    return {name: role_id for role_id, name in result.all()}


async def seed_departments(session: AsyncSession) -> None:
    for name, description in DEPARTMENTS:
        await session.execute(
            text(
                """
                INSERT INTO departments (id, name, description)
                VALUES (gen_random_uuid(), :name, :description)
                ON CONFLICT (name) DO NOTHING
                """
            ),
            {"name": name, "description": description},
        )


async def seed_designations(session: AsyncSession) -> None:
    for title, description in DESIGNATIONS:
        await session.execute(
            text(
                """
                INSERT INTO designations (id, title, description)
                VALUES (gen_random_uuid(), :title, :description)
                ON CONFLICT (title) DO NOTHING
                """
            ),
            {"title": title, "description": description},
        )


async def seed_employment_statuses(session: AsyncSession) -> None:
    for name in EMPLOYMENT_STATUSES:
        await session.execute(
            text(
                """
                INSERT INTO employment_statuses (id, name)
                VALUES (gen_random_uuid(), :name)
                ON CONFLICT (name) DO NOTHING
                """
            ),
            {"name": name},
        )


async def seed_attendance_statuses(session: AsyncSession) -> None:
    for name in ATTENDANCE_STATUSES:
        await session.execute(
            text(
                """
                INSERT INTO attendance_statuses (id, name)
                VALUES (gen_random_uuid(), :name)
                ON CONFLICT (name) DO NOTHING
                """
            ),
            {"name": name},
        )


async def seed_leave_types(session: AsyncSession) -> None:
    for name, annual_allocation in LEAVE_TYPES:
        await session.execute(
            text(
                """
                INSERT INTO leave_types (id, name, annual_allocation)
                VALUES (gen_random_uuid(), :name, :annual_allocation)
                ON CONFLICT (name) DO NOTHING
                """
            ),
            {"name": name, "annual_allocation": annual_allocation},
        )


async def seed_admin_user(session: AsyncSession, role_ids: dict[str, uuid.UUID]) -> None:
    existing = await session.execute(select(User.id).where(User.email == ADMIN_EMAIL))
    user_id = existing.scalar_one_or_none()

    if user_id is None:
        user_id = uuid.uuid4()
        await session.execute(
            insert(User).values(
                id=user_id,
                email=ADMIN_EMAIL,
                password_hash=pwd_context.hash(ADMIN_PASSWORD),
                is_active=True,
            )
        )
    else:
        await session.execute(
            text(
                """
                UPDATE users
                SET password_hash = :password_hash, is_active = TRUE, deleted_at = NULL
                WHERE email = :email
                """
            ),
            {
                "email": ADMIN_EMAIL,
                "password_hash": pwd_context.hash(ADMIN_PASSWORD),
            },
        )

    admin_role_id = role_ids[SYSTEM_ADMINISTRATOR]
    await session.execute(
        insert(UserRole)
        .values(user_id=user_id, role_id=admin_role_id)
        .on_conflict_do_nothing()
    )


async def run_seed() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        async with session.begin():
            role_ids = await seed_roles(session)
            await seed_departments(session)
            await seed_designations(session)
            await seed_employment_statuses(session)
            await seed_attendance_statuses(session)
            await seed_leave_types(session)
            await seed_admin_user(session, role_ids)


def main() -> None:
    asyncio.run(run_seed())
    print("Seed completed successfully.")


if __name__ == "__main__":
    main()
