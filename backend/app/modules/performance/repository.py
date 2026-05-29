from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.notifications.model import AuditLog, Notification
from app.modules.employee.model import Employee
from app.modules.performance.model import (
    EmployeeMetricScore,
    PerformanceCycle,
    PerformanceFeedback,
    PerformanceMetric,
    PerformanceReview,
)


class PerformanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- Employee helpers ---
    async def get_employee_by_id(
        self, employee_id: uuid.UUID
    ) -> Employee | None:
        result = await self._session.execute(
            select(Employee)
            .where(Employee.id == employee_id, Employee.deleted_at.is_(None))
            .options(selectinload(Employee.department))
        )
        return result.scalar_one_or_none()

    async def get_employee_by_user_id(
        self, user_id: uuid.UUID
    ) -> Employee | None:
        result = await self._session.execute(
            select(Employee)
            .where(Employee.user_id == user_id, Employee.deleted_at.is_(None))
            .options(selectinload(Employee.department))
        )
        return result.scalar_one_or_none()

    async def get_direct_report_ids(self, manager_employee_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(Employee.id).where(
                Employee.manager_id == manager_employee_id,
                Employee.deleted_at.is_(None),
            ),
        )
        return list(result.scalars().all())

    # --- Performance cycles ---
    async def get_cycle_by_name(self, name: str) -> PerformanceCycle | None:
        result = await self._session.execute(
            select(PerformanceCycle).where(PerformanceCycle.name == name),
        )
        return result.scalar_one_or_none()

    async def create_cycle(
        self,
        *,
        name: str,
        start_date: date,
        end_date: date,
        created_by: uuid.UUID | None,
        updated_by: uuid.UUID | None,
    ) -> PerformanceCycle:
        cycle = PerformanceCycle(
            name=name,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
            updated_by=updated_by,
        )
        self._session.add(cycle)
        await self._session.flush()
        return cycle

    async def get_cycle_by_id(
        self, cycle_id: uuid.UUID
    ) -> PerformanceCycle | None:
        result = await self._session.execute(
            select(PerformanceCycle).where(PerformanceCycle.id == cycle_id),
        )
        return result.scalar_one_or_none()

    async def list_cycles(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[PerformanceCycle], int]:
        count_query = select(func.count()).select_from(PerformanceCycle)
        total_items = int((await self._session.execute(count_query)).scalar_one())

        offset = (page - 1) * page_size
        query = (
            select(PerformanceCycle)
            .order_by(
                PerformanceCycle.start_date.desc(),
                PerformanceCycle.end_date.desc(),
                PerformanceCycle.id.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    # --- Performance reviews ---
    def _review_load_options(self):
        return (
            selectinload(PerformanceReview.cycle),
            selectinload(PerformanceReview.employee).selectinload(Employee.department),
            selectinload(PerformanceReview.reviewer).selectinload(Employee.department),
            selectinload(PerformanceReview.metric_scores).selectinload(
                EmployeeMetricScore.metric,
            ),
            selectinload(PerformanceReview.feedback_entries).selectinload(
                PerformanceFeedback.author,
            ),
        )

    async def get_review_by_keys(
        self,
        *,
        cycle_id: uuid.UUID,
        employee_id: uuid.UUID,
        reviewer_id: uuid.UUID,
    ) -> PerformanceReview | None:
        result = await self._session.execute(
            select(PerformanceReview).where(
                PerformanceReview.cycle_id == cycle_id,
                PerformanceReview.employee_id == employee_id,
                PerformanceReview.reviewer_id == reviewer_id,
            ),
        )
        return result.scalar_one_or_none()

    async def get_review_by_id(
        self,
        *,
        review_id: uuid.UUID,
    ) -> PerformanceReview | None:
        result = await self._session.execute(
            select(PerformanceReview)
            .where(PerformanceReview.id == review_id)
            .options(*self._review_load_options()),
        )
        return result.scalar_one_or_none()

    async def create_review(
        self,
        *,
        cycle_id: uuid.UUID,
        employee_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        rating: float | int,
        comments: str | None,
    ) -> PerformanceReview:
        review = PerformanceReview(
            cycle_id=cycle_id,
            employee_id=employee_id,
            reviewer_id=reviewer_id,
            rating=rating,
            comments=comments,
        )
        self._session.add(review)
        await self._session.flush()
        return await self.get_review_by_id(review_id=review.id)  # type: ignore[arg-type]

    async def list_reviews(
        self,
        *,
        employee_id: uuid.UUID,
        cycle_id: uuid.UUID | None,
        reviewer_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[list[PerformanceReview], int]:
        # Use `PerformanceReview.employee_id == ...` to leverage `idx_review_employee`.
        query = (
            select(PerformanceReview)
            .where(PerformanceReview.employee_id == employee_id)
            .options(*self._review_load_options())
            .join(PerformanceReview.cycle)
            .order_by(PerformanceCycle.start_date.desc())
        )

        count_query = (
            select(func.count())
            .select_from(PerformanceReview)
            .where(PerformanceReview.employee_id == employee_id)
        )

        if cycle_id is not None:
            query = query.where(PerformanceReview.cycle_id == cycle_id)
            count_query = count_query.where(PerformanceReview.cycle_id == cycle_id)

        if reviewer_id is not None:
            query = query.where(PerformanceReview.reviewer_id == reviewer_id)
            count_query = count_query.where(PerformanceReview.reviewer_id == reviewer_id)

        offset = (page - 1) * page_size
        total_items = int((await self._session.execute(count_query)).scalar_one())
        query = query.offset(offset).limit(page_size)

        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    async def list_reviews_for_employee_ids(
        self,
        *,
        employee_ids: list[uuid.UUID],
        cycle_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[list[PerformanceReview], int]:
        if not employee_ids:
            return [], 0

        query = (
            select(PerformanceReview)
            .where(PerformanceReview.employee_id.in_(employee_ids))
            .options(*self._review_load_options())
            .join(PerformanceReview.cycle)
            .order_by(PerformanceCycle.start_date.desc())
        )
        count_query = (
            select(func.count())
            .select_from(PerformanceReview)
            .where(PerformanceReview.employee_id.in_(employee_ids))
        )

        if cycle_id is not None:
            query = query.where(PerformanceReview.cycle_id == cycle_id)
            count_query = count_query.where(PerformanceReview.cycle_id == cycle_id)

        total_items = int((await self._session.execute(count_query)).scalar_one())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    # --- Performance metrics ---
    async def list_metrics(
        self,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[PerformanceMetric], int]:
        count_query = select(func.count()).select_from(PerformanceMetric)
        total_items = int((await self._session.execute(count_query)).scalar_one())

        offset = (page - 1) * page_size
        query = (
            select(PerformanceMetric)
            .order_by(PerformanceMetric.name.asc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        return list(result.scalars().unique().all()), total_items

    async def get_metric_by_id(
        self, metric_id: uuid.UUID
    ) -> PerformanceMetric | None:
        result = await self._session.execute(
            select(PerformanceMetric).where(PerformanceMetric.id == metric_id),
        )
        return result.scalar_one_or_none()

    async def create_metric(
        self,
        *,
        name: str,
        description: str | None,
        created_by: uuid.UUID | None,
        updated_by: uuid.UUID | None,
    ) -> PerformanceMetric:
        metric = PerformanceMetric(
            name=name,
            description=description,
            created_by=created_by,
            updated_by=updated_by,
        )
        self._session.add(metric)
        await self._session.flush()
        return metric

    async def update_metric(
        self,
        *,
        metric_id: uuid.UUID,
        name: str,
        description: str | None,
        updated_by: uuid.UUID | None,
    ) -> PerformanceMetric | None:
        await self._session.execute(
            select(PerformanceMetric.id).where(PerformanceMetric.id == metric_id),
        )
        await self._session.execute(
            PerformanceMetric.__table__.update()
            .where(PerformanceMetric.id == metric_id)
            .values(name=name, description=description, updated_by=updated_by),
        )
        return await self.get_metric_by_id(metric_id)

    async def metric_has_scores(self, metric_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(EmployeeMetricScore).where(
                EmployeeMetricScore.metric_id == metric_id,
            ),
        )
        return int(result.scalar_one()) > 0

    async def delete_metric(self, metric_id: uuid.UUID) -> None:
        await self._session.execute(
            PerformanceMetric.__table__.delete().where(PerformanceMetric.id == metric_id),
        )

    # --- Metric scores ---
    async def get_metric_score_by_keys(
        self,
        *,
        review_id: uuid.UUID,
        metric_id: uuid.UUID,
    ) -> EmployeeMetricScore | None:
        result = await self._session.execute(
            select(EmployeeMetricScore)
            .where(
                EmployeeMetricScore.review_id == review_id,
                EmployeeMetricScore.metric_id == metric_id,
            )
            .options(selectinload(EmployeeMetricScore.metric)),
        )
        return result.scalar_one_or_none()

    async def upsert_metric_score(
        self,
        *,
        review_id: uuid.UUID,
        metric_id: uuid.UUID,
        score: float | int,
        actor_user_id: uuid.UUID,
    ) -> EmployeeMetricScore:
        existing = await self.get_metric_score_by_keys(
            review_id=review_id,
            metric_id=metric_id,
        )
        if existing is None:
            created = EmployeeMetricScore(
                review_id=review_id,
                metric_id=metric_id,
                score=score,
                created_by=actor_user_id,
                updated_by=actor_user_id,
            )
            self._session.add(created)
            await self._session.flush()
            return await self.get_metric_score_by_keys(
                review_id=review_id,
                metric_id=metric_id,
            )  # type: ignore[return-value]

        await self._session.execute(
            EmployeeMetricScore.__table__.update()
            .where(EmployeeMetricScore.id == existing.id)
            .values(score=score, updated_by=actor_user_id),
        )
        return await self.get_metric_score_by_keys(
            review_id=review_id,
            metric_id=metric_id,
        )  # type: ignore[return-value]

    async def list_metric_scores_for_review(
        self, review_id: uuid.UUID
    ) -> list[EmployeeMetricScore]:
        result = await self._session.execute(
            select(EmployeeMetricScore)
            .where(EmployeeMetricScore.review_id == review_id)
            .options(selectinload(EmployeeMetricScore.metric))
            .order_by(EmployeeMetricScore.id.asc())
        )
        return list(result.scalars().unique().all())

    # --- Feedback ---
    async def create_feedback(
        self,
        *,
        review_id: uuid.UUID,
        feedback_text: str,
        created_by_employee_id: uuid.UUID,
    ) -> PerformanceFeedback:
        entry = PerformanceFeedback(
            review_id=review_id,
            feedback_text=feedback_text,
            created_by=created_by_employee_id,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_feedback_for_review(
        self, review_id: uuid.UUID
    ) -> list[PerformanceFeedback]:
        result = await self._session.execute(
            select(PerformanceFeedback)
            .where(PerformanceFeedback.review_id == review_id)
            .options(selectinload(PerformanceFeedback.author))
            .order_by(PerformanceFeedback.created_at.desc())
        )
        return list(result.scalars().unique().all())

    # --- Audit ---
    async def create_audit_log(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        resource_type: str = "performance_reviews",
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
