from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message
from app.repositories.messages import MessageRepository


class MessageService:

    def __init__(self, db: AsyncSession):
        self.repository = MessageRepository(db)

    async def save_user_message(
        self,
        conversation_id: int,
        content: str,
    ) -> Message:

        return await self.repository.create(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

    async def save_assistant_message(
        self,
        conversation_id: int,
        content: str,
    ) -> Message:

        return await self.repository.create(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
        )

    async def get_history(
        self,
        conversation_id: int,
        limit: int = 20,
    ) -> list[Message]:

        return await self.repository.get_history(
            conversation_id=conversation_id,
            limit=limit,
        )