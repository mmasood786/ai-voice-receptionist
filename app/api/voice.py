from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse

router = APIRouter(
    prefix="/webhooks/voice",
    tags=["voice"],
)


@router.post("/incoming")
async def incoming_call(request: Request):
    form = await request.form()

    call_sid = form.get("CallSid")
    from_number = form.get("From")
    to_number = form.get("To")

    print("\n========== INCOMING VOICE CALL ==========")
    print("Call SID:", call_sid)
    print("From:", from_number)
    print("To:", to_number)
    print("=========================================\n")

    response = VoiceResponse()

    response.say(
        "Hello, thanks for calling. "
        "How can I help you today?",
        voice="alice",
        language="en-US",
    )

    response.hangup()

    return Response(
        content=str(response),
        media_type="application/xml",
    )