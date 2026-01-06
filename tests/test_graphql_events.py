import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from graphsql import graphql_schema


class FakeColumn:
    def __init__(
        self, name: str, py_type, primary_key: bool = False, autoincrement: bool = False
    ) -> None:
        self.name = name
        self.primary_key = primary_key
        self.autoincrement = autoincrement
        self.type = type("T", (), {"python_type": py_type})()


class FakeTable:
    def __init__(self) -> None:
        self.columns = [
            FakeColumn("id", int, primary_key=True, autoincrement=True),
            FakeColumn("name", str),
        ]


class FakeModel:
    __table__ = FakeTable()

    def __init__(self, **kwargs) -> None:
        self.__table__ = self.__class__.__table__
        for key, value in kwargs.items():
            setattr(self, key, value)
        if not hasattr(self, "id"):
            self.id = None
        if not hasattr(self, "name"):
            self.name = None


class FakeSession:
    def add(self, _obj) -> None:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def refresh(self, obj) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = 1

    def close(self) -> None:
        return None


@pytest.fixture
def graphql_app(monkeypatch):
    calls = []

    async def fake_publish(table: str, action: str, record):
        calls.append((table, action, record))

    monkeypatch.setattr(graphql_schema, "publish_change", fake_publish)
    monkeypatch.setattr(graphql_schema.db_manager, "list_tables", lambda: ["users"])
    monkeypatch.setattr(graphql_schema.db_manager, "get_model", lambda _name: FakeModel)
    monkeypatch.setattr(graphql_schema.db_manager, "get_primary_key_column", lambda _name: "id")

    def fake_get_db():
        session = FakeSession()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(graphql_schema, "get_db", fake_get_db)

    app = FastAPI()
    app.include_router(graphql_schema.create_graphql_schema(), prefix="")
    return app, calls


def test_graphql_create_emits_event(graphql_app):
    app, calls = graphql_app
    client = TestClient(app)

    mutation = {"query": 'mutation { createUsers(data: { name: "Alice" }) { id name } }'}
    resp = client.post("/graphql", json=mutation)

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["createUsers"]["name"] == "Alice"
    assert calls
    table, action, record = calls[0]
    assert table == "users"
    assert action == "created"
    assert record["name"] == "Alice"
