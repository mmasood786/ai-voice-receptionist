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

    async def get_by_vapi_call_id(
        self,
        tenant_id: int,
        vapi_call_id: str,
    ) -> Conversation | None:

        result = await self.db.execute(
            select(Conversation).where(
                Conversation.vapi_call_id == vapi_call_id,
                Conversation.tenant_id == tenant_id,
            )
        )

        return result.scalar_one_or_none()
    
    async def create(
        self,
        tenant_id: int,
        customer_id: int | None = None,
        channel: str = "web",
        vapi_call_id: str | None = None,
    ) -> Conversation:

        conversation = Conversation(
            tenant_id=tenant_id,
            customer_id=customer_id,
            channel=channel,
            status="active",
            vapi_call_id=vapi_call_id,
        )

        self.db.add(conversation)

        await self.db.flush()

        return conversation
    
    async def get_or_create_vapi_conversation(
        self,
        tenant_id: int,
        vapi_call_id: str,
    ) -> Conversation:
        """Get or create a conversation for a Vapi call."""

        conversation = await self.get_by_vapi_call_id(
            tenant_id=tenant_id,
            vapi_call_id=vapi_call_id,
        )

        if conversation is not None:
            return conversation

        return await self.create(
            tenant_id=tenant_id,
            channel="voice",
            vapi_call_id=vapi_call_id,
        )
        
    async def update_customer(
        self,
        tenant_id: int,
        conversation_id: int,
        customer_id: int,
    ) -> Conversation | None:

        conversation = await self.get_by_id(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )

        if conversation is None:
            return None

        conversation.customer_id = customer_id

        await self.db.flush()

        return conversation
    
    
    async def update_lead(
        self,
        tenant_id: int,
        conversation_id: int,
        lead_id: int,
    ) -> Conversation | None:

        conversation = await self.get_by_id(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )

        if conversation is None:
            return None

        conversation.lead_id = lead_id

        await self.db.flush()

        return conversation
    