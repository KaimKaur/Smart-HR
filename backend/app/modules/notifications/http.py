from fastapi import HTTPException

from app.modules.notifications.errors import NotificationsError


def notifications_http_exception(exc: NotificationsError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": []},
    )

