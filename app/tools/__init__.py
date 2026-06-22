from app.tools.record_expense import record_expense
from app.tools.query_expenses import query_expenses
from app.tools.delete_last_expense import delete_last_expense_tool

ALL_TOOLS = [
    record_expense,
    query_expenses,
    delete_last_expense_tool,
]
