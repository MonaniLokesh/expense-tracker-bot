# WhatsApp Expense Tracker

Log expenses via WhatsApp (Twilio). Natural language and receipt images are handled by a Groq/LangChain agent; data is stored in Supabase.

## Setup

See [SETUP.md](SETUP.md). Copy `example.env` to `.env`, run the SQL in Supabase, then:

```bash
uv sync
uv run python run.py
```

## Stack

- FastAPI + Twilio WhatsApp
- LangChain (Groq Llama 4 Scout vision)
- Supabase PostgreSQL
