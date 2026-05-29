from fastapi import HTTPException

from app.modules.audit_logs.errors import AuditLogsError


def audit_logs_http_exception(exc: AuditLogsError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)
