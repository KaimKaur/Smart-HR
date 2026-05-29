"""Central model registry — import all ORM models for Alembic metadata and convenience."""

from app.modules.attendance.model import (
    AttendanceCorrection,
    AttendanceRecord,
    AttendanceStatus,
)
from app.modules.auth.model import (
    PasswordResetToken,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    UserRole,
)
from app.modules.employee.model import (
    Department,
    Designation,
    Employee,
    EmploymentStatus,
)
from app.modules.leave.model import LeaveApproval, LeaveBalance, LeaveRequest, LeaveType
from app.modules.notifications.model import AuditLog, Notification, NotificationPreference
from app.modules.performance.model import (
    EmployeeMetricScore,
    PerformanceCycle,
    PerformanceFeedback,
    PerformanceMetric,
    PerformanceReview,
)
from app.modules.recruitment.model import (
    Candidate,
    CandidateApplication,
    CandidateNote,
    CandidateStatusHistory,
    Interview,
    Job,
    JobSkill,
    ResumeAnalysis,
    ResumeFile,
)
from app.modules.user.model import User

__all__ = [
    "AttendanceCorrection",
    "AttendanceRecord",
    "AttendanceStatus",
    "AuditLog",
    "Candidate",
    "CandidateApplication",
    "CandidateNote",
    "CandidateStatusHistory",
    "Department",
    "Designation",
    "Employee",
    "EmployeeMetricScore",
    "EmploymentStatus",
    "Interview",
    "Job",
    "JobSkill",
    "LeaveApproval",
    "LeaveBalance",
    "LeaveRequest",
    "LeaveType",
    "Notification",
    "NotificationPreference",
    "PerformanceCycle",
    "PerformanceFeedback",
    "PerformanceMetric",
    "PerformanceReview",
    "PasswordResetToken",
    "Permission",
    "RefreshToken",
    "ResumeAnalysis",
    "ResumeFile",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
]
