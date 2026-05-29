from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import (
    DEPARTMENT_MANAGER,
    EMPLOYEE,
    HR_MANAGER,
    RECRUITER,
    SYSTEM_ADMINISTRATOR,
)
from app.core.security import CurrentUser
from app.modules.recruitment.constants import (
    ALLOWED_APPLICATION_TRANSITIONS,
    APPLICATION_APPLIED,
    APPLICATION_REJECTED,
    APPLICATION_SHORTLISTED,
    JOB_STATUS_CLOSED,
    JOB_STATUS_DRAFT,
    JOB_STATUS_PUBLISHED,
    TERMINAL_APPLICATION_STATUSES,
)
from app.modules.recruitment.errors import RecruitmentError
from app.modules.recruitment.model import (
    Candidate,
    CandidateApplication,
    CandidateNote,
    Interview,
    Job,
    ResumeAnalysis,
    ResumeFile,
)
from app.ai.screener import CandidateScreener
from app.modules.recruitment.repository import RecruitmentRepository
from app.modules.recruitment.screening_schema import (
    MatchExplanationResponse,
    ScreeningResultResponse,
)
from app.modules.recruitment.resume_utils import (
    detect_resume_mime,
    extension_for_mime,
)
from app.modules.recruitment.schema import (
    AnalysisResultRow,
    AnalysisResultsResponse,
    ApplicationListResponse,
    ApplicationResponse,
    CandidateListResponse,
    CandidateRankingResponse,
    CandidateRankingRow,
    CandidateResponse,
    CandidateTimelineItem,
    CandidateTimelineResponse,
    CreateApplicationRequest,
    CreateCandidateRequest,
    CreateJobRequest,
    CreateNoteRequest,
    InterviewListResponse,
    InterviewResponse,
    JobCandidateListResponse,
    JobCandidateRow,
    JobListResponse,
    JobResponse,
    ManualOverrideRequest,
    NoteListResponse,
    NoteResponse,
    RecruitmentReportResponse,
    RecruitmentReportRow,
    ResumeAnalysisResponse,
    ResumeUploadResponse,
    ScheduleInterviewRequest,
    UpdateInterviewRequest,
    UpdateJobRequest,
    build_pagination,
)


class RecruitmentService:
    def __init__(
        self,
        session: AsyncSession,
        repository: RecruitmentRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or RecruitmentRepository(session)
        self._settings = settings or get_settings()

    # --- Jobs (T-087) ---

    async def create_job(
        self,
        body: CreateJobRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> JobResponse:
        self._require_recruiter_or_hr(actor)
        if body.department_id is not None:
            if not await self._repository.department_exists(body.department_id):
                raise RecruitmentError("Invalid department_id", 400)

        job = await self._repository.create_job(
            title=body.title,
            department_id=body.department_id,
            description=body.description,
            status=JOB_STATUS_DRAFT,
            created_by=actor.id,
            skills=body.skills,
        )
        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="job_create",
            resource_type="jobs",
            resource_id=job.id,
            ip_address=ip_address,
            after_state=self._job_snapshot(job),
        )
        await self._session.commit()
        return self._to_job_response(job)

    async def list_jobs(
        self,
        *,
        actor: CurrentUser,
        status: str | None = None,
        department_id: uuid.UUID | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> JobListResponse:
        published_only = EMPLOYEE in actor.roles and not self._is_recruitment_staff(actor)
        if published_only:
            status = JOB_STATUS_PUBLISHED
        elif DEPARTMENT_MANAGER in actor.roles and not self._is_hr_or_admin(actor):
            manager = await self._repository.get_employee_by_user_id(actor.id)
            if manager is None:
                raise RecruitmentError("Manager profile not found", 404)
            department_id = manager.department_id

        rows, total = await self._repository.list_jobs(
            status=status,
            department_id=department_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
            published_only=published_only,
        )
        return JobListResponse(
            items=[self._to_job_response(row) for row in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_job(self, job_id: uuid.UUID, *, actor: CurrentUser) -> JobResponse:
        job = await self._get_job_or_404(job_id)
        if EMPLOYEE in actor.roles and not self._is_recruitment_staff(actor):
            if job.status != JOB_STATUS_PUBLISHED:
                raise RecruitmentError("Job not found", 404)
        elif DEPARTMENT_MANAGER in actor.roles and not self._is_hr_or_admin(actor):
            await self._ensure_dept_manager_job_access(actor, job)
        return self._to_job_response(job)

    async def update_job(
        self,
        job_id: uuid.UUID,
        body: UpdateJobRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> JobResponse:
        self._require_recruiter_or_hr(actor)
        job = await self._get_job_or_404(job_id)
        before = self._job_snapshot(job)

        if body.department_id is not None:
            if not await self._repository.department_exists(body.department_id):
                raise RecruitmentError("Invalid department_id", 400)

        updated = await self._repository.update_job(
            job_id,
            title=body.title,
            department_id=body.department_id,
            description=body.description,
            skills=body.skills,
        )
        assert updated is not None

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="job_update",
            resource_type="jobs",
            resource_id=job_id,
            ip_address=ip_address,
            before_state=before,
            after_state=self._job_snapshot(updated),
        )
        await self._session.commit()
        return self._to_job_response(updated)

    async def delete_job(
        self,
        job_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> None:
        self._require_hr_or_admin(actor)
        job = await self._get_job_or_404(job_id)
        before = self._job_snapshot(job)
        if not await self._repository.soft_delete_job(job_id):
            raise RecruitmentError("Job not found", 404)
        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="job_update",
            resource_type="jobs",
            resource_id=job_id,
            ip_address=ip_address,
            before_state=before,
            after_state={"deleted": True},
        )
        await self._session.commit()

    async def publish_job(
        self,
        job_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> JobResponse:
        return await self._transition_job(
            job_id,
            from_status=JOB_STATUS_DRAFT,
            to_status=JOB_STATUS_PUBLISHED,
            actor=actor,
            ip_address=ip_address,
        )

    async def close_job(
        self,
        job_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> JobResponse:
        return await self._transition_job(
            job_id,
            from_status=JOB_STATUS_PUBLISHED,
            to_status=JOB_STATUS_CLOSED,
            actor=actor,
            ip_address=ip_address,
        )

    async def _transition_job(
        self,
        job_id: uuid.UUID,
        *,
        from_status: str,
        to_status: str,
        actor: CurrentUser,
        ip_address: str,
    ) -> JobResponse:
        self._require_recruiter_or_hr(actor)
        job = await self._get_job_or_404(job_id)
        before = self._job_snapshot(job)

        if job.status != from_status:
            raise RecruitmentError(
                f"Job must be in '{from_status}' status for this action",
                400,
            )

        updated = await self._repository.update_job_status(job_id, to_status)
        assert updated is not None

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="job_status_change",
            resource_type="jobs",
            resource_id=job_id,
            ip_address=ip_address,
            before_state=before,
            after_state=self._job_snapshot(updated),
        )
        await self._session.commit()
        return self._to_job_response(updated)

    # --- Candidates (T-091) ---

    async def create_candidate(
        self,
        body: CreateCandidateRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> CandidateResponse:
        self._require_recruiter_or_hr(actor)

        existing = await self._repository.get_candidate_by_email(body.email)
        if existing is not None:
            raise RecruitmentError("Candidate email already exists", 409)

        candidate = await self._repository.create_candidate(
            full_name=body.full_name,
            email=body.email,
            phone=body.phone,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="candidate_create",
            resource_type="candidates",
            resource_id=candidate.id,
            ip_address=ip_address,
            after_state=self._candidate_snapshot(candidate),
        )

        if body.job_id is not None:
            await self._create_application_internal(
                candidate.id,
                body.job_id,
                actor=actor,
                ip_address=ip_address,
            )

        await self._session.commit()
        refreshed = await self._repository.get_candidate_by_id(candidate.id)
        assert refreshed is not None
        return self._to_candidate_response(refreshed)

    async def list_candidates(
        self,
        *,
        actor: CurrentUser,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CandidateListResponse:
        self._require_recruiter_or_hr(actor)
        rows, total = await self._repository.list_candidates(
            search=search,
            page=page,
            page_size=page_size,
        )
        return CandidateListResponse(
            items=[self._to_candidate_response(row) for row in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_candidate(
        self,
        candidate_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> CandidateResponse:
        self._require_recruiter_or_hr(actor)
        candidate = await self._get_candidate_or_404(candidate_id)
        return self._to_candidate_response(candidate)

    async def create_application(
        self,
        body: CreateApplicationRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> ApplicationResponse:
        self._require_recruiter_or_hr(actor)
        application = await self._create_application_internal(
            body.candidate_id,
            body.job_id,
            actor=actor,
            ip_address=ip_address,
        )
        await self._session.commit()
        return self._to_application_response(application)

    async def list_applications(
        self,
        *,
        actor: CurrentUser,
        job_id: uuid.UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> ApplicationListResponse:
        department_id = await self._application_department_scope(actor)
        rows, total = await self._repository.list_applications(
            job_id=job_id,
            status=status,
            department_id=department_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )
        return ApplicationListResponse(
            items=[self._to_application_response(row) for row in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_application(
        self,
        application_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> ApplicationResponse:
        application = await self._get_application_or_404(application_id)
        await self._ensure_application_access(actor, application)
        return self._to_application_response(application)

    async def update_application_status(
        self,
        application_id: uuid.UUID,
        new_status: str,
        *,
        actor: CurrentUser,
        ip_address: str,
        allow_override: bool = False,
        remarks: str | None = None,
    ) -> ApplicationResponse:
        self._require_recruiter_or_hr(actor)
        application = await self._get_application_or_404(application_id)
        return await self._apply_status_change(
            application,
            new_status,
            actor=actor,
            ip_address=ip_address,
            allow_override=allow_override,
            remarks=remarks,
        )

    async def shortlist_application(
        self,
        application_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> ApplicationResponse:
        return await self.update_application_status(
            application_id,
            APPLICATION_SHORTLISTED,
            actor=actor,
            ip_address=ip_address,
            allow_override=True,
        )

    async def reject_application(
        self,
        application_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> ApplicationResponse:
        return await self.update_application_status(
            application_id,
            APPLICATION_REJECTED,
            actor=actor,
            ip_address=ip_address,
            allow_override=True,
        )

    async def manual_override(
        self,
        application_id: uuid.UUID,
        body: ManualOverrideRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> ApplicationResponse:
        self._require_recruiter_or_hr(actor)
        application = await self._get_application_or_404(application_id)
        before = self._application_snapshot(application)

        updated = await self._repository.update_application_status(
            application_id,
            application_status=body.status,
            recruiter_override=True,
        )
        assert updated is not None

        await self._repository.create_status_history(
            application_id=application_id,
            old_status=application.application_status,
            new_status=body.status,
            changed_by=actor.id,
        )
        await self._repository.update_candidate_status(
            application.candidate_id,
            body.status,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="application_manual_override",
            resource_type="candidate_applications",
            resource_id=application_id,
            ip_address=ip_address,
            before_state=before,
            after_state=self._application_snapshot(updated),
        )
        await self._session.commit()
        refreshed = await self._repository.get_application_by_id(application_id)
        assert refreshed is not None
        return self._to_application_response(refreshed)

    async def get_timeline(
        self,
        application_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> CandidateTimelineResponse:
        application = await self._get_application_or_404(application_id)
        await self._ensure_application_access(actor, application)
        history = await self._repository.get_status_history(application_id)
        return CandidateTimelineResponse(
            application_id=application_id,
            items=[
                CandidateTimelineItem(
                    old_status=entry.old_status,
                    new_status=entry.new_status,
                    changed_at=entry.changed_at,
                    changed_by=entry.changed_by,
                    changed_by_name=(
                        entry.changed_by_user.email if entry.changed_by_user else None
                    ),
                )
                for entry in history
            ],
        )

    async def list_job_candidates(
        self,
        job_id: uuid.UUID,
        *,
        actor: CurrentUser,
        status: str | None = None,
        sort_by: str = "ai_score",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> JobCandidateListResponse:
        job = await self._get_job_or_404(job_id)
        await self._ensure_job_read_access(actor, job)

        rows, total = await self._repository.list_applications(
            job_id=job_id,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )
        return JobCandidateListResponse(
            items=[self._to_job_candidate_row(row) for row in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_job_ranking(
        self,
        job_id: uuid.UUID,
        *,
        actor: CurrentUser,
        page: int = 1,
        page_size: int = 20,
    ) -> CandidateRankingResponse:
        self._require_recruiter_or_hr(actor)
        await self._get_job_or_404(job_id)

        rows, total = await self._repository.list_applications(
            job_id=job_id,
            sort_by="ai_score",
            sort_order="desc",
            page=page,
            page_size=page_size,
        )
        rows.sort(
            key=lambda r: (
                -(float(r.ai_score) if r.ai_score is not None else -1),
                r.ranking if r.ranking is not None else 999999,
            ),
        )
        return CandidateRankingResponse(
            items=[
                CandidateRankingRow(
                    **self._to_job_candidate_row(row).model_dump(),
                    score=row.ai_score,
                )
                for row in rows
            ],
            pagination=build_pagination(page, page_size, total),
        )

    # --- Resume upload (T-094) ---

    async def upload_resume(
        self,
        candidate_id: uuid.UUID,
        file: UploadFile,
        *,
        actor: CurrentUser,
    ) -> ResumeUploadResponse:
        self._require_recruiter_or_hr(actor)
        await self._get_candidate_or_404(candidate_id)

        content = await file.read()
        if len(content) > self._settings.max_resume_size_bytes:
            raise RecruitmentError("Resume file exceeds 10MB limit", 400)

        mime = detect_resume_mime(content[:8])
        if mime is None:
            raise RecruitmentError("Only PDF and DOCX files are allowed", 400)

        upload_dir = Path(self._settings.resume_upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        stored_name = f"{candidate_id}_{uuid.uuid4().hex}{extension_for_mime(mime)}"
        file_path = upload_dir / stored_name
        file_path.write_bytes(content)

        file_url = f"/{self._settings.resume_upload_dir}/{stored_name}".replace("\\", "/")
        resume = await self._repository.create_resume_file(
            candidate_id=candidate_id,
            file_name=file.filename or stored_name,
            file_url=file_url,
            mime_type=mime,
            file_size_bytes=len(content),
        )
        await self._session.commit()

        response = ResumeUploadResponse(
            resume_file_id=resume.id,
            file_url=file_url,
            file_name=resume.file_name,
        )

        if self._settings.ai_auto_screen_on_upload:
            applications = await self._repository.get_applications_by_candidate(
                candidate_id,
            )
            if applications:
                try:
                    await self._run_screening(
                        applications[0].id,
                        file_path=str(file_path),
                    )
                except RecruitmentError:
                    pass

        return response

    # --- AI screening (T-111 – T-114) ---

    async def screen_application(
        self,
        application_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> ScreeningResultResponse:
        self._require_recruiter_or_hr(actor)
        application = await self._get_application_or_404(application_id)
        resume = await self._repository.get_active_resume_file(application.candidate_id)
        if resume is None:
            raise RecruitmentError("No resume file found for candidate", 400)

        result = await self._run_screening(application_id)
        return self._to_screening_response(result)

    async def analyze_candidate(
        self,
        candidate_id: uuid.UUID,
        job_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> ScreeningResultResponse:
        self._require_recruiter_or_hr(actor)
        await self._get_candidate_or_404(candidate_id)
        resume = await self._repository.get_active_resume_file(candidate_id)
        if resume is None:
            raise RecruitmentError("No resume file found for candidate", 400)

        application = await self._repository.get_application_by_candidate_job(
            candidate_id,
            job_id,
        )
        if application is None:
            raise RecruitmentError("Application not found for candidate and job", 404)

        result = await self._run_screening(application.id)
        return self._to_screening_response(result)

    async def get_match_explanation(
        self,
        application_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> MatchExplanationResponse:
        application = await self._get_application_or_404(application_id)
        await self._ensure_application_access(actor, application)

        analysis = await self._repository.get_analysis_for_application(application_id)
        if analysis is None:
            raise RecruitmentError("No resume analysis found", 404)

        matched = analysis.matched_skills.get("skills", analysis.matched_skills)
        missing = analysis.missing_skills.get("skills", analysis.missing_skills)

        return MatchExplanationResponse(
            application_id=application_id,
            score=analysis.score,
            matched_skills=matched if isinstance(matched, list) else [matched],
            missing_skills=missing if isinstance(missing, list) else [missing],
            recommendation=analysis.recommendation,
            explanation=analysis.explanation or {},
        )

    async def _run_screening(
        self,
        application_id: uuid.UUID,
        *,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        screener = CandidateScreener(self._session, repository=self._repository)
        try:
            return await screener.screen_application(
                application_id,
                file_path=file_path,
            )
        except ValueError as exc:
            raise RecruitmentError(str(exc), 400) from exc

    def _to_screening_response(self, result: dict[str, Any]) -> ScreeningResultResponse:
        return ScreeningResultResponse(
            analysis_id=uuid.UUID(result["analysis_id"]),
            application_id=uuid.UUID(result["application_id"]),
            candidate_id=uuid.UUID(result["candidate_id"]),
            job_id=uuid.UUID(result["job_id"]),
            analysis_status=result["analysis_status"],
            score=result["score"],
            ai_score=result.get("ai_score"),
            recommendation=result.get("recommendation"),
            matched_skills=result.get("matched_skills", []),
            missing_skills=result.get("missing_skills", []),
            extracted_skills=result.get("extracted_skills", []),
            explanation=result.get("explanation", {}),
        )

    # --- Notes (T-095) ---

    async def create_note(
        self,
        candidate_id: uuid.UUID,
        body: CreateNoteRequest,
        *,
        actor: CurrentUser,
    ) -> NoteResponse:
        self._require_recruiter_or_hr(actor)
        await self._get_candidate_or_404(candidate_id)
        note = await self._repository.create_note(
            candidate_id=candidate_id,
            note=body.note,
            created_by=actor.id,
        )
        await self._session.commit()
        return self._to_note_response(note)

    async def list_notes(
        self,
        candidate_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> NoteListResponse:
        self._require_recruiter_or_hr(actor)
        await self._get_candidate_or_404(candidate_id)
        notes = await self._repository.list_notes(candidate_id)
        return NoteListResponse(items=[self._to_note_response(n) for n in notes])

    # --- Analysis (T-101, T-102) ---

    async def get_candidate_analysis(
        self,
        candidate_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> ResumeAnalysisResponse:
        self._require_recruiter_or_hr(actor)
        await self._get_candidate_or_404(candidate_id)
        analysis = await self._repository.get_latest_analysis_for_candidate(candidate_id)
        if analysis is None:
            raise RecruitmentError("No resume analysis found", 404)
        return self._to_analysis_response(analysis)

    async def list_job_analysis_results(
        self,
        job_id: uuid.UUID,
        *,
        actor: CurrentUser,
        page: int = 1,
        page_size: int = 20,
    ) -> AnalysisResultsResponse:
        self._require_recruiter_or_hr(actor)
        await self._get_job_or_404(job_id)

        rows, total = await self._repository.list_analysis_results_for_job(
            job_id,
            page=page,
            page_size=page_size,
        )
        items: list[AnalysisResultRow] = []
        for application, analysis in rows:
            items.append(
                AnalysisResultRow(
                    application_id=application.id,
                    candidate_id=application.candidate_id,
                    candidate_name=application.candidate.full_name,
                    application_status=application.application_status,  # type: ignore[arg-type]
                    ai_score=application.ai_score,
                    score=analysis.score if analysis else None,
                    recommendation=(
                        analysis.recommendation if analysis else application.recommendation
                    ),
                    matched_skills=analysis.matched_skills if analysis else None,
                    missing_skills=analysis.missing_skills if analysis else None,
                ),
            )
        return AnalysisResultsResponse(
            items=items,
            pagination=build_pagination(page, page_size, total),
        )

    # --- Interviews (T-098) ---

    async def schedule_interview(
        self,
        body: ScheduleInterviewRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> InterviewResponse:
        self._require_recruiter_or_hr(actor)
        application = await self._get_application_or_404(body.application_id)

        if application.application_status in TERMINAL_APPLICATION_STATUSES:
            raise RecruitmentError(
                "Cannot schedule interview for a rejected or withdrawn application",
                409,
            )

        scheduled_at = self._ensure_aware(body.scheduled_at)
        if scheduled_at <= datetime.now(UTC):
            raise RecruitmentError("scheduled_at must be in the future", 400)

        if body.interviewer_id is not None:
            if not await self._repository.employee_exists(body.interviewer_id):
                raise RecruitmentError("Invalid interviewer_id", 400)
            if await self._repository.has_interviewer_conflict(
                body.interviewer_id,
                scheduled_at,
            ):
                raise RecruitmentError(
                    "Interviewer is already booked at this time",
                    409,
                )

        interview = await self._repository.create_interview(
            application_id=body.application_id,
            scheduled_at=scheduled_at,
            interviewer_id=body.interviewer_id,
            notes=body.notes,
            created_by=actor.id,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="interview_schedule",
            resource_type="interviews",
            resource_id=interview.id,
            ip_address=ip_address,
            after_state=self._interview_snapshot(interview),
        )
        if body.interviewer_id is not None:
            interviewer = await self._repository.get_employee_by_id(body.interviewer_id)
            if interviewer is not None and interviewer.user_id is not None:
                await self._repository.create_notification(
                    user_id=interviewer.user_id,
                    title="Interview scheduled",
                    message=(
                        f"You have an interview scheduled at {scheduled_at.isoformat()} "
                        f"for application {application.id}."
                    ),
                )
        await self._session.commit()

        refreshed = await self._repository.get_interview_by_id(interview.id)
        assert refreshed is not None
        return self._to_interview_response(refreshed)

    async def list_interviews(
        self,
        *,
        actor: CurrentUser,
        application_id: uuid.UUID | None = None,
        interviewer_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> InterviewListResponse:
        self._require_recruiter_or_hr(actor)
        rows, total = await self._repository.list_interviews(
            application_id=application_id,
            interviewer_id=interviewer_id,
            status=status,
            page=page,
            page_size=page_size,
        )
        return InterviewListResponse(
            items=[self._to_interview_response(row) for row in rows],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_interview(
        self,
        interview_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> InterviewResponse:
        self._require_recruiter_or_hr(actor)
        interview = await self._get_interview_or_404(interview_id)
        return self._to_interview_response(interview)

    async def update_interview(
        self,
        interview_id: uuid.UUID,
        body: UpdateInterviewRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> InterviewResponse:
        self._require_recruiter_or_hr(actor)
        interview = await self._get_interview_or_404(interview_id)
        before = self._interview_snapshot(interview)

        scheduled_at = body.scheduled_at
        if scheduled_at is not None:
            scheduled_at = self._ensure_aware(scheduled_at)
            if scheduled_at <= datetime.now(UTC):
                raise RecruitmentError("scheduled_at must be in the future", 400)

        interviewer_id = body.interviewer_id or interview.interviewer_id
        check_time = scheduled_at or interview.scheduled_at
        if interviewer_id is not None and scheduled_at is not None:
            if await self._repository.has_interviewer_conflict(
                interviewer_id,
                check_time,
                exclude_interview_id=interview_id,
            ):
                raise RecruitmentError(
                    "Interviewer is already booked at this time",
                    409,
                )

        updated = await self._repository.update_interview(
            interview_id,
            scheduled_at=scheduled_at,
            interviewer_id=body.interviewer_id,
            status=body.status,
            notes=body.notes,
            updated_by=actor.id,
        )
        assert updated is not None

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="interview_update",
            resource_type="interviews",
            resource_id=interview_id,
            ip_address=ip_address,
            before_state=before,
            after_state=self._interview_snapshot(updated),
        )
        await self._session.commit()
        return self._to_interview_response(updated)

    # --- Report (T-104) ---

    async def recruitment_report(
        self,
        *,
        actor: CurrentUser,
        job_id: uuid.UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> RecruitmentReportResponse:
        self._require_hr_or_admin(actor)
        rows, total = await self._repository.recruitment_report(
            job_id=job_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
        return RecruitmentReportResponse(
            items=[RecruitmentReportRow(**row) for row in rows],
            pagination=build_pagination(page, page_size, total),
        )

    # --- Internal helpers ---

    async def _create_application_internal(
        self,
        candidate_id: uuid.UUID,
        job_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> CandidateApplication:
        await self._get_candidate_or_404(candidate_id)
        job = await self._get_job_or_404(job_id)

        if await self._repository.get_application_by_candidate_job(candidate_id, job_id):
            raise RecruitmentError("Candidate already applied to this job", 409)

        application = await self._repository.create_application(
            candidate_id=candidate_id,
            job_id=job_id,
            application_status=APPLICATION_APPLIED,
        )

        await self._repository.create_status_history(
            application_id=application.id,
            old_status=None,
            new_status=APPLICATION_APPLIED,
            changed_by=actor.id,
        )
        await self._repository.update_candidate_status(
            candidate_id,
            APPLICATION_APPLIED,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="application_create",
            resource_type="candidate_applications",
            resource_id=application.id,
            ip_address=ip_address,
            after_state=self._application_snapshot(application),
        )
        return application

    async def _apply_status_change(
        self,
        application: CandidateApplication,
        new_status: str,
        *,
        actor: CurrentUser,
        ip_address: str,
        allow_override: bool,
        remarks: str | None = None,
    ) -> ApplicationResponse:
        if application.application_status in TERMINAL_APPLICATION_STATUSES:
            raise RecruitmentError("Application is in a terminal status", 400)

        old_status = application.application_status
        if not allow_override and not self._is_valid_transition(old_status, new_status):
            raise RecruitmentError(
                f"Invalid status transition from '{old_status}' to '{new_status}'",
                400,
            )

        before = self._application_snapshot(application)
        updated = await self._repository.update_application_status(
            application.id,
            application_status=new_status,
        )
        assert updated is not None

        await self._repository.create_status_history(
            application_id=application.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=actor.id,
        )
        await self._repository.update_candidate_status(
            application.candidate_id,
            new_status,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="application_status_change",
            resource_type="candidate_applications",
            resource_id=application.id,
            ip_address=ip_address,
            before_state=before,
            after_state=self._application_snapshot(updated),
        )
        await self._repository.create_notification(
            user_id=actor.id,
            title="Candidate status updated",
            message=f"Application status changed from '{old_status}' to '{new_status}'.",
        )
        await self._session.commit()

        refreshed = await self._repository.get_application_by_id(application.id)
        assert refreshed is not None
        return self._to_application_response(refreshed)

    def _is_valid_transition(self, old_status: str, new_status: str) -> bool:
        if new_status in TERMINAL_APPLICATION_STATUSES:
            return True
        allowed = ALLOWED_APPLICATION_TRANSITIONS.get(old_status, frozenset())
        return new_status in allowed

    async def _get_job_or_404(self, job_id: uuid.UUID) -> Job:
        job = await self._repository.get_job_by_id(job_id)
        if job is None:
            raise RecruitmentError("Job not found", 404)
        return job

    async def _get_candidate_or_404(self, candidate_id: uuid.UUID) -> Candidate:
        candidate = await self._repository.get_candidate_by_id(candidate_id)
        if candidate is None:
            raise RecruitmentError("Candidate not found", 404)
        return candidate

    async def _get_application_or_404(
        self,
        application_id: uuid.UUID,
    ) -> CandidateApplication:
        application = await self._repository.get_application_by_id(application_id)
        if application is None:
            raise RecruitmentError("Application not found", 404)
        return application

    async def _get_interview_or_404(self, interview_id: uuid.UUID) -> Interview:
        interview = await self._repository.get_interview_by_id(interview_id)
        if interview is None:
            raise RecruitmentError("Interview not found", 404)
        return interview

    async def _application_department_scope(
        self,
        actor: CurrentUser,
    ) -> uuid.UUID | None:
        if DEPARTMENT_MANAGER in actor.roles and not self._is_recruitment_staff(actor):
            manager = await self._repository.get_employee_by_user_id(actor.id)
            if manager is None:
                raise RecruitmentError("Manager profile not found", 404)
            return manager.department_id
        if EMPLOYEE in actor.roles and not self._is_recruitment_staff(actor):
            raise RecruitmentError("Insufficient permissions", 403)
        return None

    async def _ensure_application_access(
        self,
        actor: CurrentUser,
        application: CandidateApplication,
    ) -> None:
        if self._is_recruitment_staff(actor):
            return
        if DEPARTMENT_MANAGER in actor.roles:
            await self._ensure_dept_manager_job_access(actor, application.job)
            return
        raise RecruitmentError("Insufficient permissions", 403)

    async def _ensure_job_read_access(self, actor: CurrentUser, job: Job) -> None:
        if self._is_recruitment_staff(actor):
            return
        if DEPARTMENT_MANAGER in actor.roles:
            await self._ensure_dept_manager_job_access(actor, job)
            return
        raise RecruitmentError("Insufficient permissions", 403)

    async def _ensure_dept_manager_job_access(
        self,
        actor: CurrentUser,
        job: Job,
    ) -> None:
        manager = await self._repository.get_employee_by_user_id(actor.id)
        if manager is None or job.department_id != manager.department_id:
            raise RecruitmentError("Insufficient permissions", 403)

    def _require_recruiter_or_hr(self, actor: CurrentUser) -> None:
        if not self._is_recruitment_staff(actor):
            raise RecruitmentError("Insufficient permissions", 403)

    def _require_hr_or_admin(self, actor: CurrentUser) -> None:
        if not self._is_hr_or_admin(actor):
            raise RecruitmentError("Insufficient permissions", 403)

    def _is_hr_or_admin(self, actor: CurrentUser) -> bool:
        return bool({HR_MANAGER, SYSTEM_ADMINISTRATOR}.intersection(actor.roles))

    def _is_recruitment_staff(self, actor: CurrentUser) -> bool:
        return bool(
            {HR_MANAGER, SYSTEM_ADMINISTRATOR, RECRUITER}.intersection(actor.roles),
        )

    def _ensure_aware(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _job_snapshot(self, job: Job) -> dict[str, Any]:
        return {
            "id": str(job.id),
            "title": job.title,
            "status": job.status,
            "department_id": str(job.department_id) if job.department_id else None,
        }

    def _candidate_snapshot(self, candidate: Candidate) -> dict[str, Any]:
        return {
            "id": str(candidate.id),
            "email": candidate.email,
            "full_name": candidate.full_name,
        }

    def _application_snapshot(self, application: CandidateApplication) -> dict[str, Any]:
        return {
            "id": str(application.id),
            "application_status": application.application_status,
            "recruiter_override": application.recruiter_override,
        }

    def _interview_snapshot(self, interview: Interview) -> dict[str, Any]:
        return {
            "id": str(interview.id),
            "application_id": str(interview.application_id),
            "status": interview.status,
            "scheduled_at": interview.scheduled_at.isoformat(),
        }

    def _to_job_response(self, job: Job) -> JobResponse:
        return JobResponse(
            id=job.id,
            title=job.title,
            department_id=job.department_id,
            department_name=job.department.name if job.department else None,
            description=job.description,
            status=job.status,  # type: ignore[arg-type]
            skills=[skill.skill_name for skill in job.skills],
            created_by=job.created_by,
            created_by_name=job.creator.email if job.creator else None,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    def _to_candidate_response(self, candidate: Candidate) -> CandidateResponse:
        return CandidateResponse(
            id=candidate.id,
            full_name=candidate.full_name,
            email=candidate.email,
            phone=candidate.phone,
            current_status=candidate.current_status,
            created_at=candidate.created_at,
        )

    def _to_application_response(
        self,
        application: CandidateApplication,
    ) -> ApplicationResponse:
        return ApplicationResponse(
            id=application.id,
            candidate_id=application.candidate_id,
            candidate_name=application.candidate.full_name,
            candidate_email=application.candidate.email,
            job_id=application.job_id,
            job_title=application.job.title,
            application_status=application.application_status,  # type: ignore[arg-type]
            ai_score=application.ai_score,
            ranking=application.ranking,
            recommendation=application.recommendation,
            recruiter_override=application.recruiter_override,
            created_at=application.created_at,
        )

    def _to_job_candidate_row(self, application: CandidateApplication) -> JobCandidateRow:
        return JobCandidateRow(
            application_id=application.id,
            candidate_id=application.candidate_id,
            full_name=application.candidate.full_name,
            email=application.candidate.email,
            application_status=application.application_status,  # type: ignore[arg-type]
            ai_score=application.ai_score,
            ranking=application.ranking,
            recommendation=application.recommendation,
        )

    def _to_note_response(self, note: CandidateNote) -> NoteResponse:
        return NoteResponse(
            id=note.id,
            candidate_id=note.candidate_id,
            note=note.note,
            created_by=note.created_by,
            created_by_name=note.author.email if note.author else None,
            created_at=note.created_at,
        )

    def _to_analysis_response(self, analysis: ResumeAnalysis) -> ResumeAnalysisResponse:
        return ResumeAnalysisResponse(
            id=analysis.id,
            candidate_id=analysis.candidate_id,
            application_id=analysis.application_id,
            analysis_status=analysis.analysis_status,
            extracted_skills=analysis.extracted_skills,
            matched_skills=analysis.matched_skills,
            missing_skills=analysis.missing_skills,
            score=analysis.score,
            recommendation=analysis.recommendation,
            explanation=analysis.explanation,
            created_at=analysis.created_at,
        )

    def _to_interview_response(self, interview: Interview) -> InterviewResponse:
        application = interview.application
        interviewer_name = None
        if interview.interviewer is not None:
            interviewer_name = (
                f"{interview.interviewer.first_name} {interview.interviewer.last_name}"
            )
        return InterviewResponse(
            id=interview.id,
            application_id=interview.application_id,
            candidate_name=application.candidate.full_name,
            job_title=application.job.title,
            scheduled_at=interview.scheduled_at,
            interviewer_id=interview.interviewer_id,
            interviewer_name=interviewer_name,
            status=interview.status,  # type: ignore[arg-type]
            notes=interview.notes,
            updated_at=interview.updated_at,
        )
