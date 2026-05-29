from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import HR_MANAGER, RECRUITER, SYSTEM_ADMINISTRATOR
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.recruitment.controller import JobController
from app.modules.recruitment.schema import (
    AnalysisResultsResponse,
    CandidateRankingResponse,
    CreateJobRequest,
    JobCandidateListResponse,
    JobListResponse,
    JobResponse,
    UpdateJobRequest,
)

router = APIRouter()

_recruiter_or_hr = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER, RECRUITER)
_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)


def _controller(session: AsyncSession = Depends(get_db)) -> JobController:
    return JobController(session)


@router.post(
    "",
    response_model=SuccessResponse[JobResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    body: CreateJobRequest,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[JobResponse]:
    return await controller.create_job(body, current_user, request)


@router.get("", response_model=SuccessResponse[JobListResponse])
async def list_jobs(
    status: str | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[JobListResponse]:
    return await controller.list_jobs(
        current_user,
        status=status,
        department_id=department_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}/candidates/ranking", response_model=SuccessResponse[CandidateRankingResponse])
async def job_candidate_ranking(
    job_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[CandidateRankingResponse]:
    return await controller.job_ranking(
        job_id,
        current_user,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}/candidates/analysis-results",
    response_model=SuccessResponse[AnalysisResultsResponse],
)
async def job_analysis_results(
    job_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[AnalysisResultsResponse]:
    return await controller.job_analysis_results(
        job_id,
        current_user,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}/candidates", response_model=SuccessResponse[JobCandidateListResponse])
async def list_job_candidates(
    job_id: UUID,
    status: str | None = Query(default=None),
    sort_by: str = Query(default="ai_score"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[JobCandidateListResponse]:
    return await controller.list_job_candidates(
        job_id,
        current_user,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=SuccessResponse[JobResponse])
async def get_job(
    job_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[JobResponse]:
    return await controller.get_job(job_id, current_user)


@router.patch("/{job_id}", response_model=SuccessResponse[JobResponse])
async def update_job(
    job_id: UUID,
    body: UpdateJobRequest,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[JobResponse]:
    return await controller.update_job(job_id, body, current_user, request)


@router.delete("/{job_id}", response_model=SuccessResponse[None])
async def delete_job(
    job_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[None]:
    return await controller.delete_job(job_id, current_user, request)


@router.post("/{job_id}/publish", response_model=SuccessResponse[JobResponse])
async def publish_job(
    job_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[JobResponse]:
    return await controller.publish_job(job_id, current_user, request)


@router.post("/{job_id}/close", response_model=SuccessResponse[JobResponse])
async def close_job(
    job_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_recruiter_or_hr),
    controller: JobController = Depends(_controller),
) -> SuccessResponse[JobResponse]:
    return await controller.close_job(job_id, current_user, request)
