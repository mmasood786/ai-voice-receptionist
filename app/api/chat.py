from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agents import Runner

from app.agents.context import AgentContext
from app.agents.receptionist import receptionist_agent
from app.db.database import get_db
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


class ChatRequest(BaseModel):

    tenant_id: int = Field(
        ...,
        description="Business/tenant ID",
    )

    message: str = Field(
        ...,
        min_length=1,
        description="Customer message",
    )

    conversation_id: int | None = Field(
        default=None,
        description="Existing conversation ID",
    )

    customer_id: int | None = Field(
        default=None,
        description="Optional customer ID",
    )

    channel: str = Field(
        default="web",
        description="Conversation channel",
    )


class ChatResponse(BaseModel):

    conversation_id: int

    response: str


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    conversation_service = ConversationService(db)
    message_service = MessageService(db)

    # ---------------------------------
    # 1. Get or create conversation
    # ---------------------------------

    conversation = await conversation_service.get_or_create(
        tenant_id=request.tenant_id,
        conversation_id=request.conversation_id,
        customer_id=request.customer_id,
        channel=request.channel,
    )

    conversation_id = conversation.id

    # ---------------------------------
    # 2. Load previous conversation
    # ---------------------------------

    history = await message_service.get_history(
        conversation_id=conversation_id,
        limit=20,
    )

    # ---------------------------------
    # 3. Build agent input
    # ---------------------------------

    messages = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in history
    ]

    # Add current message exactly once
    messages.append(
        {
            "role": "user",
            "content": request.message,
        }
    )

    # ---------------------------------
    # 4. Run AI agent
    # ---------------------------------

    agent_context = AgentContext(
        tenant_id=request.tenant_id,
        conversation_id=conversation.id,
        customer_id=conversation.customer_id,
    )

    result = await Runner.run(
        receptionist_agent,
        messages,
        context=agent_context,
    )

    response = result.final_output
    

    # ---------------------------------
    # 5. Save user message
    # ---------------------------------

    await message_service.save_user_message(
        conversation_id=conversation_id,
        content=request.message,
    )

    # ---------------------------------
    # 6. Save assistant response
    # ---------------------------------

    await message_service.save_assistant_message(
        conversation_id=conversation_id,
        content=response,
    )

    # ---------------------------------
    # 7. Commit
    # ---------------------------------

    await db.commit()

    return ChatResponse(
        conversation_id=conversation_id,
        response=response,
    )
