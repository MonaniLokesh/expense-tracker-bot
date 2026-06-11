from langchain_core.tools import tool
from app.db import add_expense
from app.tools._helpers import parse_json


@tool(return_direct=True)
def record_expense(json_input: str) -> str:
    """Save an expense. JSON: user_id, amount, category, optional description, expense_date."""
    try:
        data = parse_json(json_input)
        # Only pass fields that exist on the table (ignore LLM extras like "source")
        add_expense(
            int(data["user_id"]),
            data["amount"],
            data["category"],
            data.get("description", ""),
            expense_date=data.get("expense_date"),
        )
        cat = data["category"]
        return f"Saved: Rs.{data['amount']} — {cat.title()} — {data.get('description', '') or 'expense'}."
    except Exception as e:
        return f"Error recording expense: {e}"
