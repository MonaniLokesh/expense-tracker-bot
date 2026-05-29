import json


def parse_json(text: str) -> dict:
    """Parse JSON from agent tool input."""
    clean = text.strip("`").replace("'", '"')
    return json.loads(clean)
