"""
WebSocket Manager for Real-time AI Chat
Handles WebSocket connections, message broadcasting, and real-time chat functionality
"""

from datetime import datetime
from enum import Enum
import logging

from fastapi import WebSocket
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""

    MESSAGE = "message"
    TYPING = "typing"
    SYSTEM = "system"
    ERROR = "error"
    CONNECTION_STATUS = "connection_status"
    AI_RESPONSE = "ai_response"


class WebSocketMessage(BaseModel):
    """WebSocket message model"""

    type: MessageType
    conversation_id: str
    content: str
    timestamp: datetime
    user_id: str | None = None
    message_id: str | None = None
    metadata: dict | None = None


class ConnectionManager:
    """Manages WebSocket connections for real-time chat"""

    def __init__(self):
        # Store connections by conversation_id
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Store user info for each connection
        self.connection_info: dict[str, dict] = {}

    async def connect(
        self, websocket: WebSocket, conversation_id: str, user_info: dict | None = None
    ):
        """Accept a new WebSocket connection"""
        try:
            await websocket.accept()

            # Add to active connections
            if conversation_id not in self.active_connections:
                self.active_connections[conversation_id] = []
            self.active_connections[conversation_id].append(websocket)

            # Store connection info
            connection_key = f"{conversation_id}_{id(websocket)}"
            self.connection_info[connection_key] = user_info or {}

            logger.info(f"WebSocket connected for conversation {conversation_id}")

            # Send connection confirmation
            await self.send_to_websocket(
                websocket,
                WebSocketMessage(
                    type=MessageType.CONNECTION_STATUS,
                    conversation_id=conversation_id,
                    content="Connected to AI chat",
                    timestamp=datetime.utcnow(),
                ),
            )

        except Exception as e:
            logger.exception(f"Error connecting WebSocket: {e}")
            raise

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        """Remove a WebSocket connection"""
        try:
            if conversation_id in self.active_connections:
                if websocket in self.active_connections[conversation_id]:
                    self.active_connections[conversation_id].remove(websocket)

                # Clean up empty conversation
                if not self.active_connections[conversation_id]:
                    del self.active_connections[conversation_id]

            # Clean up connection info
            connection_key = f"{conversation_id}_{id(websocket)}"
            if connection_key in self.connection_info:
                del self.connection_info[connection_key]

            logger.info(f"WebSocket disconnected for conversation {conversation_id}")

        except Exception as e:
            logger.exception(f"Error disconnecting WebSocket: {e}")

    async def send_to_websocket(self, websocket: WebSocket, message: WebSocketMessage):
        """Send message to a specific WebSocket"""
        try:
            await websocket.send_text(message.model_dump_json())
        except Exception as e:
            logger.exception(f"Error sending message to WebSocket: {e}")

    async def broadcast_to_conversation(self, conversation_id: str, message: WebSocketMessage):
        """Send message to all connections in a conversation"""
        if conversation_id not in self.active_connections:
            logger.warning(f"No active connections for conversation {conversation_id}")
            return

        # Send to all connections in the conversation
        disconnected_connections = []
        for websocket in self.active_connections[conversation_id]:
            try:
                await self.send_to_websocket(websocket, message)
            except Exception as e:
                logger.exception(f"Failed to send message to WebSocket: {e}")
                disconnected_connections.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected_connections:
            self.disconnect(websocket, conversation_id)

    async def send_ai_response(
        self,
        conversation_id: str,
        content: str,
        message_id: str | None = None,
        metadata: dict | None = None,
    ):
        """Send AI response to conversation"""
        message = WebSocketMessage(
            type=MessageType.AI_RESPONSE,
            conversation_id=conversation_id,
            content=content,
            timestamp=datetime.utcnow(),
            message_id=message_id,
            metadata=metadata,
        )
        await self.broadcast_to_conversation(conversation_id, message)

    async def send_typing_indicator(self, conversation_id: str, is_typing: bool = True):
        """Send typing indicator to conversation"""
        message = WebSocketMessage(
            type=MessageType.TYPING,
            conversation_id=conversation_id,
            content="AI is typing..." if is_typing else "",
            timestamp=datetime.utcnow(),
            metadata={"is_typing": is_typing},
        )
        await self.broadcast_to_conversation(conversation_id, message)

    async def send_system_message(self, conversation_id: str, content: str):
        """Send system message to conversation"""
        message = WebSocketMessage(
            type=MessageType.SYSTEM,
            conversation_id=conversation_id,
            content=content,
            timestamp=datetime.utcnow(),
        )
        await self.broadcast_to_conversation(conversation_id, message)

    async def send_error_message(self, conversation_id: str, error: str):
        """Send error message to conversation"""
        message = WebSocketMessage(
            type=MessageType.ERROR,
            conversation_id=conversation_id,
            content=f"Error: {error}",
            timestamp=datetime.utcnow(),
        )
        await self.broadcast_to_conversation(conversation_id, message)

    def get_active_connections_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_conversation_count(self) -> int:
        """Get number of active conversations"""
        return len(self.active_connections)

    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "active_connections": self.get_active_connections_count(),
            "active_conversations": self.get_conversation_count(),
            "conversations": list(self.active_connections.keys()),
        }


# Global connection manager instance
websocket_manager = ConnectionManager()
