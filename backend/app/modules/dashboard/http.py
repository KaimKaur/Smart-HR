from fastapi import HTTPException

from app.modules.dashboard.errors import DashboardError


def dashboard_http_exception(exc: DashboardError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": []},
    )

