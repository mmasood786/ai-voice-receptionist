import asyncio
from html import escape

from app.db.database import AsyncSessionLocal
from app.services.notification_service import NotificationService
from app.services.review_email_generator import ReviewEmailGenerator
from app.services.review_service import ReviewService


DEV_TENANT_ID = 1


async def process_due_reviews():
    async with AsyncSessionLocal() as db:
        review_service = ReviewService(db)
        notification_service = NotificationService()
        email_generator = ReviewEmailGenerator()

        try:
            reviews = await review_service.get_due_reviews(
                tenant_id=DEV_TENANT_ID,
                limit=50,
            )

            print("\n========== REVIEW REQUEST WORKER ==========")
            print(f"DUE REVIEWS: {len(reviews)}")

            if not reviews:
                print("No reviews are due for a request.")
                return

            for review, customer in reviews:
                print("\n--------------------------------------------")
                print(f"REVIEW ID: {review.id}")
                print(f"APPOINTMENT ID: {review.appointment_id}")
                print(f"CUSTOMER ID: {customer.id}")
                print(f"CUSTOMER NAME: {customer.name}")
                print(f"CUSTOMER EMAIL: {customer.email}")
                print(f"STATUS: {review.status}")
                print(f"REQUEST AT: {review.review_request_at}")

                # Safety check
                if review.status != "pending":
                    print("SKIP: review is no longer pending")
                    continue

                if review.review_request_sent_at is not None:
                    print("SKIP: review request was already sent")
                    continue

                if not customer.email:
                    print("SKIP: customer has no email address")
                    continue

                # --------------------------------------------------
                # Generate email
                # --------------------------------------------------

                print("\nGenerating AI review email...")

                try:
                    email_body = await email_generator.generate(
                        customer_name=customer.name,
                    )
                except Exception as exc:
                    print(f"AI GENERATION ERROR: {exc}")
                    print("SKIP: review remains pending")
                    continue

                if not email_body:
                    print("SKIP: AI returned empty email")
                    continue

                print("\n========== GENERATED REVIEW EMAIL ==========")
                print(email_body)

                # --------------------------------------------------
                # Build email
                # --------------------------------------------------

                subject = "We'd love your feedback"

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

                # --------------------------------------------------
                # Send email
                # --------------------------------------------------

                print("\nSending review email through Resend...")

                try:
                    email_id = await notification_service.send_review_request(
                        recipient_email=customer.email,
                        subject=subject,
                        html=html_body,
                        text=text_body,
                    )
                except Exception as exc:
                    print(f"EMAIL SEND ERROR: {exc}")
                    print("SKIP: review remains pending")
                    continue

                print(f"EMAIL SENT SUCCESSFULLY: {email_id}")

                # --------------------------------------------------
                # Mark request as sent
                # --------------------------------------------------

                try:
                    updated_review = await review_service.mark_request_sent(
                        tenant_id=DEV_TENANT_ID,
                        review_id=review.id,
                    )

                    if updated_review is None:
                        print("ERROR: review disappeared before update")
                        await db.rollback()
                        continue

                    await db.commit()

                    print("\n========== REVIEW REQUEST COMPLETED ==========")
                    print(f"REVIEW ID: {updated_review.id}")
                    print(f"STATUS: {updated_review.status}")
                    print(
                        "REQUEST SENT AT: "
                        f"{updated_review.review_request_sent_at}"
                    )
                    print("==============================================")

                except Exception as exc:
                    print(f"DB UPDATE ERROR: {exc}")
                    await db.rollback()
                    continue

        except Exception as exc:
            print(f"\nWORKER ERROR: {exc}")
            await db.rollback()


async def main():
    await process_due_reviews()


if __name__ == "__main__":
    asyncio.run(main())