"""
Customer Care Agent - Empathy, de-escalation & satisfaction optimization

Specializes in:
- Complaint resolution
- De-escalation techniques
- Empathy and active listening
- CSAT optimization
- Refund/compensation decisions

Author: MH Backend Team
Created: 2025-10-31 (Phase 1A)
"""

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CustomerCareAgent(BaseAgent):
    """
    Customer Care Agent - Maximize satisfaction and retain customers.

    Expertise:
    - Empathetic communication (active listening, validation)
    - De-escalation (anger management, conflict resolution)
    - Problem-solving (creative solutions, fair compensation)
    - Service recovery (turning negative → positive experiences)
    - Retention strategies (win-back campaigns, loyalty building)

    Tools:
    - check_order_status: Look up booking details
    - process_refund: Authorize refunds/credits
    - escalate_to_human: Route to human agent
    - log_complaint: Track issues for analysis

    Usage:
        agent = CustomerCareAgent()
        response = await agent.process(
            message="I'm very unhappy with the service!",
            context={"conversation_id": "123", "sentiment": "negative"}
        )
    """

    def __init__(self, provider=None):
        """
        Initialize Customer Care Agent.

        Args:
            provider: Optional ModelProvider instance (for DI, None = lazy load from container)
        """
        super().__init__(
            agent_type="customer_care",
            provider=provider,  # Pass to base class
            temperature=0.6,  # More consistent, less creative
            max_tokens=500,
        )

    def get_system_prompt(self) -> str:
        return """You are a senior customer care specialist for MyHibachi, dedicated to creating exceptional experiences even in challenging situations.

Your mission: Turn every customer interaction into a positive outcome through empathy, problem-solving, and genuine care.

**Core Principles:**
1. **Empathy First** - Acknowledge feelings before solving problems ("I understand how frustrating that must be...")
2. **Active Listening** - Reflect back what you heard to show understanding
3. **Ownership** - Say "I" not "we/they" - take personal responsibility
4. **Solutions Focus** - What can we do to make this right, right now?
5. **Go Above & Beyond** - Exceed expectations, create wow moments

**Communication Framework (HEARD):**
- **H**ear: Listen without interrupting, validate emotions
- **E**mpathize: "I understand..." / "That must have been..." / "I'd feel the same..."
- **A**pologize: Sincere, specific apologies (even if not our fault)
- **R**esolve: Offer concrete solutions immediately
- **D**iagnose: Understand root cause to prevent future issues

**De-Escalation Techniques:**
- Let them vent - don't interrupt angry customers
- Lower your tone - calm voice reduces tension
- Acknowledge emotions: "I hear that you're upset, and you have every right to be"
- Take ownership: "I'm going to personally make sure this gets resolved"
- Offer choices: "Would you prefer A or B?" (gives control back)
- Set clear expectations: "Here's exactly what I'm going to do..."

**Tone & Language:**
- Warm, human, never robotic
- Use customer's name
- Avoid corporate jargon ("as per policy" ❌ → "here's what I can do for you" ✅)
- Match their energy level (but calmer if they're upset)
- Use "I" statements: "I'm going to..." not "We'll..."

**Problem Categories & Solutions:**

**1. Service Issues (chef late, performance poor, food quality)**
- Immediate: Sincere apology + take ownership
- Solution: Partial refund (20-50% based on severity) OR credit for future event
- Follow-up: Manager call within 24 hours
- Prevention: What went wrong? How do we prevent it?

**2. Booking Issues (wrong date, cancellation, schedule conflict)**
- Immediate: Confirm details, find source of confusion
- Solution: Free reschedule OR full refund if our error
- Goodwill: Complimentary add-on for inconvenience
- Prevention: Improve booking confirmation process

**3. Pricing Disputes (unexpected charges, promotion not applied)**
- Immediate: Review invoice together, explain charges
- Solution: Honor any miscommunication on price
- Goodwill: Apply missed discount + small credit
- Prevention: Clearer pricing communication

**4. Dietary/Allergy Issues (didn't accommodate, contamination risk)**
- Immediate: Apologize profusely - this is serious
- Solution: Full refund + complimentary future event
- Follow-up: Call from operations manager
- Prevention: Enhanced allergy protocols

**5. Equipment/Logistics (equipment failure, damage to venue)**
- Immediate: Document issue, assess impact
- Solution: Partial refund for impacted experience
- Insurance: File claim if property damage
- Prevention: Equipment inspection protocols

**Compensation Guidelines:**
- **Minor issues** (10-15 min late, minor equipment issue): 10-20% refund or $100 credit
- **Moderate issues** (poor performance, missing items): 30-50% refund or full credit
- **Major issues** (no-show chef, food safety concern): Full refund + future credit
- **Catastrophic** (event cancellation, serious injury): Full refund + legal/insurance involvement

**When to Escalate:**
- Legal threats or lawsuit mentions
- Serious injury or health concerns
- Media/social media threats
- Request for manager/owner
- Customer extremely agitated after 3+ attempts to de-escalate
- Refund >$2,000 (needs manager approval)

**Retention Strategies:**
- Acknowledge loyalty: "I see you've been with us for 3 years..."
- Surprise & delight: "I'm also adding a $50 credit as a thank you for your patience"
- Ask for second chance: "I'd love the opportunity to show you the experience we're known for"
- Follow-up promise: "I'll personally call you in 2 days to make sure you're satisfied"

**Example Responses:**

- Customer: "The chef was 45 minutes late and ruined my party!"
  You: "I'm so sorry this happened - I completely understand your frustration. Your party was important, and being 45 minutes late is absolutely unacceptable. Here's what I'm going to do right now: I'm processing a 50% refund to your card ($XXX), which you'll see in 2-3 business days. I'm also adding a $200 credit to your account for a future event - I'd love the chance to show you the experience we're known for. And I'm flagging this with our operations manager so we can address what went wrong with that chef. Can I have your permission to call you in 2 days to make sure you're satisfied with how we've handled this?"

- Customer: "I want to speak to a manager NOW!"
  You: "I absolutely understand, and I'll get a manager involved. Before I do, I want to make sure I fully understand the situation so we can resolve this as quickly as possible. Can you tell me what happened? [Listen] Okay, here's what I'm doing: 1) I'm escalating this to our senior manager who will call you within 2 hours, 2) I'm documenting everything you've shared, and 3) I'm authorizing a [solution] right now so you don't have to wait. The manager will reach out to discuss anything else we can do. Does that work?"

**Tools Usage:**
- Use `check_order_status` immediately when customer references a booking
- Use `process_refund` for compensation decisions
- Use `escalate_to_human` when de-escalation fails or issues exceed your authority
- Use `log_complaint` to track issues for operational improvements

**Red Flags - Escalate Immediately:**
- "I'm calling my lawyer"
- "Food poisoning" or "allergic reaction"
- "Going to the news" or "posting this everywhere"
- Abusive language toward staff
- Threats of any kind

**Remember:**
- A resolved complaint creates more loyalty than if nothing went wrong
- Service recovery is your superpower - use it generously
- Every negative experience is a chance to create a brand advocate
- Your goal: Customer says "They really went above and beyond to make it right"
"""

    def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_order_status",
                    "description": "Look up booking details and status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "identifier": {
                                "type": "string",
                                "description": "Order ID, confirmation number, email, or phone number",
                            },
                            "identifier_type": {
                                "type": "string",
                                "enum": ["order_id", "email", "phone", "confirmation_code"],
                                "description": "Type of identifier provided",
                            },
                        },
                        "required": ["identifier"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "process_refund",
                    "description": "Process refund or credit for customer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string", "description": "Order/booking ID"},
                            "refund_type": {
                                "type": "string",
                                "enum": [
                                    "full_refund",
                                    "partial_refund",
                                    "account_credit",
                                    "future_discount",
                                ],
                                "description": "Type of compensation",
                            },
                            "amount": {
                                "type": "number",
                                "description": "Refund amount in USD (or percentage if partial)",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for refund (for records)",
                            },
                            "requires_approval": {
                                "type": "boolean",
                                "description": "If true, routes to manager for approval (>$2000)",
                            },
                        },
                        "required": ["order_id", "refund_type", "amount", "reason"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_to_human",
                    "description": "Route conversation to human agent",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "urgent"],
                                "description": "Escalation priority",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Why escalating (legal threat, extreme anger, complex issue)",
                            },
                            "summary": {
                                "type": "string",
                                "description": "Brief summary of issue for human agent",
                            },
                            "customer_sentiment": {
                                "type": "string",
                                "enum": ["calm", "frustrated", "angry", "threatening"],
                                "description": "Current customer emotional state",
                            },
                        },
                        "required": ["priority", "reason", "summary"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "log_complaint",
                    "description": "Log complaint for analysis and operational improvements",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": [
                                    "service_quality",
                                    "booking_issue",
                                    "pricing_dispute",
                                    "dietary_issue",
                                    "equipment_failure",
                                    "staff_behavior",
                                    "other",
                                ],
                                "description": "Complaint category",
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["minor", "moderate", "major", "critical"],
                                "description": "Issue severity",
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of issue",
                            },
                            "order_id": {
                                "type": "string",
                                "description": "Associated order ID (if applicable)",
                            },
                            "resolution": {
                                "type": "string",
                                "description": "How issue was resolved",
                            },
                        },
                        "required": ["category", "severity", "description"],
                    },
                },
            },
        ]

    async def process_tool_call(
        self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool functions"""

        try:
            if tool_name == "check_order_status":
                return await self._check_order_status(arguments)

            elif tool_name == "process_refund":
                return await self._process_refund(arguments, context)

            elif tool_name == "escalate_to_human":
                return await self._escalate_to_human(arguments, context)

            elif tool_name == "log_complaint":
                return await self._log_complaint(arguments, context)

            else:
                return {"success": False, "result": None, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}", exc_info=True)
            return {"success": False, "result": None, "error": str(e)}

    # ===== Tool Implementations =====

    async def _check_order_status(self, args: dict[str, Any]) -> dict[str, Any]:
        """Look up order details"""

        args["identifier"]
        args.get("identifier_type", "order_id")

        # TODO: Integrate with actual database
        # This is a mock implementation

        # Simulate database lookup
        order = {
            "order_id": "ORD-2024-1234",
            "customer_name": "John Smith",
            "event_date": "2024-12-15",
            "event_time": "6:00 PM",
            "package": "Premium Package",
            "num_guests": 50,
            "total_cost": "$3,250.00",
            "deposit_paid": "$1,625.00",
            "balance_due": "$1,625.00",
            "status": "Confirmed",
            "chef_assigned": "Chef Mike",
            "special_requests": "Vegetarian options for 5 guests",
            "addons": ["Sushi Station"],
            "created_at": "2024-10-15",
            "last_updated": "2024-10-20",
        }

        return {
            "success": True,
            "result": {
                "found": True,
                "order": order,
                "message": f"Found booking #{order['order_id']} for {order['customer_name']}",
            },
        }

    async def _process_refund(
        self, args: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Process refund or compensation"""

        order_id = args["order_id"]
        refund_type = args["refund_type"]
        amount = args["amount"]
        reason = args["reason"]
        requires_approval = args.get("requires_approval", False)

        # Check if needs manager approval
        if requires_approval or amount > 2000:
            return {
                "success": True,
                "result": {
                    "status": "pending_approval",
                    "message": f"Refund request for ${amount:,.2f} submitted for manager approval. Customer will be contacted within 2 hours.",
                    "reference_number": f"REF-{order_id}-001",
                    "next_steps": "Manager will review and contact customer directly",
                },
            }

        # Process refund
        refund_status = {
            "full_refund": {
                "status": "approved",
                "processing_time": "2-3 business days",
                "method": "Original payment method",
            },
            "partial_refund": {
                "status": "approved",
                "processing_time": "2-3 business days",
                "method": "Original payment method",
            },
            "account_credit": {
                "status": "approved",
                "processing_time": "Immediate",
                "method": "Account credit (valid 12 months)",
            },
            "future_discount": {
                "status": "approved",
                "processing_time": "Immediate",
                "method": "Discount code emailed",
            },
        }

        result = refund_status.get(refund_type, refund_status["account_credit"])

        return {
            "success": True,
            "result": {
                "order_id": order_id,
                "refund_type": refund_type,
                "amount": f"${amount:,.2f}",
                "reason": reason,
                "status": result["status"],
                "processing_time": result["processing_time"],
                "method": result["method"],
                "reference_number": f"REF-{order_id}-{hash(reason) % 1000:03d}",
                "confirmation": f"Refund of ${amount:,.2f} approved and processing. Customer will receive confirmation email.",
            },
        }

    async def _escalate_to_human(
        self, args: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Escalate to human agent"""

        priority = args["priority"]
        reason = args["reason"]
        summary = args["summary"]
        sentiment = args.get("customer_sentiment", "frustrated")

        # Determine routing
        routing = {
            "urgent": {
                "queue": "Senior Support Manager",
                "eta": "5-10 minutes",
                "notify": "SMS + Email",
            },
            "high": {"queue": "Support Manager", "eta": "15-30 minutes", "notify": "Email"},
            "medium": {"queue": "Support Team", "eta": "1-2 hours", "notify": "Email"},
            "low": {"queue": "General Support", "eta": "2-4 hours", "notify": "Email"},
        }

        route = routing.get(priority, routing["medium"])

        # Log escalation
        escalation = {
            "escalation_id": f"ESC-{hash(summary) % 10000:04d}",
            "priority": priority,
            "reason": reason,
            "summary": summary,
            "customer_sentiment": sentiment,
            "conversation_id": context.get("conversation_id"),
            "routed_to": route["queue"],
            "estimated_response": route["eta"],
            "created_at": "2024-10-31T10:30:00Z",
        }

        return {
            "success": True,
            "result": {
                "escalated": True,
                "escalation": escalation,
                "message": f"Your case has been escalated to our {route['queue']}. You can expect a response within {route['eta']}. Reference number: {escalation['escalation_id']}",
            },
        }

    async def _log_complaint(self, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Log complaint for analysis"""

        category = args["category"]
        severity = args["severity"]
        description = args["description"]
        order_id = args.get("order_id")
        resolution = args.get("resolution", "In progress")

        # TODO: Integrate with actual logging system
        # This would typically write to database for analytics

        complaint_id = f"CMP-{hash(description) % 10000:04d}"

        complaint = {
            "complaint_id": complaint_id,
            "category": category,
            "severity": severity,
            "description": description,
            "order_id": order_id,
            "resolution": resolution,
            "conversation_id": context.get("conversation_id"),
            "channel": context.get("channel"),
            "logged_at": "2024-10-31T10:30:00Z",
            "status": "logged",
        }

        logger.info(f"Complaint logged: {complaint_id} - {category} ({severity})")

        return {
            "success": True,
            "result": {
                "logged": True,
                "complaint": complaint,
                "message": f"Issue logged for analysis. Reference: {complaint_id}. Our team will review this to prevent future occurrences.",
            },
        }
