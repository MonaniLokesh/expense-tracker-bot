import logging
from langchain_core.tools import tool
from app.db import add_expense
from app.security import (
    get_bound_user_id,
    normalize_category,
    sanitize_description,
    validate_amount,
)
from app.tools._helpers import format_expense_confirmation, parse_json

logger = logging.getLogger(__name__)


@tool(return_direct=True)
def record_expense(json_input: str) -> str:
    """Save an expense. JSON: user_id, amount, category, optional description, expense_date."""
    try:
        data = parse_json(json_input)
        user_id = get_bound_user_id()
        amount = validate_amount(data["amount"])
        category = normalize_category(data.get("category", "other"))
        description = sanitize_description(data.get("description", ""))
        add_expense(
            user_id,
            amount,
            category,
            description,
            expense_date=data.get("expense_date"),
        )
        return format_expense_confirmation(amount, category, description)
    except Exception as e:
        logger.exception("record_expense failed: %s", e)
        return "Couldn't save that — try again?"
