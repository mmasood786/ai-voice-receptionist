import asyncio
from html import escape

from app.agents.provider import groq_model
from app.db.database import AsyncSessionLocal
from app.services.lead_email_generator import LeadEmailGenerator
from app.services.lead_follow_up_service import LeadFollowUpService
from app.services.notification_service import NotificationService

DEV_TENANT_ID = 1


async def process_due_leads():
    async with AsyncSessionLocal() as db:

        follow_up_service = LeadFollowUpService(db)
        notification_service = NotificationService()
        email_generator = LeadEmailGenerator()

        try:
            # ---------------------------------------------------------
            # 1. Get leads that are due for follow-up
            # ---------------------------------------------------------
            leads = await follow_up_service.leads.get_due_follow_ups(
                tenant_id=DEV_TENANT_ID,
                limit=50,
            )

            print(f"\n========== LEAD FOLLOW-UP WORKER ==========")
            print(f"DUE LEADS: {len(leads)}")

            if not leads:
                print("No leads are due for follow-up.")
                return

            # ---------------------------------------------------------
            # 2. Process each lead
            # ---------------------------------------------------------
            for lead in leads:

                print("\n--------------------------------------------")
                print(f"LEAD ID: {lead.id}")
                print(f"NAME: {lead.name}")
                print(f"EMAIL: {lead.email}")
                print(f"SCORE: {lead.lead_score}")
                print(f"FOLLOW-UP COUNT: {lead.follow_up_count}")
                print(f"STATUS: {lead.follow_up_status}")

                # -----------------------------------------------------
                # Safety checks
                # -----------------------------------------------------
                if lead.follow_up_status in {"stopped", "converted"}:
                    print("SKIP: lead is stopped or converted")
                    continue

                if not lead.email:
                    print("SKIP: lead has no email")
                    continue

                # -----------------------------------------------------
                # 3. Generate personalized email using Groq
                # -----------------------------------------------------
                print("\nGenerating AI follow-up...")

                try:
                    email_body = await email_generator.generate(
                        customer_name=lead.name,
                        service_interest=lead.service_interest,
                        urgency=lead.urgency,
                        budget=lead.budget,
                        timeline=lead.timeline,
                        follow_up_count=lead.follow_up_count,
                    )

                except Exception as exc:
                    print(f"AI GENERATION ERROR: {exc}")
                    print("SKIP: follow-up state will NOT be updated")
                    continue

                if not email_body:
                    print("SKIP: AI returned empty email")
                    continue

                print("\n========== GENERATED EMAIL ==========")
                print(email_body)

                # -----------------------------------------------------
                # 4. Build email
                # -----------------------------------------------------
                subject = "Following up on your inquiry"

                safe_body = escape(email_body).replace("\n", "<br>")

                html_body = f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <p>{safe_body}</p>

                    <p>
                        Best regards,<br>
                        Demo Service Company
                    </p>
                </body>
                </html>
                """

                text_body = (
                    f"{email_body}\n\n"
                    "Best regards,\n"
                    "Demo Service Company"
                )

                # -----------------------------------------------------
                # 5. Send email through Resend
                # -----------------------------------------------------
                print("\nSending email through Resend...")

                try:
                    email_id = await notification_service.send_lead_follow_up(
                        recipient_email=lead.email,
                        subject=subject,
                        html=html_body,
                        text=text_body,
                    )

                except Exception as exc:
                    print(f"EMAIL SEND ERROR: {exc}")
                    print("SKIP: follow-up state will NOT be updated")
                    continue

                print(f"EMAIL SENT SUCCESSFULLY: {email_id}")

                # -----------------------------------------------------
                # 6. ONLY after successful email:
                #    update follow-up lifecycle
                # -----------------------------------------------------
                try:
                    updated_lead = await follow_up_service.complete_follow_up(
                        tenant_id=DEV_TENANT_ID,
                        lead_id=lead.id,
                    )

                    if updated_lead is None:
                        print("ERROR: lead disappeared before update")
                        await db.rollback()
                        continue

                    # -------------------------------------------------
                    # 7. Commit DB changes
                    # -------------------------------------------------
                    await db.commit()

                    print("\n========== FOLLOW-UP COMPLETED ==========")
                    print(f"LEAD ID: {updated_lead.id}")
                    print(f"FOLLOW-UP COUNT: {updated_lead.follow_up_count}")
                    print(f"STATUS: {updated_lead.follow_up_status}")
                    print(
                        f"NEXT FOLLOW-UP: "
                        f"{updated_lead.next_follow_up_at}"
                    )

                except Exception as exc:
                    print(f"DB UPDATE ERROR: {exc}")
                    await db.rollback()
                    continue

        except Exception as exc:
            print(f"\nWORKER ERROR: {exc}")
            await db.rollback()


async def main():
    await process_due_leads()


if __name__ == "__main__":
    asyncio.run(main())