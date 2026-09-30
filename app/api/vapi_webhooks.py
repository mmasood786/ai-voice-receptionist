import secrets
import json

from agents import RunContextWrapper
from agents.tool_context import ToolContext
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Header, HTTPException, Request, Depends
from pydantic import BaseModel
from app.db.database import get_db
from app.api.dependencies.tenant import get_current_tenant_id

from app.config import get_settings

from app.agents.context import AgentContext 
from app.agents.receptionist import receptionist_agent
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/webhooks/vapi", tags=["Vapi"])

settings = get_settings()


def build_tool_registry(tools: list) -> dict:
    """Create a name-to-tool lookup."""
    return {
        tool.name: tool
        for tool in tools
    }

async def dispatch_vapi_tool_calls(
    tool_calls: list[dict],
    agent_context: AgentContext,
) -> dict:
    """
    Execute Vapi tool calls using existing Agents SDK tools.
    """

    registry = build_tool_registry(
        receptionist_agent.tools
    )

    results = []

    run_context = RunContextWrapper(
        context=agent_context
    )

    for tool_call in tool_calls:

        tool_call_id = tool_call.get("id")
        tool_name = tool_call.get("name")
        arguments = tool_call.get(
            "parameters",
            {},
        )

        try:
            if not tool_call_id:
                raise ValueError(
                    "Missing tool call ID."
                )

            if not tool_name:
                raise ValueError(
                    "Missing tool name."
                )

            tool = registry.get(tool_name)

            if tool is None:
                raise ValueError(
                    f"Unknown tool: {tool_name}"
                )

            if not isinstance(arguments, dict):
                raise ValueError(
                    "Tool parameters must be an object."
                )

            arguments_json = json.dumps(arguments)

            tool_context = (
                ToolContext.from_agent_context(
                    context=run_context,
                    tool_call_id=tool_call_id,
                    tool_name=tool_name,
                    tool_arguments=arguments_json,
                    agent=receptionist_agent,
                )
            )

            output = await tool.on_invoke_tool(
                tool_context,
                arguments_json,
            )

            if isinstance(output, str):
                result_text = output
            else:
                result_text = json.dumps(
                    output,
                    default=str,
                )

        except Exception as exc:

            result_text = json.dumps({
                "success": False,
                "error": "tool_execution_failed",
                "message": str(exc),
            })

        results.append({
            "toolCallId": tool_call_id,
            "result": result_text,
        })

    return {
        "results": results
    }

def extract_vapi_tool_calls(message: dict) -> list[dict]:
    """
    Normalize Vapi tool-call payloads into:

    {
        "id": "...",
        "name": "...",
        "parameters": {...}
    }
    """

    raw_tool_calls = message.get("toolCallList")

    if not isinstance(raw_tool_calls, list):
        raise ValueError(
            "Missing or invalid toolCallList."
        )

    normalized = []

    for item in raw_tool_calls:

        if not isinstance(item, dict):
            raise ValueError(
                "Invalid tool call."
            )

        tool_call_id = item.get("id")
        tool_name = item.get("name")
        parameters = item.get("parameters")

        # Support nested function format as well.
        if not tool_call_id:
            tool_call_id = item.get("toolCallId")

        function = item.get("function")

        if isinstance(function, dict):
            if not tool_name:
                tool_name = function.get("name")

            if parameters is None:
                parameters = function.get("arguments")

        if parameters is None:
            parameters = {}

        if isinstance(parameters, str):
            try:
                parameters = json.loads(parameters)
            except json.JSONDecodeError:
                raise ValueError(
                    f"Invalid JSON parameters for tool "
                    f"{tool_name}."
                )

        normalized.append({
            "id": tool_call_id,
            "name": tool_name,
            "parameters": parameters,
        })

    return normalized

class VapiWebhookRequest(BaseModel):
    message: dict

@router.post("")
async def handle_vapi_webhook(
    payload: VapiWebhookRequest,
    request: Request,
    vapi_secret: str | None = Header(
        default=None,
        alias="X-Vapi-Secret",
    ),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id),
):
 
    expected = settings.vapi_webhook_secret
    

    if not vapi_secret or not secrets.compare_digest(
        vapi_secret,
        expected,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook credentials.",
        )

    message = payload.message
    message_type = message.get("type")
    

    if message_type == "tool-calls":

        call = message.get("call")

        if not isinstance(call, dict):
            raise HTTPException(
                status_code=400,
                detail="Missing Vapi call information.",
            )

        vapi_call_id = call.get("id")

        if not vapi_call_id:
            raise HTTPException(
                status_code=400,
                detail="Missing Vapi call ID.",
            )

        tool_calls = extract_vapi_tool_calls(message)

        if not tool_calls:
            raise HTTPException(
                status_code=400,
                detail="No Vapi tool calls found.",
            )

        conversation_service = ConversationService(db)

        conversation = await conversation_service.get_or_create(
            tenant_id=tenant_id,
            channel="voice",
            vapi_call_id=vapi_call_id,
        )

        await db.commit()

        agent_context = AgentContext(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            customer_id=conversation.customer_id,
            lead_id=conversation.lead_id,
            time_zone="Asia/Karachi",
        )

        return await dispatch_vapi_tool_calls(
            tool_calls=tool_calls,
            agent_context=agent_context,
        )

    return {
        "received": True,
        "type": message_type,
    }