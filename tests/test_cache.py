"""Tests for Redis caching and session storage."""

import json

import fakeredis.aioredis
import pytest
import pytest_asyncio

from graphsql import cache
from graphsql.cache import (
    cache_delete,
    cache_get,
    cache_set,
    session_create,
    session_delete,
    session_get,
)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def fake_redis():
    """Provide a fakeredis client and patch the module-level client."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    cache._redis_client = fake
    yield fake
    await fake.close()
    cache._redis_client = None


@pytest.mark.asyncio
async def test_cache_set_and_get(fake_redis):
    key = "test-key"
    value = {"foo": "bar"}

    await cache_set(key, value, ttl=5)
    stored_raw = await fake_redis.get("graphsql:cache:" + key)
    assert stored_raw == json.dumps(value)

    cached = await cache_get(key)
    assert cached == value


@pytest.mark.asyncio
async def test_cache_delete(fake_redis):
    key = "delete-key"
    await cache_set(key, {"a": 1}, ttl=5)
    await cache_delete(key)
    assert await cache_get(key) is None


@pytest.mark.asyncio
async def test_session_create_and_get(fake_redis):
    session_id = "session-123"
    data = {"user_id": "u1", "scope": "admin"}

    await session_create(session_id, data, ttl=5)
    stored_raw = await fake_redis.get("graphsql:session:" + session_id)
    assert stored_raw == json.dumps(data)

    loaded = await session_get(session_id)
    assert loaded == data


@pytest.mark.asyncio
async def test_session_delete(fake_redis):
    session_id = "session-del"
    await session_create(session_id, {"x": 1}, ttl=5)
    await session_delete(session_id)
    assert await session_get(session_id) is None
