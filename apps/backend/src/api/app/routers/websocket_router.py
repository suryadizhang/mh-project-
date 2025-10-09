"""
WebSocket router for unified inbox.
Provides WebSocket endpoints for real-time communication updates.
"""
from fastapi import APIRouter, WebSocket, Query
from typing import Optional

from ..websockets.unified_inbox import (
    websocket_endpoint,
    get_websocket_stats,
    send_test_message,
    start_websocket_background_tasks
)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/unified-inbox")
async def websocket_unified_inbox(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    client_type: Optional[str] = Query("web"),
    client_version: Optional[str] = Query(None)
):
    """WebSocket endpoint for unified inbox real-time updates."""
    await websocket_endpoint(websocket, token, client_type, client_version)


@router.get("/stats")
async def websocket_statistics():
    """Get WebSocket server statistics."""
    return await get_websocket_stats()


@router.post("/test/{user_id}")
async def send_test_websocket_message(user_id: str, message: str):
    """Send test message to specific user (for debugging)."""
    return await send_test_message(user_id, message)


# Background tasks should be started by the main application, not during import
# asyncio.create_task(start_websocket_background_tasks())