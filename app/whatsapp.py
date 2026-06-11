import logging
from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
from app.config import TWILIO_AUTH_TOKEN, WEBHOOK_BASE_URL
from app.agent_runner import run_agent, phone_to_user_id
from app.agent import download_twilio_media, transcribe_audio

logger = logging.getLogger(__name__)
router = APIRouter()


def _webhook_url(request: Request) -> str:
    """URL Twilio signed — must match what ngrok/proxy forwarded, not localhost."""
    proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if host:
        return f"{proto}://{host}{request.url.path}"
    return f"{WEBHOOK_BASE_URL.rstrip('/')}{request.url.path}"


def _validate_twilio(request: Request, form: dict) -> bool:
    """Verify X-Twilio-Signature on the webhook request."""
    signature = request.headers.get("X-Twilio-Signature", "")
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    url = _webhook_url(request)
    params = {k: v if isinstance(v, str) else str(v) for k, v in form.items()}
    return validator.validate(url, params, signature)


def _twiml_reply(text: str) -> Response:
    resp = MessagingResponse()
    resp.message(text)
    return Response(content=str(resp), media_type="application/xml")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming Twilio WhatsApp messages (text, voice, or image)."""
    form = dict(await request.form())
    reply = "Something went wrong. Please try again."

    try:
        if not _validate_twilio(request, form):
            logger.warning("Invalid Twilio signature")
            return _twiml_reply("Unauthorized request.")

        from_number = form.get("From", "")
        user_id = phone_to_user_id(from_number)
        body = (form.get("Body") or "").strip()
        num_media = int(form.get("NumMedia") or 0)

        if num_media > 0 and form.get("MediaUrl0"):
            media_bytes = await download_twilio_media(form["MediaUrl0"])
            content_type = (form.get("MediaContentType0") or "").lower()
            if content_type.startswith("audio/"):
                transcript = await transcribe_audio(media_bytes, content_type)
                if transcript:
                    reply = await run_agent(user_id, message_text=transcript)
                else:
                    reply = "Couldn't understand the voice note. Please try again or type your message."
            else:
                reply = await run_agent(user_id, image_data=media_bytes)
        elif body:
            reply = await run_agent(user_id, message_text=body)
        else:
            reply = "Send a message, voice note, or receipt photo to log expenses."

    except Exception as e:
        logger.exception("WhatsApp webhook error: %s", e)

    return _twiml_reply(str(reply))
