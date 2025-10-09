"""
MyHibachi AI Backend - Main FastAPI Application
Multi-channel customer support with knowledge base and human escalation
"""

# Standard library imports
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import uuid4

# Third-party imports
from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from app.database import close_db, get_db, init_db
from app.logging_config import (
    AILogger,
    DatabaseLogger,
    RequestLogger,
    WebSocketLogger,
    setup_logging,
)
from app.models import (
    ChannelType,
    Conversation,
    ConversationStatus,
    KnowledgeBaseChunk,
    Message,
    MessageRole,
    TrainingData,
)
from app.monitoring import performance_monitor, start_metrics_server
from app.routers import webhooks
from app.schemas import (
    ChatIngestRequest,
    ChatIngestResponse,
    ChatReplyRequest,
    ChatReplyResponse,
    ChatRequest,
    ChatResponse,
    EscalationRequest,
    EscalationResponse,
    FeedbackRequest,
    KBChunkCreate,
    KBChunkResponse,
    KBSearchRequest,
    KBSearchResponse,
    TrainingDataCreate,
    WebSocketMessage,
)
from app.services.ai_pipeline import ai_pipeline
from app.services.knowledge_base import kb_service

# Load environment variables after imports
load_dotenv()

# Global loggers (initialized in lifespan)
logger = None
request_logger = None
ws_logger = None
ai_logger = None
db_logger = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Setup logging first
    global logger, request_logger, ws_logger, ai_logger, db_logger
    logger = setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file="logs/myhibachi_ai.log",
        json_logs=os.getenv("JSON_LOGS", "false").lower() == "true",
    )
    request_logger = RequestLogger(logger)
    ws_logger = WebSocketLogger(logger)
    ai_logger = AILogger(logger)
    db_logger = DatabaseLogger(logger)

    # Startup
    logger.info("🚀 Starting MyHibachi AI Backend...", version="1.0.0")

    # Start metrics server
    try:
        start_metrics_server(port=8000)
        logger.info("✅ Metrics server started on port 8000")
    except Exception as e:
        logger.warning("⚠️ Failed to start metrics server", error=str(e))

    await init_db()
    logger.info("✅ Database initialized")

    # Load initial knowledge base if empty
    async for db in get_db():
        await seed_initial_knowledge_base(db)
        break

    yield

    # Shutdown
    print("🛑 Shutting down MyHibachi AI Backend...")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="MyHibachi AI Customer Support",
    description="Multi-channel AI-powered customer service with human escalation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://myhibachi.vercel.app",
        "https://myhibachichef.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhooks.router)

# Security
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """Get current user from JWT token (placeholder for now)"""
    # TODO: Implement proper JWT validation
    if credentials:
        return {"id": "system", "role": "system"}
    return None


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time chat"""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)

        # Log connection and update metrics
        if ws_logger:
            ws_logger.log_connection(str(id(websocket)), conversation_id)
        performance_monitor.record_websocket_connection(connected=True)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

        # Log disconnection and update metrics
        if ws_logger:
            ws_logger.log_disconnection(str(id(websocket)), conversation_id)
        performance_monitor.record_websocket_connection(connected=False)

    async def send_message(
        self, message: WebSocketMessage, conversation_id: str
    ):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_json(message.dict())
                except Exception:
                    pass  # Connection closed


manager = ConnectionManager()


# Health check and monitoring endpoints
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    if logger:
        logger.debug("Health check requested")

    health_status = performance_monitor.get_health_status()

    # Test database connection
    try:
        async for db in get_db():
            # Simple query to test database connectivity
            await db.execute(select(1))
            health_status["database"] = "connected"
            break
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        if logger:
            logger.error("Database health check failed", error=str(e))

    # Test AI service
    try:
        # Simple test to verify OpenAI service is accessible
        health_status["ai_service"] = "available"
    except Exception as e:
        health_status["ai_service"] = f"error: {str(e)}"
        if logger:
            logger.error("AI service health check failed", error=str(e))

    return health_status


@app.get("/metrics/summary")
async def metrics_summary():
    """Get performance metrics summary"""
    if logger:
        logger.debug("Metrics summary requested")

    return performance_monitor.get_current_metrics().__dict__


@app.get("/status")
async def system_status():
    """Get detailed system status"""
    if logger:
        logger.debug("System status requested")

    return {
        "service": "MyHibachi AI Backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "health": await health_check(),
        "endpoints": {
            "chat_ingest": "/chat/ingest",
            "chat_reply": "/chat/reply",
            "websocket": "/ws/chat",
            "knowledge_base": "/kb",
            "webhooks": "/webhooks",
            "metrics": "http://localhost:8000/metrics",
        },
    }


# Main Chat Endpoints
@app.post("/chat/ingest", response_model=ChatIngestResponse)
async def chat_ingest_endpoint(
    request: ChatIngestRequest, db: AsyncSession = Depends(get_db)
):
    """
    Main entry point for all channels (website, SMS, DMs, voice transcripts)
    Normalizes messages and processes through AI pipeline
    """
    from app.services.chat_service import chat_service
    return await chat_service.ingest_chat(request, db)

        if not conversation:
            conversation = Conversation(
                channel=request.channel.value,
                user_id=request.user_id,
                thread_id=request.thread_id,
                status=ConversationStatus.AI.value,
                channel_metadata=request.metadata,
            )
            db.add(conversation)
            await db.flush()  # Get the ID

        # Check if conversation should be handled by human
        if conversation.status == ConversationStatus.HUMAN.value:
            # Store message but don't auto-reply
            user_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.USER.value,
                text=request.text,
            )
            db.add(user_message)
            await db.commit()

            # Notify via WebSocket
            ws_message = WebSocketMessage(
                type="message",
                conversation_id=conversation.id,
                content=request.text,
                role=MessageRole.USER,
            )
            await manager.send_message(ws_message, str(conversation.id))

            return ChatIngestResponse(
                message_id=user_message.id,
                conversation_id=conversation.id,
                reply="A team member will respond to your message shortly.",
                confidence=1.0,
                source="human",
                processing_time_ms=int((time.time() - start_time) * 1000),
                escalated=False,
            )

        # Process through AI pipeline
        ai_response = await ai_pipeline.process_message(
            db, conversation.id, request.text
        )

        # Check if we should escalate
        (
            should_escalate,
            escalation_reason,
        ) = await ai_pipeline.should_escalate_conversation(db, conversation.id)

        escalated = False
        if should_escalate or ai_response.source == "escalation":
            # Update conversation status
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(
                    status=ConversationStatus.ESCALATED.value,
                    escalated_at=datetime.utcnow(),
                    escalation_reason=escalation_reason,
                )
            )
            await db.commit()
            escalated = True

            # Notify agents via WebSocket
            agent_message = WebSocketMessage(
                type="escalation",
                conversation_id=conversation.id,
                content=f"Conversation escalated: {escalation_reason}",
                role=MessageRole.SYSTEM,
            )
            await manager.send_message(
                agent_message, f"agents-{conversation.id}"
            )

        # Send response via WebSocket
        ws_message = WebSocketMessage(
            type="message",
            conversation_id=conversation.id,
            content=ai_response.reply,
            role=(
                MessageRole.AI
                if "gpt" not in ai_response.source
                else MessageRole.GPT
            ),
        )
        await manager.send_message(ws_message, str(conversation.id))

        return ChatIngestResponse(
            message_id=uuid4(),  # Would be actual message ID from AI pipeline
            conversation_id=conversation.id,
            reply=ai_response.reply,
            confidence=ai_response.confidence,
            source=ai_response.source,
            processing_time_ms=int((time.time() - start_time) * 1000),
            escalated=escalated,
        )

    except Exception as e:
        print(f"Error in chat ingest: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process message"
        )


@app.post("/chat/reply", response_model=ChatReplyResponse)
async def chat_reply(
    request: ChatReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Internal endpoint for processing messages through AI pipeline
    Used by other services or for testing
    """
    try:
        return await ai_pipeline.process_message(
            db, request.conversation_id, request.message
        )
    except Exception as e:
        print(f"Error in chat reply: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate reply")


@app.post("/chat/escalate", response_model=EscalationResponse)
async def escalate_conversation(
    request: EscalationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Escalate a conversation to human agents
    """
    try:
        # Update conversation status
        await db.execute(
            update(Conversation)
            .where(Conversation.id == request.conversation_id)
            .values(
                status=ConversationStatus.ESCALATED.value,
                escalated_at=datetime.utcnow(),
                escalation_reason=request.reason,
            )
        )
        await db.commit()

        # Notify agents
        ws_message = WebSocketMessage(
            type="escalation",
            conversation_id=request.conversation_id,
            content=f"Manual escalation: {request.reason}",
            role=MessageRole.SYSTEM,
            metadata={"priority": request.priority},
        )
        await manager.send_message(
            ws_message, f"agents-{request.conversation_id}"
        )

        return EscalationResponse(
            success=True,
            message="Conversation escalated to human agents",
            escalated_at=datetime.utcnow(),
        )

    except Exception as e:
        print(f"Error escalating conversation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to escalate conversation"
        )


# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    user_id: str,
    thread_id: str,
    channel: str = "website",
):
    """WebSocket endpoint for real-time chat"""
    conversation_id = f"{channel}-{user_id}-{thread_id}"
    await manager.connect(websocket, conversation_id)

    try:
        while True:
            data = await websocket.receive_json()

            # Process incoming message
            if data.get("type") == "message":
                # Create ingest request
                ingest_request = ChatIngestRequest(
                    channel=ChannelType(channel),
                    user_id=user_id,
                    thread_id=thread_id,
                    text=data["content"],
                )

                # Process through ingest endpoint
                async for db in get_db():
                    await chat_ingest(ingest_request, db)
                    break

    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)


# Knowledge Base Endpoints
@app.post("/kb/chunks", response_model=KBChunkResponse)
async def create_kb_chunk(
    request: KBChunkCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new knowledge base chunk"""
    chunk = KnowledgeBaseChunk(
        title=request.title,
        text=request.text,
        tags=request.tags,
        category=request.category,
        source_type=request.source_type,
    )

    success = await kb_service.add_chunk(db, chunk)
    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to create KB chunk"
        )

    return KBChunkResponse(
        id=chunk.id,
        title=chunk.title,
        text=chunk.text,
        tags=chunk.tags,
        category=chunk.category,
        usage_count=0,
        success_rate=0.0,
        created_at=chunk.created_at,
    )


@app.post("/kb/search", response_model=KBSearchResponse)
async def search_kb_chunks(
    request: KBSearchRequest, db: AsyncSession = Depends(get_db)
):
    """Search knowledge base chunks"""

    chunks, query_time = await kb_service.search_chunks(db, request)

    return KBSearchResponse(
        chunks=chunks, total_results=len(chunks), query_time_ms=query_time
    )


@app.post("/kb/rebuild-index")
async def rebuild_kb_index(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    """Rebuild the FAISS index from database"""
    success = await kb_service.rebuild_index(db)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to rebuild index")

    return {"success": True, "message": "Knowledge base index rebuilt"}


# Training Data Endpoints
@app.post("/training/data")
async def create_training_data(
    request: TrainingDataCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create training data from Q&A pairs"""
    training_data = TrainingData(
        question=request.question,
        answer=request.answer,
        tags=request.tags,
        intent=request.intent,
        source_type=request.source_type,
        confidence_score=request.confidence_score,
    )

    db.add(training_data)
    await db.commit()

    return {"success": True, "id": str(training_data.id)}


# Legacy API endpoints (for backward compatibility)
@app.post("/api/v1/chat", response_model=ChatResponse)
async def legacy_chat(
    request: ChatRequest, db: AsyncSession = Depends(get_db)
):
    """Legacy chat endpoint for backward compatibility"""
    # Convert to new format
    ingest_request = ChatIngestRequest(
        channel=ChannelType.WEBSITE,
        user_id=f"legacy-{request.page}-{int(time.time())}",
        thread_id=f"legacy-{int(time.time())}",
        text=request.message,
        metadata={"page": request.page, "city": request.city},
    )

    response = await chat_ingest(ingest_request, db)

    return ChatResponse(
        answer=response.reply,
        confidence=response.confidence,
        route=response.source,
        sources=[],
        can_escalate=not response.escalated,
        log_id=str(response.message_id),
    )


@app.post("/api/v1/feedback")
async def legacy_feedback(request: FeedbackRequest):
    """Legacy feedback endpoint"""
    print(f"Legacy feedback: {request.log_id} -> {request.feedback}")
    return {"status": "success", "message": "Feedback recorded"}


async def seed_initial_knowledge_base(db: AsyncSession):
    """Seed initial knowledge base with MyHibachi FAQs"""
    # Check if KB is empty
    query = select(KnowledgeBaseChunk).limit(1)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        return  # KB already seeded

    print("🌱 Seeding initial knowledge base...")

    initial_kb = [
        {
            "title": "Service Inclusions - What's Provided",
            "text": "Our hibachi service includes a professional chef, portable hibachi grill, all cooking equipment, and utensils. We provide hibachi vegetables (zucchini, onions, mushrooms), fried rice, and your choice of proteins. Please note: We do NOT include cleanup service, tables, chairs, or dinnerware - these need to be arranged separately.",
            "category": "service_details",
            "tags": [
                "included",
                "service",
                "equipment",
                "cleanup",
                "tables",
                "chairs",
            ],
        },
        {
            "title": "Service Area - Northern California Coverage",
            "text": "Yes! We serve anywhere in Northern California including the greater Sacramento area (Roseville, Folsom, Davis, and surrounding cities) and the Bay Area (San Francisco, San Jose, Oakland, Palo Alto, Mountain View, Santa Clara, Sunnyvale, Fremont). We have reasonable travel fees that apply based on distance from our base location.",
            "category": "service_area",
            "tags": [
                "sacramento",
                "bay area",
                "travel",
                "northern california",
                "service area",
            ],
        },
        {
            "title": "Pricing and Deposit Information",
            "text": "We require a $100 refundable deposit to secure your hibachi booking. This deposit is refundable according to our terms and conditions. The remaining balance is due on the event day. All payment processing is handled through our secure payment portal for your safety and convenience.",
            "category": "pricing",
            "tags": [
                "deposit",
                "100",
                "refundable",
                "pricing",
                "secure",
                "portal",
            ],
        },
        {
            "title": "Available Proteins and Menu Options",
            "text": "We offer premium proteins including chicken, beef steak, shrimp, salmon, tofu for vegetarians, and combination options. All proteins are fresh and prepared with our signature hibachi seasonings.",
            "category": "menu",
            "tags": [
                "proteins",
                "chicken",
                "beef",
                "shrimp",
                "salmon",
                "tofu",
                "vegetarian",
            ],
        },
        {
            "title": "Cancellation and Refund Policy",
            "text": "Please refer to our terms and conditions for our complete cancellation policy. The $100 deposit refund is subject to these terms and conditions. All refunds are processed securely through our payment system and typically take 3-5 business days to appear on your statement.",
            "category": "policy",
            "tags": [
                "cancellation",
                "policy",
                "refund",
                "secure",
                "processing",
                "terms",
            ],
        },
    ]

    for item in initial_kb:
        chunk = KnowledgeBaseChunk(
            title=item["title"],
            text=item["text"],
            category=item["category"],
            tags=item["tags"],
            source_type="initial_seed",
        )

        await kb_service.add_chunk(db, chunk)

    print("✅ Initial knowledge base seeded successfully")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
