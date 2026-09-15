from app.services.email_service import EmailService


class NotificationService:

    def __init__(self):
        self.email = EmailService()

    async def send_lead_follow_up(
        self,
        *,
        recipient_email: str,
        subject: str,
        html: str,
        text: str,
    ) -> str:

        return await self.email.send_email(
            to=recipient_email,
            subject=subject,
            html=html,
            text=text,
        )
        
    async def send_review_request(
        self,
        *,
        recipient_email: str,
        subject: str,
        html: str,
        text: str,
    ) -> str:
        return await self.email.send_email(
            to=recipient_email,
            subject=subject,
            html=html,
            text=text,
        )