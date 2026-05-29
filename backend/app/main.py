from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.exceptions import register_exception_handlers
from app.core.schemas import SuccessResponse
from app.modules.attendance.routes import router as attendance_router
from app.modules.auth.routes import router as auth_router
from app.modules.audit_logs.routes import router as audit_logs_router
from app.modules.user.routes import router as user_router
from app.modules.employee.routes import router as employee_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.organization.department_routes import router as department_router
from app.modules.organization.designation_routes import router as designation_router
from app.modules.organization.status_routes import (
    attendance_router as attendance_status_router,
    employment_router as employment_status_router,
)
from app.modules.leave.leave_type_routes import router as leave_type_router
from app.modules.leave.routes import router as leave_router
from app.modules.notifications.routes import router as notifications_router
from app.modules.performance.routes import router as performance_router
from app.modules.recruitment.application_routes import router as application_router
from app.modules.recruitment.candidate_routes import router as candidate_router
from app.modules.recruitment.interview_routes import router as interview_router
from app.modules.recruitment.job_routes import router as job_router
from app.modules.reporting.recruitment_report_routes import (
    router as recruitment_report_router,
)
from app.modules.reporting.routes import router as reporting_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Smart HR API",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)

    application.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    application.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
    application.include_router(
        employee_router, prefix="/api/v1/employees", tags=["Employees"]
    )
    application.include_router(
        department_router, prefix="/api/v1/departments", tags=["Departments"]
    )
    application.include_router(
        designation_router, prefix="/api/v1/designations", tags=["Designations"]
    )
    application.include_router(
        employment_status_router,
        prefix="/api/v1/employment-statuses",
        tags=["Employment Statuses"],
    )
    application.include_router(
        attendance_status_router,
        prefix="/api/v1/attendance-statuses",
        tags=["Attendance Statuses"],
    )
    application.include_router(job_router, prefix="/api/v1/jobs", tags=["Jobs"])
    application.include_router(
        candidate_router,
        prefix="/api/v1/candidates",
        tags=["Candidates"],
    )
    application.include_router(
        application_router,
        prefix="/api/v1/applications",
        tags=["Applications"],
    )
    application.include_router(
        interview_router,
        prefix="/api/v1/interviews",
        tags=["Interviews"],
    )
    application.include_router(
        attendance_router, prefix="/api/v1/attendance", tags=["Attendance"]
    )
    application.include_router(leave_router, prefix="/api/v1/leave", tags=["Leave"])
    application.include_router(
        leave_type_router,
        prefix="/api/v1/leave-types",
        tags=["Leave Types"],
    )
    application.include_router(
        performance_router, prefix="/api/v1/performance", tags=["Performance"]
    )
    application.include_router(
        reporting_router, prefix="/api/v1/reports", tags=["Reporting"]
    )
    application.include_router(
        recruitment_report_router,
        prefix="/api/v1/reports",
        tags=["Reporting"],
    )
    application.include_router(
        notifications_router,
        prefix="/api/v1/notifications",
        tags=["Notifications"],
    )
    application.include_router(
        dashboard_router,
        prefix="/api/v1/dashboard",
        tags=["Dashboard"],
    )
    application.include_router(
        audit_logs_router,
        prefix="/api/v1/audit-logs",
        tags=["Audit Logs"],
    )

    @application.get("/api/v1/health", tags=["Health"])
    async def health_check() -> SuccessResponse[None]:
        return SuccessResponse(message="OK", data=None)

    return application


app = create_app()
