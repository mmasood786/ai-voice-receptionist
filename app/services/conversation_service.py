from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation
from app.repositories.conversations import ConversationRepository
from app.repositories.customers import CustomerRepository


class ConversationService:

    def __init__(self, db: AsyncSession):
        self.repository = ConversationRepository(db)
        self.customer_repository = CustomerRepository(db)

    async def get_or_create(
        self,
        tenant_id: int,
        conversation_id: int | None = None,
        customer_id: int | None = None,
        channel: str = "web",
        vapi_call_id: str | None = None,
    ) -> Conversation:

        # 1. Existing conversation ID takes priority
        if conversation_id is not None:

            conversation = await self.repository.get_by_id(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )

            if conversation is None:
                raise ValueError(
                    f"Conversation {conversation_id} not found "
                    f"for tenant {tenant_id}"
                )

            return conversation

        # 2. For voice conversations, find by Vapi call ID
        if vapi_call_id is not None:

            conversation = await self.repository.get_by_vapi_call_id(
                tenant_id=tenant_id,
                vapi_call_id=vapi_call_id,
            )

            if conversation is not None:
                return conversation

        # 3. Validate customer if provided
        if customer_id is not None:

            customer = await self.customer_repository.get_by_id(
                tenant_id=tenant_id,
                customer_id=customer_id,
            )

            if customer is None:
                raise ValueError(
                    f"Customer {customer_id} not found "
                    f"for tenant {tenant_id}"
                )

        # 4. Create a new conversation
        return await self.repository.create(
            tenant_id=tenant_id,
            customer_id=customer_id,
            channel=channel,
            vapi_call_id=vapi_call_id,
        )
        
    async def set_customer(
        self,
        tenant_id: int,
        conversation_id: int,
        customer_id: int,
    ) -> Conversation:

        conversation = await self.repository.update_customer(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
        )

        if conversation is None:
            raise ValueError(
                f"Conversation {conversation_id} not found "
                f"for tenant {tenant_id}"
            )

        return conversation
    
    async def set_lead(
        self,
        tenant_id: int,
        conversation_id: int,
        lead_id: int,
    ) -> Conversation:

        conversation = await self.repository.update_lead(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            lead_id=lead_id,
        )

        if conversation is None:
            raise ValueError(
                f"Conversation {conversation_id} not found "
                f"for tenant {tenant_id}"
            )

        return conversation
    
    
    async def get_by_id(
        self,
        tenant_id: int,
        conversation_id: int,
    ) -> Conversation | None:
        return await self.repository.get_by_id(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )