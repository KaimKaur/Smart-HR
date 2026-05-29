from fastapi import HTTPException

from app.modules.performance.errors import PerformanceError


def performance_http_exception(exc: PerformanceError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": []},
    )

