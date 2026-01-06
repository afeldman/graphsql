"""Utility functions."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict


def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove ``None`` values and normalize common Python types.

    Args:
        data: Raw dictionary of values.

    Returns:
        Dictionary without ``None`` entries and with dates/decimals/bytes
        converted to JSON-friendly representations.

    Examples:
        >>> clean_dict({"id": 1, "ts": datetime(2024, 1, 1), "note": None})
        {'id': 1, 'ts': '2024-01-01T00:00:00'}
    """
    cleaned = {}
    for key, value in data.items():
        if value is None:
            continue

        if isinstance(value, (datetime, date)):
            cleaned[key] = value.isoformat()
        elif isinstance(value, Decimal):
            cleaned[key] = float(value)
        elif isinstance(value, bytes):
            cleaned[key] = value.decode('utf-8', errors='ignore')
        else:
            cleaned[key] = value

    return cleaned
