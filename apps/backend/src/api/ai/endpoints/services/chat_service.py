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
from api.ai.endpoints.services.knowledge_base_simple import SimpleKnowledgeBaseService as KnowledgeBaseService


class ChatService:
    def __init__(self):
        self.ai_service = AIPipeline()
        self.kb_service = KnowledgeBaseService()

    async def ingest_chat(
        self, request: ChatIngestRequest, db: AsyncSession
    ) -> ChatIngestResponse:
        """
        Main entry point for all channels (website, SMS, DMs, voice transcripts)
        Normalizes messages and processes through AI pipeline
        """
        start_time = time.time()

        try:
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
                content=request.message,
                channel=request.channel.value,
                metadata=request.metadata or {},
            )
            db.add(incoming_message)

            # Process through AI pipeline
            ai_response = await self.ai_service.process_message(
                message=request.message,
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