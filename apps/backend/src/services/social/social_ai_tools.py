"""Social media function calling tools for AI API."""

from datetime import datetime, timedelta
import logging
from typing import Any
from uuid import UUID

from cqrs.base import CommandBus, QueryBus  # Phase 2C: Updated from api.app.cqrs.base
from cqrs.social_commands import (  # Phase 2C: Updated from api.app.cqrs.social_commands
    CreateLeadFromSocialCommand,
    SendSocialReplyCommand,
    UpdateThreadStatusCommand,
)
from cqrs.social_queries import (  # Phase 2C: Updated from api.app.cqrs.social_queries
    GetSocialInboxQuery,
    GetThreadDetailQuery,
    SearchSocialContentQuery,
)
from models.legacy_social import (
    MessageKind,
    SocialPlatform,
    ThreadStatus,
)  # Phase 2C: Updated from api.app.models.social
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SocialToolResult(BaseModel):
    """Result from social media tool execution."""

    success: bool
    message: str
    data: dict[str, Any] | None = None
    requires_approval: bool = False
    metadata: dict[str, Any] | None = None


class GetSocialInboxTool:
    """Tool to retrieve social media inbox messages."""

    name = "get_social_inbox"
    description = "Get social media inbox messages with filtering options. Use this to see recent customer messages, mentions, and comments across all platforms."

    parameters = {
        "type": "object",
        "properties": {
            "platforms": {
                "type": "array",
                "items": {"type": "string", "enum": ["instagram", "facebook", "google", "yelp"]},
                "description": "Filter by specific platforms",
            },
            "statuses": {
                "type": "array",
                "items": {"type": "string", "enum": ["new", "pending", "resolved", "closed"]},
                "description": "Filter by thread statuses",
            },
            "search": {"type": "string", "description": "Search term to filter messages"},
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 10,
                "description": "Number of threads to return",
            },
        },
    }

    def __init__(self, query_bus: QueryBus):
        self.query_bus = query_bus

    async def execute(self, **kwargs) -> SocialToolResult:
        """Execute the get social inbox tool."""
        try:
            query = GetSocialInboxQuery(
                platforms=kwargs.get("platforms"),
                statuses=kwargs.get("statuses"),
                search=kwargs.get("search"),
                page_size=kwargs.get("limit", 10),
                page=1,
            )

            result = await self.query_bus.execute(query)

            # Format for AI consumption
            threads_summary = []
            for thread in result["threads"][: kwargs.get("limit", 10)]:
                latest_msg = thread.get("latest_message", {})
                summary = {
                    "thread_id": thread["id"],
                    "platform": thread["platform"],
                    "customer": thread.get("customer_name") or thread.get("handle"),
                    "status": thread["status"],
                    "unread_count": thread["unread_count"],
                    "latest_message": latest_msg.get("body", "")[:100],
                    "message_kind": latest_msg.get("kind"),
                    "created_at": thread["created_at"],
                    "priority": thread["priority"],
                }
                threads_summary.append(summary)

            return SocialToolResult(
                success=True,
                message=f"Retrieved {len(threads_summary)} social inbox threads",
                data={
                    "threads": threads_summary,
                    "total_count": result["pagination"]["total_count"],
                },
            )

        except Exception as e:
            logger.exception(f"Error getting social inbox: {e}")
            return SocialToolResult(success=False, message=f"Failed to get social inbox: {e!s}")


class GetThreadDetailTool:
    """Tool to get detailed information about a social media thread."""

    name = "get_thread_detail"
    description = "Get detailed information about a specific social media thread including full message history and customer profile."

    parameters = {
        "type": "object",
        "properties": {
            "thread_id": {"type": "string", "description": "The ID of the thread to retrieve"},
            "include_customer_profile": {
                "type": "boolean",
                "default": True,
                "description": "Whether to include customer profile information",
            },
        },
        "required": ["thread_id"],
    }

    def __init__(self, query_bus: QueryBus):
        self.query_bus = query_bus

    async def execute(self, **kwargs) -> SocialToolResult:
        """Execute the get thread detail tool."""
        try:
            thread_id = UUID(kwargs["thread_id"])

            query = GetThreadDetailQuery(
                thread_id=thread_id,
                include_messages=True,
                include_customer_profile=kwargs.get("include_customer_profile", True),
                include_related_threads=False,
            )

            result = await self.query_bus.execute(query)

            # Format messages for AI
            messages_summary = []
            for msg in result.get("messages", []):
                msg_summary = {
                    "direction": msg["direction"],
                    "body": msg["body"],
                    "sender": msg["sender_name"] or msg["sender_handle"],
                    "created_at": msg["created_at"],
                    "kind": msg["kind"],
                }
                messages_summary.append(msg_summary)

            # Customer context
            customer_context = {}
            if result.get("customer_profile"):
                customer_profile = result["customer_profile"]
                customer_context = {
                    "name": f"{customer_profile.get('first_name', '')} {customer_profile.get('last_name', '')}".strip(),
                    "email": customer_profile.get("email"),
                    "phone": customer_profile.get("phone"),
                    "social_handle": customer_profile.get("social_identity", {}).get("handle"),
                    "linked": customer_profile.get("linked", True),
                }

            return SocialToolResult(
                success=True,
                message=f"Retrieved thread details with {len(messages_summary)} messages",
                data={
                    "thread": {
                        "id": result["id"],
                        "platform": result["platform"],
                        "status": result["status"],
                        "priority": result["priority"],
                        "created_at": result["created_at"],
                    },
                    "messages": messages_summary,
                    "customer_context": customer_context,
                    "conversation_summary": self._generate_conversation_summary(messages_summary),
                },
            )

        except Exception as e:
            logger.exception(f"Error getting thread detail: {e}")
            return SocialToolResult(success=False, message=f"Failed to get thread detail: {e!s}")

    def _generate_conversation_summary(self, messages: list[dict[str, Any]]) -> str:
        """Generate a brief conversation summary for AI context."""
        if not messages:
            return "No messages in thread"

        customer_messages = [m for m in messages if m["direction"] == "inbound"]
        business_messages = [m for m in messages if m["direction"] == "outbound"]

        summary_parts = [
            f"Thread has {len(messages)} total messages",
            f"Customer sent {len(customer_messages)} messages",
            f"Business sent {len(business_messages)} replies",
        ]

        # Add latest customer message context
        if customer_messages:
            latest_customer_msg = customer_messages[-1]
            summary_parts.append(
                f"Latest customer message: \"{latest_customer_msg['body'][:100]}...\""
            )

        return ". ".join(summary_parts)


class SendSocialReplyTool:
    """Tool to send a reply to a social media thread."""

    name = "send_social_reply"
    description = "Send a reply to a customer on social media. Messages are subject to approval unless marked as emergency."

    parameters = {
        "type": "object",
        "properties": {
            "thread_id": {"type": "string", "description": "The ID of the thread to reply to"},
            "message": {"type": "string", "description": "The message to send to the customer"},
            "reply_type": {
                "type": "string",
                "enum": ["dm", "comment", "review_response"],
                "default": "dm",
                "description": "Type of reply to send",
            },
            "skip_approval": {
                "type": "boolean",
                "default": False,
                "description": "Whether to skip human approval (emergency only)",
            },
            "safety_context": {
                "type": "object",
                "properties": {
                    "profanity_checked": {"type": "boolean"},
                    "policy_compliant": {"type": "boolean"},
                    "confidence_score": {"type": "number"},
                },
                "description": "Safety validation context",
            },
        },
        "required": ["thread_id", "message"],
    }

    def __init__(self, command_bus: CommandBus):
        self.command_bus = command_bus

    async def execute(self, **kwargs) -> SocialToolResult:
        """Execute the send social reply tool."""
        try:
            thread_id = UUID(kwargs["thread_id"])
            message = kwargs["message"]
            reply_type = kwargs.get("reply_type", "dm")
            skip_approval = kwargs.get("skip_approval", False)
            safety_context = kwargs.get("safety_context", {})

            # Enhanced safety checking
            safety_score = await self._calculate_safety_score(message, safety_context)

            command = SendSocialReplyCommand(
                thread_id=thread_id,
                reply_kind=MessageKind(reply_type),
                body=message,
                requires_approval=not skip_approval and safety_score < 0.95,
                safety={
                    "ai_generated": True,
                    "safety_score": safety_score,
                    "profanity_check": safety_context.get("profanity_checked", False),
                    "policy_compliant": safety_context.get("policy_compliant", True),
                    "generated_at": datetime.utcnow().isoformat(),
                },
            )

            result = await self.command_bus.execute(command)

            response_message = "Reply sent successfully"
            if result["requires_approval"]:
                response_message = "Reply created and queued for human approval"
            elif result["scheduled"]:
                response_message = "Reply scheduled for later delivery"

            return SocialToolResult(
                success=True,
                message=response_message,
                requires_approval=result["requires_approval"],
                data={
                    "message_id": result["message_id"],
                    "thread_id": result["thread_id"],
                    "sent_immediately": result["sent"],
                    "safety_score": safety_score,
                },
            )

        except Exception as e:
            logger.exception(f"Error sending social reply: {e}")
            return SocialToolResult(success=False, message=f"Failed to send social reply: {e!s}")

    async def _calculate_safety_score(self, message: str, safety_context: dict[str, Any]) -> float:
        """Calculate safety score for message."""
        base_score = 0.8

        # Check profanity
        if safety_context.get("profanity_checked") and not self._contains_profanity(message):
            base_score += 0.1

        # Check policy compliance
        if safety_context.get("policy_compliant", True):
            base_score += 0.1

        # Check message length and complexity
        if len(message) < 500 and not any(
            word in message.lower() for word in ["refund", "discount", "free", "money"]
        ):
            base_score += 0.05

        return min(base_score, 1.0)

    def _contains_profanity(self, message: str) -> bool:
        """Simple profanity check (implement proper filter in production)."""
        profanity_words = ["damn", "hell", "stupid", "idiot"]  # Simplified list
        return any(word in message.lower() for word in profanity_words)


class CreateLeadFromSocialTool:
    """Tool to create a lead from social media interaction."""

    name = "create_lead_from_social"
    description = "Create a lead from a social media customer interaction. Use when customer shows interest in booking/services."

    parameters = {
        "type": "object",
        "properties": {
            "thread_id": {
                "type": "string",
                "description": "The thread ID where lead was identified",
            },
            "platform": {
                "type": "string",
                "enum": ["instagram", "facebook", "google", "yelp"],
                "description": "Social media platform",
            },
            "customer_handle": {"type": "string", "description": "Customer's social media handle"},
            "interest_signals": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of interest signals detected (e.g., 'party size', 'date mention', 'pricing inquiry')",
            },
            "consent_dm": {
                "type": "boolean",
                "default": True,
                "description": "Customer consented to DM follow-up",
            },
            "consent_sms": {
                "type": "boolean",
                "default": False,
                "description": "Customer provided phone for SMS",
            },
            "consent_email": {
                "type": "boolean",
                "default": False,
                "description": "Customer provided email",
            },
        },
        "required": ["platform", "customer_handle", "interest_signals"],
    }

    def __init__(self, command_bus: CommandBus):
        self.command_bus = command_bus

    async def execute(self, **kwargs) -> SocialToolResult:
        """Execute the create lead from social tool."""
        try:
            thread_id = UUID(kwargs["thread_id"]) if kwargs.get("thread_id") else None
            platform = SocialPlatform(kwargs["platform"])
            handle = kwargs["customer_handle"]
            interest_signals = kwargs["interest_signals"]

            # Infer interest category from signals
            interest_category = self._infer_interest_category(interest_signals)

            command = CreateLeadFromSocialCommand(
                source=platform,
                thread_id=thread_id,
                handle=handle,
                inferred_interest=interest_category,
                consent_dm=kwargs.get("consent_dm", True),
                consent_sms=kwargs.get("consent_sms", False),
                consent_email=kwargs.get("consent_email", False),
                metadata={
                    "interest_signals": interest_signals,
                    "ai_created": True,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )

            result = await self.command_bus.execute(command)

            if result["created"]:
                return SocialToolResult(
                    success=True,
                    message=f"Created new lead from {platform} customer {handle}",
                    data={
                        "lead_id": result["lead_id"],
                        "social_identity_id": result["social_identity_id"],
                        "interest_category": interest_category,
                        "consent_status": {
                            "dm": command.consent_dm,
                            "sms": command.consent_sms,
                            "email": command.consent_email,
                        },
                    },
                )
            else:
                return SocialToolResult(
                    success=False,
                    message=f"Lead already exists for {handle} on {platform}",
                    data={"existing_lead_id": result["lead_id"]},
                )

        except Exception as e:
            logger.exception(f"Error creating lead from social: {e}")
            return SocialToolResult(success=False, message=f"Failed to create social lead: {e!s}")

    def _infer_interest_category(self, signals: list[str]) -> str:
        """Infer customer interest category from signals."""
        signals_text = " ".join(signals).lower()

        if any(
            word in signals_text for word in ["party", "group", "people", "birthday", "celebration"]
        ):
            return "private_hibachi"
        elif any(word in signals_text for word in ["catering", "event", "office", "wedding"]):
            return "catering"
        elif any(word in signals_text for word in ["class", "lesson", "learn", "teach"]):
            return "cooking_class"
        else:
            return "general_inquiry"


class SearchSocialContentTool:
    """Tool to search across social media content."""

    name = "search_social_content"
    description = (
        "Search across social media messages, comments, and reviews for specific content or topics."
    )

    parameters = {
        "type": "object",
        "properties": {
            "search_term": {
                "type": "string",
                "description": "Term to search for in social content",
            },
            "platforms": {
                "type": "array",
                "items": {"type": "string", "enum": ["instagram", "facebook", "google", "yelp"]},
                "description": "Platforms to search",
            },
            "content_types": {
                "type": "array",
                "items": {"type": "string", "enum": ["message", "comment", "review", "mention"]},
                "description": "Types of content to search",
            },
            "days_back": {
                "type": "integer",
                "minimum": 1,
                "maximum": 90,
                "default": 7,
                "description": "Number of days back to search",
            },
        },
        "required": ["search_term"],
    }

    def __init__(self, query_bus: QueryBus):
        self.query_bus = query_bus

    async def execute(self, **kwargs) -> SocialToolResult:
        """Execute the search social content tool."""
        try:
            search_term = kwargs["search_term"]
            platforms = kwargs.get("platforms")
            content_types = kwargs.get("content_types")
            days_back = kwargs.get("days_back", 7)

            date_from = datetime.utcnow() - timedelta(days=days_back)

            query = SearchSocialContentQuery(
                search_term=search_term,
                platforms=platforms,
                content_types=content_types,
                date_from=date_from,
                page_size=20,
            )

            result = await self.query_bus.execute(query)

            # Format results for AI
            search_results = []
            for item in result.get("results", []):
                search_result = {
                    "content_type": item.get("content_type"),
                    "platform": item.get("platform"),
                    "snippet": item.get("content", "")[:150],
                    "author": item.get("author"),
                    "created_at": item.get("created_at"),
                    "thread_id": item.get("thread_id"),
                    "relevance_score": item.get("relevance_score", 0),
                }
                search_results.append(search_result)

            return SocialToolResult(
                success=True,
                message=f"Found {len(search_results)} results for '{search_term}'",
                data={
                    "search_term": search_term,
                    "results": search_results,
                    "total_found": len(search_results),
                    "search_parameters": {
                        "platforms": platforms,
                        "content_types": content_types,
                        "days_back": days_back,
                    },
                },
            )

        except Exception as e:
            logger.exception(f"Error searching social content: {e}")
            return SocialToolResult(
                success=False, message=f"Failed to search social content: {e!s}"
            )


class UpdateThreadStatusTool:
    """Tool to update social media thread status."""

    name = "update_thread_status"
    description = (
        "Update the status of a social media thread (e.g., mark as resolved, escalate, assign)."
    )

    parameters = {
        "type": "object",
        "properties": {
            "thread_id": {"type": "string", "description": "The ID of the thread to update"},
            "status": {
                "type": "string",
                "enum": ["new", "pending", "resolved", "closed", "escalated"],
                "description": "New status for the thread",
            },
            "reason": {"type": "string", "description": "Reason for the status change"},
            "assigned_to": {
                "type": "string",
                "description": "User ID to assign thread to (optional)",
            },
        },
        "required": ["thread_id", "status"],
    }

    def __init__(self, command_bus: CommandBus):
        self.command_bus = command_bus

    async def execute(self, **kwargs) -> SocialToolResult:
        """Execute the update thread status tool."""
        try:
            thread_id = UUID(kwargs["thread_id"])
            status = ThreadStatus(kwargs["status"])
            reason = kwargs.get("reason", "Updated by AI assistant")
            assigned_to = UUID(kwargs["assigned_to"]) if kwargs.get("assigned_to") else None

            command = UpdateThreadStatusCommand(
                thread_id=thread_id,
                status=status,
                updated_by=UUID(int=0),  # AI system user ID
                reason=reason,
                assigned_to=assigned_to,
            )

            result = await self.command_bus.execute(command)

            return SocialToolResult(
                success=True,
                message=f"Thread status updated from {result['old_status']} to {result['new_status']}",
                data={
                    "thread_id": result["thread_id"],
                    "old_status": result["old_status"],
                    "new_status": result["new_status"],
                    "assigned_to": result.get("assigned_to"),
                    "reason": reason,
                },
            )

        except Exception as e:
            logger.exception(f"Error updating thread status: {e}")
            return SocialToolResult(success=False, message=f"Failed to update thread status: {e!s}")


class SocialMediaToolKit:
    """Collection of social media tools for AI function calling."""

    def __init__(self, command_bus: CommandBus, query_bus: QueryBus):
        self.tools = {
            "get_social_inbox": GetSocialInboxTool(query_bus),
            "get_thread_detail": GetThreadDetailTool(query_bus),
            "send_social_reply": SendSocialReplyTool(command_bus),
            "create_lead_from_social": CreateLeadFromSocialTool(command_bus),
            "search_social_content": SearchSocialContentTool(query_bus),
            "update_thread_status": UpdateThreadStatusTool(command_bus),
        }

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Get OpenAI function calling schema for all tools."""
        schemas = []

        for _tool_name, tool in self.tools.items():
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            schemas.append(schema)

        return schemas

    async def execute_tool(self, tool_name: str, **kwargs) -> SocialToolResult:
        """Execute a social media tool."""
        tool = self.tools.get(tool_name)
        if not tool:
            return SocialToolResult(success=False, message=f"Unknown tool: {tool_name}")

        return await tool.execute(**kwargs)
