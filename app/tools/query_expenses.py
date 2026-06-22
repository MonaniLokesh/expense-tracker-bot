import logging
from langchain_core.tools import tool
from app.constants import QUERY_DETAIL_LIMIT
from app.db import fetch_expenses
from app.security import get_bound_user_id
from app.tools._helpers import format_amount, format_expense_line, parse_json

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


def _item_lines(rows, limit: int = QUERY_DETAIL_LIMIT) -> list[str]:
    sorted_rows = sorted(rows, key=lambda r: r.get("expense_date", ""), reverse=True)
    lines = []
    for r in sorted_rows[:limit]:
        lines.append(
            format_expense_line(
                r["amount"],
                r.get("category", ""),
                r.get("description", ""),
                r.get("expense_date", ""),
            )
        )
    remaining = len(sorted_rows) - limit
    if remaining > 0:
        lines.append(f"• …and {remaining} more")
    return lines


@tool(return_direct=True)
def query_expenses(input_str: str) -> str:
    """Query totals and itemized breakdown. With category filter, lists each expense with description. JSON: user_id, optional start_date, end_date, category."""
    try:
        data = parse_json(input_str)
        user_id = get_bound_user_id()
        category = data.get("category")
        if category:
            category = category.strip().lower()
        rows = fetch_expenses(
            user_id,
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            category=category,
        )
        if not rows:
            return "Nothing logged for that period."

        total = sum(float(r["amount"]) for r in rows)
        period = _period_label(data)

        if category:
            cat = category.title()
            header = f"{cat} ({period}): {format_amount(total)} total"
            items = _item_lines(rows)
            return header + "\n" + "\n".join(items)

        by_cat: dict[str, float] = {}
        for r in rows:
            cat = (r.get("category") or "other").strip().lower()
            by_cat[cat] = by_cat.get(cat, 0) + float(r["amount"])

        lines = [f"• {c.title()} {format_amount(amt)}" for c, amt in sorted(by_cat.items())]
        return f"{period}: {format_amount(total)} total\n" + "\n".join(lines)
    except Exception as e:
        logger.exception("query_expenses failed: %s", e)
        return "Couldn't pull that up — try a different date range?"
