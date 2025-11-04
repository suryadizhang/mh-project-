"""
Lead Nurturing Agent - Sales psychology & conversion optimization

Specializes in:
- Upselling and cross-selling
- Product recommendations
- Pricing strategy
- Conversion optimization
- Sales psychology

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class LeadNurturingAgent(BaseAgent):
    """
    Lead Nurturing Agent - Maximize conversions and revenue.

    Expertise:
    - Sales psychology (urgency, scarcity, social proof)
    - Product recommendations based on needs
    - Upselling strategies (premium packages, add-ons)
    - Pricing optimization (bundles, discounts)
    - Objection handling (price, timing, competitors)

    Tools:
    - get_product_recommendations: AI-powered product matching
    - calculate_bundle_discount: Dynamic pricing for bundles
    - check_promotion: Active promotions and offers
    - estimate_event_cost: Event pricing calculator

    Usage:
        agent = LeadNurturingAgent()
        response = await agent.process(
            message="I'm interested in catering for 50 people",
            context={"conversation_id": "123", "channel": "webchat"}
        )
    """

    def __init__(self, provider=None):
        """
        Initialize Lead Nurturing Agent.

        Args:
            provider: Optional ModelProvider instance (for DI, None = lazy load from container)
        """
        super().__init__(
            agent_type="lead_nurturing",
            provider=provider,  # Pass to base class
            temperature=0.8,  # More creative for sales
            max_tokens=600,  # Longer responses for explanations
        )

    def get_system_prompt(self) -> str:
        return """You are an expert sales consultant for MyHibachi, a premium hibachi catering company.

Your mission: Convert inquiries into bookings while maximizing revenue through strategic upselling.

**Core Principles:**
1. **Consultative Selling** - Ask questions to understand needs before recommending
2. **Value-Based Pricing** - Emphasize quality, experience, and memories over price
3. **Urgency & Scarcity** - Mention limited availability, peak season demand
4. **Social Proof** - Reference happy customers, repeat clients, event success stories
5. **Upsell Naturally** - Suggest premium options as enhancements, not replacements

**Communication Style:**
- Enthusiastic but professional
- Use sensory language (sizzling steaks, theatrical knife skills, aromatic fried rice)
- Paint a picture of the experience, not just the food
- Address objections proactively (worth the investment, flexible payment plans)

**Product Knowledge:**
- **Standard Package**: $45/person - Hibachi chicken or steak, fried rice, vegetables, show
- **Premium Package**: $65/person - Filet mignon + lobster tail, premium sides, chef's signature dishes
- **Deluxe Package**: $85/person - Full premium menu, multiple chefs, extended performance
- **Add-ons**: Extra protein (+$15), sushi station (+$20/person), sake bar (+$300)
- **Minimum**: 20 guests for standard, 30 for premium events

**Upselling Strategy:**
1. Start with needs assessment (occasion, guests, budget, preferences)
2. Recommend base package that fits
3. Suggest 1-2 premium upgrades that enhance their event
4. Use "And for just $X more..." framing
5. Create urgency (calendar filling up, seasonal pricing)

**Example Responses:**
- Customer: "How much for 50 people?"
  You: "Great question! For 50 guests, our Standard Package starts at $2,250 total. That includes a full hibachi experience with your choice of chicken or steak, fried rice, vegetables, and our signature chef performance. Many clients celebrating special occasions opt for our Premium Package at $3,250 - it adds filet mignon and lobster tail for that unforgettable 'wow' factor. What's the occasion?"

- Customer: "That's expensive."
  You: "I totally understand - let me share why our clients say it's worth every penny. You're not just getting food, you're getting a 2-hour interactive entertainment experience that becomes the highlight of your event. Our chefs perform tricks, engage guests, and create memories. Compare that to a standard catering service - similar food costs with zero entertainment. Plus, we include setup, cleanup, and equipment. Most clients tell us their guests are STILL talking about it months later. For a once-in-a-lifetime event, would you rather save $500 or create unforgettable memories?"

**Tools Usage:**
- Use `get_product_recommendations` when customer shares event details
- Use `calculate_bundle_discount` for large parties (75+ guests)
- Use `check_promotion` to offer seasonal discounts
- Use `estimate_event_cost` for complex custom quotes

**Constraints:**
- Never discount below 10% without approval
- Always mention 50% deposit required to book
- Peak season (May-Sept) has 30-day booking lead time
- Off-season discounts up to 15% (Oct-Apr, weekday events)
- Be honest about availability and alternatives

**Objection Handling:**
- **Price**: Emphasize experience value, payment plans, compare to alternatives
- **Availability**: Offer alternative dates, suggest booking early for next event
- **Menu**: Highlight customization, dietary accommodations, tasting options
- **Trust**: Share testimonials, offer references, mention 5-star reviews

Remember: You're selling an EXPERIENCE, not just a meal. Every conversation should move toward booking."""

    def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_product_recommendations",
                    "description": "Get personalized package recommendations based on event details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "num_guests": {
                                "type": "integer",
                                "description": "Number of guests attending",
                            },
                            "occasion": {
                                "type": "string",
                                "description": "Event type (birthday, corporate, wedding, etc.)",
                            },
                            "budget_range": {
                                "type": "string",
                                "enum": ["budget", "standard", "premium", "luxury"],
                                "description": "Customer's budget indication",
                            },
                            "preferences": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Special requests (vegetarian, seafood, entertainment, etc.)",
                            },
                        },
                        "required": ["num_guests", "occasion"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_bundle_discount",
                    "description": "Calculate discounted pricing for large parties or multiple events",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package": {
                                "type": "string",
                                "enum": ["standard", "premium", "deluxe"],
                                "description": "Base package selected",
                            },
                            "num_guests": {"type": "integer", "description": "Number of guests"},
                            "addons": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Selected add-ons (extra_protein, sushi_station, sake_bar)",
                            },
                            "apply_discount": {
                                "type": "boolean",
                                "description": "Apply volume discount (75+ guests or multi-event)",
                            },
                        },
                        "required": ["package", "num_guests"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_promotion",
                    "description": "Check active promotions and seasonal discounts",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_date": {
                                "type": "string",
                                "description": "Proposed event date (YYYY-MM-DD)",
                            },
                            "is_weekday": {
                                "type": "boolean",
                                "description": "Is event on a weekday (Mon-Thu)?",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "estimate_event_cost",
                    "description": "Generate detailed cost estimate with breakdown",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package": {
                                "type": "string",
                                "enum": ["standard", "premium", "deluxe"],
                                "description": "Selected package",
                            },
                            "num_guests": {"type": "integer", "description": "Number of guests"},
                            "addons": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Selected add-ons",
                            },
                            "duration_hours": {
                                "type": "number",
                                "description": "Event duration (standard is 2 hours)",
                            },
                        },
                        "required": ["package", "num_guests"],
                    },
                },
            },
        ]

    async def process_tool_call(
        self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool functions"""

        try:
            if tool_name == "get_product_recommendations":
                return await self._get_product_recommendations(arguments)

            elif tool_name == "calculate_bundle_discount":
                return await self._calculate_bundle_discount(arguments)

            elif tool_name == "check_promotion":
                return await self._check_promotion(arguments)

            elif tool_name == "estimate_event_cost":
                return await self._estimate_event_cost(arguments)

            else:
                return {"success": False, "result": None, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}", exc_info=True)
            return {"success": False, "result": None, "error": str(e)}

    # ===== Tool Implementations =====

    async def _get_product_recommendations(self, args: dict[str, Any]) -> dict[str, Any]:
        """Recommend packages based on event details"""

        num_guests = args["num_guests"]
        occasion = args["occasion"].lower()
        budget_range = args.get("budget_range", "standard")
        preferences = args.get("preferences", [])

        recommendations = []

        # Base package recommendation
        if budget_range == "luxury" or "premium" in preferences:
            base = {
                "package": "Deluxe Package",
                "price_per_person": 85,
                "total": 85 * num_guests,
                "features": [
                    "Full premium menu (filet mignon + lobster tail + wagyu beef)",
                    "Multiple chefs for larger parties",
                    "Extended 2.5-hour performance",
                    "Premium sake tasting",
                    "Custom menu consultation",
                ],
                "best_for": "Luxury events, corporate VIP, milestone celebrations",
            }
        elif budget_range == "premium" or occasion in ["wedding", "corporate", "anniversary"]:
            base = {
                "package": "Premium Package",
                "price_per_person": 65,
                "total": 65 * num_guests,
                "features": [
                    "Filet mignon + lobster tail combo",
                    "Premium fried rice with extra vegetables",
                    "Chef's signature dishes",
                    "Professional-grade entertainment",
                    "Complimentary sake shots",
                ],
                "best_for": "Special occasions, corporate events, weddings",
            }
        else:
            base = {
                "package": "Standard Package",
                "price_per_person": 45,
                "total": 45 * num_guests,
                "features": [
                    "Hibachi chicken or steak (guest's choice)",
                    "Signature fried rice",
                    "Seasonal vegetables",
                    "Full chef performance with tricks",
                    "Includes setup and cleanup",
                ],
                "best_for": "Birthday parties, family gatherings, casual events",
            }

        recommendations.append(base)

        # Suggest add-ons
        addons = []

        if "seafood" in preferences or occasion in ["wedding", "anniversary"]:
            addons.append(
                {
                    "name": "Sushi Station",
                    "price": f"${20 * num_guests} ({num_guests} guests × $20)",
                    "description": "Professional sushi chef, California rolls, spicy tuna, salmon nigiri",
                }
            )

        if num_guests >= 40:
            addons.append(
                {
                    "name": "Extra Protein Station",
                    "price": f"${15 * num_guests} additional",
                    "description": "Add shrimp or scallops to every plate",
                }
            )

        if occasion in ["corporate", "wedding"] or num_guests >= 50:
            addons.append(
                {
                    "name": "Premium Sake Bar",
                    "price": "$300-500",
                    "description": "Curated sake selection with tasting notes, bartender included",
                }
            )

        # Special notes
        notes = []

        if num_guests < 20:
            notes.append(
                "⚠️ Minimum 20 guests required. Consider inviting more or choosing our private dining option."
            )

        if num_guests >= 75:
            notes.append("🎉 Volume discount available! 10% off for 75+ guests.")

        if occasion == "wedding":
            notes.append(
                "💍 Wedding package: Complimentary cake cutting service + champagne toast setup"
            )

        return {
            "success": True,
            "result": {
                "recommendations": recommendations,
                "suggested_addons": addons,
                "notes": notes,
                "next_steps": [
                    "Discuss menu customization options",
                    "Check calendar availability for your date",
                    "Schedule a tasting appointment (for Premium+)",
                ],
            },
        }

    async def _calculate_bundle_discount(self, args: dict[str, Any]) -> dict[str, Any]:
        """Calculate pricing with discounts"""

        package = args["package"]
        num_guests = args["num_guests"]
        addons = args.get("addons", [])
        apply_discount = args.get("apply_discount", False)

        # Base pricing
        base_prices = {"standard": 45, "premium": 65, "deluxe": 85}

        addon_prices = {
            "extra_protein": 15 * num_guests,
            "sushi_station": 20 * num_guests,
            "sake_bar": 400,
        }

        base_total = base_prices[package] * num_guests
        addons_total = sum(addon_prices.get(addon, 0) for addon in addons)
        subtotal = base_total + addons_total

        # Apply discounts
        discount_rate = 0
        discount_reason = ""

        if apply_discount:
            if num_guests >= 100:
                discount_rate = 0.15
                discount_reason = "15% volume discount (100+ guests)"
            elif num_guests >= 75:
                discount_rate = 0.10
                discount_reason = "10% volume discount (75+ guests)"

        discount_amount = subtotal * discount_rate
        final_total = subtotal - discount_amount

        # Deposit
        deposit = final_total * 0.5

        return {
            "success": True,
            "result": {
                "package": package.title(),
                "num_guests": num_guests,
                "breakdown": {
                    "base_package": f"${base_total:,.2f}",
                    "addons": f"${addons_total:,.2f}",
                    "subtotal": f"${subtotal:,.2f}",
                    "discount": f"-${discount_amount:,.2f}" if discount_amount > 0 else "$0.00",
                    "discount_reason": discount_reason,
                },
                "total": f"${final_total:,.2f}",
                "deposit_required": f"${deposit:,.2f} (50%)",
                "balance_due": f"${final_total - deposit:,.2f} (day of event)",
                "per_person_effective": f"${final_total / num_guests:.2f}",
            },
        }

    async def _check_promotion(self, args: dict[str, Any]) -> dict[str, Any]:
        """Check active promotions"""

        from datetime import datetime

        args.get("event_date")
        is_weekday = args.get("is_weekday", False)

        promotions = []

        # Parse date if provided
        current_month = datetime.now().month

        # Off-season discount (Oct-Apr)
        if current_month in [10, 11, 12, 1, 2, 3, 4]:
            promotions.append(
                {
                    "name": "Off-Season Special",
                    "discount": "15% off",
                    "conditions": "Valid Oct-Apr, weekday events only",
                    "code": "WINTER2025",
                }
            )

        # Weekday discount
        if is_weekday:
            promotions.append(
                {
                    "name": "Weekday Discount",
                    "discount": "10% off",
                    "conditions": "Monday-Thursday events only",
                    "code": "WEEKDAY10",
                }
            )

        # Holiday specials
        if current_month == 11:
            promotions.append(
                {
                    "name": "Thanksgiving Gathering Special",
                    "discount": "$200 off",
                    "conditions": "Book by Nov 30th for any 2025 event",
                    "code": "THANKS2025",
                }
            )

        # Always available
        promotions.append(
            {
                "name": "Referral Bonus",
                "discount": "$150 credit",
                "conditions": "Refer a friend who books (you both get $150)",
                "code": "REFER150",
            }
        )

        promotions.append(
            {
                "name": "Multi-Event Package",
                "discount": "20% off 2nd event",
                "conditions": "Book 2+ events within 6 months",
                "code": "MULTI20",
            }
        )

        return {
            "success": True,
            "result": {
                "active_promotions": promotions,
                "note": "Promotions cannot be combined. Best available discount will be applied automatically.",
            },
        }

    async def _estimate_event_cost(self, args: dict[str, Any]) -> dict[str, Any]:
        """Generate detailed cost estimate"""

        package = args["package"]
        num_guests = args["num_guests"]
        addons = args.get("addons", [])
        duration_hours = args.get("duration_hours", 2.0)

        # Calculate everything
        bundle_result = await self._calculate_bundle_discount(
            {
                "package": package,
                "num_guests": num_guests,
                "addons": addons,
                "apply_discount": num_guests >= 75,
            }
        )

        # Additional costs
        extras = []

        if duration_hours > 2:
            extra_hours = duration_hours - 2
            extra_cost = extra_hours * 200
            extras.append(
                {"item": f"Extended time ({extra_hours} hour)", "cost": f"${extra_cost:,.2f}"}
            )

        # Build estimate
        estimate = {
            "package_details": bundle_result["result"],
            "additional_services": extras,
            "included_services": [
                "Professional hibachi chef(s)",
                "All cooking equipment and griddles",
                "Complete setup and breakdown",
                "Dinnerware, napkins, and utensils",
                "Chef performance and entertainment",
                "On-site coordination",
                "General liability insurance",
            ],
            "not_included": [
                "Service area outside 50-mile radius (travel fee applies)",
                "Alcohol beyond complimentary sake shots (can add sake bar)",
                "Special dietary meals beyond standard modifications",
                "Event venue rental (we bring equipment to your location)",
            ],
            "payment_terms": {
                "deposit": "50% required to secure booking",
                "balance": "Due 24 hours before event",
                "accepted": "Credit card, check, Venmo, Zelle",
                "cancellation": "Full refund if cancelled 14+ days before event",
            },
        }

        return {"success": True, "result": estimate}
