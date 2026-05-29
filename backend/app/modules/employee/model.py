from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.database.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.user.model import User


class Department(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    employees: Mapped[list[Employee]] = relationship(back_populates="department")


class Designation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "designations"

    title: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    employees: Mapped[list[Employee]] = relationship(back_populates="designation")


class EmploymentStatus(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "employment_statuses"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    employees: Mapped[list[Employee]] = relationship(back_populates="employment_status")
    created_by_user: Mapped[User | None] = relationship(
        foreign_keys=[created_by],
    )
    updated_by_user: Mapped[User | None] = relationship(
        foreign_keys=[updated_by],
    )


class Employee(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "employees"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True
    )
    employee_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False
    )
    designation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designations.id"), nullable=False
    )
    employment_status_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employment_statuses.id"), nullable=False
    )
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id")
    )
    salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    join_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User | None] = relationship()
    department: Mapped[Department] = relationship(back_populates="employees")
    designation: Mapped[Designation] = relationship(back_populates="employees")
    employment_status: Mapped[EmploymentStatus] = relationship(
        back_populates="employees",
    )
    manager: Mapped[Employee | None] = relationship(
        "Employee",
        remote_side="Employee.id",
        back_populates="direct_reports",
        foreign_keys=[manager_id],
    )
    direct_reports: Mapped[list[Employee]] = relationship(
        "Employee",
        back_populates="manager",
        foreign_keys=[manager_id],
    )
