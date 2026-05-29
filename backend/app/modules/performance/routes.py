from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEPARTMENT_MANAGER,
    EMPLOYEE,
    HR_MANAGER,
    SYSTEM_ADMINISTRATOR,
)
from app.core.database import get_db
from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser, get_current_user, require_roles
from app.modules.performance.controller import PerformanceController
from app.modules.performance.schema import (
    CycleListResponse,
    CycleRequest,
    CycleResponse,
    EmployeePerformanceSummaryListResponse,
    FeedbackRequest,
    FeedbackResponse,
    MetricScoreRequest,
    MetricScoreResponse,
    PerformanceMetricListResponse,
    PerformanceMetricRequest,
    PerformanceMetricResponse,
    ReviewRequest,
    ReviewResponse,
)

router = APIRouter()

_controller_roles_review_create = require_roles(
    SYSTEM_ADMINISTRATOR,
    HR_MANAGER,
    DEPARTMENT_MANAGER,
    EMPLOYEE,
)
_hr_or_admin = require_roles(SYSTEM_ADMINISTRATOR, HR_MANAGER)
_employee_or_hr_or_admin = require_roles(EMPLOYEE, HR_MANAGER, SYSTEM_ADMINISTRATOR)
_manager_or_hr_or_admin = require_roles(
    DEPARTMENT_MANAGER,
    HR_MANAGER,
    SYSTEM_ADMINISTRATOR,
)


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


def _controller(session: AsyncSession = Depends(get_db)) -> PerformanceController:
    return PerformanceController(session)


@router.post(
    "/cycles",
    response_model=SuccessResponse[CycleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_cycle(
    body: CycleRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[CycleResponse]:
    return await controller.create_cycle(
        body,
        actor=current_user,
        request=request,
        ip_address=_client_ip(request),
    )


@router.get("/cycles", response_model=SuccessResponse[CycleListResponse])
async def list_cycles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[CycleListResponse]:
    return await controller.list_cycles(page=page, page_size=page_size)


@router.get(
    "/cycles/{cycle_id}",
    response_model=SuccessResponse[CycleResponse],
)
async def get_cycle(
    cycle_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[CycleResponse]:
    return await controller.get_cycle(cycle_id)


@router.post(
    "/reviews",
    response_model=SuccessResponse[ReviewResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    body: ReviewRequest,
    request: Request,
    current_user: CurrentUser = Depends(_controller_roles_review_create),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[ReviewResponse]:
    return await controller.create_review(
        body,
        actor=current_user,
        request=request,
        ip_address=_client_ip(request),
    )


@router.get(
    "/my-reviews",
    response_model=SuccessResponse[EmployeePerformanceSummaryListResponse],
)
async def my_reviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_employee_or_hr_or_admin),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[EmployeePerformanceSummaryListResponse]:
    return await controller.my_reviews(
        actor=current_user,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/team",
    response_model=SuccessResponse[EmployeePerformanceSummaryListResponse],
)
async def team_reviews(
    cycle_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_manager_or_hr_or_admin),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[EmployeePerformanceSummaryListResponse]:
    return await controller.team_reviews(
        actor=current_user,
        cycle_id=cycle_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/employees/{employee_id}/history",
    response_model=SuccessResponse[EmployeePerformanceSummaryListResponse],
)
async def employee_history(
    employee_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(_employee_or_hr_or_admin),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[EmployeePerformanceSummaryListResponse]:
    return await controller.history(
        actor=current_user,
        employee_id=employee_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/metrics",
    response_model=SuccessResponse[PerformanceMetricListResponse],
)
async def list_metrics(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[PerformanceMetricListResponse]:
    return await controller.list_metrics(page=page, page_size=page_size)


@router.post(
    "/metrics",
    response_model=SuccessResponse[PerformanceMetricResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_metric(
    body: PerformanceMetricRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[PerformanceMetricResponse]:
    return await controller.create_metric(
        body,
        actor=current_user,
        ip_address=_client_ip(request),
    )


@router.get(
    "/metrics/{metric_id}",
    response_model=SuccessResponse[PerformanceMetricResponse],
)
async def get_metric(
    metric_id: UUID,
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[PerformanceMetricResponse]:
    return await controller.get_metric(metric_id)


@router.patch(
    "/metrics/{metric_id}",
    response_model=SuccessResponse[PerformanceMetricResponse],
)
async def update_metric(
    metric_id: UUID,
    body: PerformanceMetricRequest,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[PerformanceMetricResponse]:
    return await controller.update_metric(
        metric_id,
        body,
        actor=current_user,
        request=request,
        ip_address=_client_ip(request),
    )


@router.delete(
    "/metrics/{metric_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_metric(
    metric_id: UUID,
    request: Request,
    current_user: CurrentUser = Depends(_hr_or_admin),
    controller: PerformanceController = Depends(_controller),
):
    return await controller.delete_metric(
        metric_id,
        actor=current_user,
        request=request,
        ip_address=_client_ip(request),
    )


@router.post(
    "/reviews/{review_id}/scores",
    response_model=SuccessResponse[MetricScoreResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_score(
    review_id: UUID,
    body: MetricScoreRequest,
    request: Request,
    current_user: CurrentUser = Depends(_controller_roles_review_create),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[MetricScoreResponse]:
    return await controller.add_score(
        review_id,
        body,
        actor=current_user,
        request=request,
        ip_address=_client_ip(request),
    )


@router.get(
    "/reviews/{review_id}/scores",
    response_model=SuccessResponse[list[MetricScoreResponse]],
)
async def list_scores(
    review_id: UUID,
    current_user: CurrentUser = Depends(_controller_roles_review_create),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[list[MetricScoreResponse]]:
    return await controller.list_scores(
        review_id,
        actor=current_user,
    )


@router.post(
    "/reviews/{review_id}/feedback",
    response_model=SuccessResponse[FeedbackResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_feedback(
    review_id: UUID,
    body: FeedbackRequest,
    request: Request,
    current_user: CurrentUser = Depends(_controller_roles_review_create),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[FeedbackResponse]:
    return await controller.add_feedback(
        review_id,
        body,
        actor=current_user,
        request=request,
        ip_address=_client_ip(request),
    )


@router.get(
    "/reviews/{review_id}/feedback",
    response_model=SuccessResponse[list[FeedbackResponse]],
)
async def list_feedback(
    review_id: UUID,
    current_user: CurrentUser = Depends(_controller_roles_review_create),
    controller: PerformanceController = Depends(_controller),
) -> SuccessResponse[list[FeedbackResponse]]:
    return await controller.list_feedback(
        review_id,
        actor=current_user,
    )

