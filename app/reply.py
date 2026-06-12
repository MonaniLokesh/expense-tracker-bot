import re

MAX_WHATSAPP_REPLY_LEN = 1500
_REACT_LEAK = re.compile(
    r"^(Thought|Action|Action Input|Observation)\s*:",
    re.IGNORECASE | re.MULTILINE,
)
_FALLBACK = "Something went wrong. Please try again."


def sanitize_whatsapp_reply(text: str) -> str:
    """Strip ReAct leakage and cap length before sending to WhatsApp."""
    if not text or not str(text).strip():
        return _FALLBACK
    lines = [
        line
        for line in str(text).splitlines()
        if line.strip() and not _REACT_LEAK.match(line.strip())
    ]
    cleaned = "\n".join(lines).strip()
    if not cleaned:
        return _FALLBACK
    if len(cleaned) > MAX_WHATSAPP_REPLY_LEN:
        cleaned = cleaned[: MAX_WHATSAPP_REPLY_LEN - 3].rstrip() + "..."
    return cleaned
