from html import escape

from app.services.notification_service import NotificationService
from app.services.review_email_generator import ReviewEmailGenerator
from app.services.review_service import ReviewService


class ReviewRequestService:
    def __init__(self, db):
        self.db = db
        self.review_service = ReviewService(db)
        self.notification_service = NotificationService()
        self.email_generator = ReviewEmailGenerator()

    async def send_review_request(
        self,
        *,
        tenant_id: int,
        review_id: int,
        customer_name: str,
        customer_email: str,
        service_name: str | None = None,
    ):

        if not customer_email:
            raise ValueError("Customer email is required.")

        review = await self.review_service._get_review(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        if review is None:
            raise ValueError("Review not found.")

        # Prevent duplicate sending.
        if review.status == "requested":
            return {
                "review_id": review.id,
                "status": review.status,
                "email_sent": False,
                "reason": "Review request already sent.",
            }

        if review.status in {"responded", "completed", "escalated"}:
            return {
                "review_id": review.id,
                "status": review.status,
                "email_sent": False,
                "reason": "Review workflow already completed.",
            }

        email_body = await self.email_generator.generate(
            customer_name=customer_name,
            service_name=service_name,
        )

        if not email_body:
            raise RuntimeError(
                "Review email generator returned an empty response."
            )

        safe_body = escape(email_body).replace("\n", "<br>")

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <p>{safe_body}</p>

            <p>
                Thank you for your time.
            </p>

            <p>
                Best regards,<br>
                Demo Service Company
            </p>
        </body>
        </html>
        """

        text_body = (
            f"{email_body}\n\n"
            "Thank you for your time.\n\n"
            "Best regards,\n"
            "Demo Service Company"
        )

        email_id = await self.notification_service.send_review_request(
            recipient_email=customer_email,
            subject="We'd love your feedback",
            html=html_body,
            text=text_body,
        )

        # Only mark requested AFTER successful email delivery request.
        updated_review = await self.review_service.mark_request_sent(
            tenant_id=tenant_id,
            review_id=review_id,
        )

        if updated_review is None:
            raise RuntimeError(
                "Review disappeared after email was sent."
            )

        return {
            "review_id": updated_review.id,
            "email_id": email_id,
            "status": updated_review.status,
            "email_sent": True,
        }