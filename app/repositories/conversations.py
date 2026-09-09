from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation


class ConversationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        tenant_id: int,
        conversation_id: int,
    ) -> Conversation | None:

        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        tenant_id: int,
        customer_id: int | None = None,
        channel: str = "web",
    ) -> Conversation:

        conversation = Conversation(
            tenant_id=tenant_id,
            customer_id=customer_id,
            channel=channel,
            status="active",
        )

        self.db.add(conversation)

        await self.db.flush()

        return conversation