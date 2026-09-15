from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.resend_inbound_service import ResendInboundService

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


class ResendWebhookData(BaseModel):
    email_id: str
    created_at: str | None = None

    from_: str | None = Field(
        default=None,
        alias="from",
    )

    to: list[str] = []
    bcc: list[str] = []
    cc: list[str] = []

    message_id: str | None = None
    subject: str | None = None
    attachments: list[dict[str, Any]] = []


class ResendWebhookPayload(BaseModel):
    type: str
    created_at: str | None = None
    data: ResendWebhookData


@router.post("/resend")
async def resend_webhook(
    payload: ResendWebhookPayload,
):
    print("\n========== RESEND WEBHOOK ==========")

    # --------------------------------------------------------
    # 1. Only process received emails
    # --------------------------------------------------------

    if payload.type != "email.received":
        return {
            "status": "ignored",
            "event_type": payload.type,
        }

    email_id = payload.data.email_id

    print(f"EMAIL ID: {email_id}")
    print(f"FROM: {payload.data.from_}")
    print(f"SUBJECT: {payload.data.subject}")
    print(f"MESSAGE ID: {payload.data.message_id}")

    # --------------------------------------------------------
    # 2. Retrieve complete email from Resend
    # --------------------------------------------------------

    inbound_service = ResendInboundService()

    try:
        email = await inbound_service.get_received_email(
            email_id=email_id
        )

    except Exception as exc:
        print(f"RESEND RETRIEVE ERROR: {exc}")

        return {
            "status": "error",
            "email_id": email_id,
            "error": "Unable to retrieve received email",
        }

    # --------------------------------------------------------
    # 3. Extract actual email content
    # --------------------------------------------------------

    sender = email.get("from")
    subject = email.get("subject")
    text = email.get("text") or ""
    html = email.get("html") or ""

    print("\n========== RECEIVED EMAIL ==========")
    print(f"FROM: {sender}")
    print(f"SUBJECT: {subject}")
    print(f"TEXT: {text}")
    print(f"HTML AVAILABLE: {bool(html)}")

    # --------------------------------------------------------
    # 4. Basic STOP detection
    # --------------------------------------------------------

    normalized_text = text.strip().lower()

    stop_words = {
        "stop",
        "unsubscribe",
        "remove me",
        "stop emailing me",
        "stop emailing",
    }

    if normalized_text in stop_words:
        print("\nSTOP REQUEST DETECTED")

        return {
            "status": "processed",
            "action": "stop_follow_up",
            "email_id": email_id,
            "sender": sender,
        }

    # --------------------------------------------------------
    # 5. Otherwise treat as a reply
    # --------------------------------------------------------

    print("\nREPLY DETECTED")

    return {
        "status": "processed",
        "action": "mark_replied",
        "email_id": email_id,
        "sender": sender,
        "subject": subject,
    }