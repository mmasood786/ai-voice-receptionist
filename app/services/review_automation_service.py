from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Appointment, Review
from app.services.review_service import ReviewService


class ReviewAutomationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.review_service = ReviewService(db)

    async def create_review_for_completed_appointment(
        self,
        *,
        tenant_id: int,
        appointment: Appointment,
    ) -> Review | None:

        # Only completed appointments qualify.
        if appointment.status != "completed":
            return None

        # A review requires a customer.
        if appointment.customer_id is None:
            return None

        review = await self.review_service.create_review_request(
            tenant_id=tenant_id,
            customer_id=appointment.customer_id,
            appointment_id=appointment.id,
        )

        return review