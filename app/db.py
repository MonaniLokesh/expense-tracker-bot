from collections import defaultdict
from datetime import date, datetime, timezone
from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY
from app.constants import DEFAULT_RECENT_EXPENSES_LIMIT

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def _execute(query):
    """Run a Supabase query builder."""
    return query.execute()


def _active_rows(rows):
    """Exclude soft-deleted rows when deleted_at exists on the row."""
    return [r for r in rows if not r.get("deleted_at")]


def add_expense(
    user_id,
    amount,
    category,
    description="",
    expense_date=None,
    raw_message=None,
    confidence=None,
):
    """Insert one expense row (core columns only — works before optional migrations)."""
    data = {
        "user_id": user_id,
        "amount": amount,
        "category": category,
        "description": description,
        "expense_date": expense_date or str(date.today()),
    }
    return supabase.table("expenses").insert(data).execute()


def fetch_expenses(user_id, start_date=None, end_date=None, category=None):
    """Fetch active expenses via Supabase."""
    q = (
        supabase.table("expenses")
        .select("amount, category, description, expense_date")
        .eq("user_id", user_id)
    )
    if start_date:
        q = q.gte("expense_date", start_date)
    if end_date:
        q = q.lte("expense_date", end_date)
    if category:
        q = q.eq("category", category.lower())
    try:
        rows = _execute(q.is_("deleted_at", "null")).data or []
    except Exception as e:
        if "deleted_at" not in str(e):
            raise
        rows = _execute(q).data or []
    return _active_rows(rows)


def summarize_expenses(rows):
    """Build total + per-category breakdown from expense rows."""
    if not rows:
        return None
    total = sum(float(r["amount"]) for r in rows)
    by_cat = defaultdict(float)
    for r in rows:
        by_cat[r["category"]] += float(r["amount"])
    lines = [f"  {c}: Rs.{amt:.2f}" for c, amt in sorted(by_cat.items())]
    return total, lines


def delete_last_expense(user_id):
    """Soft-delete the most recent expense (or hard-delete if no deleted_at column)."""
    q = (
        supabase.table("expenses")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
    )
    try:
        rows = _execute(q.is_("deleted_at", "null"))
    except Exception as e:
        if "deleted_at" not in str(e):
            raise
        rows = _execute(q)
    if not rows.data:
        return None
    row = rows.data[0]
    try:
        supabase.table("expenses").update(
            {"deleted_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", row["id"]).execute()
    except Exception as e:
        if "deleted_at" not in str(e):
            raise
        supabase.table("expenses").delete().eq("id", row["id"]).execute()
    return row


def list_recent_expenses(user_id, limit=DEFAULT_RECENT_EXPENSES_LIMIT):
    """Return last N active expenses."""
    q = (
        supabase.table("expenses")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    try:
        rows = _execute(q.is_("deleted_at", "null")).data or []
    except Exception as e:
        if "deleted_at" not in str(e):
            raise
        rows = _execute(q).data or []
    return _active_rows(rows)
