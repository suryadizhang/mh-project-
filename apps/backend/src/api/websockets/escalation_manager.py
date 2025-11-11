"""
WebSocket Manager for Escalations
Handles real-time updates for admin escalation inbox
"""

import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class EscalationWebSocketManager:
    """
    Manages WebSocket connections for escalation real-time updates.
    
    Features:
    - Admin connections by user ID
    - Broadcast new escalations to all connected admins
    - Send status updates to specific admin
    - Track connection metadata
    """

    def __init__(self):
        # Active connections by admin user ID
        self.active_connections: dict[str, set[WebSocket]] = {}
        # Connection metadata
        self.connection_metadata: dict[WebSocket, dict[str, Any]] = {}
        # Last ping time for connection health
        self.last_ping: dict[WebSocket, datetime] = {}

    async def connect(self, websocket: WebSocket, admin_id: str, client_info: dict[str, Any] | None = None):
        """
        Accept new WebSocket connection from admin.
        
        Args:
            websocket: WebSocket connection instance
            admin_id: Admin user ID
            client_info: Optional client metadata (browser, version, etc.)
        """
        await websocket.accept()

        # Add to active connections
        if admin_id not in self.active_connections:
            self.active_connections[admin_id] = set()

        self.active_connections[admin_id].add(websocket)

        # Store connection metadata
        connection_id = str(uuid4())
        self.connection_metadata[websocket] = {
            "admin_id": admin_id,
            "connection_id": connection_id,
            "connected_at": datetime.utcnow().isoformat(),
            "client_info": client_info or {},
        }

        self.last_ping[websocket] = datetime.utcnow()

        logger.info(f"✅ Admin {admin_id} connected to escalation WebSocket ({connection_id})")

        # Send connection confirmation
        await self.send_to_connection(
            websocket,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "admin_id": admin_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to escalation updates",
            },
        )

    async def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        metadata = self.connection_metadata.get(websocket)
        admin_id = metadata.get("admin_id") if metadata else None

        # Remove from active connections
        if admin_id and admin_id in self.active_connections:
            self.active_connections[admin_id].discard(websocket)

            if not self.active_connections[admin_id]:
                del self.active_connections[admin_id]

        # Clean up metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        if websocket in self.last_ping:
            del self.last_ping[websocket]

        logger.info(f"🔌 Admin {admin_id} disconnected from escalation WebSocket")

    async def send_to_connection(self, websocket: WebSocket, message: dict[str, Any]):
        """
        Send message to specific WebSocket connection.
        
        Args:
            websocket: Target WebSocket connection
            message: Message data to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to connection: {e}")
            # Connection is probably dead, disconnect it
            await self.disconnect(websocket)

    async def send_to_admin(self, admin_id: str, message: dict[str, Any]):
        """
        Send message to all connections for a specific admin.
        
        Args:
            admin_id: Admin user ID
            message: Message data to send
        """
        if admin_id in self.active_connections:
            disconnected = []

            for websocket in list(self.active_connections[admin_id]):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to admin {admin_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected connections
            for websocket in disconnected:
                await self.disconnect(websocket)

    async def broadcast_to_all_admins(self, message: dict[str, Any], exclude_admin: str | None = None):
        """
        Broadcast message to all connected admins.
        
        Args:
            message: Message data to send
            exclude_admin: Optional admin ID to exclude from broadcast
        """
        disconnected = []

        for admin_id, connections in list(self.active_connections.items()):
            if exclude_admin and admin_id == exclude_admin:
                continue

            for websocket in list(connections):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to admin {admin_id}: {e}")
                    disconnected.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def handle_ping(self, websocket: WebSocket):
        """
        Handle ping message to keep connection alive.
        
        Args:
            websocket: WebSocket connection
        """
        self.last_ping[websocket] = datetime.utcnow()

        await self.send_to_connection(
            websocket,
            {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def get_connection_stats(self) -> dict[str, Any]:
        """
        Get current connection statistics.
        
        Returns:
            Dict with connection stats
        """
        total_connections = sum(len(connections) for connections in self.active_connections.values())

        return {
            "total_connections": total_connections,
            "active_admins": len(self.active_connections),
            "connections_by_admin": {
                admin_id: len(connections)
                for admin_id, connections in self.active_connections.items()
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global connection manager instance
escalation_ws_manager = EscalationWebSocketManager()


def get_escalation_ws_manager() -> EscalationWebSocketManager:
    """Get the global escalation WebSocket manager instance."""
    return escalation_ws_manager
