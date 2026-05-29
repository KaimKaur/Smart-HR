from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.schemas import ErrorDetail, ErrorResponse


def _error_payload(
    message: str,
    errors: list[ErrorDetail] | None = None,
) -> dict:
    return ErrorResponse(
        message=message,
        errors=errors or [],
    ).model_dump()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        detail = exc.detail
        errors: list[ErrorDetail] = []
        message = "Request failed"

        if isinstance(detail, dict):
            message = str(detail.get("message", message))
            raw_errors = detail.get("errors", [])
            if isinstance(raw_errors, list):
                for item in raw_errors:
                    if isinstance(item, dict):
                        errors.append(
                            ErrorDetail(
                                field=item.get("field"),
                                message=str(item.get("message", "Error")),
                            )
                        )
        elif isinstance(detail, str):
            message = detail

        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(message, errors),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            ErrorDetail(
                field=".".join(str(part) for part in error.get("loc", [])[1:]) or None,
                message=error.get("msg", "Invalid value"),
            )
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_payload("Validation failed", errors),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload("Internal server error"),
        )
