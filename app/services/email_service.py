import resend

from app.config import get_settings


class EmailService:

    def __init__(self):
        settings = get_settings()

        resend.api_key = settings.resend_api_key

        self.from_email = (
            f"{settings.resend_from_name} "
            f"<{settings.resend_from_email}>"
        )

    async def send_email(
    self,
    *,
    to: str,
    subject: str,
    html: str,
    text: str,
    ):

        params: resend.Emails.SendParams = {
            "from": self.from_email,
            "to": [to],
            "subject": subject,
            "html": html,
            "text": text,
        }

        email = resend.Emails.send(params)

        email_id = email.get("id") if isinstance(email, dict) else None

        if not email_id:
            raise RuntimeError(
                f"Resend did not return an email ID: {email}"
            )

        print("\n========== EMAIL SENT ==========")
        print("Provider: Resend")
        print("To:", to)
        print("Subject:", subject)
        print("Email ID:", email_id)
        print("===============================\n")

        return email_id