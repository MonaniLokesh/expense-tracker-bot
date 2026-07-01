from datetime import date, datetime, timezone
from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY
from app.constants import DEFAULT_RECENT_EXPENSES_LIMIT
from app.security import normalize_category, sanitize_description

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def _active_rows(rows):
    """Exclude soft-deleted rows when deleted_at exists on the row."""
    return [r for r in rows if not r.get("deleted_at")]


def add_expense(user_id, amount, category, description="", expense_date=None):
    """Insert one expense row."""
    data = {
        "user_id": user_id,
        "amount": amount,
        "category": normalize_category(category),
        "description": sanitize_description(description),
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
    try:
        rows = q.is_("deleted_at", "null").execute().data or []
    except Exception as e:
        if "deleted_at" not in str(e):
            raise
        rows = q.execute().data or []
    rows = _active_rows(rows)
    if category:
        want = (category or "").strip().lower()
        rows = [r for r in rows if (r.get("category") or "other").strip().lower() == want]
    return rows


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
        rows = q.is_("deleted_at", "null").execute()
    except Exception as e:
        if "deleted_at" not in str(e):
            raise
        rows = q.execute()
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
        rows = q.is_("deleted_at", "null").execute().data or []
    except Exception as e:
        if "deleted_at" not in str(e):
            raise
        rows = q.execute().data or []
    return _active_rows(rows)
