from datetime import date
from uuid import UUID

from fastapi import Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.recruitment.errors import RecruitmentError
from app.modules.recruitment.http import recruitment_http_exception
from app.modules.recruitment.screening_schema import (
    MatchExplanationResponse,
    ScreeningResultResponse,
)
from app.modules.recruitment.schema import (
    AnalysisResultsResponse,
    ApplicationListResponse,
    ApplicationResponse,
    CandidateListResponse,
    CandidateRankingResponse,
    CandidateResponse,
    CandidateStatusUpdateRequest,
    CandidateTimelineResponse,
    CreateApplicationRequest,
    CreateCandidateRequest,
    CreateJobRequest,
    CreateNoteRequest,
    InterviewListResponse,
    InterviewResponse,
    JobCandidateListResponse,
    JobListResponse,
    JobResponse,
    ManualOverrideRequest,
    NoteListResponse,
    NoteResponse,
    RecruitmentReportResponse,
    ResumeAnalysisResponse,
    ResumeUploadResponse,
    ScheduleInterviewRequest,
    UpdateInterviewRequest,
    UpdateJobRequest,
)
from app.modules.recruitment.service import RecruitmentService


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


class JobController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = RecruitmentService(session)

    async def create_job(
        self,
        body: CreateJobRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[JobResponse]:
        try:
            data = await self._service.create_job(
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Job created", data=data)

    async def list_jobs(
        self,
        current_user: CurrentUser,
        *,
        status: str | None = None,
        department_id: UUID | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[JobListResponse]:
        try:
            data = await self._service.list_jobs(
                actor=current_user,
                status=status,
                department_id=department_id,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Jobs retrieved", data=data)

    async def get_job(
        self,
        job_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[JobResponse]:
        try:
            data = await self._service.get_job(job_id, actor=current_user)
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Job retrieved", data=data)

    async def update_job(
        self,
        job_id: UUID,
        body: UpdateJobRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[JobResponse]:
        try:
            data = await self._service.update_job(
                job_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Job updated", data=data)

    async def delete_job(
        self,
        job_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[None]:
        try:
            await self._service.delete_job(
                job_id,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Job deleted", data=None)

    async def publish_job(
        self,
        job_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[JobResponse]:
        try:
            data = await self._service.publish_job(
                job_id,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Job published", data=data)

    async def close_job(
        self,
        job_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[JobResponse]:
        try:
            data = await self._service.close_job(
                job_id,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Job closed", data=data)

    async def list_job_candidates(
        self,
        job_id: UUID,
        current_user: CurrentUser,
        *,
        status: str | None = None,
        sort_by: str = "ai_score",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[JobCandidateListResponse]:
        try:
            data = await self._service.list_job_candidates(
                job_id,
                actor=current_user,
                status=status,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Job candidates retrieved", data=data)

    async def job_ranking(
        self,
        job_id: UUID,
        current_user: CurrentUser,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[CandidateRankingResponse]:
        try:
            data = await self._service.get_job_ranking(
                job_id,
                actor=current_user,
                page=page,
                page_size=page_size,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Candidate ranking retrieved", data=data)

    async def job_analysis_results(
        self,
        job_id: UUID,
        current_user: CurrentUser,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[AnalysisResultsResponse]:
        try:
            data = await self._service.list_job_analysis_results(
                job_id,
                actor=current_user,
                page=page,
                page_size=page_size,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Analysis results retrieved", data=data)


class CandidateController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = RecruitmentService(session)

    async def create_candidate(
        self,
        body: CreateCandidateRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[CandidateResponse]:
        try:
            data = await self._service.create_candidate(
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Candidate created", data=data)

    async def list_candidates(
        self,
        current_user: CurrentUser,
        *,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[CandidateListResponse]:
        try:
            data = await self._service.list_candidates(
                actor=current_user,
                search=search,
                page=page,
                page_size=page_size,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Candidates retrieved", data=data)

    async def get_candidate(
        self,
        candidate_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[CandidateResponse]:
        try:
            data = await self._service.get_candidate(candidate_id, actor=current_user)
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Candidate retrieved", data=data)

    async def upload_resume(
        self,
        candidate_id: UUID,
        file: UploadFile,
        current_user: CurrentUser,
    ) -> SuccessResponse[ResumeUploadResponse]:
        try:
            data = await self._service.upload_resume(
                candidate_id,
                file,
                actor=current_user,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Resume uploaded", data=data)

    async def get_analysis(
        self,
        candidate_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[ResumeAnalysisResponse]:
        try:
            data = await self._service.get_candidate_analysis(
                candidate_id,
                actor=current_user,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Resume analysis retrieved", data=data)

    async def create_note(
        self,
        candidate_id: UUID,
        body: CreateNoteRequest,
        current_user: CurrentUser,
    ) -> SuccessResponse[NoteResponse]:
        try:
            data = await self._service.create_note(
                candidate_id,
                body,
                actor=current_user,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Note created", data=data)

    async def list_notes(
        self,
        candidate_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[NoteListResponse]:
        try:
            data = await self._service.list_notes(candidate_id, actor=current_user)
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Notes retrieved", data=data)

    async def manual_override(
        self,
        application_id: UUID,
        body: ManualOverrideRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[ApplicationResponse]:
        try:
            data = await self._service.manual_override(
                application_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Application overridden", data=data)

    async def analyze_candidate(
        self,
        candidate_id: UUID,
        job_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[ScreeningResultResponse]:
        try:
            data = await self._service.analyze_candidate(
                candidate_id,
                job_id,
                actor=current_user,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Candidate analyzed", data=data)


class ApplicationController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = RecruitmentService(session)

    async def create_application(
        self,
        body: CreateApplicationRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[ApplicationResponse]:
        try:
            data = await self._service.create_application(
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Application created", data=data)

    async def list_applications(
        self,
        current_user: CurrentUser,
        *,
        job_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[ApplicationListResponse]:
        try:
            data = await self._service.list_applications(
                actor=current_user,
                job_id=job_id,
                status=status,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Applications retrieved", data=data)

    async def get_application(
        self,
        application_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[ApplicationResponse]:
        try:
            data = await self._service.get_application(
                application_id,
                actor=current_user,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Application retrieved", data=data)

    async def update_status(
        self,
        application_id: UUID,
        body: CandidateStatusUpdateRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[ApplicationResponse]:
        try:
            data = await self._service.update_application_status(
                application_id,
                body.status,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Application status updated", data=data)

    async def shortlist(
        self,
        application_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[ApplicationResponse]:
        try:
            data = await self._service.shortlist_application(
                application_id,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Application shortlisted", data=data)

    async def reject(
        self,
        application_id: UUID,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[ApplicationResponse]:
        try:
            data = await self._service.reject_application(
                application_id,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Application rejected", data=data)

    async def timeline(
        self,
        application_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[CandidateTimelineResponse]:
        try:
            data = await self._service.get_timeline(
                application_id,
                actor=current_user,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Timeline retrieved", data=data)

    async def screen_application(
        self,
        application_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[ScreeningResultResponse]:
        try:
            data = await self._service.screen_application(
                application_id,
                actor=current_user,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Screening completed", data=data)

    async def match_explanation(
        self,
        application_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[MatchExplanationResponse]:
        try:
            data = await self._service.get_match_explanation(
                application_id,
                actor=current_user,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Match explanation retrieved", data=data)


class InterviewController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = RecruitmentService(session)

    async def schedule(
        self,
        body: ScheduleInterviewRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[InterviewResponse]:
        try:
            data = await self._service.schedule_interview(
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Interview scheduled", data=data)

    async def list_interviews(
        self,
        current_user: CurrentUser,
        *,
        application_id: UUID | None = None,
        interviewer_id: UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[InterviewListResponse]:
        try:
            data = await self._service.list_interviews(
                actor=current_user,
                application_id=application_id,
                interviewer_id=interviewer_id,
                status=status,
                page=page,
                page_size=page_size,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Interviews retrieved", data=data)

    async def get_interview(
        self,
        interview_id: UUID,
        current_user: CurrentUser,
    ) -> SuccessResponse[InterviewResponse]:
        try:
            data = await self._service.get_interview(interview_id, actor=current_user)
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Interview retrieved", data=data)

    async def update_interview(
        self,
        interview_id: UUID,
        body: UpdateInterviewRequest,
        current_user: CurrentUser,
        request: Request,
    ) -> SuccessResponse[InterviewResponse]:
        try:
            data = await self._service.update_interview(
                interview_id,
                body,
                actor=current_user,
                ip_address=_client_ip(request),
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Interview updated", data=data)


class RecruitmentReportController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = RecruitmentService(session)

    async def recruitment_report(
        self,
        current_user: CurrentUser,
        *,
        job_id: UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SuccessResponse[RecruitmentReportResponse]:
        try:
            data = await self._service.recruitment_report(
                actor=current_user,
                job_id=job_id,
                status=status,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=page_size,
            )
        except RecruitmentError as exc:
            raise recruitment_http_exception(exc) from exc
        return SuccessResponse(message="Recruitment report retrieved", data=data)
