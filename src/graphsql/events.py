"""Event publishing utilities for WebSocket consumers."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from graphsql.cache import get_redis

CHANNEL_PREFIX = "graphsql:ws:"


def build_channel(table_name: str | None = None) -> str:
    """Construct a pub/sub channel name.

    Uses a common prefix so subscriptions can target either a specific table
    or a global broadcast stream.
    """
    return f"{CHANNEL_PREFIX}{table_name or 'all'}"


def build_payload(table_name: str, action: str, record: dict[str, Any]) -> dict[str, Any]:
    """Create a standard payload for change events."""
    return {
        "table": table_name,
        "action": action,
        "record": record,
    }


async def publish_change(table_name: str, action: str, record: dict[str, Any]) -> None:
    """Publish a change event to Redis pub/sub.

    Events are broadcast to the global channel and a table-specific channel so
    clients can choose broad or narrow subscriptions.
    """
    message = json.dumps(build_payload(table_name, action, record), default=str)

    try:
        client = await get_redis()
        await client.publish(build_channel(None), message)
        await client.publish(build_channel(table_name), message)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Publish change failed for {table_name}: {exc}")
