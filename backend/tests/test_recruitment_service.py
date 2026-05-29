import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.constants import EMPLOYEE, HR_MANAGER, RECRUITER
from app.core.security import CurrentUser
from app.modules.recruitment.constants import (
    APPLICATION_APPLIED,
    APPLICATION_REJECTED,
    APPLICATION_SCREENING,
    JOB_STATUS_DRAFT,
    JOB_STATUS_PUBLISHED,
)
from app.modules.recruitment.errors import RecruitmentError
from app.modules.recruitment.schema import (
    CreateCandidateRequest,
    CreateJobRequest,
    ScheduleInterviewRequest,
)
from app.modules.recruitment.service import RecruitmentService


@pytest.fixture
def mock_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def service(mock_session: AsyncMock, mock_repository: AsyncMock) -> RecruitmentService:
    return RecruitmentService(mock_session, repository=mock_repository)


def _actor(**kwargs) -> CurrentUser:
    return CurrentUser(
        id=kwargs.get("user_id", uuid.uuid4()),
        email="user@example.com",
        roles=kwargs.get("roles", [RECRUITER]),
    )


def _job_mock(**kwargs) -> MagicMock:
    job = MagicMock()
    job.id = kwargs.get("id", uuid.uuid4())
    job.title = "Engineer"
    job.department_id = kwargs.get("department_id", uuid.uuid4())
    job.description = "Build things"
    job.status = kwargs.get("status", JOB_STATUS_DRAFT)
    job.created_by = uuid.uuid4()
    job.created_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)
    job.skills = []
    job.department = None
    job.creator = MagicMock(email="hr@example.com")
    return job


def _application_mock(**kwargs) -> MagicMock:
    application = MagicMock()
    application.id = kwargs.get("id", uuid.uuid4())
    application.candidate_id = uuid.uuid4()
    application.job_id = uuid.uuid4()
    application.application_status = kwargs.get("status", APPLICATION_APPLIED)
    application.ai_score = None
    application.ranking = None
    application.recommendation = None
    application.recruiter_override = False
    application.created_at = datetime.now(UTC)
    application.candidate = MagicMock(
        full_name="Jane Doe",
        email="jane@example.com",
    )
    application.job = MagicMock(title="Engineer", department_id=uuid.uuid4())
    return application


@pytest.mark.asyncio
async def test_publish_job_invalid_transition(
    service: RecruitmentService,
    mock_repository: AsyncMock,
) -> None:
    job = _job_mock(status=JOB_STATUS_PUBLISHED)
    mock_repository.get_job_by_id.return_value = job

    with pytest.raises(RecruitmentError) as exc_info:
        await service.publish_job(
            job.id,
            actor=_actor(roles=[HR_MANAGER]),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_create_candidate_duplicate_email(
    service: RecruitmentService,
    mock_repository: AsyncMock,
) -> None:
    mock_repository.get_candidate_by_email.return_value = MagicMock()

    with pytest.raises(RecruitmentError) as exc_info:
        await service.create_candidate(
            CreateCandidateRequest(
                full_name="Jane",
                email="jane@example.com",
            ),
            actor=_actor(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_application_skip_stage_rejected(
    service: RecruitmentService,
    mock_repository: AsyncMock,
) -> None:
    application = _application_mock(status=APPLICATION_APPLIED)
    mock_repository.get_application_by_id.return_value = application

    with pytest.raises(RecruitmentError):
        await service.update_application_status(
            application.id,
            "offered",
            actor=_actor(),
            ip_address="127.0.0.1",
        )


@pytest.mark.asyncio
async def test_employee_cannot_list_applications(
    service: RecruitmentService,
) -> None:
    with pytest.raises(RecruitmentError) as exc_info:
        await service.list_applications(actor=_actor(roles=[EMPLOYEE]))
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_schedule_interview_rejected_application(
    service: RecruitmentService,
    mock_repository: AsyncMock,
) -> None:
    application = _application_mock(status=APPLICATION_REJECTED)
    mock_repository.get_application_by_id.return_value = application

    with pytest.raises(RecruitmentError) as exc_info:
        await service.schedule_interview(
            ScheduleInterviewRequest(
                application_id=application.id,
                scheduled_at=datetime.now(UTC) + timedelta(days=1),
            ),
            actor=_actor(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_interviewer_double_booking(
    service: RecruitmentService,
    mock_repository: AsyncMock,
) -> None:
    application = _application_mock(status="screening")
    mock_repository.get_application_by_id.return_value = application
    mock_repository.employee_exists.return_value = True
    mock_repository.has_interviewer_conflict.return_value = True

    interviewer_id = uuid.uuid4()
    with pytest.raises(RecruitmentError) as exc_info:
        await service.schedule_interview(
            ScheduleInterviewRequest(
                application_id=application.id,
                scheduled_at=datetime.now(UTC) + timedelta(days=2),
                interviewer_id=interviewer_id,
            ),
            actor=_actor(),
            ip_address="127.0.0.1",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_upload_resume_invalid_mime(
    service: RecruitmentService,
    mock_repository: AsyncMock,
) -> None:
    candidate_id = uuid.uuid4()
    mock_repository.get_candidate_by_id.return_value = MagicMock(id=candidate_id)

    upload = MagicMock()
    upload.filename = "resume.txt"
    upload.read = AsyncMock(return_value=b"not a resume")

    with pytest.raises(RecruitmentError) as exc_info:
        await service.upload_resume(candidate_id, upload, actor=_actor())
    assert "PDF and DOCX" in exc_info.value.message


@pytest.mark.asyncio
async def test_upload_resume_pdf_success(
    service: RecruitmentService,
    mock_repository: AsyncMock,
    tmp_path,
) -> None:
    service._settings.resume_upload_dir = str(tmp_path)
    candidate_id = uuid.uuid4()
    mock_repository.get_candidate_by_id.return_value = MagicMock(id=candidate_id)
    mock_repository.create_resume_file.return_value = MagicMock(
        id=uuid.uuid4(),
        file_name="resume.pdf",
        file_url="/uploads/resumes/x.pdf",
    )

    upload = MagicMock()
    upload.filename = "resume.pdf"
    upload.read = AsyncMock(return_value=b"%PDF-1.4 test content")

    result = await service.upload_resume(candidate_id, upload, actor=_actor())
    assert result.resume_file_id is not None
    mock_repository.create_resume_file.assert_awaited()
