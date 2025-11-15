"""
WebSocket endpoints for compliance real-time updates
"""

import json
import logging
from typing import Any

from core.security import verify_token
from api.websockets.compliance_manager import get_compliance_ws_manager
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws/compliance-updates", tags=["websocket", "compliance"])

# Get global WebSocket manager
ws_manager = get_compliance_ws_manager()


@router.websocket("")
async def compliance_websocket(
    websocket: WebSocket,
    token: str | None = Query(None, description="JWT authentication token"),
):
    """
    WebSocket endpoint for compliance real-time updates.
    
    Connection URL:
    ws://localhost:8000/ws/compliance-updates?token=your_jwt_token
    
    Message Types (Server → Client):
    - connection_established: Initial connection confirmation
    - compliance_update: Compliance metrics changed (new SMS sent, delivery event, subscriber change)
    - pong: Response to ping (keep-alive)
    
    Message Types (Client → Server):
    - ping: Keep connection alive
    
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
        logger.info(f"Admin {admin_id} disconnected normally from compliance updates")

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
async def broadcast_compliance_update(data: dict[str, Any], exclude_admin: str | None = None):
    """
    Broadcast compliance update to all connected admins.
    
    Args:
        data: Compliance update data
        exclude_admin: Optional admin ID to exclude from broadcast
    
    This function should be called when:
    - New subscriber is added
    - SMS is sent
    - Delivery status changes
    - Campaign metrics are updated
    """
    message = {
        "type": "compliance_update",
        "data": data,
    }

    await ws_manager.broadcast_to_all_admins(message, exclude_admin=exclude_admin)


async def send_to_admin(admin_id: str, data: dict[str, Any]):
    """
    Send compliance update to specific admin.
    
    Args:
        admin_id: Admin user ID
        data: Update data
    """
    message = {
        "type": "compliance_update",
        "data": data,
    }

    await ws_manager.send_to_admin(admin_id, message)
