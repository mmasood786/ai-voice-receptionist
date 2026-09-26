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
    ) -> Conversation:

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

        return await self.repository.create(
            tenant_id=tenant_id,
            customer_id=customer_id,
            channel=channel,
        )