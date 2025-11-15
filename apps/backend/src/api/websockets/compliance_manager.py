"""
WebSocket connection manager for compliance real-time updates
"""

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ComplianceWebSocketManager:
    """
    Manager for compliance WebSocket connections.
    Handles connection lifecycle and message broadcasting.
    """

    def __init__(self):
        # Map of admin_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, admin_id: str):
        """Connect a new admin WebSocket"""
        await websocket.accept()

        if admin_id not in self.active_connections:
            self.active_connections[admin_id] = []

        self.active_connections[admin_id].append(websocket)

        logger.info(f"Admin {admin_id} connected to compliance updates. Total connections: {self.get_connection_count()}")

        # Send initial connection confirmation
        await self.send_to_connection(
            websocket,
            {
                "type": "connection_established",
                "message": "Connected to compliance updates",
                "admin_id": admin_id,
            },
        )

    async def disconnect(self, websocket: WebSocket):
        """Disconnect admin WebSocket"""
        disconnected_admin_id = None

        # Find and remove connection
        for admin_id, connections in list(self.active_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                disconnected_admin_id = admin_id

                # Clean up empty connection lists
                if not connections:
                    del self.active_connections[admin_id]

                break

        if disconnected_admin_id:
            logger.info(
                f"Admin {disconnected_admin_id} disconnected from compliance updates. "
                f"Total connections: {self.get_connection_count()}"
            )

    async def send_to_connection(self, websocket: WebSocket, message: dict[str, Any]):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to connection: {e}")

    async def send_to_admin(self, admin_id: str, message: dict[str, Any]):
        """Send message to all connections of a specific admin"""
        if admin_id not in self.active_connections:
            logger.debug(f"Admin {admin_id} has no active connections")
            return

        # Send to all connections for this admin
        for websocket in self.active_connections[admin_id]:
            await self.send_to_connection(websocket, message)

    async def broadcast_to_all_admins(self, message: dict[str, Any], exclude_admin: str | None = None):
        """Broadcast message to all connected admins"""
        for admin_id, connections in self.active_connections.items():
            if exclude_admin and admin_id == exclude_admin:
                continue

            for websocket in connections:
                await self.send_to_connection(websocket, message)

        logger.info(f"Broadcast compliance update to {self.get_connection_count()} connections")

    async def handle_ping(self, websocket: WebSocket):
        """Handle ping message (keep-alive)"""
        await self.send_to_connection(websocket, {"type": "pong"})

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_connection_stats(self) -> dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": self.get_connection_count(),
            "total_admins": len(self.active_connections),
            "connections_by_admin": {
                admin_id: len(connections) for admin_id, connections in self.active_connections.items()
            },
        }


# Global singleton instance
_compliance_ws_manager: ComplianceWebSocketManager | None = None


def get_compliance_ws_manager() -> ComplianceWebSocketManager:
    """Get global compliance WebSocket manager instance"""
    global _compliance_ws_manager
    if _compliance_ws_manager is None:
        _compliance_ws_manager = ComplianceWebSocketManager()
    return _compliance_ws_manager
