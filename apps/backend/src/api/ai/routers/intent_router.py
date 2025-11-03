"""
Intent Router - Intelligent conversation routing to specialized agents

This module classifies user intent using embeddings and routes conversations
to the appropriate agent (Lead Nurturing, Customer Care, Operations, Knowledge).

Architecture:
- Embedding-based semantic classification
- Multi-turn conversation context awareness
- Confidence scoring with fallback strategies
- Intent transition handling (switching between agents mid-conversation)

Author: AI Team
Date: 2025-10-31
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from datetime import datetime

from ..orchestrator.providers import get_provider
from ..agents import (
    LeadNurturingAgent,
    CustomerCareAgent,
    OperationsAgent,
    KnowledgeAgent
)

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Available agent types for routing"""
    LEAD_NURTURING = "lead_nurturing"
    CUSTOMER_CARE = "customer_care"
    OPERATIONS = "operations"
    KNOWLEDGE = "knowledge"


class IntentRouter:
    """
    Routes user messages to the appropriate specialized agent.
    
    Uses semantic embeddings to classify intent and maintain conversation
    context across multiple turns.
    """
    
    # Intent training examples for embedding-based classification
    INTENT_EXAMPLES = {
        AgentType.LEAD_NURTURING: [
            # Sales inquiries
            "How much does it cost?",
            "I'm interested in booking",
            "What packages do you offer?",
            "Can you give me a quote?",
            "Tell me about your pricing",
            "I want to hire a hibachi chef",
            "What's included in the package?",
            "Do you have any promotions?",
            "I'm planning an event",
            "What are your rates for 50 people?",
            "Can you recommend a package?",
            "I'm looking for catering",
            "How much for a birthday party?",
            "Tell me about your services",
            "What's the difference between packages?",
            # Upselling triggers
            "What extras can I add?",
            "Can I upgrade?",
            "What else do you offer?",
            "Tell me about add-ons",
            "What are the premium options?",
        ],
        
        AgentType.CUSTOMER_CARE: [
            # Support issues
            "I have a problem with my order",
            "The chef was late",
            "I'm not satisfied",
            "I want a refund",
            "Can I speak to a manager?",
            "This is unacceptable",
            "I need help with my booking",
            "Something went wrong",
            "I'm disappointed",
            "The service was poor",
            # Order inquiries
            "Where is my order?",
            "What's the status of my booking?",
            "When will the chef arrive?",
            "Can I track my order?",
            "I haven't received confirmation",
            # Complaints
            "I want to file a complaint",
            "This is ridiculous",
            "I'm very upset",
            "I demand compensation",
            "This ruined my event",
        ],
        
        AgentType.OPERATIONS: [
            # Booking management
            "I need to reschedule",
            "Can I change my booking date?",
            "I need to update my order",
            "Can I add more guests?",
            "I need to modify my reservation",
            # Availability
            "Are you available on Saturday?",
            "Can you check availability?",
            "Do you have any openings?",
            "When is your next available date?",
            "Can you work on December 15th?",
            # Logistics
            "Do you serve my area?",
            "How many chefs do I need?",
            "What equipment do you bring?",
            "How long does setup take?",
            "What are your service hours?",
            # Chef assignments
            "Can I request a specific chef?",
            "Do you have a vegetarian specialist?",
            "I need a bilingual chef",
            "Can I meet the chef beforehand?",
        ],
        
        AgentType.KNOWLEDGE: [
            # Policy questions
            "What's your cancellation policy?",
            "What's your refund policy?",
            "Do you require a deposit?",
            "What are your payment terms?",
            "What happens if it rains?",
            # Detailed information
            "How does hibachi catering work?",
            "What's the process for booking?",
            "Tell me about your company",
            "What's your experience?",
            "Are you licensed and insured?",
            # Menu questions
            "What's on the menu?",
            "Do you accommodate dietary restrictions?",
            "Can I customize the menu?",
            "What ingredients do you use?",
            "Do you offer vegetarian options?",
            # Technical questions
            "What equipment do you need?",
            "How much space is required?",
            "Do you need electricity?",
            "What about indoor vs outdoor?",
            "Do you provide tables and chairs?",
            # FAQ
            "How far in advance should I book?",
            "What forms of payment do you accept?",
            "Do you travel to other states?",
            "Can I get references?",
            "What if I have allergies?",
        ],
    }
    
    def __init__(self):
        """Initialize the intent router"""
        self.provider = get_provider()
        
        # Initialize agents (lazy loading)
        self._agents: Dict[AgentType, Any] = {}
        
        # Cache for intent embeddings (computed once at startup)
        self._intent_embeddings: Optional[Dict[AgentType, np.ndarray]] = None
        
        # Conversation state tracking
        self._conversation_states: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Intent router initialized")
    
    def _get_agent(self, agent_type: AgentType):
        """Get or create agent instance (lazy loading)"""
        if agent_type not in self._agents:
            if agent_type == AgentType.LEAD_NURTURING:
                self._agents[agent_type] = LeadNurturingAgent()
            elif agent_type == AgentType.CUSTOMER_CARE:
                self._agents[agent_type] = CustomerCareAgent()
            elif agent_type == AgentType.OPERATIONS:
                self._agents[agent_type] = OperationsAgent()
            elif agent_type == AgentType.KNOWLEDGE:
                self._agents[agent_type] = KnowledgeAgent()
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            logger.info(f"Created agent: {agent_type.value}")
        
        return self._agents[agent_type]
    
    async def _compute_intent_embeddings(self):
        """
        Compute embeddings for all intent examples.
        
        This is done once at startup and cached for performance.
        Uses the provider's embedding model (OpenAI text-embedding-3-small).
        """
        if self._intent_embeddings is not None:
            return  # Already computed
        
        logger.info("Computing intent embeddings...")
        
        self._intent_embeddings = {}
        
        for agent_type, examples in self.INTENT_EXAMPLES.items():
            # Get embeddings for all examples
            embeddings_response = await self.provider.embed(examples)
            embeddings = embeddings_response["embeddings"]
            
            # Compute centroid (average embedding) for this intent
            centroid = np.mean(embeddings, axis=0)
            self._intent_embeddings[agent_type] = centroid
            
            logger.info(
                f"Computed {len(examples)} embeddings for {agent_type.value} "
                f"(centroid shape: {centroid.shape})"
            )
        
        logger.info("Intent embeddings computed successfully")
    
    async def classify_intent(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        current_agent: Optional[AgentType] = None
    ) -> Tuple[AgentType, float]:
        """
        Classify user intent using semantic embeddings.
        
        Args:
            message: User message to classify
            conversation_history: Previous messages in conversation
            current_agent: Current agent handling the conversation (if any)
        
        Returns:
            Tuple of (agent_type, confidence_score)
            
        Example:
            >>> agent_type, confidence = await router.classify_intent(
            ...     "How much for 50 people?"
            ... )
            >>> print(f"Route to: {agent_type.value} (confidence: {confidence:.2f})")
            Route to: lead_nurturing (confidence: 0.92)
        """
        # Ensure embeddings are computed
        await self._compute_intent_embeddings()
        
        # Get embedding for user message
        message_embedding_response = await self.provider.embed([message])
        message_embedding = message_embedding_response["embeddings"][0]
        
        # Calculate cosine similarity with each intent centroid
        similarities = {}
        for agent_type, intent_embedding in self._intent_embeddings.items():
            similarity = self._cosine_similarity(message_embedding, intent_embedding)
            similarities[agent_type] = similarity
        
        # Get best match
        best_agent = max(similarities, key=similarities.get)
        best_confidence = similarities[best_agent]
        
        # Context-aware adjustments
        if current_agent and best_confidence < 0.75:
            # If confidence is low and we're already in a conversation,
            # prefer to stay with current agent (conversation continuity)
            logger.info(
                f"Low confidence ({best_confidence:.2f}), maintaining current agent: "
                f"{current_agent.value}"
            )
            return current_agent, similarities.get(current_agent, 0.5)
        
        # Check for agent transitions (mid-conversation intent changes)
        if current_agent and current_agent != best_agent:
            # Log intent transitions for monitoring
            logger.info(
                f"Intent transition: {current_agent.value} -> {best_agent.value} "
                f"(confidence: {best_confidence:.2f})"
            )
        
        logger.info(
            f"Classified intent: {best_agent.value} (confidence: {best_confidence:.2f})"
        )
        
        return best_agent, best_confidence
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    async def route(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Route a message to the appropriate agent and get response.
        
        This is the main entry point for the intent router.
        
        Args:
            message: User message to process
            context: Conversation context (conversation_id, customer_id, channel, etc.)
            conversation_history: Previous messages in conversation
        
        Returns:
            Agent response with routing metadata
            
        Example:
            >>> response = await router.route(
            ...     message="How much for 50 people?",
            ...     context={"conversation_id": "conv_123", "channel": "webchat"},
            ...     conversation_history=[...]
            ... )
            >>> print(response["content"])
            "Great question! For 50 guests, our Standard Package..."
            >>> print(response["routing"]["agent_type"])
            "lead_nurturing"
            >>> print(response["routing"]["confidence"])
            0.92
        """
        context = context or {}
        conversation_history = conversation_history or []
        conversation_id = context.get("conversation_id", "unknown")
        
        # Get conversation state
        conv_state = self._conversation_states.get(conversation_id, {})
        current_agent = conv_state.get("current_agent")
        
        # Classify intent
        start_time = datetime.now()
        agent_type, confidence = await self.classify_intent(
            message,
            conversation_history,
            current_agent
        )
        classification_latency = (datetime.now() - start_time).total_seconds()
        
        # Update conversation state
        self._conversation_states[conversation_id] = {
            "current_agent": agent_type,
            "last_message_time": datetime.now(),
            "intent_history": conv_state.get("intent_history", []) + [
                {
                    "agent_type": agent_type.value,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        # Get agent
        agent = self._get_agent(agent_type)
        
        # Process message with agent
        agent_start_time = datetime.now()
        agent_response = await agent.process(
            message=message,
            context=context,
            conversation_history=conversation_history
        )
        agent_latency = (datetime.now() - agent_start_time).total_seconds()
        
        # Add routing metadata
        agent_response["routing"] = {
            "agent_type": agent_type.value,
            "confidence": round(confidence, 3),
            "classification_latency_ms": round(classification_latency * 1000, 2),
            "agent_latency_ms": round(agent_latency * 1000, 2),
            "total_latency_ms": round((classification_latency + agent_latency) * 1000, 2),
            "intent_transition": current_agent.value if current_agent and current_agent != agent_type else None
        }
        
        logger.info(
            f"Routed to {agent_type.value} | "
            f"Confidence: {confidence:.2f} | "
            f"Latency: {agent_response['routing']['total_latency_ms']:.0f}ms"
        )
        
        return agent_response
    
    async def get_conversation_state(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation state for a given conversation ID.
        
        Useful for debugging and analytics.
        
        Args:
            conversation_id: Conversation ID to look up
        
        Returns:
            Conversation state or None if not found
        """
        return self._conversation_states.get(conversation_id)
    
    def clear_conversation_state(self, conversation_id: str):
        """
        Clear conversation state for a given conversation ID.
        
        Useful when a conversation ends or for testing.
        """
        if conversation_id in self._conversation_states:
            del self._conversation_states[conversation_id]
            logger.info(f"Cleared conversation state: {conversation_id}")
    
    async def route_with_fallback(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        confidence_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Route with fallback to Knowledge Agent if confidence is low.
        
        When the intent classifier is uncertain, the Knowledge Agent
        can provide general information while asking clarifying questions.
        
        Args:
            message: User message to process
            context: Conversation context
            conversation_history: Previous messages
            confidence_threshold: Minimum confidence to route to specialized agent
        
        Returns:
            Agent response with routing metadata including fallback info
        """
        context = context or {}
        conversation_history = conversation_history or []
        
        # Get conversation state
        conversation_id = context.get("conversation_id", "unknown")
        conv_state = self._conversation_states.get(conversation_id, {})
        current_agent = conv_state.get("current_agent")
        
        # Classify intent
        agent_type, confidence = await self.classify_intent(
            message,
            conversation_history,
            current_agent
        )
        
        # Check if confidence is below threshold
        is_fallback = False
        original_agent = None
        
        if confidence < confidence_threshold and agent_type != AgentType.KNOWLEDGE:
            logger.warning(
                f"Low confidence ({confidence:.2f}) for {agent_type.value}, "
                f"falling back to knowledge_agent"
            )
            original_agent = agent_type
            agent_type = AgentType.KNOWLEDGE
            is_fallback = True
        
        # Update context with fallback info
        if is_fallback:
            context["fallback_mode"] = True
            context["original_intent"] = original_agent.value if original_agent else None
        
        # Get agent
        agent = self._get_agent(agent_type)
        
        # Process message
        agent_response = await agent.process(
            message=message,
            context=context,
            conversation_history=conversation_history
        )
        
        # Add fallback metadata
        if is_fallback:
            agent_response["routing"]["fallback"] = {
                "triggered": True,
                "original_agent": original_agent.value,
                "original_confidence": round(confidence, 3),
                "threshold": confidence_threshold,
                "reason": "confidence_below_threshold"
            }
        
        return agent_response
    
    async def suggest_agent(
        self,
        message: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest top K agents for a message with confidence scores.
        
        Useful for debugging, analytics, or presenting options to users.
        
        Args:
            message: User message to analyze
            top_k: Number of suggestions to return
        
        Returns:
            List of agent suggestions with confidence scores
            
        Example:
            >>> suggestions = await router.suggest_agent(
            ...     "I'm not sure what I need",
            ...     top_k=3
            ... )
            >>> for s in suggestions:
            ...     print(f"{s['agent_type']}: {s['confidence']:.2%}")
            knowledge: 65%
            lead_nurturing: 58%
            operations: 52%
        """
        # Ensure embeddings are computed
        await self._compute_intent_embeddings()
        
        # Get embedding for user message
        message_embedding_response = await self.provider.embed([message])
        message_embedding = message_embedding_response["embeddings"][0]
        
        # Calculate similarities
        suggestions = []
        for agent_type, intent_embedding in self._intent_embeddings.items():
            similarity = self._cosine_similarity(message_embedding, intent_embedding)
            suggestions.append({
                "agent_type": agent_type.value,
                "confidence": round(similarity, 3),
                "description": self._get_agent_description(agent_type)
            })
        
        # Sort by confidence and return top K
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:top_k]
    
    @staticmethod
    def _get_agent_description(agent_type: AgentType) -> str:
        """Get human-readable description of agent"""
        descriptions = {
            AgentType.LEAD_NURTURING: "Sales & pricing inquiries, package recommendations, upselling",
            AgentType.CUSTOMER_CARE: "Support issues, refunds, complaints, order status",
            AgentType.OPERATIONS: "Booking management, scheduling, availability, logistics",
            AgentType.KNOWLEDGE: "Policies, FAQs, general information, detailed questions"
        }
        return descriptions.get(agent_type, "Unknown agent")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get router statistics.
        
        Returns:
            Statistics about routing performance and usage
        """
        # Aggregate statistics from conversation states
        total_conversations = len(self._conversation_states)
        
        # Count intents
        intent_counts = {agent_type.value: 0 for agent_type in AgentType}
        intent_transitions = 0
        
        for conv_state in self._conversation_states.values():
            intent_history = conv_state.get("intent_history", [])
            
            # Count most recent intent
            if intent_history:
                latest_intent = intent_history[-1]["agent_type"]
                intent_counts[latest_intent] += 1
            
            # Count transitions
            for i in range(1, len(intent_history)):
                if intent_history[i]["agent_type"] != intent_history[i-1]["agent_type"]:
                    intent_transitions += 1
        
        return {
            "total_conversations": total_conversations,
            "intent_distribution": intent_counts,
            "intent_transitions": intent_transitions,
            "agents_loaded": list(self._agents.keys()),
            "embeddings_computed": self._intent_embeddings is not None
        }


# Singleton instance
_router_instance: Optional[IntentRouter] = None


def get_intent_router() -> IntentRouter:
    """
    Get singleton intent router instance.
    
    Returns:
        Shared IntentRouter instance
        
    Example:
        >>> from api.ai.routers.intent_router import get_intent_router
        >>> router = get_intent_router()
        >>> response = await router.route("How much does it cost?")
    """
    global _router_instance
    
    if _router_instance is None:
        _router_instance = IntentRouter()
        logger.info("Created singleton intent router instance")
    
    return _router_instance
