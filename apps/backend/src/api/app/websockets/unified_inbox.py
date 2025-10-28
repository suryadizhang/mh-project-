"""
WebSocket server for unified inbox real-time updates.
Handles real-time communication across all channels (SMS, social media, payments, etc.).
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Set, Optional, Any
import json
import logging
from datetime import datetime
import asyncio
from uuid import uuid4

from api.app.database import get_db
from core.config import get_settings

settings = get_settings()
from api.app.models.lead_newsletter import Lead, SocialThread
from api.app.models.core import Event
from api.app.services.ai_lead_management import get_ai_lead_manager

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for unified inbox."""
    
    def __init__(self):
        # Active connections by user ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Subscriptions by connection
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, client_info: Dict[str, Any] = None):
        """Accept new WebSocket connection."""
        await websocket.accept()
        
        # Add to active connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "client_info": client_info or {},
            "connection_id": str(uuid4())
        }
        
        # Initialize empty subscriptions
        self.subscriptions[websocket] = set()
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "user_id": user_id,
            "connection_id": self.connection_metadata[websocket]["connection_id"],
            "timestamp": datetime.now().isoformat()
        }, websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            user_id = metadata["user_id"]
            
            # Remove from active connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Clean up metadata and subscriptions
            del self.connection_metadata[websocket]
            if websocket in self.subscriptions:
                del self.subscriptions[websocket]
            
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)
    
    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send message to all connections for a specific user."""
        if user_id in self.active_connections:
            for websocket in list(self.active_connections[user_id]):
                await self.send_personal_message(message, websocket)
    
    async def broadcast_to_subscribers(self, message: Dict[str, Any], subscription_type: str):
        """Broadcast message to all connections subscribed to a specific type."""
        for websocket, subscriptions in self.subscriptions.items():
            if subscription_type in subscriptions:
                await self.send_personal_message(message, websocket)
    
    async def subscribe(self, websocket: WebSocket, subscription_types: List[str]):
        """Subscribe connection to specific message types."""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(subscription_types)
            
            await self.send_personal_message({
                "type": "subscription_updated",
                "subscriptions": list(self.subscriptions[websocket]),
                "timestamp": datetime.now().isoformat()
            }, websocket)
    
    async def unsubscribe(self, websocket: WebSocket, subscription_types: List[str]):
        """Unsubscribe connection from specific message types."""
        if websocket in self.subscriptions:
            for sub_type in subscription_types:
                self.subscriptions[websocket].discard(sub_type)
            
            await self.send_personal_message({
                "type": "subscription_updated",
                "subscriptions": list(self.subscriptions[websocket]),
                "timestamp": datetime.now().isoformat()
            }, websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        
        return {
            "total_connections": total_connections,
            "active_users": len(self.active_connections),
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.active_connections.items()
            }
        }


# Global connection manager
manager = ConnectionManager()


async def authenticate_websocket(websocket: WebSocket, token: str) -> Optional[str]:
    """Authenticate WebSocket connection using JWT token."""
    try:
        # This would validate the JWT token and return user_id
        # For now, return a mock user ID
        if token:
            return f"user_{token[-4:]}"  # Mock user ID
        return None
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None


async def handle_websocket_message(websocket: WebSocket, message_data: Dict[str, Any]):
    """Handle incoming WebSocket messages."""
    try:
        message_type = message_data.get("type")
        
        if message_type == "subscribe":
            # Subscribe to specific message types
            subscription_types = message_data.get("subscriptions", [])
            await manager.subscribe(websocket, subscription_types)
            
        elif message_type == "unsubscribe":
            # Unsubscribe from specific message types
            subscription_types = message_data.get("subscriptions", [])
            await manager.unsubscribe(websocket, subscription_types)
            
        elif message_type == "get_threads":
            # Get active threads for user
            await send_active_threads(websocket)
            
        elif message_type == "mark_read":
            # Mark thread as read
            thread_id = message_data.get("thread_id")
            if thread_id:
                await mark_thread_read(websocket, thread_id)
        
        elif message_type == "ping":
            # Respond to ping with pong
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }, websocket)
        
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")


async def send_active_threads(websocket: WebSocket):
    """Send active threads to connected client."""
    try:
        metadata = manager.connection_metadata.get(websocket)
        if not metadata:
            return
        
        # This would typically get threads for the authenticated user
        # For now, send a mock response
        
        await manager.send_personal_message({
            "type": "active_threads",
            "threads": [],  # Would populate with actual thread data
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
    except Exception as e:
        logger.error(f"Error sending active threads: {e}")


async def mark_thread_read(websocket: WebSocket, thread_id: str):
    """Mark thread as read and broadcast update."""
    try:
        # Would update thread read status in database
        # For now, just acknowledge
        
        await manager.send_personal_message({
            "type": "thread_read",
            "thread_id": thread_id,
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Broadcast to other connections for same user
        metadata = manager.connection_metadata.get(websocket)
        if metadata:
            user_id = metadata["user_id"]
            for other_ws in manager.active_connections.get(user_id, set()):
                if other_ws != websocket:
                    await manager.send_personal_message({
                        "type": "thread_read_by_other",
                        "thread_id": thread_id,
                        "timestamp": datetime.now().isoformat()
                    }, other_ws)
        
    except Exception as e:
        logger.error(f"Error marking thread as read: {e}")


# WebSocket endpoint
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    client_type: Optional[str] = Query("web"),
    client_version: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for unified inbox real-time updates.
    
    Query parameters:
    - token: JWT authentication token
    - client_type: Type of client (web, mobile, etc.)
    - client_version: Client version for compatibility
    """
    
    # Authenticate connection
    user_id = await authenticate_websocket(websocket, token)
    if not user_id:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Connect to manager
    await manager.connect(websocket, user_id, {
        "client_type": client_type,
        "client_version": client_version
    })
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle the message
            await handle_websocket_message(websocket, message_data)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except json.JSONDecodeError:
        logger.error("Invalid JSON received from WebSocket client")
        await manager.send_personal_message({
            "type": "error",
            "message": "Invalid JSON format",
            "timestamp": datetime.now().isoformat()
        }, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


# Broadcast functions for webhook handlers
async def broadcast_new_message(thread_data: Dict[str, Any]):
    """Broadcast new message notification."""
    try:
        message = {
            "type": "new_message",
            "thread_id": thread_data.get("thread_id"),
            "lead_id": thread_data.get("lead_id"),
            "platform": thread_data.get("platform"),
            "sender": thread_data.get("sender"),
            "text": thread_data.get("text", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast_to_subscribers(message, "new_messages")
        logger.info(f"Broadcasted new message: {thread_data.get('platform')} - {thread_data.get('sender')}")
        
    except Exception as e:
        logger.error(f"Error broadcasting new message: {e}")


async def broadcast_thread_update(thread_data: Dict[str, Any]):
    """Broadcast thread status update."""
    try:
        message = {
            "type": "thread_update",
            "thread_id": thread_data.get("thread_id"),
            "platform": thread_data.get("platform"),
            "update_type": thread_data.get("event_type", "update"),
            "requires_attention": thread_data.get("requires_attention", False),
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast_to_subscribers(message, "thread_updates")
        logger.info(f"Broadcasted thread update: {thread_data.get('platform')}")
        
    except Exception as e:
        logger.error(f"Error broadcasting thread update: {e}")


async def broadcast_lead_update(lead_data: Dict[str, Any]):
    """Broadcast lead status update."""
    try:
        message = {
            "type": "lead_update",
            "lead_id": lead_data.get("lead_id"),
            "update_type": lead_data.get("update_type", "modified"),
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast_to_subscribers(message, "lead_updates")
        logger.info(f"Broadcasted lead update: {lead_data.get('lead_id')}")
        
    except Exception as e:
        logger.error(f"Error broadcasting lead update: {e}")


async def broadcast_system_alert(alert_data: Dict[str, Any]):
    """Broadcast system-wide alerts."""
    try:
        message = {
            "type": "system_alert",
            "alert_type": alert_data.get("alert_type"),
            "message": alert_data.get("message"),
            "severity": alert_data.get("severity", "info"),
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast_to_subscribers(message, "system_alerts")
        logger.warning(f"Broadcasted system alert: {alert_data.get('alert_type')}")
        
    except Exception as e:
        logger.error(f"Error broadcasting system alert: {e}")


# Health check and stats endpoints
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "status": "healthy",
        "service": "websocket_server",
        "stats": manager.get_connection_stats(),
        "timestamp": datetime.now().isoformat()
    }


async def send_test_message(user_id: str, message: str):
    """Send test message to specific user (for debugging)."""
    test_message = {
        "type": "test_message",
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.send_to_user(test_message, user_id)
    return {"status": "sent", "user_id": user_id, "message": message}


# Background task for periodic updates
async def periodic_health_check():
    """Send periodic health checks to all connections."""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            
            health_message = {
                "type": "health_check",
                "timestamp": datetime.now().isoformat(),
                "active_connections": sum(len(connections) for connections in manager.active_connections.values())
            }
            
            await manager.broadcast_to_subscribers(health_message, "system_updates")
            
        except Exception as e:
            logger.error(f"Error in periodic health check: {e}")


# Initialize background tasks
async def start_websocket_background_tasks():
    """Start background tasks for WebSocket server."""
    asyncio.create_task(periodic_health_check())