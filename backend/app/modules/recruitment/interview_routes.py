from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, RECRUITER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, require_roles
from app.modules.recruitment.controller import InterviewController
from app.modules.recruitment.schema import (
    InterviewListResponse,
    InterviewResponse,
    ScheduleInterviewRequest,
    UpdateInterviewRequest,
)

router = APIRouter()

_recruiter_or_hr = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER, RECRUITER)


def _controller(session: AsyncSession = Depends(get_db)) -> InterviewController:
    return InterviewController(session)


@router.post(
    "",
    response_model=SuccessResponse[InterviewResponse],
    status_code=status.HTTP_201_CREATED,
)
async def schedule_interview(
    body: ScheduleInterviewRequest,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: InterviewController = Depends(_controller),
) -> SuccessResponse[InterviewResponse]:
    return await controller.schedule(body, current_user, request)


@router.get("", response_model=SuccessResponse[InterviewListResponse])
async def list_interviews(
    application_id: UUID | None = Query(default=None),
    interviewer_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: InterviewController = Depends(_controller),
) -> SuccessResponse[InterviewListResponse]:
    return await controller.list_interviews(
        current_user,
        application_id=application_id,
        interviewer_id=interviewer_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/{interview_id}", response_model=SuccessResponse[InterviewResponse])
async def get_interview(
    interview_id: UUID,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: InterviewController = Depends(_controller),
) -> SuccessResponse[InterviewResponse]:
    return await controller.get_interview(interview_id, current_user)


@router.patch("/{interview_id}", response_model=SuccessResponse[InterviewResponse])
async def update_interview(
    interview_id: UUID,
    body: UpdateInterviewRequest,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: InterviewController = Depends(_controller),
) -> SuccessResponse[InterviewResponse]:
    return await controller.update_interview(
        interview_id,
        body,
        current_user,
        request,
    )
