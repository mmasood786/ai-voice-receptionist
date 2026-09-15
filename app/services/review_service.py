from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Review, Customer

class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review_request(
        self,
        *,
        tenant_id: int,
        customer_id: int,
        appointment_id: int,
    ) -> Review:
        # Prevent duplicate review requests for the same appointment.
        result = await self.db.execute(
            select(Review)
            .where(
                Review.tenant_id == tenant_id,
                Review.appointment_id == appointment_id,
            )
            .limit(1)
        )

        existing_review = result.scalar_one_or_none()

        if existing_review:
            return existing_review

        review = Review(
            tenant_id=tenant_id,
            customer_id=customer_id,
            appointment_id=appointment_id,
            status="pending",
        )

        self.db.add(review)
        await self.db.flush()

        return review

    async def mark_request_sent(
        self,
        *,
        tenant_id: int,
        review_id: int,
    ) -> Review | None:
        review = await self._get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        if review is None:
            return None

        review.status = "requested"
        review.review_request_sent_at = datetime.now(timezone.utc)

        await self.db.flush()

        return review

    async def record_feedback(
        self,
        *,
        tenant_id: int,
        review_id: int,
        rating: int,
        feedback: str | None = None,
    ) -> Review | None:

        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")

        if rating >= 4:
            return await self.mark_positive(
                tenant_id=tenant_id,
                review_id=review_id,
                rating=rating,
                feedback=feedback,
            )

        return await self.mark_negative(
            tenant_id=tenant_id,
            review_id=review_id,
            rating=rating,
            feedback=feedback,
        )

    async def _get_review(
        self,
        *,
        tenant_id: int,
        review_id: int,
    ) -> Review | None:
        result = await self.db.execute(
            select(Review)
            .where(
                Review.tenant_id == tenant_id,
                Review.id == review_id,
            )
        )

        return result.scalar_one_or_none()
    
    async def get_due_reviews(
        self,
        *,
        tenant_id: int,
        limit: int = 50,
    ):
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(Review, Customer)
            .join(Customer, Review.customer_id == Customer.id)
            .where(
                Review.tenant_id == tenant_id,
                Customer.tenant_id == tenant_id,
                Review.status == "pending",
                Review.review_request_at.is_not(None),
                Review.review_request_at <= now,
                Review.review_request_sent_at.is_(None),
            )
            .order_by(Review.review_request_at.asc())
            .limit(limit)
        )

        return result.all()
    
    async def mark_positive(
        self,
        *,
        tenant_id: int,
        review_id: int,
        rating: int,
        feedback: str | None = None,
    ) -> Review | None:

        review = await self._get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        if review is None:
            return None

        review.rating = rating
        review.feedback = feedback
        review.status = "completed"
        review.responded_at = datetime.now(timezone.utc)

        await self.db.flush()

        return review

    async def mark_negative(
        self,
        *,
        tenant_id: int,
        review_id: int,
        rating: int,
        feedback: str | None = None,
    ) -> Review | None:

        review = await self._get_review(
                tenant_id=tenant_id,
                review_id=review_id,
        )

        if review is None:
            return None

        review.rating = rating
        review.feedback = feedback
        review.status = "escalated"
        review.responded_at = datetime.now(timezone.utc)

        await self.db.flush()

        return review