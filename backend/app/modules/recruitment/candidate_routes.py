from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, RECRUITER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, require_roles
from app.modules.recruitment.controller import CandidateController
from app.modules.recruitment.schema import (
    ApplicationResponse,
    CandidateListResponse,
    CandidateResponse,
    CreateCandidateRequest,
    CreateNoteRequest,
    ManualOverrideRequest,
    NoteListResponse,
    NoteResponse,
    ResumeAnalysisResponse,
    ResumeUploadResponse,
)
from app.modules.recruitment.screening_schema import ScreeningResultResponse

router = APIRouter()

_recruiter_or_hr = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER, RECRUITER)


def _controller(session: AsyncSession = Depends(get_db)) -> CandidateController:
    return CandidateController(session)


@router.post(
    "",
    response_model=SuccessResponse[CandidateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_candidate(
    body: CreateCandidateRequest,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: CandidateController = Depends(_controller),
) -> SuccessResponse[CandidateResponse]:
    return await controller.create_candidate(body, current_user, request)


@router.get("", response_model=SuccessResponse[CandidateListResponse])
async def list_candidates(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: CandidateController = Depends(_controller),
) -> SuccessResponse[CandidateListResponse]:
    return await controller.list_candidates(
        current_user,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/{candidate_id}", response_model=SuccessResponse[CandidateResponse])
async def get_candidate(
    candidate_id: UUID,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: CandidateController = Depends(_controller),
) -> SuccessResponse[CandidateResponse]:
    return await controller.get_candidate(candidate_id, current_user)


@router.post(
    "/{candidate_id}/resume",
    response_model=SuccessResponse[ResumeUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    candidate_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: CandidateController = Depends(_controller),
) -> SuccessResponse[ResumeUploadResponse]:
    return await controller.upload_resume(candidate_id, file, current_user)


@router.get(
    "/{candidate_id}/analysis",
    response_model=SuccessResponse[ResumeAnalysisResponse],
)
async def get_candidate_analysis(
    candidate_id: UUID,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: CandidateController = Depends(_controller),
) -> SuccessResponse[ResumeAnalysisResponse]:
    return await controller.get_analysis(candidate_id, current_user)


@router.post(
    "/{candidate_id}/notes",
    response_model=SuccessResponse[NoteResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    candidate_id: UUID,
    body: CreateNoteRequest,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: CandidateController = Depends(_controller),
) -> SuccessResponse[NoteResponse]:
    return await controller.create_note(candidate_id, body, current_user)


@router.get("/{candidate_id}/notes", response_model=SuccessResponse[NoteListResponse])
async def list_notes(
    candidate_id: UUID,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: CandidateController = Depends(_controller),
) -> SuccessResponse[NoteListResponse]:
    return await controller.list_notes(candidate_id, current_user)


@router.post(
    "/{candidate_id}/analyze",
    response_model=SuccessResponse[ScreeningResultResponse],
)
async def analyze_candidate(
    candidate_id: UUID,
    job_id: UUID = Query(),
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: CandidateController = Depends(_controller),
) -> SuccessResponse[ScreeningResultResponse]:
    return await controller.analyze_candidate(candidate_id, job_id, current_user)


@router.post(
    "/{application_id}/override",
    response_model=SuccessResponse[ApplicationResponse],
)
async def manual_override(
    application_id: UUID,
    body: ManualOverrideRequest,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: CandidateController = Depends(_controller),
) -> SuccessResponse[ApplicationResponse]:
    return await controller.manual_override(
        application_id,
        body,
        current_user,
        request,
    )
