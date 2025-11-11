"""
Self-Learning AI Enhancement Service
Learns from user interactions to improve responses over time
"""

from collections import defaultdict
from datetime import datetime, timezone, timedelta
import logging
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SelfLearningAI:
    """
    Self-learning AI system that:
    1. Tracks user feedback on AI responses
    2. Identifies common question variations
    3. Builds knowledge base from successful interactions
    4. Detects gaps in knowledge
    5. Adapts system prompts based on performance
    """

    def __init__(self):
        self.feedback_threshold = {
            "excellent": 0.9,  # User very satisfied
            "good": 0.7,  # User satisfied
            "acceptable": 0.5,  # Neutral
            "poor": 0.3,  # User dissatisfied
        }

        # Learning metrics
        self.learning_stats = {
            "total_interactions": 0,
            "feedback_received": 0,
            "knowledge_gaps_detected": 0,
            "auto_improvements": 0,
        }

        # Question clustering for pattern detection
        self.question_clusters = defaultdict(list)

        logger.info("Self-Learning AI initialized")

    async def record_interaction(self, db: AsyncSession, interaction_data: dict[str, Any]) -> bool:
        """
        Record AI interaction for learning

        interaction_data:
        {
            "user_message": str,
            "ai_response": str,
            "confidence": float,
            "model_used": str,
            "response_time_ms": int,
            "user_feedback": Optional[str],  # "helpful", "not_helpful", "escalated"
            "conversation_id": str,
            "user_role": str,
            "intent_detected": str
        }
        """
        try:
            from api.ai.endpoints.models import (
                Message,
                MessageRole,
            )

            # Store interaction in database
            conversation_id = interaction_data.get("conversation_id")

            # Create message record with learning metadata
            message = Message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT.value,
                content=interaction_data["ai_response"],
                confidence=interaction_data.get("confidence", 0.8),
                model_used=interaction_data.get("model_used", "unknown"),
                metadata={
                    "response_time_ms": interaction_data.get("response_time_ms"),
                    "intent_detected": interaction_data.get("intent_detected"),
                    "user_feedback": interaction_data.get("user_feedback"),
                    "learning_enabled": True,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            db.add(message)
            await db.commit()

            self.learning_stats["total_interactions"] += 1

            logger.debug(f"Recorded interaction for learning: {conversation_id}")
            return True

        except Exception as e:
            logger.exception(f"Error recording interaction: {e}")
            return False

    async def process_user_feedback(
        self, db: AsyncSession, message_id: str, feedback: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process explicit user feedback on AI response

        feedback:
        {
            "rating": int (1-5),
            "helpful": bool,
            "accurate": bool,
            "comment": Optional[str],
            "action_taken": Optional[str]  # "clicked_link", "booked", "escalated", etc.
        }
        """
        try:
            from api.ai.endpoints.models import Message

            # Fetch message
            query = select(Message).where(Message.id == message_id)
            result = await db.execute(query)
            message = result.scalar_one_or_none()

            if not message:
                return {"error": "Message not found"}

            # Update message with feedback
            current_metadata = message.metadata or {}
            current_metadata["user_feedback"] = feedback
            current_metadata["feedback_timestamp"] = datetime.now(timezone.utc).isoformat()
            message.metadata = current_metadata

            await db.commit()

            self.learning_stats["feedback_received"] += 1

            # Analyze feedback for learning
            learning_insights = await self._analyze_feedback(db, message, feedback)

            logger.info(f"Processed feedback for message {message_id}: {feedback.get('rating')}/5")

            return {"success": True, "learning_insights": learning_insights}

        except Exception as e:
            logger.exception(f"Error processing feedback: {e}")
            return {"error": str(e)}

    async def _analyze_feedback(
        self, db: AsyncSession, message: Any, feedback: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze feedback to extract learning insights"""
        insights = {
            "quality_score": 0.0,
            "knowledge_gap_detected": False,
            "improvement_suggestions": [],
        }

        # Calculate quality score
        rating = feedback.get("rating", 3)
        helpful = feedback.get("helpful", True)
        accurate = feedback.get("accurate", True)

        quality_score = (
            (rating / 5.0) * 0.6
            + (1.0 if helpful else 0.0) * 0.2
            + (1.0 if accurate else 0.0) * 0.2
        )
        insights["quality_score"] = round(quality_score, 2)

        # Detect knowledge gaps
        if rating <= 2 or not accurate:
            insights["knowledge_gap_detected"] = True
            self.learning_stats["knowledge_gaps_detected"] += 1

            # Extract what was missing
            user_comment = feedback.get("comment", "")
            if user_comment:
                insights["improvement_suggestions"].append(
                    {
                        "type": "knowledge_gap",
                        "user_query": message.content,
                        "user_feedback": user_comment,
                        "suggested_action": "add_to_knowledge_base",
                    }
                )

        # Check if escalated
        if feedback.get("action_taken") == "escalated":
            insights["improvement_suggestions"].append(
                {
                    "type": "escalation",
                    "reason": "user_needed_human_help",
                    "suggested_action": "improve_context_understanding",
                }
            )

        return insights

    async def identify_common_patterns(
        self, db: AsyncSession, days: int = 7
    ) -> list[dict[str, Any]]:
        """
        Identify common question patterns from recent interactions
        """
        try:
            from api.ai.endpoints.models import Message, MessageRole

            # Get recent user messages
            since_date = datetime.now(timezone.utc) - timedelta(days=days)

            query = select(Message).where(
                and_(Message.role == MessageRole.USER.value, Message.created_at >= since_date)
            )

            result = await db.execute(query)
            messages = result.scalars().all()

            # Cluster similar questions
            patterns = self._cluster_questions([msg.content for msg in messages])

            logger.info(f"Identified {len(patterns)} common patterns from {len(messages)} messages")

            return patterns

        except Exception as e:
            logger.exception(f"Error identifying patterns: {e}")
            return []

    def _cluster_questions(self, questions: list[str]) -> list[dict[str, Any]]:
        """
        Simple keyword-based clustering of questions
        (In production, use embeddings + cosine similarity)
        """
        clusters = defaultdict(list)

        # Extract key topics
        topic_keywords = {
            "payment": ["payment", "pay", "credit", "card", "zelle", "venmo", "stripe", "plaid"],
            "booking": ["book", "reserve", "schedule", "appointment", "availability"],
            "pricing": ["price", "cost", "how much", "fee", "charge", "expensive"],
            "menu": ["menu", "food", "protein", "chicken", "beef", "shrimp", "options"],
            "service": ["service", "include", "provide", "equipment", "setup", "cleanup"],
            "location": ["where", "location", "service area", "deliver", "travel"],
            "hours": ["hours", "open", "close", "when", "time", "schedule"],
            "cancellation": ["cancel", "refund", "change", "reschedule", "policy"],
        }

        for question in questions:
            question_lower = question.lower()
            matched_topics = []

            for topic, keywords in topic_keywords.items():
                if any(kw in question_lower for kw in keywords):
                    matched_topics.append(topic)

            # Add to all matching clusters
            for topic in matched_topics if matched_topics else ["general"]:
                clusters[topic].append(question)

        # Format results
        patterns = []
        for topic, questions_list in clusters.items():
            if len(questions_list) >= 2:  # At least 2 similar questions
                patterns.append(
                    {
                        "topic": topic,
                        "frequency": len(questions_list),
                        "sample_questions": questions_list[:5],
                        "percentage": 0,  # Will be calculated later
                    }
                )

        # Sort by frequency
        patterns.sort(key=lambda x: x["frequency"], reverse=True)

        # Calculate percentages
        total = sum(p["frequency"] for p in patterns)
        for pattern in patterns:
            pattern["percentage"] = round(pattern["frequency"] / total * 100, 1)

        return patterns

    async def generate_knowledge_base_updates(
        self, db: AsyncSession, min_confidence: float = 0.8
    ) -> list[dict[str, Any]]:
        """
        Generate knowledge base updates based on successful interactions
        """
        try:
            from api.ai.endpoints.models import Message

            # Find high-quality responses
            query = (
                select(Message)
                .where(
                    and_(
                        Message.confidence >= min_confidence,
                        Message.metadata.contains({"user_feedback": {"helpful": True}}),
                    )
                )
                .limit(100)
            )

            result = await db.execute(query)
            successful_messages = result.scalars().all()

            # Extract knowledge
            kb_updates = []
            for msg in successful_messages:
                metadata = msg.metadata or {}
                user_feedback = metadata.get("user_feedback", {})

                if user_feedback.get("rating", 0) >= 4:
                    kb_updates.append(
                        {
                            "topic": metadata.get("intent_detected", "general"),
                            "content": msg.content,
                            "confidence": msg.confidence,
                            "user_rating": user_feedback.get("rating"),
                            "source": "learned_from_interaction",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            logger.info(f"Generated {len(kb_updates)} knowledge base updates")
            return kb_updates

        except Exception as e:
            logger.exception(f"Error generating KB updates: {e}")
            return []

    async def adapt_system_prompt(
        self, db: AsyncSession, current_prompt: str
    ) -> tuple[str, dict[str, Any]]:
        """
        Adapt system prompt based on performance metrics
        """
        try:
            # Analyze recent performance
            patterns = await self.identify_common_patterns(db, days=7)

            # Get top 3 topics
            top_topics = [p["topic"] for p in patterns[:3]]

            # Enhancement suggestions
            enhancements = []

            if "payment" in top_topics:
                enhancements.append(
                    "\n**Payment Priority**: Many users ask about payments. Always mention "
                    "all 4 options (Stripe, Plaid, Zelle, Venmo) clearly."
                )

            if "booking" in top_topics:
                enhancements.append(
                    "\n**Booking Emphasis**: Proactively offer booking steps and availability checking."
                )

            if "pricing" in top_topics:
                enhancements.append(
                    "\n**Pricing Clarity**: Lead with $75/person pricing to avoid follow-up questions."
                )

            # Combine enhancements with current prompt
            if enhancements:
                enhanced_prompt = (
                    current_prompt + "\n\n**Dynamic Optimizations:**" + "".join(enhancements)
                )

                changes = {
                    "enhancements_added": len(enhancements),
                    "top_topics": top_topics,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                self.learning_stats["auto_improvements"] += 1
                logger.info(f"Adapted system prompt with {len(enhancements)} enhancements")

                return enhanced_prompt, changes

            return current_prompt, {"message": "No adaptations needed"}

        except Exception as e:
            logger.exception(f"Error adapting system prompt: {e}")
            return current_prompt, {"error": str(e)}

    async def get_learning_metrics(self, db: AsyncSession) -> dict[str, Any]:
        """Get comprehensive learning metrics"""
        try:
            from api.ai.endpoints.models import Message

            # Calculate various metrics
            total_messages = await db.execute(select(func.count(Message.id)))
            total_count = total_messages.scalar()

            # Average confidence
            avg_confidence_query = select(func.avg(Message.confidence)).where(
                Message.confidence.isnot(None)
            )
            avg_conf_result = await db.execute(avg_confidence_query)
            avg_confidence = avg_conf_result.scalar() or 0

            # Feedback metrics
            feedback_query = select(func.count(Message.id)).where(
                Message.metadata.contains({"user_feedback": {}})
            )
            feedback_result = await db.execute(feedback_query)
            feedback_count = feedback_result.scalar()

            return {
                **self.learning_stats,
                "database_metrics": {
                    "total_messages": total_count,
                    "average_confidence": round(float(avg_confidence), 3),
                    "messages_with_feedback": feedback_count,
                    "feedback_rate": (
                        round(feedback_count / total_count * 100, 1) if total_count > 0 else 0
                    ),
                },
                "learning_health": self._calculate_learning_health(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.exception(f"Error getting learning metrics: {e}")
            return {"error": str(e)}

    def _calculate_learning_health(self) -> str:
        """Calculate overall learning system health"""
        feedback_rate = (
            self.learning_stats["feedback_received"] / self.learning_stats["total_interactions"]
            if self.learning_stats["total_interactions"] > 0
            else 0
        )

        if feedback_rate >= 0.3 and self.learning_stats["auto_improvements"] > 5:
            return "excellent"
        elif feedback_rate >= 0.15 and self.learning_stats["auto_improvements"] > 2:
            return "good"
        elif feedback_rate >= 0.05:
            return "fair"
        else:
            return "needs_improvement"


# Global instance
self_learning_ai = SelfLearningAI()


def get_self_learning_ai() -> SelfLearningAI:
    """Get global self-learning AI instance"""
    return self_learning_ai
