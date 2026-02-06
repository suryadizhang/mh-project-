"""
AI-Powered Newsletter Content Generation Service

Features:
- AI-powered content generation using OpenAI GPT-4
- Holiday-themed newsletter creation
- Customer segment targeting
- A/B testing support
- Content personalization

This service generates newsletter content. Use newsletter_service.py for subscriber management.
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


class NewsletterType(str, Enum):
    """Types of newsletters."""

    HOLIDAY_PROMOTION = "holiday_promotion"
    EVENT_SEASON = "event_season"
    BOOKING_REMINDER = "booking_reminder"
    NEW_FEATURE = "new_feature"
    CUSTOMER_STORY = "customer_story"
    SEASONAL_TIPS = "seasonal_tips"


class CustomerSegment(str, Enum):
    """Customer segments."""

    ALL = "all"
    FAMILIES = "families"
    EVENT_PLANNERS = "event_planners"
    CORPORATES = "corporates"
    PAST_CUSTOMERS = "past_customers"
    INACTIVE = "inactive"
    VIP = "vip"


class AINewsletterGenerator:
    """
    AI-powered newsletter content generator with holiday integration.

    Usage:
        generator = AINewsletterGenerator()

        # Generate holiday newsletters
        newsletters = await generator.generate_holiday_newsletters(days=60)

        # Get AI content
        content = await generator.generate_content(
            holiday_key="thanksgiving",
            segment=CustomerSegment.FAMILIES
        )
    """

    def __init__(self):
        self.holiday_service = get_holiday_service()

    async def generate_holiday_newsletters(self, days: int = 60) -> List[Dict]:
        """
        Generate AI-powered newsletters for all upcoming holidays.

        Returns list of newsletter configs ready to customize/send.
        """
        newsletters = []

        upcoming_holidays = self.holiday_service.get_upcoming_holidays(days=days)
        logger.info(f"Generating newsletters for {len(upcoming_holidays)} upcoming holidays")

        for holiday_key, holiday_obj, holiday_date in upcoming_holidays:
            target_segments = self._get_target_segments(holiday_obj)
            context = self.holiday_service.get_holiday_message_context(holiday_key)

            send_date = holiday_date - timedelta(days=holiday_obj.marketing_window_days)

            if send_date < date.today():
                continue

            for segment in target_segments:
                newsletter = {
                    "id": f"{holiday_key}_{segment.value}_{holiday_date.year}",
                    "type": NewsletterType.HOLIDAY_PROMOTION,
                    "holiday_key": holiday_key,
                    "holiday_name": holiday_obj.name,
                    "holiday_date": holiday_date,
                    "send_date": send_date,
                    "target_segment": segment,
                    "subject": await self._generate_subject_line(holiday_obj, segment, context),
                    "content": await self.generate_content(holiday_key, segment, context),
                    "cta": self._get_cta(holiday_obj),
                    "created_at": datetime.now(timezone.utc),
                }

                newsletters.append(newsletter)
                logger.info(f"✅ Generated: {newsletter['subject']}")

        return newsletters

    async def generate_content(
        self, holiday_key: str, segment: CustomerSegment, context: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Use OpenAI GPT-4 to generate newsletter content.

        Returns dict with html_content, text_content, preview_text.
        """
        if context is None:
            context = self.holiday_service.get_holiday_message_context(holiday_key)

        prompt = self._build_prompt(holiday_key, segment, context)

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert email marketing copywriter for a premium hibachi "
                            "catering company. Write engaging, personalized content that drives bookings. "
                            "Use warm, professional tone with storytelling."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=1500,
            )

            ai_text = response.choices[0].message.content

            html_content = self._convert_to_html(ai_text, context)
            text_content = self._strip_html(html_content)
            preview_text = text_content[:100] + "..."

            logger.info(f"✅ AI generated content for {holiday_key} - {segment.value}")

            return {
                "html_content": html_content,
                "text_content": text_content,
                "preview_text": preview_text,
                "ai_generated": True,
            }

        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._fallback_content(holiday_key, segment, context)

    def _build_prompt(self, holiday_key: str, segment: CustomerSegment, context: Dict) -> str:
        """Build AI prompt for content generation."""

        segment_guidance = {
            CustomerSegment.FAMILIES: "Target: Families. Tone: Warm, fun. Focus: Memories, bonding.",
            CustomerSegment.EVENT_PLANNERS: "Target: Planners. Tone: Professional. Focus: Execution, reliability.",
            CustomerSegment.CORPORATES: "Target: Corporate. Tone: Professional. Focus: Team building, networking.",
            CustomerSegment.PAST_CUSTOMERS: "Target: Past customers. Tone: Appreciative. Focus: Thank you, what's new.",
        }.get(segment, "Target: General. Tone: Friendly. Focus: Great experiences.")

        return f"""
Write SMS newsletter content for hibachi catering company.

IMPORTANT: This will be sent via SMS (RingCentral), NOT email!
Keep it concise and mobile-friendly.

HOLIDAY: {context['name']}
Days Until: {context['days_until']}
Events: {', '.join(context['typical_events'])}
Angle: {context['marketing_angle']}

{segment_guidance}

STRUCTURE:
1. Hook (relate to holiday, excitement)
2. Why hibachi is perfect (2-3 reasons)
3. Social proof (500+ events done)
4. Urgency ({context['days_until']} days left)
5. Strong CTA

LENGTH: 250-350 words (will be sent as SMS)
Include: live cooking, interactive experience
Mention: $550 minimum (position as value)
Use: MH Hibachi Catering

Note: STOP instructions will be added automatically by SMS service.
"""

    async def _generate_subject_line(
        self, holiday: Holiday, segment: CustomerSegment, context: Dict
    ) -> str:
        """Generate AI subject line."""
        try:
            prompt = f"""
Generate 1 SMS preview text for hibachi catering newsletter.
(This is for SMS, NOT email - newsletters are sent via RingCentral SMS)

Holiday: {context['name']}
Days: {context['days_until']}
Target: {segment.value}

Requirements:
- 50 chars max (SMS preview)
- Create urgency
- Include 1-2 emoji
- Personalized

Just the preview text:
"""
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Write compelling subject lines."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=50,
            )

            return response.choices[0].message.content.strip().strip("\"'")

        except Exception as e:
            logger.error(f"AI subject failed: {e}")
            return f"🎉 {context['name']} in {context['days_until']} Days - Book Now!"

    def _convert_to_html(self, ai_text: str, context: Dict) -> str:
        """Convert AI text to HTML email."""
        paragraphs = [p.strip() for p in ai_text.split("\n\n") if p.strip()]

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{context['name']} Newsletter</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,sans-serif;background:#f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;">
        <tr>
            <td align="center" style="padding:40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;">
                    <tr>
                        <td style="padding:40px;text-align:center;background:linear-gradient(135deg,#FF6B6B,#FF8E53);border-radius:8px 8px 0 0;">
                            <h1 style="margin:0;color:#fff;font-size:32px;">
                                🎉 {context['name']} is Coming!
                            </h1>
                            <p style="margin:10px 0 0;color:#fff;font-size:18px;">
                                Only {context['days_until']} days away!
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:40px;color:#333;font-size:16px;line-height:1.6;">
"""

        for para in paragraphs:
            html += f'                            <p style="margin:0 0 20px;">{para}</p>\n'

        html += f"""
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:30px;">
                                <tr>
                                    <td align="center">
                                        <a href="{settings.BOOKING_URL}" style="display:inline-block;padding:16px 40px;background:linear-gradient(135deg,#FF6B6B,#FF8E53);color:#fff;text-decoration:none;border-radius:6px;font-weight:bold;font-size:18px;">
                                            Book Your {context['name']} Event
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:30px;background:#f8f9fa;border-radius:0 0 8px 8px;text-align:center;color:#666;font-size:14px;">
                            <p style="margin:0;"><strong>MH Hibachi Catering</strong></p>
                            <p style="margin:10px 0;font-size:12px;color:#999;">
                                <a href="{{{{unsubscribe_url}}}}" style="color:#999;">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

        return html

    def _strip_html(self, html: str) -> str:
        """Convert HTML to plain text."""
        import re

        text = re.sub(r"<[^>]+>", "", html)
        text = text.replace("&nbsp;", " ").replace("&amp;", "&")
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    def _get_target_segments(self, holiday: Holiday) -> List[CustomerSegment]:
        """Determine target segments for holiday."""
        if holiday.category == HolidayCategory.EVENT_SEASON:
            return [
                CustomerSegment.EVENT_PLANNERS,
                CustomerSegment.FAMILIES,
                CustomerSegment.PAST_CUSTOMERS,
            ]
        elif holiday.category == HolidayCategory.FEDERAL:
            return [
                CustomerSegment.FAMILIES,
                CustomerSegment.PAST_CUSTOMERS,
                CustomerSegment.INACTIVE,
            ]
        else:
            return [CustomerSegment.ALL]

    def _get_cta(self, holiday: Holiday) -> Dict[str, str]:
        """Get CTA for holiday."""
        return {
            "text": f"Book Your {holiday.name} Event",
            "url": settings.BOOKING_URL,
        }

    def _fallback_content(
        self, holiday_key: str, segment: CustomerSegment, context: Dict
    ) -> Dict[str, str]:
        """Fallback if AI fails."""
        content = f"""
Hi there!

{context['name']} is coming up in just {context['days_until']} days! 🎉

{context['marketing_angle']}

Our hibachi catering is perfect for:
{chr(10).join(f'• {event}' for event in context['typical_events'])}

Book now for {context['name']}!
"""
        html = self._convert_to_html(content, context)

        return {
            "html_content": html,
            "text_content": content,
            "preview_text": f"{context['name']} is in {context['days_until']} days!",
            "ai_generated": False,
        }


def get_ai_newsletter_generator() -> AINewsletterGenerator:
    """Get AI newsletter generator instance."""
    return AINewsletterGenerator()
