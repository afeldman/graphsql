"""Tests for pagination clamping and rate-limited list endpoint."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from graphsql import rest_routes
from graphsql.config import settings
from graphsql.database import get_db
from graphsql.main import app


class FakeColumn:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeTable:
    def __init__(self, column_names: list[str]) -> None:
        self.columns = [FakeColumn(name) for name in column_names]


class FakeModel:
    __table__ = FakeTable(["id", "name"])


class FakeRecord:
    __table__ = FakeTable(["id", "name"])

    def __init__(self, idx: int) -> None:
        self.id = idx
        self.name = f"record-{idx}"


class FakeQuery:
    def __init__(self, count_result: int) -> None:
        self._count_result = count_result
        self.limit_value = None

    def count(self) -> int:
        return self._count_result

    def offset(self, _: int) -> "FakeQuery":
        return self

    def limit(self, value: int) -> "FakeQuery":
        self.limit_value = value
        return self

    def all(self) -> list[FakeRecord]:
        size = min(self.limit_value or 0, self._count_result)
        return [FakeRecord(i) for i in range(size)]


class FakeSession:
    def __init__(self, count_result: int = 7) -> None:
        self._count_result = count_result
        self.query_obj = FakeQuery(count_result)

    def query(self, _model: Any) -> FakeQuery:
        return self.query_obj

    def close(self) -> None:  # pragma: no cover - no-op for test
        return None


@pytest.fixture
def override_db(monkeypatch) -> None:
    """Override the DB dependency with a fake session."""

    def _override_get_db():
        fake = FakeSession()
        try:
            yield fake
        finally:
            fake.close()

    app.dependency_overrides[get_db] = _override_get_db

    # Patch db_manager.get_model to return our fake model
    monkeypatch.setattr(rest_routes.db_manager, "get_model", lambda _name: FakeModel())

    yield

    app.dependency_overrides.pop(get_db, None)


def test_limit_is_clamped_to_max(monkeypatch, override_db):
    """Requesting a huge limit should be clamped to settings.max_page_size."""
    monkeypatch.setattr(settings, "max_page_size", 5)
    monkeypatch.setattr(settings, "default_page_size", 2)

    client = TestClient(app)
    response = client.get("/api/users", params={"limit": 9999, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5  # clamped
    assert len(data["data"]) == 5  # we only return up to the clamp


def test_limit_respects_requested_within_bounds(monkeypatch, override_db):
    """A small requested limit should be honored when within bounds."""
    monkeypatch.setattr(settings, "max_page_size", 50)
    monkeypatch.setattr(settings, "default_page_size", 2)

    client = TestClient(app)
    response = client.get("/api/users", params={"limit": 3, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 3
    assert len(data["data"]) == 3
