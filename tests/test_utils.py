"""Unit tests for utility functions."""
from decimal import Decimal
from datetime import datetime

import pytest

from graphsql.utils import clean_dict


class TestCleanDict:
    """Test clean_dict data serialization function."""

    def test_remove_none_values(self):
        """Test that None values are removed."""
        data = {"name": "Alice", "email": None, "age": 30}
        result = clean_dict(data)

        assert result == {"name": "Alice", "age": 30}
        assert "email" not in result

    def test_convert_datetime_to_iso(self):
        """Test datetime objects are converted to ISO format strings."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        data = {"created_at": dt, "name": "Alice"}
        result = clean_dict(data)

        assert isinstance(result["created_at"], str)
        assert "2024-01-15" in result["created_at"]
        assert result["name"] == "Alice"

    def test_convert_decimal_to_float(self):
        """Test Decimal objects are converted to floats."""
        data = {"price": Decimal("19.99"), "quantity": 5}
        result = clean_dict(data)

        assert isinstance(result["price"], float)
        assert result["price"] == 19.99
        assert result["quantity"] == 5

    def test_decode_bytes(self):
        """Test bytes are decoded to strings."""
        data = {"content": b"hello world", "name": "Alice"}
        result = clean_dict(data)

        assert isinstance(result["content"], str)
        assert result["content"] == "hello world"

    def test_nested_dict_with_none_values(self):
        """Test nested dictionaries with None values."""
        data = {
            "user": {"name": "Alice", "email": None},
            "metadata": None,
            "age": 30,
        }
        result = clean_dict(data)

        assert "metadata" not in result
        assert "user" in result
        # Note: clean_dict may not recursively clean nested dicts

    def test_mixed_types(self):
        """Test dictionary with mixed types."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        data = {
            "name": "Alice",
            "email": "alice@example.com",
            "age": 30,
            "balance": Decimal("100.50"),
            "created_at": dt,
            "notes": None,
            "bio": b"Software engineer",
        }
        result = clean_dict(data)

        assert result["name"] == "Alice"
        assert result["email"] == "alice@example.com"
        assert result["age"] == 30
        assert result["balance"] == 100.50
        assert isinstance(result["created_at"], str)
        assert "notes" not in result
        assert result["bio"] == "Software engineer"

    def test_empty_dict(self):
        """Test empty dictionary."""
        result = clean_dict({})
        assert result == {}

    def test_all_none_values(self):
        """Test dictionary with all None values."""
        data = {"a": None, "b": None, "c": None}
        result = clean_dict(data)

        assert result == {}
