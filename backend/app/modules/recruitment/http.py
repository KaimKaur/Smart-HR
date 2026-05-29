from fastapi import HTTPException

from app.modules.recruitment.errors import RecruitmentError


def recruitment_http_exception(exc: RecruitmentError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "errors": []},
    )
