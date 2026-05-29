from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, require_roles
from app.modules.recruitment.controller import RecruitmentReportController
from app.modules.recruitment.schema import RecruitmentReportResponse

router = APIRouter()

_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)


def _controller(session: AsyncSession = Depends(get_db)) -> RecruitmentReportController:
    return RecruitmentReportController(session)


@router.get("/recruitment", response_model=SuccessResponse[RecruitmentReportResponse])
async def recruitment_report(
    job_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: RecruitmentReportController = Depends(_controller),
) -> SuccessResponse[RecruitmentReportResponse]:
    return await controller.recruitment_report(
        current_user,
        job_id=job_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
