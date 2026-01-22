"""
Operations Agent - Logistics, scheduling & practical problem-solving

Specializes in:
- Booking management
- Schedule coordination
- Equipment logistics
- Status tracking
- Practical problem-solving

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OperationsAgent(BaseAgent):
    """
    Operations Agent - Handle logistics, scheduling, and practical execution.

    Expertise:
    - Calendar management (availability, conflicts, bookings)
    - Equipment logistics (what's needed, where, when)
    - Travel coordination (routes, timing, setup requirements)
    - Status tracking (order updates, chef assignments)
    - Practical problem-solving (can we do X? How do we handle Y?)

    Tools:
    - check_availability: Check chef/equipment availability
    - create_booking: Create new booking
    - update_booking: Modify existing booking
    - assign_chef: Assign chef to event

    Usage:
        agent = OperationsAgent()
        response = await agent.process(
            message="Can you check if Dec 15th is available?",
            context={"conversation_id": "123"}
        )
    """

    def __init__(self, provider=None):
        """
        Initialize Operations Agent.

        Args:
            provider: Optional ModelProvider instance (for DI, None = lazy load from container)
        """
        super().__init__(
            agent_type="operations",
            provider=provider,  # Pass to base class
            temperature=0.4,
            max_tokens=400,  # Very consistent, factual
        )

    def get_system_prompt(self, context: dict[str, Any] = None) -> str:
        """
        Build system prompt with tone adaptation (Week 1: AI Hospitality Training).

        Args:
            context: Request context with tone and business knowledge
        """
        # Week 1: Extract tone information
        customer_tone = context.get("customer_tone", "casual") if context else "casual"
        tone_guidelines = context.get("tone_guidelines", {}) if context else {}

        # Week 4: Extract DYNAMIC knowledge context from database
        knowledge_context = context.get("knowledge_context", "") if context else ""

        # Get tone-specific instructions
        tone_style = tone_guidelines.get("style", "Clear and professional")

        base_prompt = f"""You are the operations coordinator for MyHibachi, responsible for logistics, scheduling, and practical execution.

Your mission: Ensure every event runs flawlessly through precise planning and proactive problem-solving.

**🎭 CUSTOMER TONE DETECTED: {customer_tone.upper()}**
**Response Style**: {tone_style}

⚠️ ADAPT: While maintaining operational precision, adjust your communication style to match the customer's tone.

**Core Responsibilities:**
1. **Calendar Management** - Check availability, prevent double-bookings, optimize schedules
2. **Equipment Logistics** - Ensure right equipment at right place at right time
3. **Chef Coordination** - Match chefs to events based on skills, availability, location
4. **Status Tracking** - Keep customers informed of booking status, chef assignments, preparations
5. **Problem-Solving** - Find practical solutions to logistical challenges

**Communication Style** (Adapted to {customer_tone}):\n"""

        if customer_tone == "formal":
            base_prompt += """- Professional and detailed
- Use complete sentences and proper formatting
- Structured responses with clear sections
- Formal confirmation language"""
        elif customer_tone == "casual":
            base_prompt += """- Friendly but still precise
- Conversational while maintaining accuracy
- It's okay to be personable
- Keep facts clear, tone warm"""
        elif customer_tone == "direct":
            base_prompt += """- Ultra-concise, bullet points
- Lead with key facts (date, time, cost)
- Minimal explanation unless asked
- Action-oriented language"""
        elif customer_tone == "warm":
            base_prompt += """- Enthusiastic about their event
- Personal touches while staying factual
- Show excitement for their special day
- Warm confirmations and reassurances"""
        else:  # anxious
            base_prompt += """- Extra reassurance and detail
- Patient explanations
- Confirm multiple times if needed
- Reduce uncertainty with specifics"""

        # Week 4: Inject DYNAMIC knowledge from database
        if knowledge_context:
            base_prompt += f"\n\n{knowledge_context}"
        else:
            base_prompt += """

**Key Information:**

**Service Areas:**
- Primary: 50-mile radius from headquarters (no travel fee)
- Extended: 51-100 miles (travel fee: $100-300 based on distance)
- Special: 100+ miles (case-by-case, requires advance booking)

**Availability:**
- Peak season: May-September (book 30+ days in advance)
- Off-season: October-April (book 14+ days in advance)
- Weekends: Book 45+ days in advance (high demand)
- Weekdays: More flexible, often 7-14 days sufficient

**Equipment Required:**
- Standard events (20-50 guests): 1-2 griddles, 1 chef
- Large events (51-100 guests): 2-3 griddles, 2 chefs
- Extra large (100+): Custom setup, 3+ chefs

**Timing:**
- Setup time: 1 hour before event start
- Event duration: 2 hours standard (can extend for $200/hr)
- Breakdown: 30 minutes after event
- Total time on-site: ~3.5 hours

**Chef Assignments:**
- Match skill level to event type (corporate = experienced chefs)
- Consider dietary restrictions (vegetarian chef for large vegetarian groups)
- Location proximity (reduce travel time)
- Customer preferences (returning customers may request specific chefs)

**Common Scenarios:**

**1. Availability Check:**
"Let me check our calendar for [date]. [Check availability]. We have [X] chefs and [Y] equipment sets available. For your event of [Z] guests, we'd need [requirements]. I can hold this date for you for 48 hours while you finalize details."

**2. Booking Creation:**
"Perfect! Here's what I'll need to create your booking:
- Event date and time
- Number of guests
- Event location and address
- Package selection
- Any dietary restrictions
- Contact information
Once you confirm, I'll send a booking confirmation with your $100 deposit invoice."

**3. Schedule Change:**
"I understand you need to change the date. Let me check what options are available. [Check availability]. I can offer you [alternative dates]. There's no charge for date changes if made 14+ days before the original event. Would any of these work for you?"

**4. Special Requests:**
"You mentioned [special request]. Here's what we can do:
- Feasibility: [Yes/No with reasoning]
- Requirements: [What's needed]
- Additional cost: [If any]
- Timeline: [When to confirm by]
Would you like me to add this to your booking?"

**5. Status Updates:**
"Your event status:
- Booking: Confirmed ✓
- Deposit: Received ✓
- Chef: [Name] assigned ✓
- Equipment: Reserved ✓
- Setup time: [Time]
Everything is on track! I'll send you a reminder 3 days before with final details."

**Constraints & Policies:**
- Minimum booking: 20 guests (below this, suggest private dining option)
- Maximum per event: 150 guests (above this, requires multiple chefs/setups)
- Weather policy: Indoor events preferred; outdoor requires backup plan
- Venue requirements: Access to electricity (standard outlet), flat surface (10x10 ft minimum)
- Cancellation: Full refund if canceled 4+ days before event, non-refundable within 4 days
- Rescheduling: One free reschedule if requested 24+ hours before event, $200 fee for additional reschedules

**Problem-Solving Examples:**

**Problem:** "We have 75 guests but only 1 chef available that day"
**Solution:** "I can bring in a backup chef from our extended team. This adds $400 to ensure we have adequate coverage for 75 guests. Alternatively, we could split into two smaller groups with staggered timing."

**Problem:** "Customer wants event in 3 days"
**Solution:** "Our standard booking window is 14 days, but let me see if I can accommodate this as a rush booking. We have [Chef X] available and equipment on hand. I can make this work for a $300 rush fee to prioritize your event. Does that work?"

**Problem:** "Venue is outdoors, 80% chance of rain"
**Solution:** "For outdoor events, we require a covered backup area (tent or indoor space) due to electrical equipment. If you can confirm a backup location, we're good to go. Otherwise, I'd recommend rescheduling to a date with better weather forecast."

**Tools Usage:**
- Use `check_availability` for all date-related inquiries
- Use `create_booking` when customer confirms all details
- Use `update_booking` for changes to existing bookings
- Use `assign_chef` when confirming chef assignments

**Escalation:**
- Refer sales/pricing questions to Lead Nurturing Agent
- Refer complaints to Customer Care Agent
- Refer technical questions to Knowledge Agent
- Handle all logistics, scheduling, operations yourself

**Remember:**
- Be precise with dates, times, numbers
- Confirm understanding before making changes
- Proactively mention requirements (venue, access, timing)
- Set clear expectations (what happens next, timelines)
- Always have a backup plan for logistical challenges
- ADAPT YOUR TONE to match the customer while maintaining operational accuracy
"""

        return base_prompt

    def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": "Check chef and equipment availability for a date",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_date": {
                                "type": "string",
                                "description": "Event date (YYYY-MM-DD)",
                            },
                            "event_time": {
                                "type": "string",
                                "description": "Event start time (HH:MM AM/PM)",
                            },
                            "num_guests": {
                                "type": "integer",
                                "description": "Number of guests",
                            },
                            "location": {
                                "type": "string",
                                "description": "Event location (city or zip code)",
                            },
                        },
                        "required": ["event_date"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_booking",
                    "description": "Create a new booking in the system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_name": {
                                "type": "string",
                                "description": "Customer's full name",
                            },
                            "customer_email": {
                                "type": "string",
                                "description": "Customer's email address",
                            },
                            "customer_phone": {
                                "type": "string",
                                "description": "Customer's phone number",
                            },
                            "event_date": {
                                "type": "string",
                                "description": "Event date (YYYY-MM-DD)",
                            },
                            "event_time": {
                                "type": "string",
                                "description": "Event start time (HH:MM AM/PM)",
                            },
                            "num_guests": {
                                "type": "integer",
                                "description": "Number of guests",
                            },
                            "package": {
                                "type": "string",
                                "enum": ["standard", "premium", "deluxe"],
                                "description": "Selected package",
                            },
                            "location_address": {
                                "type": "string",
                                "description": "Full event address",
                            },
                            "special_requests": {
                                "type": "string",
                                "description": "Any special requests or dietary restrictions",
                            },
                        },
                        "required": [
                            "customer_name",
                            "customer_email",
                            "customer_phone",
                            "event_date",
                            "num_guests",
                            "package",
                            "location_address",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_booking",
                    "description": "Update an existing booking",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Booking order ID",
                            },
                            "changes": {
                                "type": "object",
                                "description": "Fields to update (event_date, event_time, num_guests, etc.)",
                                "properties": {
                                    "event_date": {"type": "string"},
                                    "event_time": {"type": "string"},
                                    "num_guests": {"type": "integer"},
                                    "package": {"type": "string"},
                                    "special_requests": {"type": "string"},
                                },
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for change",
                            },
                        },
                        "required": ["order_id", "changes"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "assign_chef",
                    "description": "Assign a chef to an event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "Booking order ID",
                            },
                            "chef_preference": {
                                "type": "string",
                                "description": "Preferred chef name or 'auto' for automatic assignment",
                            },
                            "requirements": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Special chef requirements (vegetarian_expert, corporate_experience, etc.)",
                            },
                        },
                        "required": ["order_id"],
                    },
                },
            },
        ]

    async def process_tool_call(
        self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool functions"""

        try:
            if tool_name == "check_availability":
                return await self._check_availability(arguments)

            elif tool_name == "create_booking":
                return await self._create_booking(arguments, context)

            elif tool_name == "update_booking":
                return await self._update_booking(arguments, context)

            elif tool_name == "assign_chef":
                return await self._assign_chef(arguments)

            else:
                return {
                    "success": False,
                    "result": None,
                    "error": f"Unknown tool: {tool_name}",
                }

        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}", exc_info=True)
            return {"success": False, "result": None, "error": str(e)}

    # ===== Tool Implementations =====

    async def _check_availability(self, args: dict[str, Any]) -> dict[str, Any]:
        """Check availability for date"""

        event_date = args["event_date"]
        event_time = args.get("event_time", "6:00 PM")
        num_guests = args.get("num_guests", 50)
        location = args.get("location", "Unknown")

        # TODO: Integrate with actual calendar system
        # This is a mock implementation

        import random
        from datetime import datetime

        # Parse date
        date_obj = datetime.strptime(event_date, "%Y-%m-%d")
        day_of_week = date_obj.strftime("%A")

        # Simulate availability (random for demo)
        is_weekend = day_of_week in ["Saturday", "Sunday"]
        is_peak_season = date_obj.month in [5, 6, 7, 8, 9]

        # Calculate available resources
        chefs_needed = 1 if num_guests <= 50 else 2
        chefs_available = (
            random.randint(2, 5) if not is_weekend else random.randint(0, 3)
        )
        equipment_sets_available = random.randint(1, 4)

        is_available = chefs_available >= chefs_needed and equipment_sets_available >= 1

        result = {
            "event_date": event_date,
            "day_of_week": day_of_week,
            "event_time": event_time,
            "location": location,
            "num_guests": num_guests,
            "is_available": is_available,
            "chefs_available": chefs_available,
            "chefs_needed": chefs_needed,
            "equipment_sets_available": equipment_sets_available,
            "peak_season": is_peak_season,
            "booking_deadline": "ASAP" if is_weekend else "14 days before",
            "alternative_dates": [],
        }

        # Suggest alternatives if not available
        if not is_available:
            result["alternative_dates"] = [
                {"date": "2024-12-16", "day": "Monday", "availability": "High"},
                {"date": "2024-12-20", "day": "Friday", "availability": "Medium"},
                {"date": "2024-12-22", "day": "Sunday", "availability": "Low"},
            ]

        return {"success": True, "result": result}

    async def _create_booking(
        self, args: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Create new booking"""

        # Extract all booking details
        booking = {
            "order_id": f"ORD-2024-{random.randint(1000, 9999)}",
            "customer_name": args["customer_name"],
            "customer_email": args["customer_email"],
            "customer_phone": args["customer_phone"],
            "event_date": args["event_date"],
            "event_time": args["event_time"],
            "num_guests": args["num_guests"],
            "package": args["package"],
            "location_address": args["location_address"],
            "special_requests": args.get("special_requests", "None"),
            "status": "Pending Deposit",
            "created_at": "2024-10-31T10:30:00Z",
            "deposit_amount": 0,
            "total_amount": 0,
        }

        # Calculate pricing
        base_prices = {"standard": 45, "premium": 65, "deluxe": 85}
        total = base_prices[args["package"]] * args["num_guests"]
        deposit = total * 0.5

        booking["total_amount"] = total
        booking["deposit_amount"] = deposit

        logger.info(f"Booking created: {booking['order_id']}")

        return {
            "success": True,
            "result": {
                "booking": booking,
                "next_steps": [
                    f"Invoice sent to {args['customer_email']}",
                    "Deposit due: $100.00 (fixed)",
                    "Payment link included in email",
                    "Booking confirmed upon deposit receipt",
                    "Final balance due on event day",
                ],
                "confirmation": f"Booking #{booking['order_id']} created successfully!",
            },
        }

    async def _update_booking(
        self, args: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Update existing booking"""

        order_id = args["order_id"]
        changes = args["changes"]
        reason = args.get("reason", "Customer request")

        # TODO: Integrate with actual database
        # This is a mock implementation

        import random

        # Calculate if fees apply
        has_fee = False
        fee_amount = 0

        if "event_date" in changes:
            # Date changes may incur fees
            has_fee = random.choice([True, False])
            fee_amount = 200 if has_fee else 0

        updated_fields = list(changes.keys())

        result = {
            "order_id": order_id,
            "updated_fields": updated_fields,
            "changes": changes,
            "reason": reason,
            "fee_applied": has_fee,
            "fee_amount": f"${fee_amount}" if has_fee else "$0",
            "updated_at": "2024-10-31T10:30:00Z",
            "confirmation": f"Booking #{order_id} updated successfully!",
        }

        if has_fee:
            result["note"] = "Change fee applies due to less than 14 days notice"

        return {"success": True, "result": result}

    async def _assign_chef(self, args: dict[str, Any]) -> dict[str, Any]:
        """Assign chef to event"""

        order_id = args["order_id"]
        chef_preference = args.get("chef_preference", "auto")
        requirements = args.get("requirements", [])

        # TODO: Integrate with chef scheduling system
        # This is a mock implementation

        # Available chefs (mock data)
        chefs = [
            {
                "name": "Chef Mike",
                "specialties": ["corporate_experience", "large_events"],
                "rating": 4.9,
                "events_completed": 250,
            },
            {
                "name": "Chef Sarah",
                "specialties": ["vegetarian_expert", "dietary_accommodations"],
                "rating": 4.8,
                "events_completed": 180,
            },
            {
                "name": "Chef Tom",
                "specialties": ["entertainment_focus", "family_events"],
                "rating": 4.7,
                "events_completed": 200,
            },
        ]

        # Auto-assign based on requirements
        if chef_preference == "auto":
            # Match requirements
            best_match = chefs[0]  # Default

            for chef in chefs:
                if any(req in chef["specialties"] for req in requirements):
                    best_match = chef
                    break

            assigned_chef = best_match
        else:
            # Find requested chef
            assigned_chef = next(
                (c for c in chefs if c["name"].lower() == chef_preference.lower()),
                chefs[0],
            )

        result = {
            "order_id": order_id,
            "chef_assigned": assigned_chef["name"],
            "chef_rating": assigned_chef["rating"],
            "chef_experience": f"{assigned_chef['events_completed']} events",
            "chef_specialties": assigned_chef["specialties"],
            "assignment_date": "2024-10-31T10:30:00Z",
            "confirmation": f"{assigned_chef['name']} assigned to booking #{order_id}",
        }

        return {"success": True, "result": result}


import random  # Add at top of file for mock implementations
