"""Enhanced AI lead management and social media integration."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import json
from dataclasses import dataclass

from api.app.services.openai_service import OpenAIService
from api.app.models.lead_newsletter import Lead, LeadStatus, LeadQuality, LeadSource, SocialThread
from api.app.services.ringcentral_sms import send_sms_notification

logger = logging.getLogger(__name__)


@dataclass
class SocialMediaPost:
    """Represents a social media post to analyze."""
    platform: str
    author: str
    content: str
    timestamp: datetime
    engagement: Dict[str, int]
    post_id: str


@dataclass
class LeadScoringContext:
    """Context for AI lead scoring."""
    source_quality: float
    engagement_history: List[Dict]
    timing_factors: Dict[str, Any]
    content_analysis: Dict[str, Any]
    response_speed: Optional[float] = None


class AILeadManager:
    """
    AI-powered lead management with intelligent scoring,
    quality assessment, and automated responses.
    """

    def __init__(self, openai_service: OpenAIService):
        self.openai = openai_service
        
        # Lead scoring weights
        self.scoring_weights = {
            "source_quality": 0.3,
            "engagement_speed": 0.25,
            "content_relevance": 0.2,
            "timing": 0.15,
            "contact_completeness": 0.1
        }

    async def analyze_social_engagement(self, post: SocialMediaPost) -> Dict[str, Any]:
        """Analyze social media post for lead potential."""
        
        prompt = f"""
        Analyze this social media post for lead generation potential:

        Platform: {post.platform}
        Content: {post.content}
        Engagement: {post.engagement}
        
        Assess:
        1. Intent level (information seeking, ready to book, just browsing)
        2. Budget indicators
        3. Event timing urgency
        4. Decision maker signals
        5. Geographic relevance

        Return analysis in JSON format with scores 0-100 for each factor.
        """

        try:
            response = await self.openai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4",
                temperature=0.3
            )
            
            return json.loads(response["content"])
            
        except Exception as e:
            logger.error(f"Social engagement analysis failed: {e}")
            return {"intent_level": 50, "budget_indicators": 50, "urgency": 50}

    async def score_lead_with_ai(self, lead: Lead, conversation_data: Optional[List[Dict]] = None) -> float:
        """
        Use AI to score lead quality based on multiple factors.
        Returns score from 0-100.
        """
        
        lead_data = {
            "source": lead.source.value,
            "contact_completeness": self._calculate_contact_completeness(lead),
            "timing": lead.created_at.isoformat(),
            "context": {
                "party_size": lead.context.party_size_adults if lead.context else None,
                "event_date": lead.context.event_date_pref.isoformat() if lead.context and lead.context.event_date_pref else None,
                "zip_code": lead.context.zip_code if lead.context else None,
                "budget_range": lead.context.budget_range if lead.context else None
            },
            "conversation": conversation_data or []
        }

        prompt = f"""
        Score this catering lead from 0-100 based on likelihood to convert:

        Lead Data: {json.dumps(lead_data, default=str)}

        Consider:
        - Source quality (social media < website < referral)
        - Contact completeness (phone + email = higher score)
        - Event timing (sooner = higher score)
        - Budget indicators
        - Engagement quality in conversations
        - Party size (larger = higher score)

        Return only a numeric score from 0-100.
        """

        try:
            response = await self.openai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4",
                temperature=0.2
            )
            
            score_text = response["content"].strip()
            # Extract numeric score
            score = float(''.join(filter(str.isdigit, score_text)))
            return min(max(score, 0), 100)
            
        except Exception as e:
            logger.error(f"AI lead scoring failed: {e}")
            # Fallback to rule-based scoring
            return self._fallback_lead_scoring(lead)

    def _calculate_contact_completeness(self, lead: Lead) -> float:
        """Calculate how complete the contact information is."""
        score = 0
        if lead.email:
            score += 40
        if lead.phone:
            score += 40
        if lead.name:
            score += 20
        return score

    def _fallback_lead_scoring(self, lead: Lead) -> float:
        """Fallback rule-based scoring when AI is unavailable."""
        score = 0
        
        # Source quality
        source_scores = {
            LeadSource.WEB_QUOTE: 80,
            LeadSource.REFERRAL: 90,
            LeadSource.INSTAGRAM: 60,
            LeadSource.FACEBOOK: 60,
            LeadSource.GOOGLE: 65,
            LeadSource.YELP: 65,
            LeadSource.CHAT: 70,
            LeadSource.PHONE: 85,
            LeadSource.SMS: 65,
            LeadSource.EVENT: 75
        }
        score += source_scores.get(lead.source, 50) * 0.3
        
        # Contact completeness
        score += self._calculate_contact_completeness(lead) * 0.3
        
        # Context completeness
        if lead.context:
            if lead.context.event_date_pref:
                score += 20
            if lead.context.party_size_adults and lead.context.party_size_adults > 6:
                score += 15
            if lead.context.budget_range:
                score += 10
        
        return min(score, 100)

    async def determine_lead_quality(self, lead: Lead, ai_score: float) -> LeadQuality:
        """Determine lead quality category based on AI score."""
        if ai_score >= 80:
            return LeadQuality.HOT
        elif ai_score >= 60:
            return LeadQuality.WARM
        elif ai_score >= 40:
            return LeadQuality.COLD
        else:
            return LeadQuality.UNQUALIFIED

    async def suggest_next_actions(self, lead: Lead) -> List[str]:
        """AI-suggested next actions for lead nurturing."""
        
        lead_context = {
            "quality": lead.quality.value if lead.quality else "unknown",
            "source": lead.source.value,
            "days_since_created": (datetime.now() - lead.created_at).days,
            "has_context": bool(lead.context),
            "last_contact": lead.last_contacted_at.isoformat() if lead.last_contacted_at else None
        }

        prompt = f"""
        Suggest 3-5 specific next actions for this catering lead:

        Lead Info: {json.dumps(lead_context, default=str)}

        Consider:
        - Lead temperature and quality
        - Time since last contact
        - Source-specific approaches
        - Urgency based on event timing

        Return specific, actionable suggestions as a JSON array of strings.
        """

        try:
            response = await self.openai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-3.5-turbo",
                temperature=0.5
            )
            
            return json.loads(response["content"])
            
        except Exception as e:
            logger.error(f"Next action suggestions failed: {e}")
            return self._fallback_next_actions(lead)

    def _fallback_next_actions(self, lead: Lead) -> List[str]:
        """Fallback next actions when AI is unavailable."""
        actions = []
        
        if not lead.last_contacted_at:
            actions.append("Send initial welcome message")
        elif (datetime.now() - lead.last_contacted_at).days > 3:
            actions.append("Send follow-up message")
        
        if not lead.context or not lead.context.event_date_pref:
            actions.append("Gather event date preference")
        
        if not lead.context or not lead.context.party_size_adults:
            actions.append("Ask for party size details")
        
        if lead.quality == LeadQuality.HOT:
            actions.append("Schedule consultation call")
        elif lead.quality == LeadQuality.WARM:
            actions.append("Send menu samples and pricing")
        
        return actions[:5]


class SocialMediaAI:
    """
    AI-powered social media management for lead generation
    and customer engagement.
    """

    def __init__(self, openai_service: OpenAIService):
        self.openai = openai_service

    async def analyze_mention(self, content: str, platform: str) -> Dict[str, Any]:
        """Analyze social media mention for intent and response strategy."""
        
        prompt = f"""
        Analyze this {platform} mention for catering business:

        Content: "{content}"

        Determine:
        1. Intent type (inquiry, complaint, compliment, question)
        2. Response urgency (1-10)
        3. Suggested response tone (professional, friendly, apologetic)
        4. Lead potential (0-100)
        5. Key topics mentioned

        Return as JSON with these exact keys.
        """

        try:
            response = await self.openai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4",
                temperature=0.3
            )
            
            return json.loads(response["content"])
            
        except Exception as e:
            logger.error(f"Mention analysis failed: {e}")
            return {
                "intent_type": "inquiry",
                "urgency": 5,
                "tone": "friendly",
                "lead_potential": 50,
                "topics": []
            }

    async def generate_response(self, mention_content: str, analysis: Dict[str, Any]) -> str:
        """Generate contextual response to social media mention."""
        
        prompt = f"""
        Generate a response to this social media mention:

        Original: "{mention_content}"
        Analysis: {json.dumps(analysis)}

        Guidelines:
        - Tone: {analysis.get('tone', 'friendly')}
        - Be helpful and engaging
        - Include subtle call-to-action when appropriate
        - Keep under 280 characters for Twitter compatibility
        - Mention "My Hibachi Chef" naturally

        Response:
        """

        try:
            response = await self.openai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-3.5-turbo",
                temperature=0.7
            )
            
            return response["content"].strip().strip('"')
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "Thank you for your interest in My Hibachi Chef! We'd love to help make your event special. Please visit our website or DM us for more information!"

    async def create_promotional_content(self, campaign_type: str, target_audience: str) -> str:
        """Create promotional social media content."""
        
        prompt = f"""
        Create engaging social media content for My Hibachi Chef catering:

        Campaign: {campaign_type}
        Audience: {target_audience}

        Requirements:
        - Engaging and appetizing
        - Include relevant hashtags
        - Call-to-action
        - Professional yet approachable tone
        - Highlight unique value (live hibachi experience)

        Content:
        """

        try:
            response = await self.openai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4",
                temperature=0.8
            )
            
            return response["content"].strip()
            
        except Exception as e:
            logger.error(f"Content creation failed: {e}")
            return f"Experience the magic of hibachi at your next event! 🥢✨ #MyHibachiChef #CateringServices #{campaign_type}"


class LeadNurtureAI:
    """
    AI-powered lead nurturing with personalized messaging
    and automated follow-up sequences.
    """

    def __init__(self, openai_service: OpenAIService, lead_manager: AILeadManager):
        self.openai = openai_service
        self.lead_manager = lead_manager

        # Message templates by lead quality
        self.message_templates = {
            LeadQuality.HOT: {
                "initial": "Thanks for your interest! I'd love to discuss your event details. When would be a good time for a quick call?",
                "follow_up": "Hi! Just wanted to follow up on your catering inquiry. Are you still looking for hibachi catering for your event?",
                "reminder": "Your event date is coming up! Let's finalize your hibachi catering details."
            },
            LeadQuality.WARM: {
                "initial": "Thank you for your interest in My Hibachi Chef! I'd be happy to send you our menu and pricing information.",
                "follow_up": "Hi! Did you have a chance to review our hibachi catering options? I'm here to answer any questions!",
                "reminder": "Still planning that special event? Our hibachi chefs would love to make it memorable!"
            },
            LeadQuality.COLD: {
                "initial": "Thanks for connecting! Here's some information about our amazing hibachi catering services.",
                "follow_up": "Hope you're doing well! Just wanted to check if you have any upcoming events we could help make special.",
                "reminder": "Hi! We're here whenever you're ready to plan an unforgettable hibachi experience."
            }
        }

    async def create_nurture_sequence(self, lead: Lead) -> List[Dict[str, Any]]:
        """Create personalized nurture sequence for lead."""
        
        sequence = []
        lead_quality = lead.quality or LeadQuality.WARM
        
        # Immediate response
        sequence.append({
            "delay_hours": 0,
            "message": await self.personalize_message(
                self.message_templates[lead_quality]["initial"], lead
            ),
            "channel": "sms" if lead.phone else "email"
        })
        
        # Follow-up based on lead quality
        if lead_quality == LeadQuality.HOT:
            sequence.append({
                "delay_hours": 24,
                "message": await self.personalize_message(
                    self.message_templates[lead_quality]["follow_up"], lead
                ),
                "channel": "sms" if lead.phone else "email"
            })
        elif lead_quality == LeadQuality.WARM:
            sequence.append({
                "delay_hours": 48,
                "message": await self.personalize_message(
                    self.message_templates[lead_quality]["follow_up"], lead
                ),
                "channel": "email"
            })
        
        # Reminder if event date is soon
        if (lead.context and lead.context.event_date_pref and
            (lead.context.event_date_pref - datetime.now().date()).days <= 30):
            sequence.append({
                "delay_hours": 168,  # 1 week
                "message": await self.personalize_message(
                    self.message_templates[lead_quality]["reminder"], lead
                ),
                "channel": "sms" if lead.phone else "email"
            })
        
        return sequence

    async def personalize_message(self, template: str, lead: Lead) -> str:
        """Personalize message template for specific lead."""
        
        lead_data = {
            "source": lead.source.value,
            "party_size": lead.context.party_size_adults if lead.context else None,
            "event_date": lead.context.event_date_pref.isoformat() if lead.context and lead.context.event_date_pref else None,
            "location": lead.context.zip_code if lead.context else None
        }

        prompt = f"""
        Personalize this message template using lead information:

        Template: {template}
        Lead Data: {json.dumps(lead_data, default=str)}

        Rules:
        - Keep the core message intent
        - Add personal touches based on lead data
        - Maintain professional yet friendly tone
        - Include specific details when available

        Personalized message:
        """

        try:
            response = await self.openai.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-3.5-turbo",
                temperature=0.6
            )

            return response["content"].strip()

        except Exception as e:
            logger.error(f"Message personalization failed: {e}")
            return template


# Service instances
async def get_ai_lead_manager() -> AILeadManager:
    """Get AI lead manager instance."""
    from .openai_service import get_openai_service
    openai_service = get_openai_service()
    return AILeadManager(openai_service)


async def get_social_media_ai() -> SocialMediaAI:
    """Get social media AI instance."""
    from .openai_service import get_openai_service
    openai_service = get_openai_service()
    return SocialMediaAI(openai_service)


async def get_lead_nurture_ai() -> LeadNurtureAI:
    """Get lead nurture AI instance."""
    from .openai_service import get_openai_service
    openai_service = get_openai_service()
    lead_manager = await get_ai_lead_manager()
    return LeadNurtureAI(openai_service, lead_manager)