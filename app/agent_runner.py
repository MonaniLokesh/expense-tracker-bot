from datetime import date
from app.agent import agent_executor, process_image_expense, tool_names
from app.constants import CHAT_HISTORY_MAX_TURNS, MAX_USER_MESSAGE_LEN, RECENT_CONTEXT_LIMIT
from app.db import list_recent_expenses
from app.prompt import (
    EXPENSE_CATEGORIES_PROMPT,
    MEMORY_CONTEXT_RULES,
    PROMPT_INJECTION_GUARDRAILS,
    QUERY_RESPONSE_FORMAT,
    REACT_FORMAT,
    TOOL_GUIDE,
    WHATSAPP_REPLY_STYLE,
)
from app.reply import sanitize_whatsapp_reply
from app.security import (
    bind_request_user_id,
    reset_request_user_id,
    sanitize_description,
    truncate_user_message,
)
from app.tools._helpers import format_amount
from app.tools import ALL_TOOLS

CHAT_HISTORY = {}

def phone_to_user_id(phone: str) -> int:
    """Map WhatsApp number to numeric user_id for the DB."""
    digits = "".join(c for c in phone if c.isdigit())
    return int(digits) if digits else 0


def get_formatted_history(user_id: int) -> str:
    history = CHAT_HISTORY.get(user_id, [])
    if not history:
        return "No previous conversation."
    lines = []
    for i, turn in enumerate(history, start=1):
        lines.append(f"--- Turn {i} ---")
        lines.append(turn)
    return "\n".join(lines)


def format_recent_expenses_context(user_id: int, limit: int = RECENT_CONTEXT_LIMIT) -> str:
    rows = list_recent_expenses(user_id, limit)
    if not rows:
        return "No expenses logged yet."
    lines = []
    for r in rows:
        cat = (r.get("category") or "other").strip().lower()
        desc = sanitize_description((r.get("description") or "").strip())
        detail = f" · {desc}" if desc and desc.lower() != cat else ""
        date_str = r.get("expense_date", "")
        lines.append(f"{format_amount(r['amount'])} {cat}{detail} · {date_str}")
    return "Most recent expenses (newest first):\n" + "\n".join(lines)


def update_history(user_id: int, user_input: str, agent_output: str):
    if user_id not in CHAT_HISTORY:
        CHAT_HISTORY[user_id] = []
    CHAT_HISTORY[user_id].append(f"User: {user_input}\nAssistant: {agent_output}")
    if len(CHAT_HISTORY[user_id]) > CHAT_HISTORY_MAX_TURNS:
        CHAT_HISTORY[user_id].pop(0)


async def run_agent(
    user_id: int,
    message_text: str = None,
    image_data: bytes = None,
) -> str:
    token = bind_request_user_id(user_id)
    try:
        if image_data:
            output = sanitize_whatsapp_reply(await process_image_expense(user_id, image_data))
            update_history(user_id, "[receipt photo]", output)
            return output

    if message_text:
        result = await agent_executor.ainvoke(
            {
                "input": message_text,
                "user_id": user_id,
                "today": str(date.today()),
                "schema": EXPENSES_SCHEMA.format(user_id=user_id),
                "categories": EXPENSE_CATEGORIES_PROMPT,
                "reply_style": WHATSAPP_REPLY_STYLE,
                "injection_guards": PROMPT_INJECTION_GUARDRAILS,
                "query_format": QUERY_RESPONSE_FORMAT,
                "chat_history": get_formatted_history(user_id),
                "tool_names": tool_names,
                "tools": ", ".join(tool_names),
            }
        )
        output = sanitize_whatsapp_reply(result.get("output") or "")
        update_history(user_id, message_text, output)
        return output

        return "No input received."
    finally:
        reset_request_user_id(token)
