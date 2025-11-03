"""
Knowledge Agent - RAG specialist, policy lookup & source citation

Specializes in:
- RAG (Retrieval-Augmented Generation)
- Policy and pricing lookup
- FAQ answering
- Source citation
- Technical documentation

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class KnowledgeAgent(BaseAgent):
    """
    Knowledge Agent - Expert in company policies, pricing, and FAQs.

    Expertise:
    - RAG (search knowledge base, cite sources)
    - Policy interpretation (cancellation, refunds, terms)
    - Pricing details (packages, add-ons, seasonal rates)
    - FAQ answering (with source attribution)
    - Technical documentation (equipment, setup, requirements)

    Tools:
    - search_knowledge_base: Semantic search across documents
    - get_policy_details: Look up specific policies
    - calculate_pricing: Detailed pricing breakdowns
    - find_faq_answer: Search FAQs

    Usage:
        agent = KnowledgeAgent()
        response = await agent.process(
            message="What's your cancellation policy?",
            context={"conversation_id": "123"}
        )
    """

    def __init__(self):
        super().__init__(
            agent_type="knowledge",
            temperature=0.3,  # Very factual, low creativity
            max_tokens=600,  # Longer for detailed explanations
        )

    def get_system_prompt(self) -> str:
        return """You are the knowledge expert for MyHibachi, specializing in accurate information retrieval and policy interpretation.

Your mission: Provide precise, well-sourced answers to customer questions about policies, pricing, and procedures.

**Core Principles:**
1. **Accuracy First** - Use knowledge base, don't guess or make up information
2. **Cite Sources** - Always mention where information comes from (policy doc, FAQ, pricing sheet)
3. **Clear Communication** - Explain complex policies in simple terms
4. **Comprehensive** - Cover all relevant details, exceptions, and edge cases
5. **Up-to-Date** - Flag if information might be outdated or needs verification

**Communication Style:**
- Authoritative but friendly
- Use bullet points for multi-part answers
- Bold key terms (refund policy, deposit requirement, etc.)
- Provide examples when helpful
- Offer related information proactively

**Knowledge Domains:**

**1. Policies & Terms:**
- Cancellation policy (14/7/0 day rules)
- Refund policy (conditions, processing time)
- Deposit requirements (50% upfront)
- Payment methods (credit card, check, Venmo, Zelle)
- Insurance and liability (what's covered)
- Weather policy (outdoor events)
- Privacy policy (data usage)

**2. Pricing & Packages:**
- Standard Package ($45/person)
- Premium Package ($65/person)
- Deluxe Package ($85/person)
- Add-ons (extra protein, sushi, sake bar)
- Seasonal pricing (peak vs off-season)
- Volume discounts (75+ guests)
- Travel fees (51+ miles)

**3. Operational Details:**
- Service area (50-mile radius standard)
- Equipment requirements (electricity, space)
- Setup/breakdown timing (1 hr / 30 min)
- Event duration (2 hours standard)
- Chef-to-guest ratio (1:50 standard)
- Dietary accommodations (vegetarian, gluten-free, allergies)

**4. FAQs:**
- How far in advance to book?
- What's included in packages?
- Can we customize the menu?
- Do you provide tables/chairs?
- What if it rains (outdoor events)?
- Can we request a specific chef?
- How does payment work?
- What's your cancellation policy?

**5. Technical Specs:**
- Equipment dimensions
- Power requirements (standard 110V outlet)
- Space requirements (10x10 ft minimum)
- Weight capacity considerations
- Outdoor event requirements
- Venue access needs

**Answer Framework:**

**For Policy Questions:**
1. State the policy clearly and directly
2. Explain the reasoning (if helpful)
3. Cover exceptions or special cases
4. Provide examples
5. Cite source document

Example:
"Our cancellation policy works on a sliding scale based on notice:
- **14+ days notice**: Full refund, no questions asked
- **7-13 days notice**: 50% refund
- **Less than 7 days**: No refund, but we'll issue a credit for a future event

This policy exists because we turn away other bookings once we reserve your date. However, we understand emergencies happen - if you have an extenuating circumstance (medical, weather, etc.), please reach out and we'll work with you.

Source: Booking Terms & Conditions, Section 4.2"

**For Pricing Questions:**
1. Provide base pricing
2. Break down what's included
3. Mention add-ons and upgrades
4. Note any applicable discounts
5. Calculate total if numbers provided

Example:
"For 60 guests with our Premium Package:
- **Base**: $65/person × 60 = $3,900
- **Included**: Filet mignon + lobster tail, premium fried rice, vegetables, chef performance, setup, cleanup
- **Popular add-ons**:
  - Sushi station: +$1,200 ($20/person)
  - Extra protein: +$900 ($15/person)
- **Discount**: None (need 75+ guests for volume discount)
- **Total**: $3,900 (or $6,000 with both add-ons)

Source: Current Pricing Sheet (updated October 2024)"

**For FAQ Questions:**
1. Answer directly first
2. Provide context/reasoning
3. Mention related information
4. Link to full documentation if complex

Example:
"Yes, we can accommodate dietary restrictions! We regularly handle:
- Vegetarian/vegan guests (tofu or veggie-only preparations)
- Gluten-free (swap soy sauce, modify rice prep)
- Allergies (we take these very seriously - please inform us in advance)
- Religious dietary needs (kosher-style prep available)

**Important**: For severe allergies, please notify us at least 7 days before your event so we can implement proper protocols. We take cross-contamination seriously and will prep allergen-free meals separately.

For events with 10+ dietary restriction meals, we recommend our Deluxe Package which includes menu consultation.

Source: Dietary Accommodations Guide"

**Tools Usage:**
- Use `search_knowledge_base` for complex or unfamiliar questions
- Use `get_policy_details` when customer asks about specific policies
- Use `calculate_pricing` for detailed cost breakdowns
- Use `find_faq_answer` to check if there's a standard answer

**Handling Unknowns:**
- If you don't know: "Let me verify that information for you" → use search tool
- If information is outdated: "Based on our October 2024 pricing, [answer]. Let me confirm this is still current."
- If contradictory sources: "I'm seeing conflicting information. Let me escalate this to verify the current policy."
- If extremely specific: "That's a great question that requires specialist input. Let me connect you with [appropriate agent/manager]."

**Source Citation Format:**
Always cite sources:
- "According to our Cancellation Policy (Section 3)..."
- "As outlined in the Premium Package brochure..."
- "Per our FAQ page (updated October 2024)..."
- "Based on the Booking Terms & Conditions..."

**Escalation:**
- Refer sales negotiations to Lead Nurturing Agent
- Refer complaints to Customer Care Agent
- Refer booking/scheduling to Operations Agent
- Handle all factual, policy, and pricing questions yourself

**Remember:**
- Accuracy > Speed - better to search than guess
- Cite sources - builds trust and allows verification
- Explain "why" - helps customers understand policies
- Proactive information - mention related details they might need
- Update awareness - flag if information seems outdated
"""

    def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "Semantic search across company knowledge base (policies, docs, FAQs)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (question or keywords)",
                            },
                            "document_type": {
                                "type": "string",
                                "enum": ["all", "policies", "pricing", "faq", "technical_docs"],
                                "description": "Filter by document type",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return (default 3)",
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_policy_details",
                    "description": "Retrieve specific policy document details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "policy_name": {
                                "type": "string",
                                "enum": [
                                    "cancellation_policy",
                                    "refund_policy",
                                    "deposit_policy",
                                    "payment_terms",
                                    "weather_policy",
                                    "liability_insurance",
                                    "privacy_policy",
                                    "dietary_accommodations",
                                ],
                                "description": "Name of policy to retrieve",
                            }
                        },
                        "required": ["policy_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_pricing",
                    "description": "Calculate detailed pricing breakdown with all fees and discounts",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package": {
                                "type": "string",
                                "enum": ["standard", "premium", "deluxe"],
                                "description": "Package type",
                            },
                            "num_guests": {"type": "integer", "description": "Number of guests"},
                            "addons": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "extra_protein",
                                        "sushi_station",
                                        "sake_bar",
                                        "extended_time",
                                    ],
                                },
                                "description": "Selected add-ons",
                            },
                            "travel_distance": {
                                "type": "integer",
                                "description": "Distance from headquarters in miles",
                            },
                            "is_peak_season": {
                                "type": "boolean",
                                "description": "Is event during peak season (May-Sep)?",
                            },
                        },
                        "required": ["package", "num_guests"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "find_faq_answer",
                    "description": "Search FAQ database for common questions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string", "description": "Customer's question"},
                            "category": {
                                "type": "string",
                                "enum": [
                                    "booking",
                                    "pricing",
                                    "menu",
                                    "logistics",
                                    "policies",
                                    "general",
                                ],
                                "description": "FAQ category to search",
                            },
                        },
                        "required": ["question"],
                    },
                },
            },
        ]

    async def process_tool_call(
        self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool functions"""

        try:
            if tool_name == "search_knowledge_base":
                return await self._search_knowledge_base(arguments)

            elif tool_name == "get_policy_details":
                return await self._get_policy_details(arguments)

            elif tool_name == "calculate_pricing":
                return await self._calculate_pricing(arguments)

            elif tool_name == "find_faq_answer":
                return await self._find_faq_answer(arguments)

            else:
                return {"success": False, "result": None, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}", exc_info=True)
            return {"success": False, "result": None, "error": str(e)}

    # ===== Tool Implementations =====

    async def _search_knowledge_base(self, args: dict[str, Any]) -> dict[str, Any]:
        """Search knowledge base using RAG"""

        query = args["query"]
        document_type = args.get("document_type", "all")
        top_k = args.get("top_k", 3)

        # TODO: Integrate with actual vector database (Pinecone, Weaviate, or PostgreSQL pgvector)
        # This is a mock implementation showing the structure

        # Simulate embedding generation + similarity search
        mock_results = [
            {
                "content": "Our cancellation policy provides full refunds for cancellations made 14 or more days before the event. For cancellations between 7-13 days, we offer a 50% refund. Unfortunately, we cannot provide refunds for cancellations made less than 7 days before the event, though we're happy to discuss event credits for extenuating circumstances.",
                "source": "Booking Terms & Conditions - Section 4.2 (Cancellation Policy)",
                "document_type": "policies",
                "relevance_score": 0.95,
                "last_updated": "2024-10-01",
            },
            {
                "content": "Deposit requirement: We require a 50% deposit to secure your booking. The deposit is non-refundable but can be transferred to a different date if changed with 14+ days notice. The remaining 50% balance is due 24 hours before your event.",
                "source": "Payment Terms Document - Section 2.1",
                "document_type": "policies",
                "relevance_score": 0.88,
                "last_updated": "2024-10-01",
            },
            {
                "content": "For events cancelled due to weather (outdoor events only), we offer full rescheduling at no charge. We monitor weather forecasts 48 hours before your event and will proactively reach out if conditions look unfavorable.",
                "source": "Weather Policy FAQ",
                "document_type": "faq",
                "relevance_score": 0.82,
                "last_updated": "2024-09-15",
            },
        ]

        # Filter by document type if specified
        if document_type != "all":
            mock_results = [r for r in mock_results if r["document_type"] == document_type]

        # Limit to top_k
        results = mock_results[:top_k]

        return {
            "success": True,
            "result": {
                "query": query,
                "results_found": len(results),
                "results": results,
                "note": "Results ranked by semantic relevance",
            },
        }

    async def _get_policy_details(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get specific policy document"""

        policy_name = args["policy_name"]

        # Mock policy database
        policies = {
            "cancellation_policy": {
                "title": "Cancellation Policy",
                "version": "3.1",
                "last_updated": "2024-10-01",
                "content": {
                    "overview": "Flexible cancellation with sliding scale refunds based on notice period",
                    "tiers": [
                        {
                            "notice": "14+ days",
                            "refund": "100%",
                            "notes": "Full refund, no questions asked",
                        },
                        {
                            "notice": "7-13 days",
                            "refund": "50%",
                            "notes": "Partial refund to cover committed resources",
                        },
                        {
                            "notice": "Less than 7 days",
                            "refund": "0%",
                            "notes": "No refund, but event credit offered",
                        },
                    ],
                    "exceptions": [
                        "Medical emergencies with documentation",
                        "Weather emergencies (outdoor events)",
                        "Venue cancellations beyond customer control",
                    ],
                    "process": "Contact us via email or phone, cancellation effective upon our confirmation",
                    "refund_timeline": "Refunds processed within 5-7 business days",
                },
            },
            "refund_policy": {
                "title": "Refund Policy",
                "version": "2.0",
                "last_updated": "2024-10-01",
                "content": {
                    "methods": [
                        "Original payment method",
                        "Account credit",
                        "Check (for certain cases)",
                    ],
                    "timeline": "5-7 business days for card refunds, immediate for account credits",
                    "partial_refunds": "Available for service issues, calculated based on severity",
                    "dispute_process": "Contact customer care → escalate to manager if unresolved → third-party mediation if needed",
                },
            },
            "deposit_policy": {
                "title": "Deposit Policy",
                "version": "1.5",
                "last_updated": "2024-09-01",
                "content": {
                    "amount": "50% of total event cost",
                    "due_date": "Within 48 hours of booking confirmation",
                    "payment_methods": ["Credit card", "Debit card", "Check", "Venmo", "Zelle"],
                    "refundable": "Yes, subject to cancellation policy terms",
                    "transferable": "Yes, to different date with 14+ days notice (no fee)",
                    "hold_period": "We'll hold your date for 48 hours without deposit, then release if not paid",
                },
            },
            "payment_terms": {
                "title": "Payment Terms",
                "version": "2.1",
                "last_updated": "2024-10-01",
                "content": {
                    "deposit": "50% upfront to secure booking",
                    "balance": "50% due 24 hours before event",
                    "late_payment": "Event may be cancelled if balance not received on time",
                    "payment_methods": [
                        "All major credit cards",
                        "Checks (7 days before event)",
                        "Venmo/Zelle",
                        "Wire transfer (corporate only)",
                    ],
                    "invoicing": "Automatic via email upon booking",
                    "payment_plans": "Available for events >$5,000 (split into 3 payments)",
                },
            },
            "weather_policy": {
                "title": "Weather Policy (Outdoor Events)",
                "version": "1.2",
                "last_updated": "2024-09-15",
                "content": {
                    "requirement": "Covered backup area (tent or indoor space) required for all outdoor events",
                    "monitoring": "We monitor forecasts 48 hours before event",
                    "proactive_outreach": "We'll contact you if weather looks unfavorable",
                    "rescheduling": "Free rescheduling for weather-related cancellations",
                    "equipment_protection": "We cannot operate in rain (electrical safety) or extreme winds (safety hazard)",
                    "customer_decision": "Final decision to proceed or reschedule is yours, made 24 hours before event",
                },
            },
            "liability_insurance": {
                "title": "Liability Insurance & Coverage",
                "version": "1.0",
                "last_updated": "2024-08-01",
                "content": {
                    "coverage_amount": "$2M general liability insurance",
                    "what_covered": [
                        "Property damage to venue",
                        "Injury from equipment",
                        "Food safety incidents",
                    ],
                    "what_not_covered": [
                        "Guest injuries unrelated to our service",
                        "Venue-provided equipment damage",
                        "Pre-existing venue damage",
                    ],
                    "certificate": "Certificate of insurance available upon request (needed for some venues)",
                    "claims_process": "Report immediately → we file claim → insurance handles settlement",
                },
            },
            "privacy_policy": {
                "title": "Privacy Policy",
                "version": "4.0",
                "last_updated": "2024-07-01",
                "content": {
                    "data_collected": [
                        "Name, email, phone",
                        "Event details",
                        "Payment information (encrypted)",
                        "Communication history",
                    ],
                    "data_usage": [
                        "Event coordination",
                        "Payment processing",
                        "Marketing (opt-in only)",
                        "Service improvements",
                    ],
                    "data_sharing": "Never sold to third parties; shared only with payment processors and service providers",
                    "data_retention": "5 years for business records, then securely deleted",
                    "your_rights": [
                        "Access your data",
                        "Request deletion",
                        "Opt out of marketing",
                        "Correct inaccuracies",
                    ],
                },
            },
            "dietary_accommodations": {
                "title": "Dietary Accommodations Guide",
                "version": "2.0",
                "last_updated": "2024-10-15",
                "content": {
                    "supported": [
                        "Vegetarian/vegan",
                        "Gluten-free",
                        "Common allergies (nuts, dairy, shellfish)",
                        "Religious restrictions (halal, kosher-style)",
                    ],
                    "notice_required": "7 days advance notice for best accommodation",
                    "allergy_protocol": "Separate prep area, dedicated equipment, ingredient verification",
                    "limitations": "Cannot guarantee 100% allergen-free environment (shared kitchen)",
                    "recommendations": "For severe allergies, consider our private kitchen events",
                    "no_extra_charge": "Standard dietary modifications included; custom menus may incur additional cost",
                },
            },
        }

        policy = policies.get(policy_name)

        if not policy:
            return {"success": False, "result": None, "error": f"Policy not found: {policy_name}"}

        return {"success": True, "result": policy}

    async def _calculate_pricing(self, args: dict[str, Any]) -> dict[str, Any]:
        """Calculate detailed pricing"""

        package = args["package"]
        num_guests = args["num_guests"]
        addons = args.get("addons", [])
        travel_distance = args.get("travel_distance", 0)
        args.get("is_peak_season", False)

        # Base pricing
        base_prices = {"standard": 45, "premium": 65, "deluxe": 85}
        base_cost = base_prices[package] * num_guests

        # Add-ons
        addon_costs = {
            "extra_protein": 15 * num_guests,
            "sushi_station": 20 * num_guests,
            "sake_bar": 400,
            "extended_time": 200,  # per hour
        }

        addons_cost = sum(addon_costs.get(addon, 0) for addon in addons)

        # Travel fee
        travel_fee = 0
        if travel_distance > 50:
            if travel_distance <= 100:
                travel_fee = (travel_distance - 50) * 3  # $3/mile over 50
            else:
                travel_fee = 150 + ((travel_distance - 100) * 5)  # Custom quote

        # Volume discount
        discount = 0
        discount_reason = None
        if num_guests >= 100:
            discount = (base_cost + addons_cost) * 0.15
            discount_reason = "15% volume discount (100+ guests)"
        elif num_guests >= 75:
            discount = (base_cost + addons_cost) * 0.10
            discount_reason = "10% volume discount (75+ guests)"

        # Calculate totals
        subtotal = base_cost + addons_cost + travel_fee
        total = subtotal - discount
        deposit = total * 0.5

        return {
            "success": True,
            "result": {
                "breakdown": {
                    "package": {
                        "name": package.title(),
                        "guests": num_guests,
                        "price_per_person": f"${base_prices[package]}",
                        "subtotal": f"${base_cost:,.2f}",
                    },
                    "addons": [
                        {"name": addon, "cost": f"${addon_costs[addon]:,.2f}"} for addon in addons
                    ],
                    "addons_total": f"${addons_cost:,.2f}",
                    "travel_fee": f"${travel_fee:,.2f}" if travel_fee > 0 else "Included",
                    "subtotal": f"${subtotal:,.2f}",
                    "discount": f"-${discount:,.2f}" if discount > 0 else "$0.00",
                    "discount_reason": discount_reason,
                },
                "total": f"${total:,.2f}",
                "deposit_required": f"${deposit:,.2f} (50%)",
                "balance_due": f"${total - deposit:,.2f}",
                "per_person_effective": f"${total / num_guests:.2f}",
                "notes": [
                    "Deposit due within 48 hours of booking",
                    "Balance due 24 hours before event",
                    "Prices valid for 30 days",
                ],
            },
        }

    async def _find_faq_answer(self, args: dict[str, Any]) -> dict[str, Any]:
        """Search FAQ database"""

        question = args["question"].lower()
        category = args.get("category", "general")

        # Mock FAQ database
        faqs = [
            {
                "category": "booking",
                "question": "How far in advance should I book?",
                "answer": "We recommend booking 30-45 days in advance for weekends and peak season (May-September), and 14-21 days for weekdays and off-season. Last-minute bookings (less than 7 days) may be possible with a rush fee.",
                "related": ["What's your availability?", "Do you charge rush fees?"],
            },
            {
                "category": "pricing",
                "question": "What's included in the package price?",
                "answer": "All packages include: hibachi chef performance, all food (protein, fried rice, vegetables), cooking equipment, setup and breakdown, plates/utensils, and cleanup. We bring everything - you just provide the space and guests!",
                "related": ["Do I need to provide anything?", "What add-ons are available?"],
            },
            {
                "category": "menu",
                "question": "Can you accommodate dietary restrictions?",
                "answer": "Yes! We handle vegetarian, vegan, gluten-free, and most allergies regularly. Please notify us at least 7 days before your event so we can prepare properly. For severe allergies, we use separate equipment and prep areas.",
                "related": [
                    "Do you charge extra for dietary accommodations?",
                    "Can you do kosher/halal?",
                ],
            },
            {
                "category": "logistics",
                "question": "What do you need from the venue?",
                "answer": "We need: (1) access to a standard electrical outlet, (2) flat surface area of at least 10x10 feet, (3) setup time of 1 hour before event, (4) water access nearby (for cleanup). For outdoor events, we also need a covered backup area.",
                "related": ["Can you do outdoor events?", "Do you need a kitchen?"],
            },
            {
                "category": "policies",
                "question": "What's your cancellation policy?",
                "answer": "Full refund for cancellations 14+ days before event, 50% refund for 7-13 days, no refund less than 7 days (but we offer event credit). We understand emergencies happen and will work with you on extenuating circumstances.",
                "related": ["Can I reschedule my event?", "What if there's bad weather?"],
            },
        ]

        # Simple keyword matching (in production, would use semantic search)
        matches = []
        for faq in faqs:
            if category == "general" or faq["category"] == category:
                if any(word in faq["question"].lower() for word in question.split()):
                    matches.append(faq)

        if not matches:
            # Return top 3 from category
            matches = [f for f in faqs if f["category"] == category][:3]

        return {
            "success": True,
            "result": {
                "matches_found": len(matches),
                "faqs": matches,
                "source": "MyHibachi FAQ Database (updated October 2024)",
            },
        }
