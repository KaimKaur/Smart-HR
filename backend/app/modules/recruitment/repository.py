from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.employee.model import Department, Employee
from app.modules.notifications.model import AuditLog, Notification
from app.modules.recruitment.constants import INTERVIEW_SCHEDULED
from app.modules.recruitment.model import (
    Candidate,
    CandidateApplication,
    CandidateNote,
    CandidateStatusHistory,
    Interview,
    Job,
    JobSkill,
    ResumeAnalysis,
    ResumeFile,
)
from app.modules.user.model import User


class RecruitmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- Jobs ---

    async def create_job(
        self,
        *,
        title: str,
        department_id: uuid.UUID | None,
        description: str,
        status: str,
        created_by: uuid.UUID | None,
        skills: list[str],
    ) -> Job:
        job = Job(
            title=title,
            department_id=department_id,
            description=description,
            status=status,
            created_by=created_by,
        )
        self._session.add(job)
        await self._session.flush()
        for skill in skills:
            self._session.add(JobSkill(job_id=job.id, skill_name=skill))
        await self._session.flush()
        return await self.get_job_by_id(job.id)  # type: ignore[return-value]

    async def get_job_by_id(self, job_id: uuid.UUID) -> Job | None:
        result = await self._session.execute(
            select(Job)
            .where(Job.id == job_id, Job.deleted_at.is_(None))
            .options(
                selectinload(Job.skills),
                selectinload(Job.department),
                selectinload(Job.creator),
            ),
        )
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        *,
        status: str | None = None,
        department_id: uuid.UUID | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
        published_only: bool = False,
    ) -> tuple[list[Job], int]:
        query = (
            select(Job)
            .where(Job.deleted_at.is_(None))
            .options(
                selectinload(Job.skills),
                selectinload(Job.department),
                selectinload(Job.creator),
            )
        )
        count_query = select(func.count()).select_from(Job).where(Job.deleted_at.is_(None))

        if published_only:
            query = query.where(Job.status == "published")
            count_query = count_query.where(Job.status == "published")
        elif status is not None:
            query = query.where(Job.status == status)
            count_query = count_query.where(Job.status == status)

        if department_id is not None:
            query = query.where(Job.department_id == department_id)
            count_query = count_query.where(Job.department_id == department_id)

        if search:
            pattern = f"%{search}%"
            query = query.where(Job.title.ilike(pattern))
            count_query = count_query.where(Job.title.ilike(pattern))

        sort_column = Job.created_at
        if sort_by == "title":
            sort_column = Job.title
        elif sort_by == "status":
            sort_column = Job.status

        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        result = await self._session.execute(query.offset(offset).limit(page_size))
        return list(result.scalars().unique().all()), total_items

    async def update_job(
        self,
        job_id: uuid.UUID,
        *,
        title: str | None = None,
        department_id: uuid.UUID | None = None,
        description: str | None = None,
        skills: list[str] | None = None,
    ) -> Job | None:
        values: dict[str, Any] = {"updated_at": datetime.now(UTC)}
        if title is not None:
            values["title"] = title
        if department_id is not None:
            values["department_id"] = department_id
        if description is not None:
            values["description"] = description

        if values:
            await self._session.execute(
                update(Job).where(Job.id == job_id).values(**values),
            )

        if skills is not None:
            existing = await self._session.execute(
                select(JobSkill).where(JobSkill.job_id == job_id),
            )
            for row in existing.scalars().all():
                await self._session.delete(row)
            for skill in skills:
                self._session.add(JobSkill(job_id=job_id, skill_name=skill))
            await self._session.flush()

        return await self.get_job_by_id(job_id)

    async def update_job_status(self, job_id: uuid.UUID, status: str) -> Job | None:
        await self._session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(status=status, updated_at=datetime.now(UTC)),
        )
        return await self.get_job_by_id(job_id)

    async def soft_delete_job(self, job_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            update(Job)
            .where(Job.id == job_id, Job.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC)),
        )
        return result.rowcount > 0

    async def get_job_skills(self, job_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(JobSkill.skill_name)
            .where(JobSkill.job_id == job_id)
            .order_by(JobSkill.skill_name.asc()),
        )
        return list(result.scalars().all())

    async def department_exists(self, department_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Department.id).where(Department.id == department_id),
        )
        return result.scalar_one_or_none() is not None

    # --- Candidates ---

    async def create_candidate(
        self,
        *,
        full_name: str,
        email: str,
        phone: str | None,
    ) -> Candidate:
        candidate = Candidate(
            full_name=full_name,
            email=email.lower(),
            phone=phone,
        )
        self._session.add(candidate)
        await self._session.flush()
        return await self.get_candidate_by_id(candidate.id)  # type: ignore[return-value]

    async def get_candidate_by_id(self, candidate_id: uuid.UUID) -> Candidate | None:
        result = await self._session.execute(
            select(Candidate).where(
                Candidate.id == candidate_id,
                Candidate.deleted_at.is_(None),
            ),
        )
        return result.scalar_one_or_none()

    async def get_candidate_by_email(self, email: str) -> Candidate | None:
        result = await self._session.execute(
            select(Candidate).where(
                Candidate.email == email.lower(),
                Candidate.deleted_at.is_(None),
            ),
        )
        return result.scalar_one_or_none()

    async def list_candidates(
        self,
        *,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Candidate], int]:
        query = select(Candidate).where(Candidate.deleted_at.is_(None))
        count_query = select(func.count()).select_from(Candidate).where(
            Candidate.deleted_at.is_(None),
        )

        if search:
            pattern = f"%{search}%"
            query = query.where(
                Candidate.full_name.ilike(pattern) | Candidate.email.ilike(pattern),
            )
            count_query = count_query.where(
                Candidate.full_name.ilike(pattern) | Candidate.email.ilike(pattern),
            )

        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        query = query.order_by(Candidate.created_at.desc()).offset(offset).limit(page_size)
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_items

    async def soft_delete_candidate(self, candidate_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            update(Candidate)
            .where(Candidate.id == candidate_id, Candidate.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC)),
        )
        return result.rowcount > 0

    async def update_candidate_status(
        self,
        candidate_id: uuid.UUID,
        current_status: str | None,
    ) -> None:
        await self._session.execute(
            update(Candidate)
            .where(Candidate.id == candidate_id)
            .values(current_status=current_status),
        )

    # --- Applications ---

    async def create_application(
        self,
        *,
        candidate_id: uuid.UUID,
        job_id: uuid.UUID,
        application_status: str,
    ) -> CandidateApplication:
        application = CandidateApplication(
            candidate_id=candidate_id,
            job_id=job_id,
            application_status=application_status,
        )
        self._session.add(application)
        await self._session.flush()
        return await self.get_application_by_id(application.id)  # type: ignore[return-value]

    async def get_application_by_id(
        self,
        application_id: uuid.UUID,
    ) -> CandidateApplication | None:
        result = await self._session.execute(
            select(CandidateApplication)
            .where(
                CandidateApplication.id == application_id,
                CandidateApplication.deleted_at.is_(None),
            )
            .options(
                selectinload(CandidateApplication.candidate),
                selectinload(CandidateApplication.job).selectinload(Job.department),
                selectinload(CandidateApplication.job).selectinload(Job.skills),
                selectinload(CandidateApplication.status_history).selectinload(
                    CandidateStatusHistory.changed_by_user,
                ),
            ),
        )
        return result.scalar_one_or_none()

    async def get_application_by_candidate_job(
        self,
        candidate_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> CandidateApplication | None:
        result = await self._session.execute(
            select(CandidateApplication).where(
                CandidateApplication.candidate_id == candidate_id,
                CandidateApplication.job_id == job_id,
                CandidateApplication.deleted_at.is_(None),
            ),
        )
        return result.scalar_one_or_none()

    async def get_applications_by_candidate(
        self,
        candidate_id: uuid.UUID,
    ) -> list[CandidateApplication]:
        result = await self._session.execute(
            select(CandidateApplication)
            .where(
                CandidateApplication.candidate_id == candidate_id,
                CandidateApplication.deleted_at.is_(None),
            )
            .options(selectinload(CandidateApplication.job)),
        )
        return list(result.scalars().unique().all())

    async def list_applications(
        self,
        *,
        job_id: uuid.UUID | None = None,
        status: str | None = None,
        department_id: uuid.UUID | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[CandidateApplication], int]:
        query = (
            select(CandidateApplication)
            .where(CandidateApplication.deleted_at.is_(None))
            .options(
                selectinload(CandidateApplication.candidate),
                selectinload(CandidateApplication.job),
            )
        )
        count_query = select(func.count()).select_from(CandidateApplication).where(
            CandidateApplication.deleted_at.is_(None),
        )

        if job_id is not None:
            query = query.where(CandidateApplication.job_id == job_id)
            count_query = count_query.where(CandidateApplication.job_id == job_id)

        if status is not None:
            query = query.where(CandidateApplication.application_status == status)
            count_query = count_query.where(
                CandidateApplication.application_status == status,
            )

        if department_id is not None or search:
            query = query.join(Candidate, Candidate.id == CandidateApplication.candidate_id)
            count_query = count_query.join(
                Candidate,
                Candidate.id == CandidateApplication.candidate_id,
            )

        if department_id is not None:
            query = query.join(Job, Job.id == CandidateApplication.job_id).where(
                Job.department_id == department_id,
            )
            count_query = count_query.join(
                Job,
                Job.id == CandidateApplication.job_id,
            ).where(Job.department_id == department_id)

        if search:
            pattern = f"%{search}%"
            query = query.where(
                Candidate.full_name.ilike(pattern) | Candidate.email.ilike(pattern),
            )
            count_query = count_query.where(
                Candidate.full_name.ilike(pattern) | Candidate.email.ilike(pattern),
            )

        if sort_by == "ai_score":
            order_col = CandidateApplication.ai_score
        elif sort_by == "ranking":
            order_col = CandidateApplication.ranking
        else:
            order_col = CandidateApplication.created_at

        if sort_order.lower() == "asc":
            query = query.order_by(order_col.asc().nulls_last())
        else:
            query = query.order_by(order_col.desc().nulls_last())

        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        result = await self._session.execute(query.offset(offset).limit(page_size))
        return list(result.scalars().unique().all()), total_items

    async def update_application_status(
        self,
        application_id: uuid.UUID,
        *,
        application_status: str,
        recruiter_override: bool | None = None,
    ) -> CandidateApplication | None:
        values: dict[str, Any] = {"application_status": application_status}
        if recruiter_override is not None:
            values["recruiter_override"] = recruiter_override

        await self._session.execute(
            update(CandidateApplication)
            .where(CandidateApplication.id == application_id)
            .values(**values),
        )
        return await self.get_application_by_id(application_id)

    async def create_status_history(
        self,
        *,
        application_id: uuid.UUID,
        old_status: str | None,
        new_status: str,
        changed_by: uuid.UUID | None,
    ) -> CandidateStatusHistory:
        entry = CandidateStatusHistory(
            application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_status_history(
        self,
        application_id: uuid.UUID,
    ) -> list[CandidateStatusHistory]:
        result = await self._session.execute(
            select(CandidateStatusHistory)
            .where(CandidateStatusHistory.application_id == application_id)
            .options(selectinload(CandidateStatusHistory.changed_by_user))
            .order_by(CandidateStatusHistory.changed_at.asc()),
        )
        return list(result.scalars().all())

    # --- Resume files ---

    async def create_resume_file(
        self,
        *,
        candidate_id: uuid.UUID,
        file_name: str,
        file_url: str,
        mime_type: str,
        file_size_bytes: int,
    ) -> ResumeFile:
        await self._session.execute(
            update(ResumeFile)
            .where(
                ResumeFile.candidate_id == candidate_id,
                ResumeFile.is_active.is_(True),
            )
            .values(is_active=False),
        )
        resume = ResumeFile(
            candidate_id=candidate_id,
            file_name=file_name,
            file_url=file_url,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            is_active=True,
        )
        self._session.add(resume)
        await self._session.flush()
        return resume

    # --- Notes ---

    async def create_note(
        self,
        *,
        candidate_id: uuid.UUID,
        note: str,
        created_by: uuid.UUID,
    ) -> CandidateNote:
        entry = CandidateNote(
            candidate_id=candidate_id,
            note=note,
            created_by=created_by,
        )
        self._session.add(entry)
        await self._session.flush()
        return await self.get_note_by_id(entry.id)  # type: ignore[return-value]

    async def get_note_by_id(self, note_id: uuid.UUID) -> CandidateNote | None:
        result = await self._session.execute(
            select(CandidateNote)
            .where(CandidateNote.id == note_id)
            .options(selectinload(CandidateNote.author)),
        )
        return result.scalar_one_or_none()

    async def list_notes(self, candidate_id: uuid.UUID) -> list[CandidateNote]:
        result = await self._session.execute(
            select(CandidateNote)
            .where(CandidateNote.candidate_id == candidate_id)
            .options(selectinload(CandidateNote.author))
            .order_by(CandidateNote.created_at.desc()),
        )
        return list(result.scalars().all())

    # --- Resume files (read) ---

    async def get_active_resume_file(self, candidate_id: uuid.UUID) -> ResumeFile | None:
        result = await self._session.execute(
            select(ResumeFile)
            .where(
                ResumeFile.candidate_id == candidate_id,
                ResumeFile.is_active.is_(True),
            )
            .order_by(ResumeFile.uploaded_at.desc())
            .limit(1),
        )
        return result.scalar_one_or_none()

    # --- Resume analysis ---

    async def get_analysis_for_application(
        self,
        application_id: uuid.UUID,
    ) -> ResumeAnalysis | None:
        result = await self._session.execute(
            select(ResumeAnalysis)
            .where(ResumeAnalysis.application_id == application_id)
            .order_by(ResumeAnalysis.created_at.desc())
            .limit(1),
        )
        return result.scalar_one_or_none()

    async def delete_analyses_for_application(self, application_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(ResumeAnalysis).where(
                ResumeAnalysis.application_id == application_id,
            ),
        )
        for row in result.scalars().all():
            await self._session.delete(row)
        await self._session.flush()

    async def create_resume_analysis(
        self,
        *,
        candidate_id: uuid.UUID,
        application_id: uuid.UUID,
        analysis_status: str,
        extracted_skills: dict,
        matched_skills: dict,
        missing_skills: dict,
        score: Decimal,
        recommendation: str | None,
        explanation: dict | None,
    ) -> ResumeAnalysis:
        analysis = ResumeAnalysis(
            candidate_id=candidate_id,
            application_id=application_id,
            analysis_status=analysis_status,
            extracted_skills=extracted_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            score=score,
            recommendation=recommendation,
            explanation=explanation,
        )
        self._session.add(analysis)
        await self._session.flush()
        return analysis

    async def update_application_ai_fields(
        self,
        application_id: uuid.UUID,
        *,
        ai_score: Decimal,
        recommendation: str | None,
    ) -> None:
        await self._session.execute(
            update(CandidateApplication)
            .where(CandidateApplication.id == application_id)
            .values(ai_score=ai_score, recommendation=recommendation),
        )

    async def recompute_job_rankings(self, job_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(CandidateApplication)
            .where(
                CandidateApplication.job_id == job_id,
                CandidateApplication.deleted_at.is_(None),
                CandidateApplication.ai_score.is_not(None),
            )
            .order_by(
                CandidateApplication.ai_score.desc(),
                CandidateApplication.created_at.asc(),
            ),
        )
        applications = list(result.scalars().all())
        for rank, application in enumerate(applications, start=1):
            await self._session.execute(
                update(CandidateApplication)
                .where(CandidateApplication.id == application.id)
                .values(ranking=rank),
            )

        await self._session.execute(
            update(CandidateApplication)
            .where(
                CandidateApplication.job_id == job_id,
                CandidateApplication.deleted_at.is_(None),
                CandidateApplication.ai_score.is_(None),
            )
            .values(ranking=None),
        )

    async def get_latest_analysis_for_candidate(
        self,
        candidate_id: uuid.UUID,
    ) -> ResumeAnalysis | None:
        result = await self._session.execute(
            select(ResumeAnalysis)
            .where(ResumeAnalysis.candidate_id == candidate_id)
            .order_by(ResumeAnalysis.created_at.desc())
            .limit(1),
        )
        return result.scalar_one_or_none()

    async def list_analysis_results_for_job(
        self,
        job_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[CandidateApplication, ResumeAnalysis | None]], int]:
        base = (
            select(CandidateApplication, ResumeAnalysis)
            .outerjoin(
                ResumeAnalysis,
                ResumeAnalysis.application_id == CandidateApplication.id,
            )
            .where(
                CandidateApplication.job_id == job_id,
                CandidateApplication.deleted_at.is_(None),
            )
            .options(selectinload(CandidateApplication.candidate))
        )

        count_query = select(func.count()).select_from(CandidateApplication).where(
            CandidateApplication.job_id == job_id,
            CandidateApplication.deleted_at.is_(None),
        )
        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        result = await self._session.execute(
            base.order_by(
                ResumeAnalysis.score.desc().nulls_last(),
                CandidateApplication.created_at.desc(),
            )
            .offset(offset)
            .limit(page_size),
        )
        return list(result.all()), total_items

    async def list_ranked_applications_for_job(
        self,
        job_id: uuid.UUID,
        *,
        status: str | None = None,
        page: int,
        page_size: int,
    ) -> tuple[list[CandidateApplication], int]:
        return await self.list_applications(
            job_id=job_id,
            status=status,
            sort_by="ai_score",
            sort_order="desc",
            page=page,
            page_size=page_size,
        )

    # --- Interviews ---

    async def create_interview(
        self,
        *,
        application_id: uuid.UUID,
        scheduled_at: datetime,
        interviewer_id: uuid.UUID | None,
        notes: str | None,
        created_by: uuid.UUID | None,
    ) -> Interview:
        interview = Interview(
            application_id=application_id,
            scheduled_at=scheduled_at,
            interviewer_id=interviewer_id,
            status=INTERVIEW_SCHEDULED,
            notes=notes,
            created_by=created_by,
        )
        self._session.add(interview)
        await self._session.flush()
        return await self.get_interview_by_id(interview.id)  # type: ignore[return-value]

    async def get_interview_by_id(self, interview_id: uuid.UUID) -> Interview | None:
        result = await self._session.execute(
            select(Interview)
            .where(Interview.id == interview_id)
            .options(
                selectinload(Interview.application).selectinload(
                    CandidateApplication.candidate,
                ),
                selectinload(Interview.application).selectinload(
                    CandidateApplication.job,
                ),
                selectinload(Interview.interviewer),
            ),
        )
        return result.scalar_one_or_none()

    async def list_interviews(
        self,
        *,
        application_id: uuid.UUID | None = None,
        interviewer_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Interview], int]:
        query = select(Interview).options(
            selectinload(Interview.application),
            selectinload(Interview.interviewer),
        )
        count_query = select(func.count()).select_from(Interview)

        if application_id is not None:
            query = query.where(Interview.application_id == application_id)
            count_query = count_query.where(Interview.application_id == application_id)

        if interviewer_id is not None:
            query = query.where(Interview.interviewer_id == interviewer_id)
            count_query = count_query.where(Interview.interviewer_id == interviewer_id)

        if status is not None:
            query = query.where(Interview.status == status)
            count_query = count_query.where(Interview.status == status)

        total_result = await self._session.execute(count_query)
        total_items = int(total_result.scalar_one())

        offset = (page - 1) * page_size
        query = query.order_by(Interview.scheduled_at.desc()).offset(offset).limit(page_size)
        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    async def update_interview(
        self,
        interview_id: uuid.UUID,
        *,
        scheduled_at: datetime | None = None,
        interviewer_id: uuid.UUID | None = None,
        status: str | None = None,
        notes: str | None = None,
        updated_by: uuid.UUID | None = None,
    ) -> Interview | None:
        values: dict[str, Any] = {"updated_at": datetime.now(UTC)}
        if scheduled_at is not None:
            values["scheduled_at"] = scheduled_at
        if interviewer_id is not None:
            values["interviewer_id"] = interviewer_id
        if status is not None:
            values["status"] = status
        if notes is not None:
            values["notes"] = notes
        if updated_by is not None:
            values["updated_by"] = updated_by

        if len(values) > 1:
            await self._session.execute(
                update(Interview).where(Interview.id == interview_id).values(**values),
            )
        return await self.get_interview_by_id(interview_id)

    async def has_interviewer_conflict(
        self,
        interviewer_id: uuid.UUID,
        scheduled_at: datetime,
        *,
        exclude_interview_id: uuid.UUID | None = None,
    ) -> bool:
        window_start = scheduled_at
        window_end = scheduled_at
        conditions = [
            Interview.interviewer_id == interviewer_id,
            Interview.status == INTERVIEW_SCHEDULED,
            Interview.scheduled_at == scheduled_at,
        ]
        if exclude_interview_id is not None:
            conditions.append(Interview.id != exclude_interview_id)

        result = await self._session.execute(
            select(func.count()).select_from(Interview).where(*conditions),
        )
        return int(result.scalar_one()) > 0

    async def employee_exists(self, employee_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Employee.id).where(
                Employee.id == employee_id,
                Employee.deleted_at.is_(None),
            ),
        )
        return result.scalar_one_or_none() is not None

    async def get_employee_by_user_id(self, user_id: uuid.UUID) -> Employee | None:
        result = await self._session.execute(
            select(Employee).where(
                Employee.user_id == user_id,
                Employee.deleted_at.is_(None),
            ),
        )
        return result.scalar_one_or_none()

    async def get_employee_by_id(self, employee_id: uuid.UUID) -> Employee | None:
        result = await self._session.execute(
            select(Employee).where(
                Employee.id == employee_id,
                Employee.deleted_at.is_(None),
            ),
        )
        return result.scalar_one_or_none()

    # --- Notifications ---

    async def create_notification(
        self,
        *,
        user_id: uuid.UUID,
        title: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            is_read=False,
        )
        self._session.add(notification)
        await self._session.flush()
        return notification

    # --- Reporting ---

    async def recruitment_report(
        self,
        *,
        job_id: uuid.UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        job_query = select(Job.id, Job.title).where(Job.deleted_at.is_(None))
        if job_id is not None:
            job_query = job_query.where(Job.id == job_id)

        jobs_result = await self._session.execute(job_query.order_by(Job.title.asc()))
        jobs = jobs_result.all()

        rows: list[dict[str, Any]] = []
        for jid, title in jobs:
            app_query = select(
                func.count(CandidateApplication.id),
                CandidateApplication.application_status,
            ).where(
                CandidateApplication.job_id == jid,
                CandidateApplication.deleted_at.is_(None),
            )
            if date_from is not None:
                app_query = app_query.where(
                    CandidateApplication.created_at >= datetime.combine(
                        date_from,
                        datetime.min.time(),
                        tzinfo=UTC,
                    ),
                )
            if date_to is not None:
                app_query = app_query.where(
                    CandidateApplication.created_at
                    <= datetime.combine(date_to, datetime.max.time(), tzinfo=UTC),
                )
            app_query = app_query.group_by(CandidateApplication.application_status)

            counts_result = await self._session.execute(app_query)
            status_counts = {row[1]: int(row[0]) for row in counts_result.all()}

            if status is not None and status not in status_counts:
                continue

            avg_result = await self._session.execute(
                select(func.avg(CandidateApplication.ai_score)).where(
                    CandidateApplication.job_id == jid,
                    CandidateApplication.deleted_at.is_(None),
                    CandidateApplication.ai_score.is_not(None),
                ),
            )
            avg_score = avg_result.scalar_one()

            total = sum(status_counts.values())
            rows.append(
                {
                    "job_id": jid,
                    "job_title": title,
                    "total_candidates": total,
                    "shortlisted": status_counts.get("shortlisted", 0),
                    "rejected": status_counts.get("rejected", 0),
                    "pending": status_counts.get("applied", 0)
                    + status_counts.get("screening", 0),
                    "average_ai_score": float(avg_score) if avg_score is not None else None,
                    "status_breakdown": status_counts,
                },
            )

        total_items = len(rows)
        offset = (page - 1) * page_size
        return rows[offset : offset + page_size], total_items

    # --- Audit ---

    async def create_audit_log(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        ip_address: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            before_state=before_state,
            after_state=after_state,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
