"""WebSocket endpoints for streaming change events."""
from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from loguru import logger

from graphsql.cache import get_redis
from graphsql.events import build_channel
from graphsql.auth import verify_token
from graphsql.config import settings

router = APIRouter(tags=["WebSocket"])


POLICY_VIOLATION = status.WS_1008_POLICY_VIOLATION


async def _authenticate(websocket: WebSocket) -> Optional[str]:
    """Authenticate a WebSocket connection when auth is enabled."""
    if not settings.enable_auth:
        return None

    token = websocket.query_params.get("token")

    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]

    if not token:
        await websocket.close(code=POLICY_VIOLATION)
        return None

    try:
        user = verify_token(token)
        return user.user_id
    except HTTPException as exc:  # noqa: BLE001
        logger.debug(f"WebSocket auth failed: {exc.detail}")
        await websocket.close(code=POLICY_VIOLATION)
        return None


async def _stream_messages(websocket: WebSocket, table_name: Optional[str]) -> None:
    """Subscribe to Redis channels and forward messages to the client."""
    client = await get_redis()
    pubsub = client.pubsub()

    channels: List[str] = [build_channel(None)]
    if table_name:
        channels.append(build_channel(table_name))

    await pubsub.subscribe(*channels)
    await websocket.accept()
    await websocket.send_json({
        "type": "welcome",
        "channels": channels,
        "table": table_name,
    })

    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue

            raw = message.get("data")
            try:
                payload = json.loads(raw)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"Dropping malformed pubsub payload: {exc}")
                continue

            await websocket.send_json(payload)
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected")
    finally:
        try:
            await pubsub.unsubscribe(*channels)
            await pubsub.close()
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"PubSub cleanup failed: {exc}")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for change notifications.

    Query parameter ``table`` limits messages to a specific table; otherwise
    the connection receives all broadcast events.
    """
    user_id = await _authenticate(websocket)
    if settings.enable_auth and user_id is None:
        return

    table_param = websocket.query_params.get("table")
    await _stream_messages(websocket, table_param)
