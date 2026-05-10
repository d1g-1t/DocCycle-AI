"""WebSocket endpoint for streaming AI review progress."""
from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Simple in-memory registry (production: use Redis pub/sub)
_active_connections: dict[str, list[WebSocket]] = {}


async def notify_review_progress(run_id: UUID, step: str, data: dict[str, Any]) -> None:
    """Send review progress to all connected WebSocket clients."""
    key = str(run_id)
    if key not in _active_connections:
        return
    payload = json.dumps({"step": step, "run_id": key, **data})
    disconnected: list[WebSocket] = []
    for ws in _active_connections[key]:
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        _active_connections[key].remove(ws)


@router.websocket("/ws/review/{run_id}")
async def review_websocket(websocket: WebSocket, run_id: UUID) -> None:
    """WebSocket endpoint for real-time AI review streaming."""
    await websocket.accept()
    key = str(run_id)
    if key not in _active_connections:
        _active_connections[key] = []
    _active_connections[key].append(websocket)

    try:
        while True:
            # Keep connection alive; client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        if key in _active_connections and websocket in _active_connections[key]:
            _active_connections[key].remove(websocket)
            if not _active_connections[key]:
                del _active_connections[key]
