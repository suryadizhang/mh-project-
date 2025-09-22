"""
OpenAI service for GPT integration with cost optimization and model selection
"""

import asyncio
import os
from typing import Optional

from openai import AsyncOpenAI


class OpenAIService:
    """Service for OpenAI GPT integration with intelligent model selection"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Model configuration with pricing (per 1M tokens)
        self.models = {
            "gpt-5-nano": {
                "name": "gpt-3.5-turbo",  # Using 3.5-turbo as proxy for nano pricing
                "input_cost": 0.0010,  # $0.001 per 1K tokens
                "output_cost": 0.0020,  # $0.002 per 1K tokens
                "max_tokens": 4096,
                "context_limit": 16385,
                "good_for": ["simple_queries", "faq", "basic_conversation"],
            },
            "gpt-4-1-mini": {
                "name": "gpt-4-turbo-preview",  # Using 4-turbo as proxy
                "input_cost": 0.0100,  # $0.01 per 1K tokens
                "output_cost": 0.0300,  # $0.03 per 1K tokens
                "max_tokens": 4096,
                "context_limit": 128000,
                "good_for": [
                    "complex_queries",
                    "multi_step",
                    "reasoning",
                    "escalation",
                ],
            },
        }

        # Escalation keywords that trigger human handoff
        self.escalation_keywords = [
            "allergy",
            "allergic",
            "allergies",
            "refund",
            "money back",
            "charge back",
            "legal",
            "lawsuit",
            "lawyer",
            "attorney",
            "complaint",
            "angry",
            "furious",
            "terrible",
            "manager",
            "supervisor",
            "speak to someone",
            "cancel",
            "cancellation",
            "weather",
            "rain",
            "storm",
            "covid",
        ]

        # Load system prompts
        self.system_prompts = self._load_system_prompts()

    def _load_system_prompts(self) -> dict[str, str]:
        """Load system prompts from files"""
        prompts = {}
        prompts_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "prompts"
        )

        try:
            # Base system prompt
            base_path = os.path.join(prompts_dir, "system_base.md")
            if os.path.exists(base_path):
                with open(base_path, encoding="utf-8") as f:
                    prompts["base"] = f.read()
            else:
                prompts["base"] = self._get_default_system_prompt()

            # GPT answer wrapper prompt
            wrapper_path = os.path.join(prompts_dir, "gpt_answer_wrapper.md")
            if os.path.exists(wrapper_path):
                with open(wrapper_path, encoding="utf-8") as f:
                    prompts["wrapper"] = f.read()
            else:
                prompts["wrapper"] = self._get_default_wrapper_prompt()

        except Exception as e:
            print(f"Error loading prompts: {e}")
            prompts["base"] = self._get_default_system_prompt()
            prompts["wrapper"] = self._get_default_wrapper_prompt()

        return prompts

    def _get_default_system_prompt(self) -> str:
        """Default system prompt for MyHibachi"""
        return """You are a helpful assistant for MyHibachi, a premium hibachi catering service in Northern California.

IMPORTANT SERVICE DETAILS:
- We serve throughout Northern California (Bay Area: San Francisco, San Jose, Oakland, Palo Alto, Mountain View, Santa Clara, Sunnyvale, Fremont; Sacramento area: Roseville, Folsom, Davis)
- Deposit: $100 refundable (subject to terms and conditions in our agreement)
- We DO NOT provide cleanup service, tables, chairs, or dinnerware - customers must arrange these separately
- We DO provide: professional chef, portable hibachi grill, all cooking equipment, utensils, hibachi vegetables (zucchini, onions, mushrooms), fried rice, and premium proteins
- Travel fees apply based on distance from our base location
- Proteins: chicken, beef steak, shrimp, salmon, tofu (vegetarian), and combination options

TONE AND APPROACH:
- Be friendly, professional, and enthusiastic about hibachi catering
- Use the EXACT information provided above - never invent pricing or policies
- Keep responses concise but informative
- If asked about booking, direct customers to contact us directly
- If uncertain about specific details, recommend contacting our team

ESCALATION TRIGGERS:
- Allergy/dietary restrictions requiring detailed discussion
- Refund or billing disputes
- Complaints or negative feedback
- Legal concerns
- Weather-related cancellations
- Complex booking modifications"""

    def _get_default_wrapper_prompt(self) -> str:
        """Default wrapper prompt for GPT responses"""
        return """When responding to customer inquiries:

1. First check if the internal knowledge base summary provided answers the question
2. If not fully answered, use your knowledge but stay within MyHibachi's service boundaries
3. Always be concise, friendly, and confident
4. Never invent pricing, policies, or service details not provided
5. If uncertain, suggest the customer contact our team directly
6. For booking inquiries, provide helpful information but direct them to complete booking through our website or by contacting us
7. If the query involves allergies, refunds, legal issues, or complaints, acknowledge the concern but recommend direct contact with our team

Keep responses under 150 words when possible."""

    def should_escalate(self, message: str) -> tuple[bool, Optional[str]]:
        """Check if message should be escalated to human"""
        message_lower = message.lower()

        for keyword in self.escalation_keywords:
            if keyword in message_lower:
                return True, f"Escalation keyword detected: {keyword}"

        # Check for sentiment indicators
        angry_indicators = [
            "awful",
            "horrible",
            "worst",
            "hate",
            "disgusted",
            "never again",
        ]
        for indicator in angry_indicators:
            if indicator in message_lower:
                return True, f"Negative sentiment detected: {indicator}"

        return False, None

    def select_model(self, message: str, confidence: float) -> str:
        """Select appropriate GPT model based on message complexity and confidence"""
        # If confidence is very low, use more powerful model
        if confidence < 0.3:
            return "gpt-4-1-mini"

        # Check for complex query indicators
        complex_indicators = [
            "explain",
            "how does",
            "why",
            "compare",
            "difference",
            "multiple",
            "several",
            "both",
            "either",
            "schedule",
            "availability",
            "when can",
            "what if",
            "suppose",
        ]

        message_lower = message.lower()
        complexity_score = sum(
            1 for indicator in complex_indicators if indicator in message_lower
        )

        # Use GPT-4 for complex queries
        if complexity_score >= 2 or len(message.split()) > 50:
            return "gpt-4-1-mini"

        # Default to cost-effective model
        return "gpt-5-nano"

    async def generate_response(
        self,
        message: str,
        context: Optional[str] = None,
        conversation_history: Optional[list[dict[str, str]]] = None,
        force_model: Optional[str] = None,
    ) -> tuple[str, float, str, int, int, float]:
        """
        Generate response using OpenAI GPT
        Returns: (response, confidence, model_used, tokens_in, tokens_out, cost_usd)
        """
        try:
            # Check for escalation
            should_escalate, escalation_reason = self.should_escalate(message)
            if should_escalate:
                return (
                    "I understand your concern. Let me connect you with one of our team members who can provide personalized assistance. Please hold on while I transfer you to a live agent.",
                    0.95,
                    "escalation",
                    0,
                    0,
                    0.0,
                )

            # Select model
            model_key = force_model or self.select_model(
                message, 0.5
            )  # Default confidence for model selection
            model_config = self.models[model_key]

            # Build messages
            messages = []

            # System prompt
            system_content = self.system_prompts["base"]
            if context:
                system_content += f"\n\nKnowledge Base Context:\n{context}"
            messages.append({"role": "system", "content": system_content})

            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[
                    -6:
                ]:  # Last 6 messages for context
                    messages.append(
                        {"role": msg["role"], "content": msg["content"]}
                    )

            # Add current message
            messages.append({"role": "user", "content": message})

            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=model_config["name"],
                messages=messages,
                max_tokens=min(
                    300, model_config["max_tokens"]
                ),  # Limit for cost control
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
            )

            # Extract response
            content = response.choices[0].message.content

            # Calculate tokens and cost
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens

            cost_usd = (tokens_in / 1000) * model_config["input_cost"] + (
                tokens_out / 1000
            ) * model_config["output_cost"]

            # Calculate confidence based on model and response length
            base_confidence = 0.8 if model_key == "gpt-4-1-mini" else 0.7
            confidence = min(base_confidence + (len(content) / 1000), 0.95)

            return (
                content,
                confidence,
                model_key,
                tokens_in,
                tokens_out,
                cost_usd,
            )

        except Exception as e:
            print(f"OpenAI error: {e}")
            return (
                "I'm having trouble accessing my knowledge right now. Please contact our team directly for immediate assistance with your hibachi catering needs.",
                0.2,
                "error",
                0,
                0,
                0.0,
            )

    async def generate_batch_responses(
        self, messages: list[str], context: Optional[str] = None
    ) -> list[tuple[str, float, str, int, int, float]]:
        """Generate responses for multiple messages (for batch processing)"""
        tasks = []
        for message in messages:
            task = self.generate_response(message, context)
            tasks.append(task)

        # Process in batches to avoid rate limits
        batch_size = 5
        results = []

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i : i + batch_size]
            batch_results = await asyncio.gather(
                *batch, return_exceptions=True
            )

            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(
                        ("Error processing request", 0.1, "error", 0, 0, 0.0)
                    )
                else:
                    results.append(result)

            # Rate limiting delay
            if i + batch_size < len(tasks):
                await asyncio.sleep(1)

        return results

    def calculate_cost_savings(
        self, tokens_in: int, tokens_out: int, model_used: str
    ) -> dict[str, float]:
        """Calculate cost savings compared to GPT-4"""
        model_config = self.models[model_used]
        actual_cost = (tokens_in / 1000) * model_config["input_cost"] + (
            tokens_out / 1000
        ) * model_config["output_cost"]

        # Calculate what GPT-4 would cost
        gpt4_config = self.models["gpt-4-1-mini"]
        gpt4_cost = (tokens_in / 1000) * gpt4_config["input_cost"] + (
            tokens_out / 1000
        ) * gpt4_config["output_cost"]

        savings = gpt4_cost - actual_cost
        savings_percent = (savings / gpt4_cost * 100) if gpt4_cost > 0 else 0

        return {
            "actual_cost": actual_cost,
            "gpt4_cost": gpt4_cost,
            "savings": savings,
            "savings_percent": savings_percent,
        }


# Global instance
openai_service = OpenAIService()
