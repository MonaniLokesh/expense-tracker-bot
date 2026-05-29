from langchain_core.tools import tool
from app.db import delete_last_expense


@tool
def delete_last_expense_tool(user_id: str) -> str:
    """Delete the most recent expense. Input is user_id as string."""
    try:
        row = delete_last_expense(int(user_id))
        if not row:
            return "No expenses to delete."
        return f"Deleted: Rs.{row['amount']} on {row['category']} ({row.get('description', '')})."
    except Exception as e:
        return f"Error deleting: {e}"
