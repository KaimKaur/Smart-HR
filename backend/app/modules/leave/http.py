from fastapi import HTTPException

from app.core.schemas import ErrorDetail
from app.modules.leave.errors import LeaveError


def leave_http_exception(exc: LeaveError) -> HTTPException:
    errors = [
        ErrorDetail(field=item.get("field"), message=str(item.get("message", "Error")))
        for item in exc.errors
    ]
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": [e.model_dump() for e in errors]},
    )
