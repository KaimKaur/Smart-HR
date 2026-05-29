from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.database.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

CORRECTION_STATUS_CHECK = "correction_status IN ('pending','approved','rejected')"


class AttendanceStatus(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "attendance_statuses"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    records: Mapped[list[AttendanceRecord]] = relationship(back_populates="status")
    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by])


class AttendanceRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "attendance_date",
            name="uq_employee_attendance",
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_in_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    work_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    attendance_status_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_statuses.id"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    employee: Mapped[Employee] = relationship()
    status: Mapped[AttendanceStatus] = relationship(back_populates="records")
    corrections: Mapped[list[AttendanceCorrection]] = relationship(
        back_populates="attendance_record",
    )
    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by])


class AttendanceCorrection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "attendance_corrections"
    __table_args__ = (
        CheckConstraint(CORRECTION_STATUS_CHECK, name="chk_correction_status"),
    )

    attendance_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attendance_records.id"),
        nullable=False,
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    correction_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attendance_record: Mapped[AttendanceRecord] = relationship(
        back_populates="corrections",
    )
    requester: Mapped[User] = relationship(foreign_keys=[requested_by])
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by])
