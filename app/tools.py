import json
from langchain.tools import tool
from app.db import add_expense, get_total_expenses

@tool
def record_expense(json_input: str) -> str:
    """
    Records an expense. 
    Input MUST be a JSON string with keys: "user_id", "amount", "category".
    """
    try:
        clean_input = json_input.strip("`").replace("'", '"')
        data = json.loads(clean_input)
        
        user_id = data.get("user_id")
        amount = data.get("amount")
        category = data.get("category")
        description = data.get("description", "Expense") 
        
        add_expense(user_id, amount, category, description)
        
        return f"Saved: Rs.{amount} on {category}."

    except Exception as e:
        return f"Error recording expense: {str(e)}"

@tool
def get_expense_total(user_id: str) -> str:
    """Retrieves total expenses from Supabase. Input is the user_id string."""
    try:
        total = get_total_expenses(int(user_id))
        return f"Total expenses: Rs.{total:.2f}"
    except Exception as e:
        return f"Error getting total: {e}"