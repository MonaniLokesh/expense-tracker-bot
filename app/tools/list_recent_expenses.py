from langchain_core.tools import tool
from app.constants import DEFAULT_RECENT_EXPENSES_LIMIT
from app.db import list_recent_expenses
from app.tools._helpers import parse_json


@tool
def list_recent_expenses_tool(json_input: str) -> str:
    """List recent expenses. JSON: user_id, optional limit."""
    try:
        data = parse_json(json_input)
        rows = list_recent_expenses(
            int(data["user_id"]), int(data.get("limit", DEFAULT_RECENT_EXPENSES_LIMIT))
        )
        if not rows:
            return "No recent expenses."
        return "\n".join(
            f"{i}. Rs.{r['amount']} — {r['category'].title()} — "
            f"{r.get('description', '') or 'expense'} ({r['expense_date']})"
            for i, r in enumerate(rows, 1)
        )
    except Exception as e:
        return f"Error listing expenses: {e}"
