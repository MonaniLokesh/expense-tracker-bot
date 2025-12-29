from datetime import date
import json
import re
from app.gemini import ask_gemini

EXPENSE_PROMPT = """
Extract expense info from the message.

Rules:
- If the user DOES NOT mention a date (yesterday, today, last week, etc),
  return date as "TODAY"
- Return ONLY valid JSON
- No explanations

Fields:
- amount (number)
- category (food, coffee, shopping, travel, misc)
- description (short text)
- date (YYYY-MM-DD or "TODAY")

Message:
{text}
"""

def parse_expense(text: str) -> dict:
    response = ask_gemini(EXPENSE_PROMPT.format(text=text))
    print("Gemini raw response:", response)

    data = json.loads(re.search(r"\{.*\}", response, re.DOTALL).group())

    if data["date"] == "TODAY":
        data["date"] = date.today().isoformat()

    return data
