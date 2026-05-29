import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.screener import CandidateScreener
from app.core.config import Settings
from app.core.security import CurrentUser
from app.core.constants import RECRUITER
from app.modules.recruitment.service import RecruitmentService


def _application_mock(**kwargs) -> MagicMock:
    application = MagicMock()
    application.id = kwargs.get("id", uuid.uuid4())
    application.candidate_id = uuid.uuid4()
    application.job_id = uuid.uuid4()
    application.application_status = "applied"
    application.ai_score = None
    application.ranking = None
    application.recommendation = None
    application.recruiter_override = False
    application.created_at = datetime.now(UTC)

    candidate = MagicMock()
    candidate.id = application.candidate_id
    candidate.full_name = "Jane Doe"
    candidate.email = "jane@example.com"

    skill = MagicMock()
    skill.skill_name = "Python"

    job = MagicMock()
    job.id = application.job_id
    job.title = "Backend Engineer"
    job.description = "Build APIs with Python"
    job.skills = [skill]

    application.candidate = candidate
    application.job = job
    return application


@pytest.mark.asyncio
async def test_screener_persists_analysis_and_score() -> None:
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_repository = AsyncMock()

    application = _application_mock()
    mock_repository.get_application_by_id.return_value = application
    mock_repository.get_active_resume_file.return_value = MagicMock(
        file_url="/uploads/resumes/test.pdf",
    )
    mock_repository.create_resume_analysis.return_value = MagicMock(
        id=uuid.uuid4(),
    )

    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        JWT_SECRET_KEY="test-jwt-secret-key-min-32-chars-long",
        JWT_REFRESH_SECRET_KEY="test-jwt-refresh-secret-key-min-32-chars",
        AI_API_KEY="test",
        resume_upload_dir="uploads/resumes",
    )

    screener = CandidateScreener(
        mock_session,
        repository=mock_repository,
        settings=settings,
    )

    llm_payload = {
        "score": 75,
        "summary": "Good match",
        "strengths": ["Python"],
        "weaknesses": [],
        "recommendation": "proceed",
    }

    with (
        patch("app.ai.screener.extract_text", return_value="Python FastAPI SQL developer"),
        patch.object(
            screener._llm,
            "complete_json",
            new_callable=AsyncMock,
            return_value=llm_payload,
        ),
        patch.object(
            screener,
            "_resolve_file_path",
            return_value="fake.pdf",
        ),
    ):
        result = await screener.screen_application(application.id)

    assert 0 <= result["score"] <= 100
    assert result["ai_score"] == 75
    assert "Python" in result["matched_skills"] or result["matched_skills"]
    mock_repository.update_application_ai_fields.assert_awaited()
    mock_repository.recompute_job_rankings.assert_awaited()
    mock_repository.create_resume_analysis.assert_awaited()


@pytest.mark.asyncio
async def test_screen_application_endpoint_flow() -> None:
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_repository = AsyncMock()

    application = _application_mock()
    mock_repository.get_application_by_id.return_value = application
    mock_repository.get_active_resume_file.return_value = MagicMock(
        file_url="/uploads/resumes/r.pdf",
    )

    service = RecruitmentService(mock_session, repository=mock_repository)
    screening_result = {
        "analysis_id": str(uuid.uuid4()),
        "application_id": str(application.id),
        "candidate_id": str(application.candidate_id),
        "job_id": str(application.job_id),
        "analysis_status": "complete",
        "score": 80.0,
        "ai_score": 80.0,
        "recommendation": "Shortlist",
        "matched_skills": ["python"],
        "missing_skills": [],
        "extracted_skills": ["Python"],
        "explanation": {"summary": "ok"},
    }

    with patch.object(
        service,
        "_run_screening",
        new_callable=AsyncMock,
        return_value=screening_result,
    ):
        response = await service.screen_application(
            application.id,
            actor=CurrentUser(
                id=uuid.uuid4(),
                email="r@example.com",
                roles=[RECRUITER],
            ),
        )

    assert response.score == 80.0
    assert response.ai_score == 80.0


@pytest.mark.asyncio
async def test_llm_failure_leaves_ai_score_null() -> None:
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_repository = AsyncMock()

    application = _application_mock()
    mock_repository.get_application_by_id.return_value = application
    mock_repository.get_active_resume_file.return_value = MagicMock(
        file_url="/uploads/resumes/r.pdf",
    )
    mock_repository.create_resume_analysis.return_value = MagicMock(id=uuid.uuid4())

    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        JWT_SECRET_KEY="test-jwt-secret-key-min-32-chars-long",
        JWT_REFRESH_SECRET_KEY="test-jwt-refresh-secret-key-min-32-chars",
        AI_API_KEY="test",
    )

    screener = CandidateScreener(mock_session, repository=mock_repository, settings=settings)

    with (
        patch("app.ai.screener.extract_text", return_value="Python developer"),
        patch.object(
            screener._llm,
            "complete_json",
            new_callable=AsyncMock,
            side_effect=Exception("LLM down"),
        ),
        patch.object(screener, "_resolve_file_path", return_value="f.pdf"),
    ):
        result = await screener.screen_application(application.id)

    assert result["analysis_status"] == "failed"
    assert result["ai_score"] is None
    mock_repository.update_application_ai_fields.assert_not_awaited()
