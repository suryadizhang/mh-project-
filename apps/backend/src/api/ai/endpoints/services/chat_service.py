"""
Chat service for handling chat ingestion and processing
"""
import time
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.ai.endpoints.models import (
    ChannelType,
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
)
from api.ai.endpoints.schemas import ChatIngestRequest, ChatIngestResponse
from api.ai.endpoints.services.ai_pipeline import AIPipeline
from api.ai.endpoints.services.knowledge_base_simple import ProductionKnowledgeBaseService as KnowledgeBaseService
from api.ai.endpoints.services.ai_cache_service import get_ai_cache


class ChatService:
    def __init__(self):
        self.ai_service = AIPipeline()
        self.kb_service = KnowledgeBaseService()
        self.cache = get_ai_cache()  # ✅ Initialize cache

    async def ingest_chat(
        self, request: ChatIngestRequest, db: AsyncSession
    ) -> ChatIngestResponse:
        """
        Main entry point for all channels (website, SMS, DMs, voice transcripts)
        Normalizes messages and processes through AI pipeline
        """
        start_time = time.time()

        try:
            # ✅ STEP 1: Check cache first
            cache_context = {
                "user_role": "customer",
                "channel": request.channel.value,
                "user_id": request.user_id
            }
            
            cached_response = await self.cache.get_cached_response(
                message=request.text,  # ✅ Use request.text
                context=cache_context
            )
            
            if cached_response:
                # Cache hit! Return immediately (skip AI processing)
                return ChatIngestResponse(
                    conversation_id=cached_response.get("conversation_id", str(uuid4())),
                    message_id=cached_response.get("message_id", str(uuid4())),
                    response=cached_response["response"],
                    confidence=cached_response.get("confidence", 0.95),
                    source=f"{cached_response.get('source', 'cache')} (cached)",
                    processing_time=time.time() - start_time,  # <50ms for cache hits
                    needs_human_review=False,
                )

            # Find or create conversation
            conversation_query = select(Conversation).where(
                Conversation.channel == request.channel.value,
                Conversation.user_id == request.user_id,
                Conversation.thread_id == request.thread_id,
                Conversation.status != ConversationStatus.CLOSED.value,
            )
            result = await db.execute(conversation_query)
            conversation = result.scalar_one_or_none()

            if not conversation:
                conversation = Conversation(
                    channel=request.channel.value,
                    user_id=request.user_id,
                    thread_id=request.thread_id,
                    status=ConversationStatus.ACTIVE.value,
                    metadata=request.metadata or {},
                )
                db.add(conversation)
                await db.flush()

            # Store the incoming message
            incoming_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.USER.value,
                content=request.text,  # ✅ Use request.text
                channel=request.channel.value,
                metadata=request.metadata or {},
            )
            db.add(incoming_message)

            # Process through AI pipeline
            ai_response = await self.ai_service.process_message(
                message=request.text,  # ✅ Use request.text
                conversation_id=conversation.id,
                channel=request.channel,
                user_context=request.metadata or {},
                db=db,
            )

            # Store AI response
            response_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT.value,
                content=ai_response.message,
                channel=request.channel.value,
                metadata={
                    "confidence": ai_response.confidence,
                    "source": ai_response.source,
                    "processing_time": time.time() - start_time,
                },
            )
            db.add(response_message)

            # Update conversation metadata
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(
                    last_activity=incoming_message.created_at,
                    message_count=Conversation.message_count + 2,
                )
            )

            await db.commit()

            # ✅ STEP 2: Cache the AI response for future use
            cache_data = {
                "conversation_id": str(conversation.id),
                "message_id": str(response_message.id),
                "response": ai_response.message,
                "confidence": ai_response.confidence,
                "source": ai_response.source,
            }
            
            await self.cache.cache_response(
                message=request.text,  # ✅ Use request.text
                response=cache_data,
                context=cache_context
            )

            return ChatIngestResponse(
                conversation_id=str(conversation.id),
                message_id=str(response_message.id),
                response=ai_response.message,
                confidence=ai_response.confidence,
                source=ai_response.source,
                processing_time=time.time() - start_time,
                needs_human_review=ai_response.confidence < 0.5,
            )

        except Exception as e:
            await db.rollback()
            raise e


# Create a global instance
chat_service = ChatService()