from datetime import date
from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_expense(user_id, amount, category, description=""):
    """Inserts a new expense row into Supabase."""
    
    data = {
        "user_id": user_id,
        "amount": amount,
        "category": category,
        "description": description,
        "expense_date": str(date.today()) 
    }
    
    try:
        response = supabase.table("expenses").insert(data).execute()
        return response
    except Exception as e:
        print(f"Supabase Insert Error: {e}")
        raise e

def get_total_expenses(user_id):
    """Fetches all expenses for a user and sums the 'amount' column."""
    try:
        response = supabase.table("expenses").select("amount").eq("user_id", user_id).execute()
        total = sum(record['amount'] for record in response.data)
        return total
    except Exception as e:
        print(f"Supabase Select Error: {e}")
        return 0.0