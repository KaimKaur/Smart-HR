from fastapi import HTTPException

from app.modules.organization.errors import OrganizationError


def organization_http_exception(exc: OrganizationError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": []},
    )
