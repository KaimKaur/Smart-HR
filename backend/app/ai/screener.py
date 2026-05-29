from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.extractor import extract_skills
from app.ai.llm_client import LLMClient, LLMClientError
from app.ai.matcher import compute_match
from app.ai.parser import extract_text
from app.ai.prompts import SCREENING_SYSTEM_PROMPT, build_screening_user_prompt
from app.ai.schemas import LLMScreeningResult
from app.ai.scorer import generate_recommendation, map_llm_recommendation
from app.core.config import Settings, get_settings
from app.modules.recruitment.repository import RecruitmentRepository

logger = logging.getLogger(__name__)


class CandidateScreener:
    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: RecruitmentRepository | None = None,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or RecruitmentRepository(session)
        self._settings = settings or get_settings()
        self._llm = llm_client or LLMClient(self._settings)

    async def screen_application(
        self,
        application_id: uuid.UUID,
        *,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        application = await self._repository.get_application_by_id(application_id)
        if application is None:
            raise ValueError("Application not found")

        candidate = application.candidate
        job = application.job

        resolved_path = file_path
        if resolved_path is None:
            resume = await self._repository.get_active_resume_file(candidate.id)
            if resume is None:
                raise ValueError("No resume file found for candidate")
            resolved_path = self._resolve_file_path(resume.file_url)

        resume_text = extract_text(resolved_path)
        job_skills = [skill.skill_name for skill in job.skills]

        candidate_skills = extract_skills(resume_text)
        match = compute_match(job_skills, candidate_skills)

        llm_result: LLMScreeningResult | None = None
        llm_error: str | None = None

        if self._llm.is_configured and resume_text.strip():
            try:
                raw = await self._llm.complete_json(
                    system_prompt=SCREENING_SYSTEM_PROMPT,
                    user_prompt=build_screening_user_prompt(
                        job_title=job.title,
                        job_description=job.description,
                        job_skills=job_skills,
                        resume_text=resume_text,
                    ),
                )
                llm_result = LLMScreeningResult.model_validate(raw)
            except (LLMClientError, ValidationError, Exception) as exc:
                llm_error = str(exc)
                logger.warning("LLM screening failed for %s: %s", application_id, exc)

        if llm_result is not None:
            final_score = Decimal(str(llm_result.score))
            recommendation = map_llm_recommendation(llm_result.recommendation)
            analysis_status = "complete"
            explanation: dict[str, Any] = {
                "summary": llm_result.summary,
                "strengths": llm_result.strengths,
                "weaknesses": llm_result.weaknesses,
                "llm_recommendation": llm_result.recommendation,
                "tfidf_score": float(match.score),
            }
            ai_score: Decimal | None = final_score
        else:
            final_score = Decimal(str(match.score))
            recommendation = generate_recommendation(float(match.score))
            analysis_status = "failed" if llm_error else "complete"
            explanation = {
                "summary": "Automated skill-based screening",
                "tfidf_score": float(match.score),
                "error": llm_error,
            }
            ai_score = final_score if llm_error is None else None

        await self._repository.delete_analyses_for_application(application_id)

        analysis = await self._repository.create_resume_analysis(
            candidate_id=candidate.id,
            application_id=application_id,
            analysis_status=analysis_status,
            extracted_skills={"skills": candidate_skills},
            matched_skills={"skills": match.matched_skills},
            missing_skills={"skills": match.missing_skills},
            score=final_score if ai_score is not None else Decimal("0"),
            recommendation=recommendation,
            explanation=explanation,
        )

        if ai_score is not None:
            await self._repository.update_application_ai_fields(
                application_id,
                ai_score=ai_score,
                recommendation=recommendation,
            )
            await self._repository.recompute_job_rankings(job.id)

        await self._session.commit()

        return {
            "analysis_id": str(analysis.id),
            "application_id": str(application_id),
            "candidate_id": str(candidate.id),
            "job_id": str(job.id),
            "analysis_status": analysis_status,
            "score": float(final_score),
            "ai_score": float(ai_score) if ai_score is not None else None,
            "recommendation": recommendation,
            "matched_skills": match.matched_skills,
            "missing_skills": match.missing_skills,
            "extracted_skills": candidate_skills,
            "explanation": explanation,
        }

    async def screen_candidate(
        self,
        candidate_id: uuid.UUID,
        job_id: uuid.UUID,
        *,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        application = await self._repository.get_application_by_candidate_job(
            candidate_id,
            job_id,
        )
        if application is None:
            raise ValueError("Application not found for candidate and job")
        return await self.screen_application(application.id, file_path=file_path)

    def _resolve_file_path(self, file_url: str) -> str:
        name = file_url.rstrip("/").split("/")[-1]
        return str(Path(self._settings.resume_upload_dir) / name)
