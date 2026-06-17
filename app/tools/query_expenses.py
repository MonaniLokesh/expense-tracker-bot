import logging
from langchain_core.tools import tool
from app.db import fetch_expenses
from app.tools._helpers import format_amount, parse_json

logger = logging.getLogger(__name__)


def _period_label(data: dict) -> str:
    start = data.get("start_date")
    end = data.get("end_date")
    if not start and not end:
        return "All time"
    if start and end and start == end:
        return "Today" if start == end else start
    if start and end:
        return f"{start} to {end}"
    if start:
        return f"From {start}"
    return f"Until {end}"


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
        if not rows:
            return "Nothing logged for that period."

        total = sum(float(r["amount"]) for r in rows)
        by_cat: dict[str, float] = {}
        for r in rows:
            cat = (r.get("category") or "other").strip().lower()
            by_cat[cat] = by_cat.get(cat, 0) + float(r["amount"])

        period = _period_label(data)
        if data.get("category"):
            cat = data["category"].strip().lower()
            header = f"{cat.title()} ({period}): {format_amount(total)} total"
            return header

        lines = [f"• {c.title()} {format_amount(amt)}" for c, amt in sorted(by_cat.items())]
        return f"{period}: {format_amount(total)} total\n" + "\n".join(lines)
    except Exception as e:
        logger.exception("query_expenses failed: %s", e)
        return "Couldn't pull that up — try a different date range?"
