from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEPARTMENT_MANAGER, HR_MANAGER, RECRUITER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.recruitment.controller import ApplicationController
from app.modules.recruitment.schema import (
    ApplicationListResponse,
    ApplicationResponse,
    CandidateStatusUpdateRequest,
    CandidateTimelineResponse,
    CreateApplicationRequest,
)
from app.modules.recruitment.screening_schema import (
    MatchExplanationResponse,
    ScreeningResultResponse,
)

router = APIRouter()

_recruiter_or_hr = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER, RECRUITER)
_read_staff = require_roles(
    SYSTEM_ADMINISTRATOR,
    HR_MANAGER,
    RECRUITER,
    DEPARTMENT_MANAGER,
)


def _controller(session: AsyncSession = Depends(get_db)) -> ApplicationController:
    return ApplicationController(session)


@router.post(
    "",
    response_model=SuccessResponse[ApplicationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    body: CreateApplicationRequest,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: ApplicationController = Depends(_controller),
) -> SuccessResponse[ApplicationResponse]:
    return await controller.create_application(body, current_user, request)


@router.get("", response_model=SuccessResponse[ApplicationListResponse])
async def list_applications(
    job_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_read_staff),
    controller: ApplicationController = Depends(_controller),
) -> SuccessResponse[ApplicationListResponse]:
    return await controller.list_applications(
        current_user,
        job_id=job_id,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/{application_id}", response_model=SuccessResponse[ApplicationResponse])
async def get_application(
    application_id: UUID,
    current_user: CurrentUser = Depends(_read_staff),
    controller: ApplicationController = Depends(_controller),
) -> SuccessResponse[ApplicationResponse]:
    return await controller.get_application(application_id, current_user)


@router.patch("/{application_id}/status", response_model=SuccessResponse[ApplicationResponse])
async def update_application_status(
    application_id: UUID,
    body: CandidateStatusUpdateRequest,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: ApplicationController = Depends(_controller),
) -> SuccessResponse[ApplicationResponse]:
    return await controller.update_status(
        application_id,
        body,
        current_user,
        request,
    )


@router.get("/{application_id}/timeline", response_model=SuccessResponse[CandidateTimelineResponse])
async def application_timeline(
    application_id: UUID,
    current_user: CurrentUser = Depends(_read_staff),
    controller: ApplicationController = Depends(_controller),
) -> SuccessResponse[CandidateTimelineResponse]:
    return await controller.timeline(application_id, current_user)


@router.post("/{application_id}/shortlist", response_model=SuccessResponse[ApplicationResponse])
async def shortlist_application(
    application_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: ApplicationController = Depends(_controller),
) -> SuccessResponse[ApplicationResponse]:
    return await controller.shortlist(application_id, current_user, request)


@router.post("/{application_id}/reject", response_model=SuccessResponse[ApplicationResponse])
async def reject_application(
    application_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: ApplicationController = Depends(_controller),
) -> SuccessResponse[ApplicationResponse]:
    return await controller.reject(application_id, current_user, request)


@router.post(
    "/{application_id}/screen",
    response_model=SuccessResponse[ScreeningResultResponse],
)
async def screen_application(
    application_id: UUID,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: ApplicationController = Depends(_controller),
) -> SuccessResponse[ScreeningResultResponse]:
    return await controller.screen_application(application_id, current_user)


@router.get(
    "/{application_id}/match-explanation",
    response_model=SuccessResponse[MatchExplanationResponse],
)
async def match_explanation(
    application_id: UUID,
    current_user: CurrentUser = Depends(_read_staff),
    controller: ApplicationController = Depends(_controller),
) -> SuccessResponse[MatchExplanationResponse]:
    return await controller.match_explanation(application_id, current_user)
