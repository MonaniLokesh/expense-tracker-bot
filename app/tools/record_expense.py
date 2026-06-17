import logging
from langchain_core.tools import tool
from app.db import add_expense
from app.tools._helpers import format_expense_confirmation, parse_json

logger = logging.getLogger(__name__)


@tool(return_direct=True)
def record_expense(json_input: str) -> str:
    """Save an expense. JSON: user_id, amount, category, optional description, expense_date."""
    try:
        data = parse_json(json_input)
        add_expense(
            int(data["user_id"]),
            data["amount"],
            data["category"],
            data.get("description", ""),
            expense_date=data.get("expense_date"),
        )
        return format_expense_confirmation(
            data["amount"],
            data["category"],
            data.get("description", ""),
        )
    except Exception as e:
        logger.exception("record_expense failed: %s", e)
        return "Couldn't save that — try again?"
