import json
import logging
from app.constants import CATEGORY_EMOJI

logger = logging.getLogger(__name__)


def parse_json(text: str) -> dict:
    """Parse JSON from agent tool input."""
    clean = text.strip("`").replace("'", '"')
    return json.loads(clean)


def format_amount(amount) -> str:
    """Format amount with ₹ for WhatsApp."""
    value = float(amount)
    if value == int(value):
        return f"₹{int(value):,}"
    return f"₹{value:,.2f}"


def _display_label(category: str, description: str) -> str:
    """Prefer specific description over generic category name."""
    cat = (category or "").strip().lower()
    desc = (description or "").strip().lower()
    if desc and desc != cat and desc != "expense":
        return description.strip()
    return cat


def format_expense_confirmation(amount, category: str, description: str = "") -> str:
    """User-facing confirmation for a saved expense."""
    label = _display_label(category, description)
    emoji = CATEGORY_EMOJI.get((category or "").strip().lower(), "")
    suffix = f" {emoji}" if emoji else ""
    return f"Added {format_amount(amount)} for {label}{suffix}"


def format_receipt_confirmation(amount, category: str = "") -> str:
    """User-facing confirmation for a receipt upload."""
    cat = (category or "").strip().lower()
    emoji = CATEGORY_EMOJI.get(cat) or "🧾"
    return f"Added {format_amount(amount)} from receipt {emoji}"
