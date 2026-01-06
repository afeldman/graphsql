"""Redis-based caching and session storage utilities."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger
from redis.asyncio import Redis

from graphsql.config import settings

_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """Lazily initialize and return a Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        logger.info(
            "Redis client initialized",
            extra={"redis_url": settings.redis_url},
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection if open."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def cache_get(key: str) -> Any | None:
    """Retrieve a cached value by key.

    Returns None on cache miss or connection issues.
    """
    try:
        client = await get_redis()
        value = await client.get(settings.cache_prefix + key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Cache get failed for key {key}: {exc}")
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    """Store a value in cache with optional TTL."""
    try:
        client = await get_redis()
        await client.set(
            settings.cache_prefix + key,
            json.dumps(value, default=str),
            ex=ttl or settings.cache_ttl_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Cache set failed for key {key}: {exc}")


async def cache_delete(key: str) -> None:
    """Delete a cached key."""
    try:
        client = await get_redis()
        await client.delete(settings.cache_prefix + key)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Cache delete failed for key {key}: {exc}")


async def session_create(session_id: str, data: dict, ttl: int | None = None) -> None:
    """Create a session stored in Redis."""
    try:
        client = await get_redis()
        await client.set(
            settings.session_prefix + session_id,
            json.dumps(data, default=str),
            ex=ttl or settings.session_ttl_seconds,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Session create failed for {session_id}: {exc}")


async def session_get(session_id: str) -> dict | None:
    """Fetch a session payload from Redis."""
    try:
        client = await get_redis()
        value = await client.get(settings.session_prefix + session_id)
        return json.loads(value) if value else None
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Session get failed for {session_id}: {exc}")
        return None


async def session_delete(session_id: str) -> None:
    """Delete a stored session."""
    try:
        client = await get_redis()
        await client.delete(settings.session_prefix + session_id)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Session delete failed for {session_id}: {exc}")
