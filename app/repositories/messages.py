from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message


class MessageRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        conversation_id: int,
        role: str,
        content: str,
    ) -> Message:

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.db.add(message)

        await self.db.flush()

        return message

    async def get_history(
        self,
        conversation_id: int,
        limit: int = 20,
    ) -> list[Message]:

        result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id
            )
            .order_by(
                Message.created_at.desc()
            )
            .limit(limit)
        )

        messages = list(result.scalars().all())

        messages.reverse()

        return messages