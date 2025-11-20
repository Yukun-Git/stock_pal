"""Response formatting utilities."""

from datetime import datetime, date
from decimal import Decimal


def convert_to_json_serializable(data):
    """
    Convert data to JSON serializable format.

    Handles:
    - datetime/date objects → ISO format strings
    - Decimal objects → float
    - dict → recursive conversion
    - list → recursive conversion

    Args:
        data: Data to convert

    Returns:
        JSON-serializable data
    """
    if isinstance(data, dict):
        return {k: convert_to_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_json_serializable(item) for item in data]
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data
