import base64
import logging
from datetime import date
import httpx
from groq import AsyncGroq
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_react_agent
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from app.constants import GROQ_MODEL, GROQ_WHISPER_MODEL, LLM_TEMPERATURE, AGENT_VERBOSE
from app.db import add_expense
from app.prompt import REACT_AGENT_PROMPT, vision_classify_receipt_text, vision_receipt_extract_text
from app.security import normalize_category, sanitize_description, validate_amount
from app.tools import ALL_TOOLS
from app.tools._helpers import format_receipt_confirmation, parse_json

logger = logging.getLogger(__name__)

llm = ChatGroq(model=GROQ_MODEL, temperature=LLM_TEMPERATURE)

tool_names = [t.name for t in ALL_TOOLS]

_REACT_PARSING_HINT = (
    "Invalid format. After Thought: include Action: + Action Input: OR Final Answer:. "
    "For greetings, refusals, and off-topic messages: "
    "Thought: Do I need to use a tool? No, then Final Answer: <your reply>. "
    "Never end with only Thought:."
)

agent = create_react_agent(llm=llm, tools=ALL_TOOLS, prompt=REACT_AGENT_PROMPT)
agent_executor = AgentExecutor(
    agent=agent,
    tools=ALL_TOOLS,
    verbose=AGENT_VERBOSE,
    handle_parsing_errors=_REACT_PARSING_HINT,
    max_iterations=4,
)

def _groq_audio_file(audio_bytes: bytes, content_type: str) -> tuple[str, bytes, str]:
    """Pick a Groq-accepted filename from audio magic bytes (WhatsApp sends OGG/Opus)."""
    if audio_bytes[:4] == b"OggS":
        return "audio.ogg", audio_bytes, "audio/ogg"
    if audio_bytes[:3] == b"ID3" or (
        len(audio_bytes) > 1 and audio_bytes[0] == 0xFF and audio_bytes[1] in (0xFB, 0xF3, 0xF2)
    ):
        return "audio.mp3", audio_bytes, "audio/mpeg"
    if len(audio_bytes) > 8 and audio_bytes[4:8] == b"ftyp":
        return "audio.m4a", audio_bytes, "audio/mp4"
    mime = content_type.split(";")[0].strip().lower()
    if mime.startswith("audio/"):
        return "audio.ogg", audio_bytes, mime or "audio/ogg"
    return "audio.ogg", audio_bytes, "audio/ogg"


async def transcribe_audio(audio_bytes: bytes, content_type: str) -> str:
    """Transcribe voice note with Groq Whisper; text agent handles the rest."""
    filename, payload, mime = _groq_audio_file(audio_bytes, content_type)
    client = AsyncGroq()
    transcription = await client.audio.transcriptions.create(
        model=GROQ_WHISPER_MODEL,
        file=(filename, payload, mime),
    )
    return (transcription.text or "").strip()


async def download_twilio_media(media_url: str) -> bytes:
    """Download WhatsApp image from Twilio using Basic auth."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            media_url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            follow_redirects=True,
        )
        r.raise_for_status()
        return r.content

_NOT_RECEIPT_REPLY = "That doesn't look like a bill or receipt — send a photo of one, or type what you spent."
_RECEIPT_FAIL_REPLY = "Couldn't read that receipt — try a clearer photo?"


def _image_message(text: str, image_data: bytes) -> HumanMessage:
    b64 = base64.b64encode(image_data).decode("utf-8")
    return HumanMessage(
        content=[
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ]
    )


def _parse_json_blob(content: str) -> dict:
    clean = content.replace("```json", "").replace("```", "").strip()
    start, end = clean.find("{"), clean.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError("no JSON object in response")
    return parse_json(clean[start:end])


def _normalize_receipt_fields(data: dict, today: str) -> dict:
    return {
        "amount": validate_amount(data["amount"]),
        "category": normalize_category(data.get("category", "other")),
        "description": sanitize_description(data.get("description", "")),
        "expense_date": data.get("expense_date") or today,
    }


async def _is_receipt_image(image_data: bytes) -> bool:
    """Stage 1 vision gate — only bills/receipts proceed to extraction."""
    try:
        response = await llm.ainvoke([_image_message(vision_classify_receipt_text(), image_data)])
        data = _parse_json_blob(response.content)
        return bool(data.get("is_receipt"))
    except Exception as e:
        logger.warning("receipt classification failed: %s", e)
        return False


async def process_image_expense(user_id: int, image_data: bytes):
    """Classify image, then extract receipt fields and save."""
    today = str(date.today())
    try:
        if not await _is_receipt_image(image_data):
            return _NOT_RECEIPT_REPLY

        response = await llm.ainvoke([_image_message(vision_receipt_extract_text(today), image_data)])
        fields = _normalize_receipt_fields(_parse_json_blob(response.content), today)
        add_expense(
            user_id,
            fields["amount"],
            fields["category"],
            fields["description"],
            expense_date=fields["expense_date"],
        )
        return format_receipt_confirmation(fields["amount"], fields["category"])
    except Exception as e:
        logger.exception("process_image_expense failed: %s", e)
        return _RECEIPT_FAIL_REPLY
