from langchain_core.tools import tool
from app.db import fetch_expenses, summarize_expenses
from app.tools._helpers import parse_json


@tool
def query_expenses(input_str: str) -> str:
    """Query totals and breakdown. JSON: user_id, optional start_date, end_date, category (YYYY-MM-DD)."""
    try:
        data = parse_json(input_str)
        user_id = int(data["user_id"])
        rows = fetch_expenses(
            user_id,
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            category=data.get("category"),
        )
        summary = summarize_expenses(rows)
        if not summary:
            return "No expenses found for that period."
        total, lines = summary
        period = "all time"
        if data.get("start_date") or data.get("end_date"):
            period = f"{data.get('start_date', '...')} to {data.get('end_date', '...')}"
        header = f"Spending ({period}):\nTotal: Rs.{total:.2f}"
        if data.get("category"):
            header = (
                f"Spending — {data['category'].title()} ({period}):\n"
                f"Total: Rs.{total:.2f}"
            )
        breakdown = "By category:\n" + "\n".join(lines)
        return header + "\n\n" + breakdown
    except Exception as e:
        return f"Query error: {e}"
