import logging
from langchain_core.tools import tool
from app.db import delete_last_expense
from app.security import get_bound_user_id
from app.tools._helpers import format_amount

logger = logging.getLogger(__name__)


@tool
def delete_last_expense_tool(user_id: str) -> str:
    """Delete the most recent expense. Input is user_id as string."""
    try:
        row = delete_last_expense(get_bound_user_id())
        if not row:
            return "Nothing to undo."
        cat = (row.get("category") or "expense").strip().lower()
        return f"Removed your last one — {format_amount(row['amount'])} {cat}."
    except Exception as e:
        logger.exception("delete_last_expense failed: %s", e)
        return "Couldn't undo that — try again?"
