# Groq / LangChain
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"
LLM_TEMPERATURE = 0
AGENT_VERBOSE = True

# Expenses
EXPENSE_CATEGORIES = ("food", "transport", "shopping", "bills", "other")
CATEGORY_EMOJI = {
    "food": "🍔",
    "transport": "🚗",
    "shopping": "🛍️",
    "bills": "📄",
    "other": "",
}
DEFAULT_RECENT_EXPENSES_LIMIT = 5
RECENT_CONTEXT_LIMIT = 5
QUERY_DETAIL_LIMIT = 15

# In-memory chat history (per user; lost on server restart)
CHAT_HISTORY_MAX_TURNS = 10

# Security limits
MAX_USER_MESSAGE_LEN = 2000
MAX_DESCRIPTION_LEN = 200
MAX_EXPENSE_AMOUNT = 10000000  # ₹1 crore
