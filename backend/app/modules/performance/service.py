from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEPARTMENT_MANAGER,
    EMPLOYEE,
    HR_MANAGER,
    SYSTEM_ADMINISTRATOR,
)
from app.core.security import CurrentUser
from app.modules.employee.model import Department, Employee
from app.modules.performance.errors import PerformanceError
from app.modules.performance.model import (
    EmployeeMetricScore,
    PerformanceCycle,
    PerformanceFeedback,
    PerformanceMetric,
    PerformanceReview,
)
from app.modules.performance.repository import PerformanceRepository
from app.modules.performance.schema import (
    CycleListResponse,
    CycleRequest,
    CycleResponse,
    EmployeePerformanceSummary,
    EmployeePerformanceSummaryListResponse,
    FeedbackRequest,
    FeedbackResponse,
    MetricScoreRequest,
    MetricScoreResponse,
    PerformanceMetricListResponse,
    PerformanceMetricRequest,
    PerformanceMetricResponse,
    ReviewListResponse,
    ReviewRequest,
    ReviewResponse,
    build_pagination,
)


class PerformanceService:
    def __init__(
        self,
        session: AsyncSession,
        repository: PerformanceRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or PerformanceRepository(session)

    # --- Helpers ---
    def _is_hr_or_admin(self, actor: CurrentUser) -> bool:
        return bool({HR_MANAGER, SYSTEM_ADMINISTRATOR}.intersection(actor.roles))

    def _is_manager(self, actor: CurrentUser) -> bool:
        return DEPARTMENT_MANAGER in actor.roles

    def _is_employee(self, actor: CurrentUser) -> bool:
        return EMPLOYEE in actor.roles

    async def resolve_actor_employee(self, actor: CurrentUser) -> Employee:
        employee = await self._repository.get_employee_by_user_id(actor.id)
        if employee is None:
            raise PerformanceError("Employee profile not found", 404)
        return employee

    def _full_name(self, employee: Employee) -> str:
        return f"{employee.first_name} {employee.last_name}".strip()

    def _cycle_status(self, cycle: PerformanceCycle) -> str:
        today = date.today()
        if today < cycle.start_date:
            return "draft"
        if cycle.start_date <= today <= cycle.end_date:
            return "active"
        return "completed"

    def _to_employee_summary(self, employee: Employee) -> dict[str, Any]:
        return {
            "id": employee.id,
            "employee_code": employee.employee_code,
            "full_name": self._full_name(employee),
            "department_name": employee.department.name if employee.department else None,
        }

    def _to_cycle_response(self, cycle: PerformanceCycle) -> CycleResponse:
        return CycleResponse(
            id=cycle.id,
            name=cycle.name,
            start_date=cycle.start_date,
            end_date=cycle.end_date,
            status=self._cycle_status(cycle),  # type: ignore[arg-type]
        )

    def _average_metric_score(self, scores: Iterable[EmployeeMetricScore]) -> float | None:
        values = [float(s.score) for s in scores]
        if not values:
            return None
        return sum(values) / len(values)

    def _to_metric_score_response(
        self, score: EmployeeMetricScore
    ) -> MetricScoreResponse:
        return MetricScoreResponse(
            id=score.id,
            review_id=score.review_id,
            metric_id=score.metric_id,
            metric_name=score.metric.name if score.metric else "",  # type: ignore[union-attr]
            score=float(score.score),
        )

    def _to_feedback_response(
        self,
        feedback: PerformanceFeedback,
    ) -> FeedbackResponse:
        author = (
            self._to_employee_summary(feedback.author)
            if getattr(feedback, "author", None) is not None
            else None
        )
        return FeedbackResponse(
            id=feedback.id,
            review_id=feedback.review_id,
            feedback_text=feedback.feedback_text,
            created_by=feedback.created_by,
            author=author,  # type: ignore[arg-type]
            created_at=feedback.created_at,
        )

    def _to_review_response(self, review: PerformanceReview) -> ReviewResponse:
        employee_summary = self._to_employee_summary(review.employee)
        reviewer_summary = self._to_employee_summary(review.reviewer)
        cycle_response = self._to_cycle_response(review.cycle)
        average = self._average_metric_score(review.metric_scores)

        return ReviewResponse(
            id=review.id,
            cycle=cycle_response,
            employee=employee_summary,  # type: ignore[arg-type]
            reviewer=reviewer_summary,  # type: ignore[arg-type]
            rating=float(review.rating),
            comments=review.comments,
            created_at=review.created_at,
            average_metric_score=average,
            metric_scores=[self._to_metric_score_response(s) for s in review.metric_scores],
            feedback_entries=[self._to_feedback_response(f) for f in review.feedback_entries],
        )

    def _to_employee_performance_summary(
        self, review: PerformanceReview
    ) -> EmployeePerformanceSummary:
        full = self._to_review_response(review)
        return EmployeePerformanceSummary(
            review_id=full.id,
            cycle=full.cycle,
            employee=full.employee,
            reviewer=full.reviewer,
            rating=full.rating,
            average_metric_score=full.average_metric_score,
            metric_scores=full.metric_scores,
            feedback_entries=full.feedback_entries,
            feedback_count=len(full.feedback_entries),
        )

    # --- Cycles ---
    async def create_cycle(
        self,
        body: CycleRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> CycleResponse:
        if not self._is_hr_or_admin(actor):
            raise PerformanceError("Insufficient permissions", 403)

        if body.end_date < body.start_date:
            raise PerformanceError("end_date must be on or after start_date", 400)

        existing = await self._repository.get_cycle_by_name(body.name)
        if existing is not None:
            raise PerformanceError("A cycle with this name already exists", 409)

        cycle = await self._repository.create_cycle(
            name=body.name,
            start_date=body.start_date,
            end_date=body.end_date,
            created_by=actor.id,
            updated_by=actor.id,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="review_cycle_create",
            resource_type="performance_cycles",
            resource_id=cycle.id,
            ip_address=ip_address,
            after_state=self._cycle_snapshot(cycle),
        )

        await self._session.commit()
        return self._to_cycle_response(cycle)

    async def list_cycles(
        self,
        *,
        page: int,
        page_size: int,
    ) -> CycleListResponse:
        cycles, total = await self._repository.list_cycles(page=page, page_size=page_size)
        return CycleListResponse(
            items=[self._to_cycle_response(c) for c in cycles],
            pagination=build_pagination(page, page_size, total),
        )

    async def get_cycle(self, cycle_id: uuid.UUID) -> CycleResponse:
        cycle = await self._repository.get_cycle_by_id(cycle_id)
        if cycle is None:
            raise PerformanceError("Cycle not found", 404)
        return self._to_cycle_response(cycle)

    def _cycle_snapshot(self, cycle: PerformanceCycle) -> dict[str, Any]:
        return {
            "id": str(cycle.id),
            "name": cycle.name,
            "start_date": cycle.start_date.isoformat(),
            "end_date": cycle.end_date.isoformat(),
        }

    # --- Reviews ---
    async def _resolve_reviewer_id_for_create(
        self,
        *,
        actor: CurrentUser,
        employee_id: uuid.UUID,
    ) -> tuple[uuid.UUID, uuid.UUID]:
        actor_employee = await self.resolve_actor_employee(actor)
        reviewer_id = actor_employee.id

        if self._is_hr_or_admin(actor):
            return reviewer_id, employee_id

        if self._is_manager(actor):
            direct_ids = await self._repository.get_direct_report_ids(reviewer_id)
            if employee_id not in direct_ids:
                raise PerformanceError("Insufficient permissions", 403)
            return reviewer_id, employee_id

        if self._is_employee(actor):
            if employee_id != reviewer_id:
                raise PerformanceError("Insufficient permissions", 403)
            return reviewer_id, employee_id

        raise PerformanceError("Insufficient permissions", 403)

    def _can_read_review(self, *, actor: CurrentUser, review: PerformanceReview) -> bool:
        # HR/admin can read everything. Others can read if they are involved.
        if self._is_hr_or_admin(actor):
            return True

        # For non-admin roles, reviewer_id and employee_id are the relevant scopes.
        return actor.id in {review.employee.user_id, review.reviewer.user_id}  # type: ignore[attr-defined]

    def _can_modify_review(
        self,
        *,
        actor: CurrentUser,
        actor_employee_id: uuid.UUID,
        review: PerformanceReview,
    ) -> None:
        if self._is_hr_or_admin(actor):
            return

        if review.reviewer_id != actor_employee_id:
            raise PerformanceError("Insufficient permissions", 403)

        # Employees can only modify self-review (reviewer is the employee).
        if self._is_employee(actor) and review.employee_id != actor_employee_id:
            raise PerformanceError("Insufficient permissions", 403)

    async def create_review(
        self,
        body: ReviewRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> ReviewResponse:
        if body.rating < 1.0 or body.rating > 5.0:
            raise PerformanceError("rating must be between 1 and 5", 400)

        cycle = await self._repository.get_cycle_by_id(body.cycle_id)
        if cycle is None:
            raise PerformanceError("Cycle not found", 404)

        reviewer_id, employee_id = await self._resolve_reviewer_id_for_create(
            actor=actor,
            employee_id=body.employee_id,
        )

        employee = await self._repository.get_employee_by_id(employee_id)
        if employee is None:
            raise PerformanceError("Employee not found", 404)

        reviewer = await self._repository.get_employee_by_id(reviewer_id)
        if reviewer is None:
            raise PerformanceError("Reviewer not found", 404)

        existing = await self._repository.get_review_by_keys(
            cycle_id=body.cycle_id,
            employee_id=employee_id,
            reviewer_id=reviewer_id,
        )
        if existing is not None:
            raise PerformanceError(
                "Duplicate performance review for this cycle/employee/reviewer",
                409,
            )

        review = await self._repository.create_review(
            cycle_id=body.cycle_id,
            employee_id=employee_id,
            reviewer_id=reviewer_id,
            rating=body.rating,
            comments=body.comments,
        )

        # Repository creates/flushes, but we still snapshot the payload for audit.
        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="performance_review_create",
            resource_type="performance_reviews",
            resource_id=review.id,
            ip_address=ip_address,
            after_state={
                "cycle_id": str(review.cycle_id),
                "employee_id": str(review.employee_id),
                "reviewer_id": str(review.reviewer_id),
                "rating": float(review.rating),
                "comments": review.comments,
            },
        )

        # Notification trigger (T-135): notify employee when a review is created for them.
        if employee.user_id is not None:
            await self._repository.create_notification(
                user_id=employee.user_id,
                title="Performance review created",
                message=(
                    f"A performance review was created for cycle '{cycle.name}' "
                    f"by {reviewer.first_name} {reviewer.last_name}."
                ),
            )

        await self._session.commit()
        return self._to_review_response(review)

    async def list_my_reviews(
        self,
        *,
        actor: CurrentUser,
        page: int,
        page_size: int,
    ) -> EmployeePerformanceSummaryListResponse:
        actor_employee = await self.resolve_actor_employee(actor)
        reviews, total = await self._repository.list_reviews(
            employee_id=actor_employee.id,
            cycle_id=None,
            reviewer_id=None,
            page=page,
            page_size=page_size,
        )
        return EmployeePerformanceSummaryListResponse(
            items=[self._to_employee_performance_summary(r) for r in reviews],
            pagination=build_pagination(page, page_size, total),
        )

    async def list_team_reviews(
        self,
        *,
        actor: CurrentUser,
        cycle_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> EmployeePerformanceSummaryListResponse:
        if not (self._is_manager(actor) or self._is_hr_or_admin(actor)):
            raise PerformanceError("Insufficient permissions", 403)

        manager_employee = await self.resolve_actor_employee(actor)
        direct_ids = await self._repository.get_direct_report_ids(manager_employee.id)
        reviews, total = await self._repository.list_reviews_for_employee_ids(
            employee_ids=direct_ids,
            cycle_id=cycle_id,
            page=page,
            page_size=page_size,
        )
        return EmployeePerformanceSummaryListResponse(
            items=[self._to_employee_performance_summary(r) for r in reviews],
            pagination=build_pagination(page, page_size, total),
        )

    async def list_employee_history(
        self,
        *,
        actor: CurrentUser,
        employee_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> EmployeePerformanceSummaryListResponse:
        if not (self._is_hr_or_admin(actor) or self._is_employee(actor)):
            raise PerformanceError("Insufficient permissions", 403)

        if self._is_employee(actor):
            actor_employee = await self.resolve_actor_employee(actor)
            if actor_employee.id != employee_id:
                raise PerformanceError("Insufficient permissions", 403)

        reviews, total = await self._repository.list_reviews(
            employee_id=employee_id,
            cycle_id=None,
            reviewer_id=None,
            page=page,
            page_size=page_size,
        )
        return EmployeePerformanceSummaryListResponse(
            items=[self._to_employee_performance_summary(r) for r in reviews],
            pagination=build_pagination(page, page_size, total),
        )

    # --- Metrics ---
    async def list_metrics(
        self,
        *,
        page: int,
        page_size: int,
    ) -> PerformanceMetricListResponse:
        metrics, total = await self._repository.list_metrics(page=page, page_size=page_size)
        return PerformanceMetricListResponse(
            items=[
                PerformanceMetricResponse(
                    id=m.id,
                    name=m.name,
                    description=m.description,
                )
                for m in metrics
            ],
            pagination=build_pagination(page, page_size, total),
        )

    async def create_metric(
        self,
        body: PerformanceMetricRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> PerformanceMetricResponse:
        if not self._is_hr_or_admin(actor):
            raise PerformanceError("Insufficient permissions", 403)

        if len(body.name) > 150:
            raise PerformanceError("Metric name max 150 chars", 400)

        metric = await self._repository.create_metric(
            name=body.name,
            description=body.description,
            created_by=actor.id,
            updated_by=actor.id,
        )
        await self._session.commit()
        return PerformanceMetricResponse(id=metric.id, name=metric.name, description=metric.description)

    async def get_metric(self, metric_id: uuid.UUID) -> PerformanceMetricResponse:
        metric = await self._repository.get_metric_by_id(metric_id)
        if metric is None:
            raise PerformanceError("Metric not found", 404)
        return PerformanceMetricResponse(id=metric.id, name=metric.name, description=metric.description)

    async def update_metric(
        self,
        metric_id: uuid.UUID,
        body: PerformanceMetricRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> PerformanceMetricResponse:
        if not self._is_hr_or_admin(actor):
            raise PerformanceError("Insufficient permissions", 403)

        updated = await self._repository.update_metric(
            metric_id=metric_id,
            name=body.name,
            description=body.description,
            updated_by=actor.id,
        )
        if updated is None:
            raise PerformanceError("Metric not found", 404)

        await self._session.commit()
        return PerformanceMetricResponse(id=updated.id, name=updated.name, description=updated.description)

    async def delete_metric(
        self,
        metric_id: uuid.UUID,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> None:
        if not self._is_hr_or_admin(actor):
            raise PerformanceError("Insufficient permissions", 403)

        if await self._repository.metric_has_scores(metric_id):
            raise PerformanceError("Cannot delete metric with existing scores", 409)

        await self._repository.delete_metric(metric_id)
        await self._session.commit()

    # --- Metric scores ---
    async def add_metric_score(
        self,
        review_id: uuid.UUID,
        body: MetricScoreRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> MetricScoreResponse:
        if body.score < 0.0 or body.score > 100.0:
            raise PerformanceError("score must be between 0 and 100", 400)

        review = await self._repository.get_review_by_id(review_id=review_id)
        if review is None:
            raise PerformanceError("Review not found", 404)

        metric = await self._repository.get_metric_by_id(body.metric_id)
        if metric is None:
            raise PerformanceError("Metric not found", 404)

        actor_employee = await self.resolve_actor_employee(actor)
        self._can_modify_review(
            actor=actor,
            actor_employee_id=actor_employee.id,
            review=review,
        )

        before = await self._repository.get_metric_score_by_keys(
            review_id=review_id,
            metric_id=body.metric_id,
        )

        updated_score = await self._repository.upsert_metric_score(
            review_id=review_id,
            metric_id=body.metric_id,
            score=body.score,
            actor_user_id=actor.id,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="performance_review_update",
            resource_type="performance_reviews",
            resource_id=review_id,
            ip_address=ip_address,
            before_state={"score": float(before.score) if before else None},
            after_state={"score": float(updated_score.score), "metric_id": str(metric.id)},
        )

        await self._session.commit()
        return self._to_metric_score_response(updated_score)

    async def list_metric_scores(
        self,
        review_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> list[MetricScoreResponse]:
        review = await self._repository.get_review_by_id(review_id=review_id)
        if review is None:
            raise PerformanceError("Review not found", 404)

        if not self._is_hr_or_admin(actor):
            actor_employee = await self.resolve_actor_employee(actor)
            if review.employee_id != actor_employee.id and review.reviewer_id != actor_employee.id:
                raise PerformanceError("Insufficient permissions", 403)

        # `get_review_by_id` already pre-loads metric_scores.
        return [self._to_metric_score_response(s) for s in review.metric_scores]

    # --- Feedback ---
    async def add_feedback(
        self,
        review_id: uuid.UUID,
        body: FeedbackRequest,
        *,
        actor: CurrentUser,
        ip_address: str,
    ) -> FeedbackResponse:
        review = await self._repository.get_review_by_id(review_id=review_id)
        if review is None:
            raise PerformanceError("Review not found", 404)

        actor_employee = await self.resolve_actor_employee(actor)
        self._can_modify_review(
            actor=actor,
            actor_employee_id=actor_employee.id,
            review=review,
        )

        entry = await self._repository.create_feedback(
            review_id=review_id,
            feedback_text=body.feedback_text,
            created_by_employee_id=actor_employee.id,
        )

        await self._repository.create_audit_log(
            actor_user_id=actor.id,
            action="performance_review_update",
            resource_type="performance_reviews",
            resource_id=review_id,
            ip_address=ip_address,
            after_state={"feedback_text": body.feedback_text},
        )

        await self._session.commit()

        # Build response with author details.
        author = await self._repository.get_employee_by_id(entry.created_by)
        return FeedbackResponse(
            id=entry.id,
            review_id=entry.review_id,
            feedback_text=entry.feedback_text,
            created_by=entry.created_by,
            author=self._to_employee_summary(author) if author else None,  # type: ignore[arg-type]
            created_at=entry.created_at,
        )

    async def list_feedback(
        self,
        review_id: uuid.UUID,
        *,
        actor: CurrentUser,
    ) -> list[FeedbackResponse]:
        review = await self._repository.get_review_by_id(review_id=review_id)
        if review is None:
            raise PerformanceError("Review not found", 404)

        if not self._is_hr_or_admin(actor):
            actor_employee = await self.resolve_actor_employee(actor)
            if (
                review.employee_id != actor_employee.id
                and review.reviewer_id != actor_employee.id
            ):
                raise PerformanceError("Insufficient permissions", 403)

        entries = await self._repository.list_feedback_for_review(review_id=review_id)
        return [
            FeedbackResponse(
                id=f.id,
                review_id=f.review_id,
                feedback_text=f.feedback_text,
                created_by=f.created_by,
                author=(
                    self._to_employee_summary(f.author)
                    if getattr(f, "author", None) is not None
                    else None
                ),  # type: ignore[arg-type]
                created_at=f.created_at,
            )
            for f in entries
        ]

    # --- Reporting ---
    async def performance_report(
        self,
        *,
        actor: CurrentUser,
        cycle_id: uuid.UUID | None,
        department_id: uuid.UUID | None,
        date_from: date,
        date_to: date,
        page: int,
        page_size: int,
    ):
        if not self._is_hr_or_admin(actor):
            raise PerformanceError("Insufficient permissions", 403)

        if date_from > date_to:
            raise PerformanceError("date_from must be on or before date_to", 400)

        # --- Summary: average rating per department ---
        base_reviews = (
            select(
                Employee.department_id.label("department_id"),
                Department.name.label("department_name"),
                func.avg(PerformanceReview.rating).label("avg_rating"),
            )
            .select_from(PerformanceReview)
            .join(Employee, Employee.id == PerformanceReview.employee_id)
            .join(Department, Department.id == Employee.department_id)
            .join(
                PerformanceCycle,
                PerformanceCycle.id == PerformanceReview.cycle_id,
            )
            .where(
                PerformanceCycle.start_date >= date_from,
                PerformanceCycle.start_date <= date_to,
            )
        )

        if cycle_id is not None:
            base_reviews = base_reviews.where(PerformanceReview.cycle_id == cycle_id)
        if department_id is not None:
            base_reviews = base_reviews.where(Employee.department_id == department_id)

        base_reviews = base_reviews.group_by(Employee.department_id, Department.name)

        avg_rows = (await self._session.execute(base_reviews)).all()
        average_rating_per_department = [
            {
                "department_id": r.department_id,
                "department_name": r.department_name,
                "average_rating": float(r.avg_rating) if r.avg_rating is not None else None,
            }
            for r in avg_rows
        ]

        # --- Top performers (avg rating >= 4.0) ---
        top_query = (
            select(
                Employee.id.label("employee_id"),
                Employee.employee_code.label("employee_code"),
                Employee.first_name.label("first_name"),
                Employee.last_name.label("last_name"),
                Department.name.label("department_name"),
                func.avg(PerformanceReview.rating).label("avg_rating"),
            )
            .select_from(PerformanceReview)
            .join(Employee, Employee.id == PerformanceReview.employee_id)
            .join(Department, Department.id == Employee.department_id)
            .join(
                PerformanceCycle,
                PerformanceCycle.id == PerformanceReview.cycle_id,
            )
            .where(
                PerformanceCycle.start_date >= date_from,
                PerformanceCycle.start_date <= date_to,
            )
        )

        if cycle_id is not None:
            top_query = top_query.where(PerformanceReview.cycle_id == cycle_id)
        if department_id is not None:
            top_query = top_query.where(Employee.department_id == department_id)

        top_query = top_query.group_by(
            Employee.id,
            Employee.employee_code,
            Employee.first_name,
            Employee.last_name,
            Department.name,
        ).having(func.avg(PerformanceReview.rating) >= 4.0)

        top_query = top_query.order_by(func.avg(PerformanceReview.rating).desc()).limit(20)
        top_rows = (await self._session.execute(top_query)).all()
        top_performers = [
            {
                "employee": {
                    "id": r.employee_id,
                    "employee_code": r.employee_code,
                    "full_name": f"{r.first_name} {r.last_name}".strip(),
                    "department_name": r.department_name,
                },
                "average_rating": float(r.avg_rating) if r.avg_rating is not None else None,
            }
            for r in top_rows
        ]

        # --- Score distribution across metric scores ---
        # Buckets: 0-25, 26-50, 51-75, 76-100
        # Using explicit SQL CASE via text is overkill; use SQLAlchemy `case` instead.
        from sqlalchemy import case  # local import to keep dependencies explicit

        distribution_bucket = case(
            (EmployeeMetricScore.score <= 25, "0-25"),
            (EmployeeMetricScore.score <= 50, "26-50"),
            (EmployeeMetricScore.score <= 75, "51-75"),
            else_="76-100",
        )

        dist_query = (
            select(
                distribution_bucket.label("bucket"),
                func.count(EmployeeMetricScore.id).label("count"),
            )
            .select_from(EmployeeMetricScore)
            .join(PerformanceReview, PerformanceReview.id == EmployeeMetricScore.review_id)
            .join(Employee, Employee.id == PerformanceReview.employee_id)
            .join(PerformanceCycle, PerformanceCycle.id == PerformanceReview.cycle_id)
            .where(
                PerformanceCycle.start_date >= date_from,
                PerformanceCycle.start_date <= date_to,
            )
        )

        if cycle_id is not None:
            dist_query = dist_query.where(PerformanceReview.cycle_id == cycle_id)
        if department_id is not None:
            dist_query = dist_query.where(Employee.department_id == department_id)

        dist_query = dist_query.group_by(distribution_bucket)
        dist_rows = (await self._session.execute(dist_query)).all()

        total_scores_query = (
            select(func.count(EmployeeMetricScore.id))
            .select_from(EmployeeMetricScore)
            .join(PerformanceReview, PerformanceReview.id == EmployeeMetricScore.review_id)
            .join(PerformanceCycle, PerformanceCycle.id == PerformanceReview.cycle_id)
            .join(Employee, Employee.id == PerformanceReview.employee_id)
            .where(
                PerformanceCycle.start_date >= date_from,
                PerformanceCycle.start_date <= date_to,
            )
        )
        if cycle_id is not None:
            total_scores_query = total_scores_query.where(PerformanceReview.cycle_id == cycle_id)
        if department_id is not None:
            total_scores_query = total_scores_query.where(Employee.department_id == department_id)
        total_scores = int((await self._session.execute(total_scores_query)).scalar_one())

        score_distribution = [
            {
                "bucket": r.bucket,
                "count": int(r.count),
                "percentage": (int(r.count) / total_scores * 100) if total_scores else 0.0,
            }
            for r in dist_rows
        ]

        # --- Paginated employee list ---
        count_query = (
            select(func.count(func.distinct(Employee.id)))
            .select_from(PerformanceReview)
            .join(Employee, Employee.id == PerformanceReview.employee_id)
            .join(PerformanceCycle, PerformanceCycle.id == PerformanceReview.cycle_id)
            .where(
                PerformanceCycle.start_date >= date_from,
                PerformanceCycle.start_date <= date_to,
            )
        )
        if cycle_id is not None:
            count_query = count_query.where(PerformanceReview.cycle_id == cycle_id)
        if department_id is not None:
            count_query = count_query.where(Employee.department_id == department_id)
        total_employees = int((await self._session.execute(count_query)).scalar_one())

        offset = (page - 1) * page_size
        employee_query = (
            select(
                Employee.id.label("employee_id"),
                Employee.employee_code.label("employee_code"),
                Employee.first_name.label("first_name"),
                Employee.last_name.label("last_name"),
                Department.name.label("department_name"),
                func.avg(PerformanceReview.rating).label("avg_rating"),
                func.avg(EmployeeMetricScore.score).label("avg_score"),
            )
            .select_from(PerformanceReview)
            .join(Employee, Employee.id == PerformanceReview.employee_id)
            .join(Department, Department.id == Employee.department_id)
            .join(PerformanceCycle, PerformanceCycle.id == PerformanceReview.cycle_id)
            .outerjoin(EmployeeMetricScore, EmployeeMetricScore.review_id == PerformanceReview.id)
            .where(
                PerformanceCycle.start_date >= date_from,
                PerformanceCycle.start_date <= date_to,
            )
        )
        if cycle_id is not None:
            employee_query = employee_query.where(PerformanceReview.cycle_id == cycle_id)
        if department_id is not None:
            employee_query = employee_query.where(Employee.department_id == department_id)

        employee_query = employee_query.group_by(
            Employee.id,
            Employee.employee_code,
            Employee.first_name,
            Employee.last_name,
            Department.name,
        ).order_by(func.avg(PerformanceReview.rating).desc())

        employee_query = employee_query.offset(offset).limit(page_size)
        rows = (await self._session.execute(employee_query)).all()

        employees = [
            {
                "employee": {
                    "id": r.employee_id,
                    "employee_code": r.employee_code,
                    "full_name": f"{r.first_name} {r.last_name}".strip(),
                    "department_name": r.department_name,
                },
                "average_rating": float(r.avg_rating) if r.avg_rating is not None else None,
                "average_score": float(r.avg_score) if r.avg_score is not None else None,
            }
            for r in rows
        ]

        return {
            "average_rating_per_department": average_rating_per_department,
            "top_performers": top_performers,
            "score_distribution": score_distribution,
            "employees": employees,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_employees,
                "total_pages": (total_employees + page_size - 1) // page_size,
            },
        }
