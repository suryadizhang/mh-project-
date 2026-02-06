"""
AI-Powered Marketing Campaign Automation

Features:
- Automatic campaign scheduling based on holidays/seasons
- AI-generated campaign content using OpenAI GPT-4
- Multi-channel support (email, SMS, social media, paid ads)
- Budget allocation optimization
- Performance tracking and A/B testing
- Customer segment targeting

Usage:
    automation = AIMarketingAutomation()

    # Generate year-long campaign calendar
    campaigns = await automation.generate_annual_campaigns()

    # Get AI content for specific campaign
    content = await automation.generate_campaign_content(
        campaign_type="holiday_promotion",
        holiday_key="thanksgiving"
    )
"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Optional
from enum import Enum
import logging

import openai

from services.holiday_service import get_holiday_service, HolidayCategory, Holiday
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize OpenAI
openai.api_key = settings.OPENAI_API_KEY


class CampaignType(str, Enum):
    """Types of marketing campaigns."""

    HOLIDAY_PROMOTION = "holiday_promotion"
    SEASON_LAUNCH = "season_launch"
    FLASH_SALE = "flash_sale"
    BRAND_AWARENESS = "brand_awareness"
    RETARGETING = "retargeting"
    REFERRAL = "referral"


class MarketingChannel(str, Enum):
    """Marketing channels."""

    EMAIL = "email"
    SMS = "sms"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    GOOGLE_ADS = "google_ads"
    TIKTOK = "tiktok"


class BudgetTier(str, Enum):
    """Campaign budget tiers."""

    LOW = "low"  # $500-$1,000
    MEDIUM = "medium"  # $1,000-$3,000
    HIGH = "high"  # $3,000-$5,000
    PREMIUM = "premium"  # $5,000+


class AIMarketingAutomation:
    """
    AI-powered marketing campaign automation with holiday integration.

    Automatically:
    - Schedules campaigns based on holidays/seasons
    - Generates content for each channel using AI
    - Optimizes budget allocation
    - Tracks performance and ROI
    """

    def __init__(self):
        self.holiday_service = get_holiday_service()

    async def generate_annual_campaigns(
        self, start_date: Optional[date] = None, days: int = 365
    ) -> List[Dict]:
        """
        Generate complete marketing campaign calendar for the year.

        Args:
            start_date: Start date (defaults to today)
            days: How many days ahead to plan

        Returns:
            List of campaign configs with AI-generated content

        Example Output:
            [
                {
                    "name": "Thanksgiving Family Feast Campaign",
                    "type": "holiday_promotion",
                    "start_date": "2025-11-06",
                    "end_date": "2025-11-30",
                    "budget_tier": "high",
                    "estimated_budget": "$4,500",
                    "channels": ["email", "sms", "facebook", "google_ads"],
                    "target_audience": "families",
                    "ai_content": {...},
                },
                ...
            ]
        """
        if start_date is None:
            start_date = date.today()

        campaigns = []

        # Get all holidays in the period
        upcoming_holidays = self.holiday_service.get_upcoming_holidays(
            days=days, from_date=start_date
        )

        logger.info(f"Generating campaigns for {len(upcoming_holidays)} holidays")

        for holiday_key, holiday_obj, holiday_date in upcoming_holidays:
            # Determine campaign parameters based on holiday type
            campaign_config = self._get_campaign_config(holiday_obj, holiday_date)

            # Get holiday context for AI generation
            context = self.holiday_service.get_holiday_message_context(holiday_key)

            # Generate AI content for all channels
            ai_content = await self.generate_campaign_content(
                campaign_type=CampaignType.HOLIDAY_PROMOTION,
                holiday_key=holiday_key,
                context=context,
                channels=campaign_config["channels"],
            )

            campaign = {
                "id": f"campaign_{holiday_key}_{holiday_date.year}",
                "name": f"{holiday_obj.name} Campaign {holiday_date.year}",
                "type": CampaignType.HOLIDAY_PROMOTION,
                "holiday_key": holiday_key,
                "holiday_name": holiday_obj.name,
                "holiday_date": holiday_date,
                "start_date": campaign_config["start_date"],
                "end_date": campaign_config["end_date"],
                "budget_tier": campaign_config["budget_tier"],
                "estimated_budget": campaign_config["estimated_budget"],
                "channels": campaign_config["channels"],
                "target_audience": campaign_config["target_audience"],
                "ai_content": ai_content,
                "kpis": campaign_config["kpis"],
                "created_at": datetime.now(timezone.utc),
            }

            campaigns.append(campaign)
            logger.info(f"✅ Generated campaign: {campaign['name']}")

        # Sort by start date
        campaigns.sort(key=lambda x: x["start_date"])

        return campaigns

    def _get_campaign_config(self, holiday: Holiday, holiday_date: date) -> Dict:
        """
        Determine campaign configuration based on holiday type.

        Different holidays get different:
        - Budget allocation
        - Channel mix
        - Campaign duration
        - Target audience
        """

        # Event seasons get premium treatment (highest ROI)
        if holiday.category == HolidayCategory.EVENT_SEASON:
            return {
                "start_date": holiday_date - timedelta(days=60),  # 8 weeks before
                "end_date": holiday_date + timedelta(days=30),
                "budget_tier": BudgetTier.PREMIUM,
                "estimated_budget": "$5,000-$8,000",
                "channels": [
                    MarketingChannel.EMAIL,
                    MarketingChannel.SMS,
                    MarketingChannel.FACEBOOK,
                    MarketingChannel.INSTAGRAM,
                    MarketingChannel.GOOGLE_ADS,
                ],
                "target_audience": "event_planners, families",
                "kpis": {
                    "target_bookings": 20,
                    "target_revenue": "$15,000",
                    "target_roas": "3x",  # Return on ad spend
                },
            }

        # Federal holidays (family-focused, medium budget)
        elif holiday.category == HolidayCategory.FEDERAL:
            return {
                "start_date": holiday_date - timedelta(days=21),  # 3 weeks
                "end_date": holiday_date + timedelta(days=3),
                "budget_tier": BudgetTier.HIGH,
                "estimated_budget": "$3,000-$5,000",
                "channels": [
                    MarketingChannel.EMAIL,
                    MarketingChannel.SMS,
                    MarketingChannel.FACEBOOK,
                    MarketingChannel.GOOGLE_ADS,
                ],
                "target_audience": "families, past_customers",
                "kpis": {
                    "target_bookings": 15,
                    "target_revenue": "$10,000",
                    "target_roas": "2.5x",
                },
            }

        # Commercial holidays (broader reach, lower budget)
        elif holiday.category == HolidayCategory.COMMERCIAL:
            return {
                "start_date": holiday_date - timedelta(days=14),  # 2 weeks
                "end_date": holiday_date + timedelta(days=2),
                "budget_tier": BudgetTier.MEDIUM,
                "estimated_budget": "$1,500-$3,000",
                "channels": [
                    MarketingChannel.EMAIL,
                    MarketingChannel.FACEBOOK,
                    MarketingChannel.INSTAGRAM,
                ],
                "target_audience": "all_customers",
                "kpis": {
                    "target_bookings": 8,
                    "target_revenue": "$5,000",
                    "target_roas": "2x",
                },
            }

        # Cultural events (awareness building, lower budget)
        else:
            return {
                "start_date": holiday_date - timedelta(days=7),
                "end_date": holiday_date + timedelta(days=1),
                "budget_tier": BudgetTier.LOW,
                "estimated_budget": "$500-$1,500",
                "channels": [
                    MarketingChannel.EMAIL,
                    MarketingChannel.FACEBOOK,
                ],
                "target_audience": "all_customers",
                "kpis": {
                    "target_bookings": 5,
                    "target_revenue": "$3,000",
                    "target_roas": "2x",
                },
            }

    async def generate_campaign_content(
        self,
        campaign_type: CampaignType,
        holiday_key: str,
        context: Optional[Dict] = None,
        channels: Optional[List[MarketingChannel]] = None,
    ) -> Dict[str, Dict]:
        """
        Generate AI content for all specified channels.

        Returns:
            Dict with content for each channel:
            {
                "email": {"subject": "...", "body": "..."},
                "sms": {"message": "..."},
                "facebook": {"post": "...", "image_prompt": "..."},
                "instagram": {"caption": "...", "hashtags": [...], "image_prompt": "..."},
                "google_ads": {"headline": "...", "description": "..."},
            }
        """
        if context is None:
            context = self.holiday_service.get_holiday_message_context(holiday_key)

        if channels is None:
            channels = [MarketingChannel.EMAIL, MarketingChannel.SMS]

        content = {}

        # Generate content for each channel
        for channel in channels:
            try:
                if channel == MarketingChannel.EMAIL:
                    content["email"] = await self._generate_email_content(context)

                elif channel == MarketingChannel.SMS:
                    content["sms"] = await self._generate_sms_content(context)

                elif channel == MarketingChannel.FACEBOOK:
                    content["facebook"] = await self._generate_facebook_content(context)

                elif channel == MarketingChannel.INSTAGRAM:
                    content["instagram"] = await self._generate_instagram_content(context)

                elif channel == MarketingChannel.GOOGLE_ADS:
                    content["google_ads"] = await self._generate_google_ads_content(context)

                elif channel == MarketingChannel.TIKTOK:
                    content["tiktok"] = await self._generate_tiktok_content(context)

                logger.info(f"✅ Generated {channel.value} content for {context['name']}")

            except Exception as e:
                logger.error(f"Failed to generate {channel.value} content: {e}")
                content[channel.value] = {"error": str(e)}

        return content

    async def _generate_email_content(self, context: Dict) -> Dict:
        """Generate email campaign content using AI."""
        prompt = f"""
Write a promotional email for hibachi catering company.

Holiday: {context['name']}
Days Until: {context['days_until']}
Events: {', '.join(context['typical_events'])}

Requirements:
- Subject line (50 chars max, include emoji)
- Email body (200-300 words)
- Clear CTA
- Create urgency
- Professional but warm tone

Format:
SUBJECT: [subject line]
BODY: [email content]
"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an email marketing expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=800,
        )

        result = response.choices[0].message.content

        # Parse response
        lines = result.split("\n")
        subject = ""
        body = []

        for line in lines:
            if line.startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
            elif line.startswith("BODY:"):
                body.append(line.replace("BODY:", "").strip())
            elif line.strip() and not line.startswith("SUBJECT"):
                body.append(line.strip())

        return {
            "subject": subject or f"🎉 {context['name']} is Coming!",
            "body": "\n\n".join(body),
            "cta": f"Book Your {context['name']} Event",
            "cta_url": settings.BOOKING_URL,
        }

    async def _generate_sms_content(self, context: Dict) -> Dict:
        """Generate SMS campaign content using AI."""
        prompt = f"""
Write a promotional SMS for hibachi catering (160 chars max).

Holiday: {context['name']}
Days: {context['days_until']}

Requirements:
- 160 characters max (with URL)
- Include emoji
- Create urgency
- Include booking link placeholder

Just the SMS text:
"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Write concise SMS marketing messages."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=100,
        )

        message = response.choices[0].message.content.strip()

        # Ensure URL is included
        if "http" not in message.lower() and "[url]" not in message.lower():
            message += f" Book: {settings.BOOKING_URL}"

        return {
            "message": message,
            "max_length": 160,
        }

    async def _generate_facebook_content(self, context: Dict) -> Dict:
        """Generate Facebook post content using AI."""
        prompt = f"""
Write a Facebook post for hibachi catering company.

Holiday: {context['name']}
Days Until: {context['days_until']}
Events: {', '.join(context['typical_events'])}

Requirements:
- 150-250 words
- Engaging opening
- Include emojis
- Ask question for engagement
- Clear CTA
- Also suggest image description for visual

Format:
POST: [post content]
IMAGE: [description for photo/video]
"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a social media expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=600,
        )

        result = response.choices[0].message.content

        post = ""
        image_prompt = ""

        for line in result.split("\n"):
            if line.startswith("POST:"):
                post = line.replace("POST:", "").strip()
            elif line.startswith("IMAGE:"):
                image_prompt = line.replace("IMAGE:", "").strip()
            elif post and not image_prompt:
                post += " " + line.strip()
            elif image_prompt:
                image_prompt += " " + line.strip()

        return {
            "post": post,
            "image_prompt": image_prompt
            or f"Hibachi chef cooking for {context['name']} celebration",
            "cta_button": "Book Now",
            "cta_url": settings.BOOKING_URL,
        }

    async def _generate_instagram_content(self, context: Dict) -> Dict:
        """Generate Instagram content using AI."""
        prompt = f"""
Write an Instagram caption for hibachi catering.

Holiday: {context['name']}
Days: {context['days_until']}

Requirements:
- 100-150 words
- Include emojis
- Conversational tone
- Include relevant hashtags (10-15)
- Suggest image concept

Format:
CAPTION: [caption]
HASHTAGS: [hashtags]
IMAGE: [image concept]
"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an Instagram marketing expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=500,
        )

        result = response.choices[0].message.content

        # Parse sections
        caption = ""
        hashtags = []
        image = ""

        current_section = None
        for line in result.split("\n"):
            if line.startswith("CAPTION:"):
                current_section = "caption"
                caption = line.replace("CAPTION:", "").strip()
            elif line.startswith("HASHTAGS:"):
                current_section = "hashtags"
                hashtag_line = line.replace("HASHTAGS:", "").strip()
                hashtags = [h.strip() for h in hashtag_line.split() if h.startswith("#")]
            elif line.startswith("IMAGE:"):
                current_section = "image"
                image = line.replace("IMAGE:", "").strip()
            elif current_section == "caption" and line.strip():
                caption += " " + line.strip()
            elif current_section == "image" and line.strip():
                image += " " + line.strip()

        return {
            "caption": caption,
            "hashtags": hashtags,
            "image_prompt": image,
        }

    async def _generate_google_ads_content(self, context: Dict) -> Dict:
        """Generate Google Ads content using AI."""
        prompt = f"""
Write Google Search Ads for hibachi catering.

Holiday: {context['name']}
Days: {context['days_until']}

Create 3 ad variations with:
- Headline 1 (30 chars)
- Headline 2 (30 chars)
- Headline 3 (30 chars)
- Description (90 chars)

Focus on: premium, professional, booking now

Format:
AD 1:
H1: [headline]
H2: [headline]
H3: [headline]
DESC: [description]
"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Google Ads expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=400,
        )

        return {
            "ads_copy": response.choices[0].message.content,
            "keywords": [
                f"{context['name'].lower()} catering",
                "hibachi catering",
                f"{context['name'].lower()} event catering",
                "mobile hibachi chef",
            ],
            "budget_recommendation": "$50-$100/day",
        }

    async def _generate_tiktok_content(self, context: Dict) -> Dict:
        """Generate TikTok content concept using AI."""
        prompt = f"""
Create TikTok video concept for hibachi catering.

Holiday: {context['name']}

Suggest:
- Video concept (15-30 seconds)
- Hook (first 3 seconds)
- Key moments
- Caption
- Trending audio suggestion

Keep it entertaining, show live cooking, create FOMO.
"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a TikTok content strategist."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=400,
        )

        return {
            "video_concept": response.choices[0].message.content,
            "duration": "15-30 seconds",
            "style": "entertaining, fast-paced",
        }


def get_ai_marketing_automation() -> AIMarketingAutomation:
    """Get AI marketing automation instance."""
    return AIMarketingAutomation()
