import secrets

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(prefix="/webhooks/vapi", tags=["Vapi"])

settings = get_settings()


class VapiWebhookRequest(BaseModel):
    message: dict


@router.post("")
async def handle_vapi_webhook(
    payload: VapiWebhookRequest,
    request: Request,
    authorization: str | None = Header(default=None),
):
    expected = f"Bearer {settings.vapi_webhook_secret}"

    if not authorization or not secrets.compare_digest(
        authorization,
        expected,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook credentials.",
        )

    message = payload.message
    message_type = message.get("type")

    if message_type == "tool-calls":
        # Tool execution will be implemented in the next step.
        raise HTTPException(
            status_code=501,
            detail="Tool execution is not configured yet.",
        )

    return {"received": True, "type": message_type}