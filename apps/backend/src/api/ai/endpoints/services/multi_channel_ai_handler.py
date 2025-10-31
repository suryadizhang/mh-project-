"""
Multi-Channel AI Handler for Customer Communications
Handles: Email, SMS/Text, Instagram DM, Facebook Messenger, Phone Transcripts

This service provides a unified interface for processing customer inquiries across
all communication channels with channel-specific optimizations and response formatting.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class MultiChannelAIHandler:
    """
    Handles customer inquiries across multiple channels with channel-specific
    formatting, tone adjustments, and response strategies.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Channel-specific configuration
        self.channel_config = {
            "email": {
                "max_length": 2000,
                "tone": "professional",
                "include_signature": True,
                "include_contact_info": True,
                "format": "paragraphs",
                "response_time_expectation": "24 hours"
            },
            "sms": {
                "max_length": 160,
                "tone": "friendly_casual",
                "include_signature": False,
                "include_contact_info": False,
                "format": "brief",
                "response_time_expectation": "1 hour"
            },
            "instagram": {
                "max_length": 1000,
                "tone": "casual_enthusiastic",
                "include_signature": False,
                "include_contact_info": True,
                "format": "conversational",
                "response_time_expectation": "2 hours"
            },
            "facebook": {
                "max_length": 1200,
                "tone": "friendly_professional",
                "include_signature": False,
                "include_contact_info": True,
                "format": "conversational",
                "response_time_expectation": "2 hours"
            },
            "phone_transcript": {
                "max_length": 1500,
                "tone": "conversational",
                "include_signature": False,
                "include_contact_info": True,
                "format": "bullet_points",
                "response_time_expectation": "immediate"
            },
            "web_chat": {
                "max_length": 800,
                "tone": "friendly_professional",
                "include_signature": False,
                "include_contact_info": True,
                "format": "conversational",
                "response_time_expectation": "immediate"
            }
        }
    
    async def extract_inquiry_details(self, message: str, channel: str) -> Dict[str, Any]:
        """
        Extract structured information from customer inquiry.
        
        Args:
            message: The raw customer message
            channel: Communication channel (email, sms, instagram, etc.)
        
        Returns:
            Dictionary with extracted details
        """
        details = {
            "party_size": None,
            "event_date": None,
            "event_month": None,
            "event_year": None,
            "location": None,
            "special_requests": [],
            "dietary_restrictions": [],
            "customer_name": None,
            "customer_phone": None,
            "customer_email": None,
            "inquiry_type": None,  # quote, booking, info, complaint
            "urgency": "normal",  # low, normal, high, urgent
            "sentiment": "positive"  # positive, neutral, negative
        }
        
        # Extract party size
        party_size_patterns = [
            r'(\d+)\s+(?:people|guests|persons?)',
            r'party\s+of\s+(\d+)',
            r'for\s+(\d+)',
            r'group\s+of\s+(\d+)'
        ]
        for pattern in party_size_patterns:
            match = re.search(pattern, message.lower())
            if match:
                details["party_size"] = int(match.group(1))
                break
        
        # Extract date/month/year
        month_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', message.lower())
        if month_match:
            month_map = {
                'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
                'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
                'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
                'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                'october': 10, 'oct': 10, 'november': 11, 'nov': 11,
                'december': 12, 'dec': 12
            }
            details["event_month"] = month_map.get(month_match.group(1).lower())
        
        year_match = re.search(r'20(\d{2})', message)
        if year_match:
            details["event_year"] = int(f"20{year_match.group(1)}")
        
        # Extract location
        location_patterns = [
            r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'near\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'area:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        for pattern in location_patterns:
            match = re.search(pattern, message)
            if match:
                location = match.group(1)
                # Common California areas
                if any(area in location.lower() for area in ['sonoma', 'sacramento', 'san francisco', 'bay area', 'napa', 'san jose', 'oakland']):
                    details["location"] = location
                    break
        
        # Extract customer name
        name_patterns = [
            r'(?:^|\n)([A-Z][a-z]+)\s*$',  # Name at end of message
            r'(?:Thanks|Best|Regards|Sincerely),?\s*([A-Z][a-z]+)',
            r'(?:I\'m|I am)\s+([A-Z][a-z]+)',
            r'--\s*\n([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message, re.MULTILINE)
            if match:
                name = match.group(1)
                if len(name) > 2 and name not in ['Thanks', 'Best', 'Regards', 'Sincerely']:
                    details["customer_name"] = name
                    break
        
        # Extract phone number
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{10}'
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, message)
            if match:
                details["customer_phone"] = match.group(0)
                break
        
        # Extract email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
        if email_match:
            details["customer_email"] = email_match.group(0)
        
        # Determine inquiry type
        if any(word in message.lower() for word in ['quote', 'pricing', 'cost', 'price', 'how much']):
            details["inquiry_type"] = "quote"
        elif any(word in message.lower() for word in ['book', 'reserve', 'schedule', 'availability']):
            details["inquiry_type"] = "booking"
        elif any(word in message.lower() for word in ['disappointed', 'refund', 'complaint', 'unhappy', 'terrible']):
            details["inquiry_type"] = "complaint"
        else:
            details["inquiry_type"] = "info"
        
        # Determine urgency
        if any(word in message.lower() for word in ['urgent', 'asap', 'emergency', 'immediately']):
            details["urgency"] = "urgent"
        elif any(word in message.lower() for word in ['soon', 'quickly', 'this week']):
            details["urgency"] = "high"
        
        # Determine sentiment
        if any(word in message.lower() for word in ['disappointed', 'unhappy', 'terrible', 'worst', 'refund', 'awful']):
            details["sentiment"] = "negative"
        elif any(word in message.lower() for word in ['excited', 'looking forward', 'great', 'wonderful', 'love']):
            details["sentiment"] = "positive"
        else:
            details["sentiment"] = "neutral"
        
        # Extract special requests
        if 'dietary' in message.lower() or 'allerg' in message.lower():
            details["special_requests"].append("dietary_accommodations")
        if 'vegetarian' in message.lower() or 'vegan' in message.lower():
            details["dietary_restrictions"].append("vegetarian/vegan")
        if 'gluten' in message.lower():
            details["dietary_restrictions"].append("gluten-free")
        if 'nut' in message.lower() and 'allerg' in message.lower():
            details["dietary_restrictions"].append("nut allergy")
        
        # Extract protein selections
        details["protein_selections"] = self.extract_protein_selections(message)
        
        self.logger.info(f"📋 Extracted inquiry details: {json.dumps(details, indent=2)}")
        return details
    
    def extract_protein_selections(self, message: str) -> Dict[str, int]:
        """
        Extract protein selections and quantities from customer message.
        
        Args:
            message: Customer message text
        
        Returns:
            Dictionary with protein names as keys and counts as values
        """
        selections = {}
        message_lower = message.lower()
        
        # Protein name mappings (various ways customers might mention proteins)
        protein_patterns = {
            "chicken": [r'(\d+)\s*(?:×|x)?\s*chicken', r'chicken.*?(\d+)'],
            "steak": [r'(\d+)\s*(?:×|x)?\s*(?:steak|strip)', r'(?:ny\s*strip|strip\s*steak).*?(\d+)'],
            "shrimp": [r'(\d+)\s*(?:×|x)?\s*shrimp', r'shrimp.*?(\d+)'],
            "tofu": [r'(\d+)\s*(?:×|x)?\s*tofu', r'tofu.*?(\d+)'],
            "vegetables": [r'(\d+)\s*(?:×|x)?\s*(?:veg|vegetable)', r'(?:veg|vegetable).*?(\d+)'],
            "salmon": [r'(\d+)\s*(?:×|x)?\s*salmon', r'salmon.*?(\d+)'],
            "scallops": [r'(\d+)\s*(?:×|x)?\s*scallop', r'scallop.*?(\d+)'],
            "filet_mignon": [r'(\d+)\s*(?:×|x)?\s*(?:filet|mignon)', r'filet\s*mignon.*?(\d+)'],
            "lobster_tail": [r'(\d+)\s*(?:×|x)?\s*lobster', r'lobster.*?(\d+)']
        }
        
        for protein, patterns in protein_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    count = int(match.group(1))
                    selections[protein] = count
                    break  # Use first match for each protein
        
        return selections
    
    def build_system_prompt_for_channel(self, channel: str, inquiry_details: Dict) -> str:
        """
        Build channel-specific system prompt with extracted inquiry details.
        
        Args:
            channel: Communication channel
            inquiry_details: Extracted customer inquiry details
        
        Returns:
            Customized system prompt
        """
        config = self.channel_config.get(channel, self.channel_config["email"])
        
        base_prompt = f"""You are a professional customer service AI for a premium hibachi catering company.

**Communication Channel**: {channel.upper()}
**Tone**: {config['tone']}
**Max Response Length**: {config['max_length']} characters
**Response Format**: {config['format']}

**Company Information**:
- Service: Private hibachi chef catering for homes and events
- Pricing: $75 per person (base rate)
- Service Areas: Sacramento, Bay Area, Sonoma, Napa Valley
- Payment Methods: Stripe, Plaid, Zelle, Venmo
- Phone: (916) 123-4567
- Email: bookings@hibachiathome.com
- Website: www.hibachiathome.com

**PROTEIN OPTIONS & PRICING** (IMPORTANT - Always mention to customers):
Each guest gets 2 FREE proteins to choose from:
• FREE Options: Chicken, NY Strip Steak, Shrimp, Tofu, Vegetables

Premium Upgrade Options (optional):
• Salmon: +$5 per protein selection
• Scallops: +$5 per protein selection
• Filet Mignon: +$5 per protein selection
• Lobster Tail: +$15 per protein selection

3rd Protein Rule:
• If total proteins selected > (number of guests × 2), then charge +$10 per extra protein
• Example: 10 guests = 20 FREE protein selections included
  - If they select 25 proteins total → 5 extra proteins × $10 = $50 additional charge
  - Plus any premium upgrade costs

Example Protein Pricing for 10 guests:
• Scenario 1: 10 Chicken + 10 Shrimp = $0 (within 20 free)
• Scenario 2: 10 Filet Mignon + 10 Chicken = $50 (10 Filet upgrades × $5)
• Scenario 3: 10 Lobster + 12 Chicken + 10 Shrimp = $150 Lobster + $20 extra proteins = $170
  (32 total proteins, 12 over the 20 free limit)

Always educate customers about protein options - this is a key differentiator!

**Customer Inquiry Details**:
- Party Size: {inquiry_details.get('party_size', 'Not specified')}
- Event Date: {inquiry_details.get('event_month', 'Not specified')} {inquiry_details.get('event_year', '')}
- Location: {inquiry_details.get('location', 'Not specified')}
- Customer Name: {inquiry_details.get('customer_name', 'Valued Customer')}
- Inquiry Type: {inquiry_details.get('inquiry_type', 'general')}
- Urgency: {inquiry_details.get('urgency', 'normal')}
- Sentiment: {inquiry_details.get('sentiment', 'neutral')}

**Response Guidelines**:
"""
        
        # Channel-specific guidelines
        if channel == "email":
            base_prompt += """
1. Start with professional greeting: "Dear [Name]" or "Hi [Name]"
2. Thank them for their inquiry
3. Address ALL specific questions (party size, date, location, pricing)
4. Provide detailed quote breakdown:
   - Base cost: $75 × [party_size] = $[total]
   - What's included: Chef, ingredients, cooking equipment, setup/cleanup
   - Additional options: Premium menu (+$15/person), extra time (+$50/hour)
5. Mention service area confirmation (Sonoma is within our service area)
6. Next steps: "To proceed with booking..." or "Would you like to schedule a call?"
7. Include contact information (phone + email)
8. Professional sign-off: "Best regards," or "Looking forward to serving you,"
9. Company signature

**IMPORTANT**: If customer provided phone/email, acknowledge it: "I'll also follow up at [phone/email]"
"""
        elif channel == "sms":
            base_prompt += """
1. Keep it BRIEF (max 160 chars if possible, 2-3 messages if needed)
2. Use friendly, casual tone
3. Get to the point immediately
4. Format: "Hi [Name]! For [party_size] people in [location]: $[total]. Includes chef, food, setup. Book: [link]"
5. Use emojis sparingly: 🍱 for food, 📅 for booking
6. End with clear CTA: "Reply YES to book" or "Call us: [phone]"
"""
        elif channel == "instagram":
            base_prompt += """
1. Use casual, enthusiastic tone with emojis 🎉🍱
2. Start: "Hey [Name]! Thanks for reaching out! 😊"
3. Provide quote in friendly format: "For your party of [X] in [location]: $[total] 🎊"
4. Highlight what makes you special: "Fresh ingredients + pro chef at YOUR place!"
5. Include CTA: "DM us to book or tap link in bio!"
6. Use line breaks for readability
7. Add relevant hashtags: #HibachiAtHome #SonomaEats
"""
        elif channel == "facebook":
            base_prompt += """
1. Friendly, professional tone (balance of casual + professional)
2. Start: "Hi [Name], thanks for your message!"
3. Address each point in their inquiry
4. Use bullet points for clarity:
   • Party size: [X] guests
   • Location: [Location] ✓ (we serve this area!)
   • Pricing: $[total] ($75/person)
   • Includes: Everything you need for amazing hibachi
5. End with: "Ready to book? Click the link below or call us!"
"""
        elif channel == "phone_transcript":
            base_prompt += """
1. Conversational, natural speech style
2. Start: "Thank you for calling! I can help you with that."
3. Use bullet points to organize talking points:
   • Confirm details: "So you're looking at [party_size] people in [location]?"
   • Provide quote: "That would be $[total] total"
   • Explain what's included
   • Address any concerns
4. End with: "Would you like me to reserve that date for you?"
5. Provide callback number if needed
"""
        
        # Inquiry type specific additions
        if inquiry_details.get("inquiry_type") == "quote":
            base_prompt += f"""

**QUOTE CALCULATION**:
Party Size: {inquiry_details.get('party_size', '[NUMBER]')} people
Base Rate: $75 per person
Subtotal: ${inquiry_details.get('party_size', 0) * 75 if inquiry_details.get('party_size') else '[TOTAL]'}

**What's Included**:
- Professional hibachi chef (2-3 hours)
- All fresh ingredients (protein, vegetables, rice, noodles)
- Commercial-grade cooking equipment
- Complete setup and cleanup
- Entertainment (chef tricks, cooking show)

**Optional Add-ons**:
- Premium menu (wagyu beef, lobster): +$15/person
- Extended time: +$50/hour
- Sake pairing: +$20/person
"""
        
        if inquiry_details.get("urgency") in ["high", "urgent"]:
            base_prompt += "\n\n⚠️ **URGENT INQUIRY**: Prioritize quick response with immediate action steps."
        
        if inquiry_details.get("sentiment") == "negative":
            base_prompt += "\n\n⚠️ **NEGATIVE SENTIMENT**: Show empathy, offer immediate escalation to manager."
        
        # Location confirmation
        if inquiry_details.get("location"):
            location = inquiry_details["location"]
            if any(area in location.lower() for area in ['sonoma', 'napa', 'sacramento', 'bay area']):
                base_prompt += f"\n\n✓ **Location Confirmed**: {location} is within our service area!"
        
        return base_prompt
    
    def format_response_for_channel(self, ai_response: str, channel: str, inquiry_details: Dict) -> Dict[str, Any]:
        """
        Format AI response according to channel requirements.
        
        Args:
            ai_response: Raw AI response text
            channel: Communication channel
            inquiry_details: Customer inquiry details
        
        Returns:
            Formatted response with metadata
        """
        config = self.channel_config.get(channel, self.channel_config["email"])
        
        # Truncate if needed
        if len(ai_response) > config["max_length"]:
            # Try to truncate at sentence boundary
            truncate_point = ai_response[:config["max_length"]].rfind('.')
            if truncate_point > config["max_length"] * 0.8:
                ai_response = ai_response[:truncate_point + 1]
            else:
                ai_response = ai_response[:config["max_length"]] + "..."
        
        formatted_response = {
            "channel": channel,
            "response_text": ai_response,
            "metadata": {
                "customer_name": inquiry_details.get("customer_name"),
                "party_size": inquiry_details.get("party_size"),
                "location": inquiry_details.get("location"),
                "inquiry_type": inquiry_details.get("inquiry_type"),
                "urgency": inquiry_details.get("urgency"),
                "sentiment": inquiry_details.get("sentiment"),
                "requires_follow_up": inquiry_details.get("urgency") in ["high", "urgent"] or inquiry_details.get("sentiment") == "negative",
                "estimated_quote": inquiry_details.get("party_size", 0) * 75 if inquiry_details.get("party_size") else None
            },
            "suggested_actions": [],
            "response_time_expectation": config["response_time_expectation"]
        }
        
        # Add suggested actions
        if inquiry_details.get("inquiry_type") == "quote":
            formatted_response["suggested_actions"].append("send_detailed_quote")
            formatted_response["suggested_actions"].append("schedule_consultation_call")
        
        if inquiry_details.get("inquiry_type") == "booking":
            formatted_response["suggested_actions"].append("check_calendar_availability")
            formatted_response["suggested_actions"].append("send_booking_link")
        
        if inquiry_details.get("urgency") in ["high", "urgent"]:
            formatted_response["suggested_actions"].append("priority_follow_up")
        
        if inquiry_details.get("sentiment") == "negative":
            formatted_response["suggested_actions"].append("escalate_to_manager")
            formatted_response["suggested_actions"].append("offer_compensation")
        
        if inquiry_details.get("customer_phone"):
            formatted_response["suggested_actions"].append("call_customer")
        
        self.logger.info(f"✅ Formatted response for {channel}: {len(ai_response)} chars, {len(formatted_response['suggested_actions'])} actions")
        return formatted_response
    
    async def process_multi_channel_inquiry(
        self, 
        message: str, 
        channel: str,
        customer_booking_ai  # Pass the AI service instance
    ) -> Dict[str, Any]:
        """
        Complete pipeline for processing customer inquiry from any channel.
        
        Args:
            message: Raw customer message
            channel: Communication channel (email, sms, instagram, facebook, phone_transcript)
            customer_booking_ai: Instance of CustomerBookingAI service
        
        Returns:
            Formatted response with metadata and suggested actions
        """
        self.logger.info(f"🔄 Processing {channel} inquiry: {message[:100]}...")
        
        # Step 1: Extract inquiry details
        inquiry_details = await self.extract_inquiry_details(message, channel)
        
        # Step 1.5: Calculate protein costs if selections provided
        protein_info = None
        if inquiry_details.get("protein_selections") and inquiry_details.get("party_size"):
            try:
                from .protein_calculator_service import get_protein_calculator_service
                protein_calc = get_protein_calculator_service()
                protein_info = protein_calc.calculate_protein_costs(
                    guest_count=inquiry_details["party_size"],
                    protein_selections=inquiry_details["protein_selections"]
                )
                self.logger.info(f"🥩 Protein cost calculated: ${protein_info['total_protein_cost']}")
            except Exception as e:
                self.logger.error(f"❌ Error calculating protein cost: {str(e)}")
        
        # Step 2: Build channel-specific system prompt
        system_prompt = self.build_system_prompt_for_channel(channel, inquiry_details)
        
        # Step 3: Build context for AI
        context = {
            "user_role": "customer",
            "channel": channel,
            "inquiry_details": inquiry_details,
            "protein_info": protein_info,  # Add protein information to context
            "system_prompt_override": system_prompt
        }
        
        # Add protein details to system prompt if available
        if protein_info:
            protein_context = f"""

**CUSTOMER'S PROTEIN SELECTION ANALYSIS**:
{protein_info['proteins_summary']}

Protein Cost Breakdown:
• Premium Upgrades: ${protein_info['upgrade_cost']}
• Extra Proteins (3rd+): ${protein_info['third_protein_cost']}
• Total Protein Cost: ${protein_info['total_protein_cost']}

Include this information naturally in your response!
"""
            context["system_prompt_override"] += protein_context
        
        # Step 4: Process through optimized AI pipeline
        ai_response = await customer_booking_ai.process_customer_message(
            message=message,
            context=context
        )
        
        # Step 5: Format response for channel
        formatted_response = self.format_response_for_channel(
            ai_response["content"],
            channel,
            inquiry_details
        )
        
        # Add protein information to metadata if available
        if protein_info:
            formatted_response["metadata"]["protein_breakdown"] = protein_info["breakdown"]
            formatted_response["metadata"]["protein_summary"] = protein_info["proteins_summary"]
            formatted_response["metadata"]["protein_cost"] = float(protein_info["total_protein_cost"])
        
        # Add AI metadata
        formatted_response["ai_metadata"] = {
            "model_used": ai_response.get("model_used"),
            "confidence": ai_response.get("confidence"),
            "response_time_ms": ai_response.get("response_time_ms"),
            "from_cache": ai_response.get("from_cache", False),
            "complexity_score": ai_response.get("model_analysis", {}).get("complexity_score")
        }
        
        self.logger.info(f"✅ Multi-channel processing complete for {channel}")
        return formatted_response


# Singleton instance
_multi_channel_handler = None

def get_multi_channel_handler() -> MultiChannelAIHandler:
    """Get or create singleton instance of MultiChannelAIHandler."""
    global _multi_channel_handler
    if _multi_channel_handler is None:
        _multi_channel_handler = MultiChannelAIHandler()
    return _multi_channel_handler
