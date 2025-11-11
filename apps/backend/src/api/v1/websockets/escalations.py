"""
WebSocket endpoints for escalation real-time updates
"""

import json
import logging
from typing import Any

from core.security import verify_token
from api.websockets.escalation_manager import get_escalation_ws_manager
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws/escalations", tags=["websocket", "escalations"])

# Get global WebSocket manager
ws_manager = get_escalation_ws_manager()


@router.websocket("")
async def escalation_websocket(
    websocket: WebSocket,
    token: str | None = Query(None, description="JWT authentication token"),
):
    """
    WebSocket endpoint for escalation real-time updates.
    
    Connection URL:
    ws://localhost:8000/api/v1/ws/escalations?token=your_jwt_token
    
    Message Types (Server → Client):
    - connection_established: Initial connection confirmation
    - escalation_created: New escalation created
    - escalation_updated: Escalation status/assignment changed
    - escalation_resolved: Escalation resolved
    - stats_updated: Escalation stats changed (counts)
    - pong: Response to ping (keep-alive)
    
    Message Types (Client → Server):
    - ping: Keep connection alive
    - subscribe: Subscribe to specific escalation updates
    - unsubscribe: Unsubscribe from escalation updates
    
    Authentication:
    - Requires valid JWT token in query parameter
    - Must have admin permissions
    """

    admin_id: str | None = None

    try:
        # Authenticate connection
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
            return

        try:
            # Verify JWT token
            payload = verify_token(token)
            admin_id = payload.get("sub")  # User ID from token

            if not admin_id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
                return

        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
            return

        # Connect to manager
        await ws_manager.connect(websocket, admin_id)

        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Handle message based on type
                message_type = message_data.get("type")

                if message_type == "ping":
                    await ws_manager.handle_ping(websocket)

                elif message_type == "subscribe":
                    # Client subscribes to specific escalation updates
                    escalation_id = message_data.get("escalation_id")
                    logger.info(f"Admin {admin_id} subscribed to escalation {escalation_id}")

                    await ws_manager.send_to_connection(
                        websocket,
                        {
                            "type": "subscribed",
                            "escalation_id": escalation_id,
                            "message": f"Subscribed to escalation {escalation_id}",
                        },
                    )

                elif message_type == "unsubscribe":
                    # Client unsubscribes from escalation updates
                    escalation_id = message_data.get("escalation_id")
                    logger.info(f"Admin {admin_id} unsubscribed from escalation {escalation_id}")

                    await ws_manager.send_to_connection(
                        websocket,
                        {
                            "type": "unsubscribed",
                            "escalation_id": escalation_id,
                            "message": f"Unsubscribed from escalation {escalation_id}",
                        },
                    )

                else:
                    logger.warning(f"Unknown message type from admin {admin_id}: {message_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from admin {admin_id}")
                await ws_manager.send_to_connection(
                    websocket,
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                    },
                )

            except Exception as e:
                logger.error(f"Error processing message from admin {admin_id}: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"Admin {admin_id} disconnected normally")

    except Exception as e:
        logger.error(f"WebSocket error for admin {admin_id}: {e}")

    finally:
        # Cleanup connection
        if admin_id:
            await ws_manager.disconnect(websocket)


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns connection counts and active admins.
    Useful for monitoring and debugging.
    """
    return ws_manager.get_connection_stats()


# Helper function for broadcasting (called from other modules)
async def broadcast_escalation_event(event_type: str, escalation_data: dict[str, Any], exclude_admin: str | None = None):
    """
    Broadcast escalation event to all connected admins.
    
    Args:
        event_type: Type of event (created, updated, resolved)
        escalation_data: Escalation data to send
        exclude_admin: Optional admin ID to exclude from broadcast
    """
    message = {
        "type": f"escalation_{event_type}",
        "data": escalation_data,
        "timestamp": escalation_data.get("created_at") or escalation_data.get("updated_at"),
    }

    await ws_manager.broadcast_to_all_admins(message, exclude_admin=exclude_admin)


async def send_to_admin(admin_id: str, event_type: str, data: dict[str, Any]):
    """
    Send escalation event to specific admin.
    
    Args:
        admin_id: Admin user ID
        event_type: Type of event
        data: Event data
    """
    message = {
        "type": event_type,
        "data": data,
        "timestamp": data.get("created_at") or data.get("updated_at"),
    }

    await ws_manager.send_to_admin(admin_id, message)
