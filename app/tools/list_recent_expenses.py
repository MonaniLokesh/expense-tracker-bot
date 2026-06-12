import logging
from langchain_core.tools import tool
from app.constants import DEFAULT_RECENT_EXPENSES_LIMIT
from app.db import list_recent_expenses
from app.tools._helpers import format_amount, parse_json

logger = logging.getLogger(__name__)


@tool
def list_recent_expenses_tool(json_input: str) -> str:
    """List recent expenses. JSON: user_id, optional limit."""
    try:
        data = parse_json(json_input)
        limit = int(data.get("limit", DEFAULT_RECENT_EXPENSES_LIMIT))
        rows = list_recent_expenses(int(data["user_id"]), limit)
        if not rows:
            return "Nothing logged yet."
        lines = []
        for r in rows:
            cat = (r.get("category") or "other").strip().lower()
            desc = (r.get("description") or "").strip()
            detail = f" · {desc}" if desc and desc.lower() != cat else ""
            date_str = r.get("expense_date", "")
            lines.append(f"{format_amount(r['amount'])} {cat}{detail} · {date_str}")
        return f"Last {len(rows)}:\n" + "\n".join(lines)
    except Exception as e:
        logger.exception("list_recent_expenses failed: %s", e)
        return "Couldn't fetch recent expenses — try again?"
