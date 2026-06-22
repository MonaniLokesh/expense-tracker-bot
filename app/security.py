"""Request-scoped security helpers — user binding and input validation."""

from contextvars import ContextVar, Token
from typing import Optional

from app.constants import EXPENSE_CATEGORIES, MAX_DESCRIPTION_LEN, MAX_EXPENSE_AMOUNT

_request_user_id: ContextVar[Optional[int]] = ContextVar("request_user_id", default=None)


def bind_request_user_id(user_id: int) -> Token:
    return _request_user_id.set(int(user_id))


def reset_request_user_id(token: Token) -> None:
    _request_user_id.reset(token)


def get_bound_user_id() -> int:
    user_id = _request_user_id.get()
    if user_id is None:
        raise RuntimeError("No request user_id bound")
    return user_id


def validate_amount(amount) -> float:
    value = float(amount)
    if value <= 0:
        raise ValueError("amount must be positive")
    if value > MAX_EXPENSE_AMOUNT:
        raise ValueError("amount too large")
    return value


def normalize_category(category: str) -> str:
    cat = (category or "other").strip().lower()
    if cat not in EXPENSE_CATEGORIES:
        return "other"
    return cat


def sanitize_description(text: str) -> str:
    """Single-line description safe for DB storage and prompt context."""
    if not text:
        return ""
    cleaned = " ".join(str(text).replace("\n", " ").replace("\r", " ").split())
    return cleaned[:MAX_DESCRIPTION_LEN]


def truncate_user_message(text: str, max_len: int) -> str:
    if not text or len(text) <= max_len:
        return text or ""
    return text[:max_len]
