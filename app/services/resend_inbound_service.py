import resend

from app.config import get_settings


class ResendInboundService:

    def __init__(self):
        settings = get_settings()
        resend.api_key = settings.resend_api_key

    async def get_received_email(self, email_id: str) -> dict:
        """
        Retrieve the complete inbound email from Resend.

        Resend endpoint:
        GET /emails/receiving/{email_id}
        """

        response = resend.Emails.Receiving.get(email_id)

        if isinstance(response, dict):
            return response

        # Some SDK versions may return an object
        data = getattr(response, "data", None)

        if data is None:
            raise RuntimeError(
                f"Unable to retrieve received email: {response}"
            )

        if isinstance(data, dict):
            return data

        return data.__dict__