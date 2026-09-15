from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.review_service import ReviewService
from app.db.models import Appointment,Customer, Review
from app.services.review_automation_service import ReviewAutomationService
from app.services.review_request_service import ReviewRequestService

from app.services.review_escalation_service import (
    ReviewEscalationService,
)

router = APIRouter(prefix="/reviews", tags=["Reviews"])

DEV_TENANT_ID = 1


class ReviewFeedbackRequest(BaseModel):
    review_id: int
    rating: int
    feedback: str | None = None


@router.post("/create/{appointment_id}")
async def create_review(
    appointment_id: int,
    customer_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = ReviewService(db)

    review = await service.create_review_request(
        tenant_id=DEV_TENANT_ID,
        customer_id=customer_id,
        appointment_id=appointment_id,
    )

    await db.commit()

    return {
        "id": review.id,
        "appointment_id": review.appointment_id,
        "customer_id": review.customer_id,
        "status": review.status,
    }


@router.post("/feedback")
async def submit_feedback(
    payload: ReviewFeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ReviewService(db)

    try:
        review = await service.record_feedback(
        tenant_id=DEV_TENANT_ID,
        review_id=payload.review_id,
        rating=payload.rating,
        feedback=payload.feedback,
        )

        if review is None:
            raise HTTPException(
                status_code=404,
                detail="Review not found",
            )

        if review.rating is not None and review.rating <= 3:
            escalation_service = ReviewEscalationService()

            await escalation_service.escalate(
                review_id=review.id,
                rating=review.rating,
                feedback=review.feedback,
            )

        await db.commit()

        return {
            "id": review.id,
            "rating": review.rating,
            "feedback": review.feedback,
            "status": review.status,
            "responded_at": review.responded_at,
        }

    except ValueError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        await db.rollback()
        raise
    
@router.post("/create-from-appointment/{appointment_id}")
async def create_review_from_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.tenant_id == DEV_TENANT_ID,
        )
    )

    appointment = result.scalar_one_or_none()

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    if appointment.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Appointment is not completed. "
                f"Current status: {appointment.status}"
            ),
        )

    if appointment.customer_id is None:
        raise HTTPException(
            status_code=400,
            detail="Appointment has no customer_id",
        )

    service = ReviewAutomationService(db)

    review = await service.create_review_for_completed_appointment(
        tenant_id=DEV_TENANT_ID,
        appointment=appointment,
    )

    if review is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to create review",
        )

    await db.commit()

    return {
        "review_id": review.id,
        "appointment_id": review.appointment_id,
        "customer_id": review.customer_id,
        "status": review.status,
    }
    
@router.post("/send-request/{review_id}")
async def send_review_request(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review, Customer)
        .join(
            Customer,
            Review.customer_id == Customer.id,
        )
        .where(
            Review.id == review_id,
            Review.tenant_id == DEV_TENANT_ID,
            Customer.tenant_id == DEV_TENANT_ID,
        )
    )

    row = result.first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Review or customer not found",
        )

    review, customer = row

    if not customer.email:
        raise HTTPException(
            status_code=400,
            detail="Customer does not have an email address",
        )

    service = ReviewRequestService(db)

    try:
        result = await service.send_review_request(
            tenant_id=DEV_TENANT_ID,
            review_id=review.id,
            customer_name=customer.name,
            customer_email=customer.email,
        )

        await db.commit()

        return result

    except Exception:
        await db.rollback()
        raise