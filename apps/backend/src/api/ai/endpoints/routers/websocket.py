"""
WebSocket routes for real-time AI chat
Provides WebSocket endpoints for live chat functionality with role-based AI routing
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
import logging
from typing import Optional
import json
from datetime import datetime

from api.ai.endpoints.websocket_manager import websocket_manager, MessageType, WebSocketMessage
from api.ai.endpoints.services.chat_service import ChatService
from api.ai.endpoints.services.role_based_ai import UserRole
from api.ai.endpoints.services.customer_booking_ai import customer_booking_ai
from api.ai.endpoints.services.admin_management_ai import admin_management_ai
from api.ai.endpoints.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# Lead generation and newsletter services
from api.app.services.lead_service import LeadService
from api.app.services.newsletter_service import NewsletterService
from api.app.models.lead_newsletter import LeadSource

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    conversation_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query("admin"),
    channel: Optional[str] = Query("admin"),
    user_role: Optional[str] = Query("customer")
):
    """
    WebSocket endpoint for real-time AI chat with role-based routing
    
    Query parameters:
    - conversation_id: Optional existing conversation ID
    - user_id: User identifier (default: "admin")
    - channel: Communication channel (default: "admin")
    - user_role: User role for AI routing (customer, admin, staff, super_admin)
    """
    
    # Generate conversation ID if not provided
    if not conversation_id:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        conversation_id = f"{channel}_{user_id}_{timestamp}"
    
    # Parse user role
    try:
        parsed_user_role = UserRole(user_role.lower())
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse user role '{user_role}', defaulting to CUSTOMER")
        parsed_user_role = UserRole.CUSTOMER
    
    # User info for this connection
    user_info = {
        "user_id": user_id,
        "channel": channel,
        "user_role": parsed_user_role.value,
        "connected_at": datetime.utcnow().isoformat()
    }
    
    # Connect to WebSocket manager
    await websocket_manager.connect(websocket, conversation_id, user_info)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")
                content = message_data.get("content", "")
                
                logger.info(f"Received WebSocket message: {message_type} in conversation {conversation_id}")
                
                # Handle different message types
                if message_type == "message" and content.strip():
                    # Extract contact information for lead generation
                    user_name = message_data.get("userName")
                    user_phone = message_data.get("userPhone")
                    user_email = message_data.get("userEmail")
                    auto_subscribe = message_data.get("autoSubscribeNewsletter", False)
                    
                    # Process lead generation and newsletter subscription if contact info provided
                    if user_name and user_phone:
                        try:
                            # Get database session
                            db_gen = get_db()
                            db = await anext(db_gen)
                            
                            try:
                                # Create or update lead
                                lead_service = LeadService(db)
                                lead = await lead_service.capture_quote_request(
                                    name=user_name,
                                    phone=user_phone,
                                    email=user_email,
                                    message=f"Chat conversation: {content[:100]}..."
                                )
                                logger.info(f"Created/updated lead {lead.id} from chat for {user_name}")
                                
                                # Subscribe to newsletter (opt-out system)
                                if auto_subscribe:
                                    newsletter_service = NewsletterService(db)
                                    subscriber = await newsletter_service.subscribe(
                                        phone=user_phone,
                                        email=user_email,
                                        name=user_name,
                                        source='chat',
                                        auto_subscribed=True
                                    )
                                    logger.info(
                                        f"Auto-subscribed {user_name} to newsletter. "
                                        f"Subscriber ID: {subscriber.id}"
                                    )
                                
                                await db.commit()
                                
                            except Exception as lead_error:
                                await db.rollback()
                                logger.error(f"Error creating lead or subscribing to newsletter: {lead_error}")
                                # Continue processing the chat message even if lead creation fails
                            
                            finally:
                                await db.close()
                                
                        except Exception as db_error:
                            logger.error(f"Error getting database session: {db_error}")
                            # Continue processing the chat message even if database fails
                    
                    # Process AI chat message with role-based routing
                    await handle_chat_message_with_role(
                        conversation_id, content, user_id, channel, parsed_user_role
                    )
                
                elif message_type == "ping":
                    # Respond to ping with pong
                    pong_message = WebSocketMessage(
                        type=MessageType.SYSTEM,
                        conversation_id=conversation_id,
                        content="pong",
                        timestamp=datetime.utcnow()
                    )
                    await websocket_manager.send_to_websocket(websocket, pong_message)
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await websocket_manager.send_error_message(
                    conversation_id, 
                    "Invalid message format. Please send valid JSON."
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket_manager.send_error_message(
                    conversation_id, 
                    f"Error processing message: {str(e)}"
                )
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        websocket_manager.disconnect(websocket, conversation_id)


async def handle_chat_message_with_role(
    conversation_id: str, content: str, user_id: str, channel: str, user_role: UserRole
):
    """Handle incoming chat message with role-based AI routing"""
    try:
        # Send typing indicator
        await websocket_manager.send_typing_indicator(conversation_id, True)
        
        # Prepare context for AI processing
        context = {
            "user_id": user_id,
            "user_role": user_role,
            "channel": channel,
            "conversation_id": conversation_id,
            "websocket": True,
            "real_time": True
        }
        
        # Route to appropriate AI service based on role
        if user_role == UserRole.CUSTOMER:
            logger.info(f"Routing to customer_booking_ai for message: '{content[:50]}...'")
            ai_response = await customer_booking_ai.process_customer_message(content, context)
        elif user_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]:
            logger.info(f"Routing to admin_management_ai for message: '{content[:50]}...'")
            ai_response = await admin_management_ai.process_admin_message(content, context)
        else:
            logger.warning(f"Unknown user role: {user_role}, using default response")
            ai_response = {
                "response": "Hello! I'm MyHibachi's AI assistant. How can I help you today?",
                "intent": "general"
            }
        
        # Stop typing indicator
        await websocket_manager.send_typing_indicator(conversation_id, False)
        
        # Extract response content
        response_content = ai_response.get("response", "I'm here to help!")
        intent = ai_response.get("intent", "general")
        
        # Send AI response via WebSocket
        await websocket_manager.send_ai_response(
            conversation_id=conversation_id,
            content=response_content,
            message_id=f"ws_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            metadata={
                "user_role": user_role.value,
                "intent": intent,
                "channel": channel,
                "ai_service": "customer_booking" if user_role == UserRole.CUSTOMER else "admin_management"
            }
        )
        
        logger.info(f"Role-based AI response sent via WebSocket: {user_role.value} - {intent}")
        
    except Exception as e:
        logger.error(f"Error handling role-based chat message: {e}")
        
        # Stop typing indicator
        await websocket_manager.send_typing_indicator(conversation_id, False)
        
        # Send error message
        await websocket_manager.send_error_message(
            conversation_id, 
            "Sorry, I'm having trouble processing your message right now."
        )


async def handle_chat_message(conversation_id: str, content: str, user_id: str, channel: str):
    """Handle incoming chat message and generate AI response (legacy method)"""
    # Default to customer role for backward compatibility
    await handle_chat_message_with_role(
        conversation_id, content, user_id, channel, UserRole.CUSTOMER
    )


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()


@router.post("/ws/broadcast/{conversation_id}")
async def broadcast_message(
    conversation_id: str,
    message: dict
):
    """
    Broadcast a message to all connections in a conversation
    (Admin endpoint for testing)
    """
    try:
        ws_message = WebSocketMessage(
            type=MessageType.SYSTEM,
            conversation_id=conversation_id,
            content=message.get("content", ""),
            timestamp=datetime.utcnow(),
            metadata=message.get("metadata")
        )
        
        await websocket_manager.broadcast_to_conversation(conversation_id, ws_message)
        
        return {
            "success": True,
            "message": f"Message broadcasted to conversation {conversation_id}"
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return {
            "success": False,
            "error": str(e)
        }