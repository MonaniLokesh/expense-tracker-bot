from datetime import date
from app.agent import agent_executor, process_image_expense, tool_names
from app.constants import CHAT_HISTORY_MAX_TURNS
from app.prompt import (
    EXPENSES_SCHEMA,
    EXPENSE_CATEGORIES_PROMPT,
    QUERY_RESPONSE_FORMAT,
    WHATSAPP_REPLY_STYLE,
    PROMPT_INJECTION_GUARDRAILS,
)
from app.reply import sanitize_whatsapp_reply

CHAT_HISTORY = {}


def phone_to_user_id(phone: str) -> int:
    """Map WhatsApp number to numeric user_id for the DB."""
    digits = "".join(c for c in phone if c.isdigit())
    return int(digits) if digits else 0

def get_formatted_history(user_id: int) -> str:
    history = CHAT_HISTORY.get(user_id, [])
    return "\n".join(history) if history else "No previous conversation."

def update_history(user_id: int, user_input: str, agent_output: str):
    if user_id not in CHAT_HISTORY:
        CHAT_HISTORY[user_id] = []
    CHAT_HISTORY[user_id].append(f"User: {user_input}\nAI: {agent_output}")
    if len(CHAT_HISTORY[user_id]) > CHAT_HISTORY_MAX_TURNS:
        CHAT_HISTORY[user_id].pop(0)

async def run_agent(
    user_id: int,
    message_text: str = None,
    image_data: bytes = None,
) -> str:
    if image_data:
        return sanitize_whatsapp_reply(await process_image_expense(user_id, image_data))

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
        output = sanitize_whatsapp_reply(result["output"])
        update_history(user_id, message_text, output)
        return output

    return "No input received."
