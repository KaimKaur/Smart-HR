from fastapi import HTTPException

from app.modules.attendance.errors import AttendanceError


def attendance_http_exception(exc: AttendanceError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": []},
    )
