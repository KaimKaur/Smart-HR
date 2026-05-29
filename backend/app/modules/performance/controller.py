import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SuccessResponse
from app.core.security import CurrentUser
from app.modules.performance.errors import PerformanceError
from app.modules.performance.http import performance_http_exception
from app.modules.performance.schema import (
    CycleListResponse,
    CycleRequest,
    CycleResponse,
    EmployeePerformanceSummaryListResponse,
    FeedbackResponse,
    MetricScoreResponse,
    PerformanceMetricListResponse,
    PerformanceMetricRequest,
    PerformanceMetricResponse,
    ReviewRequest,
    ReviewResponse,
    build_pagination,
)
from app.modules.performance.service import PerformanceService


class PerformanceController:
    def __init__(self, session: AsyncSession) -> None:
        self._service = PerformanceService(session)

    async def create_cycle(
        self,
        body: CycleRequest,
        *,
        actor: CurrentUser,
        request: Request,
        ip_address: str,
    ) -> SuccessResponse[CycleResponse]:
        try:
            data = await self._service.create_cycle(
                body,
                actor=actor,
                ip_address=ip_address,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="Cycle created", data=data)

    async def list_cycles(
        self,
        *,
        page: int,
        page_size: int,
    ) -> SuccessResponse[CycleListResponse]:
        try:
            data = await self._service.list_cycles(page=page, page_size=page_size)
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def get_cycle(
        self,
        cycle_id: uuid.UUID,
    ) -> SuccessResponse[CycleResponse]:
        try:
            data = await self._service.get_cycle(cycle_id)
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def create_review(
        self,
        body: ReviewRequest,
        *,
        actor: CurrentUser,
        request: Request,
        ip_address: str,
    ) -> SuccessResponse[ReviewResponse]:
        try:
            data = await self._service.create_review(
                body,
                actor=actor,
                ip_address=ip_address,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="Review created", data=data)

    async def my_reviews(
        self,
        *,
        actor: CurrentUser,
        page: int,
        page_size: int,
    ) -> SuccessResponse[EmployeePerformanceSummaryListResponse]:
        try:
            data = await self._service.list_my_reviews(
                actor=actor,
                page=page,
                page_size=page_size,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def team_reviews(
        self,
        *,
        actor: CurrentUser,
        cycle_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> SuccessResponse[EmployeePerformanceSummaryListResponse]:
        try:
            data = await self._service.list_team_reviews(
                actor=actor,
                cycle_id=cycle_id,
                page=page,
                page_size=page_size,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def history(
        self,
        *,
        actor: CurrentUser,
        employee_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> SuccessResponse[EmployeePerformanceSummaryListResponse]:
        try:
            data = await self._service.list_employee_history(
                actor=actor,
                employee_id=employee_id,
                page=page,
                page_size=page_size,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def list_metrics(
        self,
        *,
        page: int,
        page_size: int,
    ) -> SuccessResponse[PerformanceMetricListResponse]:
        try:
            data = await self._service.list_metrics(page=page, page_size=page_size)
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def create_metric(
        self,
        body: PerformanceMetricRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> SuccessResponse[PerformanceMetricResponse]:
        try:
            data = await self._service.create_metric(
                body,
                actor=actor,
                ip_address=ip_address,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="Metric created", data=data)

    async def get_metric(
        self,
        metric_id: uuid.UUID,
    ) -> SuccessResponse[PerformanceMetricResponse]:
        try:
            data = await self._service.get_metric(metric_id)
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def update_metric(
        self,
        metric_id: uuid.UUID,
        body: PerformanceMetricRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
        request: Request,
    ) -> SuccessResponse[PerformanceMetricResponse]:
        try:
            data = await self._service.update_metric(
                metric_id,
                body,
                actor=actor,
                ip_address=ip_address,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="Metric updated", data=data)

    async def delete_metric(
        self,
        metric_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
        request: Request,
    ) -> None:
        try:
            await self._service.delete_metric(
                metric_id,
                actor=actor,
                ip_address=ip_address,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return None

    async def add_score(
        self,
        review_id: uuid.UUID,
        body,
        *,
        actor: CurrentUser,
        ip_address: str,
        request: Request,
    ) -> SuccessResponse[MetricScoreResponse]:
        try:
            data = await self._service.add_metric_score(
                review_id,
                body,
                actor=actor,
                ip_address=ip_address,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="Score updated", data=data)

    async def list_scores(
        self,
        review_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[list[MetricScoreResponse]]:
        try:
            data = await self._service.list_metric_scores(
                review_id,
                actor=actor,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def add_feedback(
        self,
        review_id: uuid.UUID,
        body,
        *,
        actor: CurrentUser,
        ip_address: str,
        request: Request,
    ) -> SuccessResponse[FeedbackResponse]:
        try:
            data = await self._service.add_feedback(
                review_id,
                body,
                actor=actor,
                ip_address=ip_address,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="Feedback added", data=data)

    async def list_feedback(
        self,
        review_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> SuccessResponse[list[FeedbackResponse]]:
        try:
            data = await self._service.list_feedback(
                review_id,
                actor=actor,
            )
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
        return SuccessResponse(message="OK", data=data)

    async def performance_report(
        self,
        *,
        actor: CurrentUser,
        cycle_id: uuid.UUID | None,
        department_id: uuid.UUID | None,
        date_from,
        date_to,
        page: int,
        page_size: int,
    ) -> SuccessResponse[object]:
        try:
            data = await self._service.performance_report(
                actor=actor,
                cycle_id=cycle_id,
                department_id=department_id,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=page_size,
            )
            return SuccessResponse(message="Performance report generated", data=data)
        except PerformanceError as exc:
            raise performance_http_exception(exc) from exc
