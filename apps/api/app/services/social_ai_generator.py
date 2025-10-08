"""Context-aware AI response generator for social media."""

import logging
from typing import Any, Optional
from uuid import UUID

import openai
from pydantic import BaseModel

from app.config import settings
from app.cqrs.base import CommandBus, QueryBus
from app.models.social import SocialPlatform
from app.services.social_ai_tools import SocialMediaToolKit

logger = logging.getLogger(__name__)


class SocialResponseContext(BaseModel):
    """Context for generating social media responses."""

    class Config:
        arbitrary_types_allowed = True

    thread_id: UUID
    platform: SocialPlatform
    customer_handle: str
    customer_name: Optional[str] = None
    conversation_history: list[dict[str, Any]]
    customer_profile: Optional[dict[str, Any]] = None
    business_context: dict[str, Any] = {}
    response_tone: str = "friendly"
    urgency_level: int = 3  # 1-5 scale
    requires_approval: bool = True


class ResponseSafetyValidator:
    """Validator for AI-generated social media responses."""

    def __init__(self):
        self.prohibited_topics = [
            "pricing without context",
            "medical claims",
            "guarantees about outcomes",
            "personal information requests",
            "off-topic discussions"
        ]

        self.required_disclaimers = {
            "pricing": "Prices may vary based on location, group size, and specific requirements.",
            "booking": "Final booking details subject to availability and confirmation.",
            "dietary": "Please inform us of any allergies or dietary restrictions."
        }

    async def validate_response(self, response: str, context: SocialResponseContext) -> tuple[bool, float, list[str]]:
        """Validate AI response for safety and compliance."""
        issues = []
        safety_score = 1.0

        # Check response length
        if len(response) > 2000:
            issues.append("Response too long for social media")
            safety_score -= 0.2

        # Check for prohibited content
        response_lower = response.lower()
        for topic in self.prohibited_topics:
            if any(word in response_lower for word in topic.split()):
                issues.append(f"Contains prohibited topic: {topic}")
                safety_score -= 0.3

        # Check for required disclaimers
        if "price" in response_lower or "cost" in response_lower or "$" in response:
            if not any(disclaimer in response for disclaimer in self.required_disclaimers.values()):
                issues.append("Missing required pricing disclaimer")
                safety_score -= 0.1

        # Check tone appropriateness
        if context.urgency_level <= 2:  # High urgency
            if not any(urgent_word in response_lower for urgent_word in ["sorry", "apologize", "understand", "immediate"]):
                issues.append("Response tone may not match urgency level")
                safety_score -= 0.1

        # Profanity check (simplified)
        profanity_words = ["damn", "hell", "stupid", "crap", "suck"]
        if any(word in response_lower for word in profanity_words):
            issues.append("Contains inappropriate language")
            safety_score -= 0.4

        is_safe = safety_score >= 0.7 and len(issues) == 0

        return is_safe, max(safety_score, 0.0), issues


class SocialAIResponseGenerator:
    """AI response generator for social media interactions."""

    def __init__(self, command_bus: CommandBus, query_bus: QueryBus):
        self.command_bus = command_bus
        self.query_bus = query_bus
        self.toolkit = SocialMediaToolKit(command_bus, query_bus)
        self.safety_validator = ResponseSafetyValidator()
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

        # Response templates by scenario
        self.response_templates = {
            "pricing_inquiry": {
                "template": "Thanks for your interest! Our hibachi chef services start at ${base_price} for groups of {min_people}. The final price depends on your group size, location, and specific menu preferences. Would you like me to get you a personalized quote?",
                "requires_approval": False,
                "tone": "helpful"
            },
            "booking_request": {
                "template": "I'd love to help you book a hibachi chef experience! To give you the best service, I'll need a few details: How many guests? What date are you thinking? And what's your location? Once I have these details, I can check availability and pricing.",
                "requires_approval": False,
                "tone": "enthusiastic"
            },
            "complaint_response": {
                "template": "I'm really sorry to hear about your experience. This definitely doesn't meet our standards, and I want to make it right. Let me connect you with our manager who can address this personally. Can you DM me your contact info?",
                "requires_approval": True,
                "tone": "apologetic"
            },
            "general_inquiry": {
                "template": "Thanks for reaching out! I'd be happy to help answer your questions about our hibachi chef services. What would you like to know?",
                "requires_approval": False,
                "tone": "friendly"
            }
        }

    async def generate_response(self, context: SocialResponseContext) -> dict[str, Any]:
        """Generate AI response for social media interaction."""
        try:
            # Analyze conversation to determine intent and urgency
            conversation_analysis = await self._analyze_conversation(context)

            # Determine response scenario
            scenario = conversation_analysis.get("scenario", "general_inquiry")

            # Generate response using GPT
            ai_response = await self._generate_ai_response(context, conversation_analysis, scenario)

            # Validate response safety
            is_safe, safety_score, safety_issues = await self.safety_validator.validate_response(ai_response, context)

            # Determine if approval is required
            requires_approval = (
                safety_score < 0.9 or
                len(safety_issues) > 0 or
                context.urgency_level <= 2 or
                scenario == "complaint_response"
            )

            # Prepare response data
            response_data = {
                "response": ai_response,
                "scenario": scenario,
                "safety_score": safety_score,
                "safety_issues": safety_issues,
                "requires_approval": requires_approval,
                "confidence": conversation_analysis.get("confidence", 0.8),
                "suggested_actions": self._get_suggested_actions(scenario, conversation_analysis),
                "context_used": {
                    "conversation_length": len(context.conversation_history),
                    "customer_profile_available": context.customer_profile is not None,
                    "urgency_level": context.urgency_level,
                    "platform": context.platform
                }
            }

            logger.info(f"Generated AI response for thread {context.thread_id}: scenario={scenario}, safety_score={safety_score:.2f}")

            return response_data

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                "response": "Thanks for reaching out! Let me connect you with someone who can help you right away.",
                "scenario": "fallback",
                "safety_score": 1.0,
                "safety_issues": [],
                "requires_approval": True,
                "confidence": 0.0,
                "error": str(e)
            }

    async def _analyze_conversation(self, context: SocialResponseContext) -> dict[str, Any]:
        """Analyze conversation to determine intent and context."""
        try:
            # Prepare conversation history for analysis
            conversation_text = self._format_conversation_for_analysis(context.conversation_history)

            analysis_prompt = f"""
            Analyze this social media conversation for a hibachi chef service business:

            Platform: {context.platform}
            Customer: {context.customer_handle}

            Conversation:
            {conversation_text}

            Determine:
            1. Primary customer intent (pricing_inquiry, booking_request, complaint, general_inquiry, compliment)
            2. Urgency level (1-5, where 1 is critical/angry, 5 is casual)
            3. Key topics mentioned
            4. Sentiment (positive, neutral, negative)
            5. Whether customer seems ready to book
            6. Any specific requirements mentioned (location, date, group size, dietary needs)

            Respond in JSON format only.
            """

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing customer service conversations. Always respond with valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            analysis_text = response.choices[0].message.content.strip()

            # Parse JSON response
            import json
            analysis = json.loads(analysis_text)

            # Map intent to scenario
            intent = analysis.get("primary_intent", "general_inquiry")
            scenario_mapping = {
                "pricing_inquiry": "pricing_inquiry",
                "booking_request": "booking_request",
                "complaint": "complaint_response",
                "general_inquiry": "general_inquiry",
                "compliment": "general_inquiry"
            }

            analysis["scenario"] = scenario_mapping.get(intent, "general_inquiry")
            analysis["confidence"] = 0.8  # Base confidence

            # Adjust urgency based on sentiment
            if analysis.get("sentiment") == "negative":
                analysis["urgency_level"] = min(analysis.get("urgency_level", 3), 2)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return {
                "scenario": "general_inquiry",
                "primary_intent": "general_inquiry",
                "urgency_level": 3,
                "sentiment": "neutral",
                "confidence": 0.5
            }

    async def _generate_ai_response(self, context: SocialResponseContext, analysis: dict[str, Any], scenario: str) -> str:
        """Generate AI response using GPT."""
        try:
            # Get response template
            template_info = self.response_templates.get(scenario, self.response_templates["general_inquiry"])

            # Build context for AI
            conversation_text = self._format_conversation_for_analysis(context.conversation_history)

            # Customer profile context
            customer_context = ""
            if context.customer_profile:
                customer_context = f"Customer info: {context.customer_name or context.customer_handle}"
                if context.customer_profile.get("previous_bookings"):
                    customer_context += " (returning customer)"

            # Business context
            business_info = """
            Business: My Hibachi Chef - Premium hibachi chef services in Sacramento area
            Services: Private hibachi chef experiences for parties, events, and celebrations
            Key points:
            - Professional hibachi chefs who come to your location
            - Full hibachi setup included (grill, utensils, ingredients)
            - Customizable menus (steak, chicken, shrimp, vegetables, fried rice)
            - Serves groups of 8-50+ people
            - Prices vary by location, group size, and menu selection
            - Book through our website or by calling
            """

            system_prompt = f"""You are a friendly, professional customer service representative for My Hibachi Chef.

            {business_info}

            Guidelines:
            - Be enthusiastic but not pushy
            - Keep responses concise (under 200 words for social media)
            - Always be helpful and solution-oriented
            - If customer seems upset, acknowledge and apologize first
            - For pricing questions, give helpful ranges but recommend personalized quotes
            - For bookings, ask for key details: group size, date, location
            - Use emojis sparingly and appropriately for the platform
            - Match the customer's energy level and tone

            Platform: {context.platform}
            Tone: {template_info['tone']}
            Scenario: {scenario}
            """

            user_prompt = f"""
            {customer_context}

            Recent conversation:
            {conversation_text}

            Customer analysis:
            - Intent: {analysis.get('primary_intent')}
            - Sentiment: {analysis.get('sentiment')}
            - Topics: {analysis.get('key_topics', [])}
            - Urgency: {analysis.get('urgency_level')}/5

            Generate a helpful, professional response that addresses the customer's needs. Be specific and actionable.
            """

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            generated_response = response.choices[0].message.content.strip()

            # Add platform-appropriate formatting
            if context.platform in ["instagram", "facebook"]:
                # Remove excessive line breaks for social media
                generated_response = " ".join(generated_response.split())

            return generated_response

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            # Fallback to template
            return template_info["template"]

    def _format_conversation_for_analysis(self, conversation: list[dict[str, Any]]) -> str:
        """Format conversation history for AI analysis."""
        formatted = []

        for msg in conversation[-10:]:  # Last 10 messages for context
            sender = "Customer" if msg.get("direction") == "inbound" else "Business"
            timestamp = msg.get("created_at", "")
            body = msg.get("body", "")

            formatted.append(f"{sender} ({timestamp}): {body}")

        return "\n".join(formatted)

    def _get_suggested_actions(self, scenario: str, analysis: dict[str, Any]) -> list[str]:
        """Get suggested follow-up actions based on scenario."""
        actions = []

        if scenario == "pricing_inquiry":
            actions.extend([
                "Gather group size and location details",
                "Send personalized quote within 2 hours",
                "Follow up in 24 hours if no response"
            ])

        elif scenario == "booking_request":
            actions.extend([
                "Check calendar availability",
                "Send booking link if dates available",
                "Create lead in CRM system"
            ])

        elif scenario == "complaint_response":
            actions.extend([
                "Escalate to manager immediately",
                "Schedule follow-up call within 4 hours",
                "Document complaint details"
            ])

        # Add urgency-based actions
        urgency = analysis.get("urgency_level", 3)
        if urgency <= 2:
            actions.insert(0, "PRIORITY: Respond within 30 minutes")
        elif urgency <= 3:
            actions.insert(0, "Respond within 2 hours")

        return actions

    async def auto_respond_with_approval(self, context: SocialResponseContext) -> dict[str, Any]:
        """Generate response and queue for approval if needed."""
        try:
            # Generate AI response
            response_data = await self.generate_response(context)

            if response_data["requires_approval"]:
                # Queue for human approval
                logger.info(f"Response queued for approval: thread {context.thread_id}")
                return {
                    "status": "pending_approval",
                    "message": "Response generated and queued for human approval",
                    "response_preview": response_data["response"][:100] + "...",
                    "safety_score": response_data["safety_score"]
                }
            else:
                # Send automatically using toolkit
                send_result = await self.toolkit.execute_tool(
                    "send_social_reply",
                    thread_id=str(context.thread_id),
                    message=response_data["response"],
                    reply_type="dm",
                    skip_approval=True,
                    safety_context={
                        "profanity_checked": True,
                        "policy_compliant": True,
                        "confidence_score": response_data["safety_score"]
                    }
                )

                return {
                    "status": "sent_automatically",
                    "message": "Response sent automatically",
                    "send_result": send_result.model_dump(),
                    "response_text": response_data["response"]
                }

        except Exception as e:
            logger.error(f"Error in auto-respond: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate/send response: {str(e)}"
            }
