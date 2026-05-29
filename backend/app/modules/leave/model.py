from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
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

LEAVE_DATES_CHECK = "end_date >= start_date"
LEAVE_STATUS_CHECK = "status IN ('pending','approved','rejected','cancelled')"
BALANCE_NON_NEGATIVE_CHECK = "balance >= 0"


class LeaveType(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "leave_types"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    annual_allocation: Mapped[int] = mapped_column(Integer, nullable=False)

    balances: Mapped[list[LeaveBalance]] = relationship(back_populates="leave_type")
    requests: Mapped[list[LeaveRequest]] = relationship(back_populates="leave_type")


class LeaveBalance(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "leave_balances"
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type_id"),
        CheckConstraint(BALANCE_NON_NEGATIVE_CHECK, name="chk_balance_non_negative"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    leave_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leave_types.id"), nullable=False
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    employee: Mapped[Employee] = relationship()
    leave_type: Mapped[LeaveType] = relationship(back_populates="balances")
    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by])


class LeaveRequest(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "leave_requests"
    __table_args__ = (
        CheckConstraint(LEAVE_DATES_CHECK, name="chk_leave_dates"),
        CheckConstraint(LEAVE_STATUS_CHECK, name="chk_leave_status"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    leave_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leave_types.id"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    employee: Mapped[Employee] = relationship()
    leave_type: Mapped[LeaveType] = relationship(back_populates="requests")
    approvals: Mapped[list[LeaveApproval]] = relationship(back_populates="leave_request")
    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by])


class LeaveApproval(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "leave_approvals"

    leave_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leave_requests.id"), nullable=False
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    approval_level: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    leave_request: Mapped[LeaveRequest] = relationship(back_populates="approvals")
    approver: Mapped[User] = relationship()
