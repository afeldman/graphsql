import asyncio
import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from graphsql import cache
from graphsql.auth import create_access_token
from graphsql.config import settings
from graphsql.events import publish_change
from graphsql.main import app


def _use_fake_redis(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(cache, "_redis_client", fake, raising=True)
    return fake


def _run(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def test_websocket_receives_table_events(monkeypatch):
    _use_fake_redis(monkeypatch)
    monkeypatch.setattr(settings, "enable_auth", False)
    client = TestClient(app)

    with client.websocket_connect("/ws?table=users") as websocket:
        welcome = websocket.receive_json()
        assert welcome["type"] == "welcome"

        payload = {"id": 1, "name": "Alice"}
        _run(publish_change("users", "created", payload))

        message = websocket.receive_json()
        assert message["table"] == "users"
        assert message["action"] == "created"
        assert message["record"]["name"] == "Alice"


def test_websocket_receives_global_events(monkeypatch):
    _use_fake_redis(monkeypatch)
    monkeypatch.setattr(settings, "enable_auth", False)
    client = TestClient(app)

    with client.websocket_connect("/ws") as websocket:
        welcome = websocket.receive_json()
        assert welcome["type"] == "welcome"

        _run(publish_change("orders", "deleted", {"id": 42}))

        message = websocket.receive_json()
        assert message["table"] == "orders"
        assert message["action"] == "deleted"
        assert message["record"]["id"] == 42


def test_websocket_requires_auth_when_enabled(monkeypatch):
    _use_fake_redis(monkeypatch)
    monkeypatch.setattr(settings, "enable_auth", True)
    client = TestClient(app)

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws"):
            pass


def test_websocket_allows_authenticated_client(monkeypatch):
    _use_fake_redis(monkeypatch)
    monkeypatch.setattr(settings, "enable_auth", True)
    token = create_access_token("user1").access_token
    client = TestClient(app)

    headers = {"Authorization": f"Bearer {token}"}
    with client.websocket_connect("/ws?table=users", headers=headers) as websocket:
        welcome = websocket.receive_json()
        assert welcome["type"] == "welcome"

        payload = {"id": 2, "name": "Bob"}
        _run(publish_change("users", "created", payload))

        message = websocket.receive_json()
        assert message["table"] == "users"
        assert message["record"]["name"] == "Bob"
