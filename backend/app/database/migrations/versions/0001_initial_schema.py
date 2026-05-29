"""Initial schema from docs/schema.sql (DDL only).

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-26

"""

from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SQL_PATH = Path(__file__).resolve().parents[1] / "sql" / "initial_schema.sql"

TABLES_IN_DEPENDENCY_ORDER = [
    "audit_logs",
    "notification_preferences",
    "notifications",
    "performance_feedback",
    "employee_metric_scores",
    "performance_metrics",
    "performance_reviews",
    "performance_cycles",
    "leave_approvals",
    "leave_requests",
    "leave_balances",
    "leave_types",
    "attendance_corrections",
    "attendance_records",
    "attendance_statuses",
    "interviews",
    "candidate_notes",
    "resume_analysis",
    "resume_files",
    "candidate_status_history",
    "candidate_applications",
    "candidates",
    "job_skills",
    "jobs",
    "employees",
    "employment_statuses",
    "designations",
    "departments",
    "password_reset_tokens",
    "refresh_tokens",
    "role_permissions",
    "user_roles",
    "permissions",
    "roles",
    "users",
]


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []

    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        buffer.append(line)
        if line.rstrip().endswith(";"):
            statement = "\n".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []

    trailing = "\n".join(buffer).strip()
    if trailing:
        statements.append(trailing)

    return statements


def upgrade() -> None:
    ddl = SQL_PATH.read_text(encoding="utf-8-sig")
    for statement in _split_sql_statements(ddl):
        op.execute(sa.text(statement))


def downgrade() -> None:
    for table in TABLES_IN_DEPENDENCY_ORDER:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table} CASCADE"))
    op.execute(sa.text("DROP EXTENSION IF EXISTS pgcrypto"))
