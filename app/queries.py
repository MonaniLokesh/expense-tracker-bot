from datetime import date, timedelta
from app.db import supabase

def insert_expense(user_id, data):
    supabase.table("expenses").insert({
        "user_id": user_id,
        "amount": data["amount"],
        "category": data["category"],
        "description": data.get("description"),
        "expense_date": data["date"]
    }).execute()


def get_total(user_id, start_date, end_date):
    res = (
        supabase.table("expenses")
        .select("amount")
        .eq("user_id", user_id)
        .gte("expense_date", start_date)
        .lte("expense_date", end_date)
        .execute()
    )

    return sum(float(row["amount"]) for row in res.data)


def date_range(period: str):
    today = date.today()

    if period == "yesterday":
        return today - timedelta(days=1), today - timedelta(days=1)

    if period == "last week":
        return today - timedelta(days=7), today

    if period == "last month":
        return today - timedelta(days=30), today
