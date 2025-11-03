"""
Emotion Detection Service

This service analyzes customer sentiment from text (and eventually voice) to:
1. Detect emotional state (negative, neutral, positive)
2. Score emotion intensity (0.0 = very negative, 1.0 = very positive)
3. Trigger escalations for very negative sentiment
4. Adjust agent tone based on detected emotion

The service uses OpenAI's API for sentiment analysis with carefully crafted
prompts to ensure accurate emotion detection.

Architecture:
- EmotionResult: Structured emotion data (score, label, confidence, triggers)
- EmotionService: Core detection logic with OpenAI integration
- Agent tone adjustment: Dynamic prompt modification based on emotion
- Escalation triggers: Automatic routing to human agents for negative sentiment

Author: MyHibachi Development Team
Created: October 31, 2025
Phase: 1B - Intelligence Layer
"""

from datetime import datetime
import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EmotionResult(BaseModel):
    """
    Structured emotion detection result.

    Attributes:
        score: Emotion intensity (0.0 = very negative, 1.0 = very positive)
        label: Emotion category (negative, neutral, positive)
        confidence: Detection confidence (0.0-1.0)
        should_escalate: Whether to escalate to human agent
        detected_emotions: List of specific emotions detected (anger, frustration, joy, etc.)
        reasoning: Brief explanation of the emotion detection
        timestamp: When the emotion was detected
    """

    score: float = Field(ge=0.0, le=1.0, description="Emotion intensity score")
    label: str = Field(description="Emotion category: negative, neutral, or positive")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    should_escalate: bool = Field(description="Whether to escalate to human agent")
    detected_emotions: list[str] = Field(default_factory=list, description="Specific emotions")
    reasoning: str | None = Field(None, description="Explanation of detection")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "score": 0.15,
                "label": "negative",
                "confidence": 0.92,
                "should_escalate": True,
                "detected_emotions": ["anger", "frustration"],
                "reasoning": "Customer expressed strong dissatisfaction with service delay",
                "timestamp": "2025-10-31T23:30:00Z",
            }
        }


class EmotionService:
    """
    Service for detecting and analyzing customer emotions from text.

    This service provides:
    1. Sentiment analysis (negative/neutral/positive)
    2. Emotion scoring (0.0-1.0 scale)
    3. Specific emotion detection (anger, joy, frustration, etc.)
    4. Escalation recommendations
    5. Agent tone adjustment

    Uses OpenAI API for accurate emotion detection with specialized prompts.

    Example Usage:
        ```python
        emotion_service = EmotionService()

        # Detect emotion
        result = await emotion_service.detect_emotion(
            "I'm very disappointed with the service. This is unacceptable!"
        )

        # Check if escalation needed
        if result.should_escalate:
            # Route to human agent
            pass

        # Adjust agent tone
        adjusted_prompt = emotion_service.adjust_agent_tone(
            agent_prompt="You are a helpful assistant",
            emotion_result=result
        )
        ```
    """

    # Escalation thresholds
    ESCALATION_THRESHOLD = 0.3  # Escalate if score < 0.3 (very negative)
    NEGATIVE_THRESHOLD = 0.4  # Negative if score < 0.4
    POSITIVE_THRESHOLD = 0.6  # Positive if score > 0.6

    # Specific emotions by category
    NEGATIVE_EMOTIONS = [
        "anger",
        "frustration",
        "disappointment",
        "annoyance",
        "irritation",
        "upset",
        "dissatisfaction",
        "complaint",
    ]

    NEUTRAL_EMOTIONS = ["curiosity", "inquiry", "confusion", "uncertainty", "interest"]

    POSITIVE_EMOTIONS = [
        "joy",
        "excitement",
        "satisfaction",
        "happiness",
        "enthusiasm",
        "gratitude",
        "appreciation",
        "delight",
    ]

    def __init__(self, provider=None):
        """
        Initialize emotion service.

        Args:
            provider: Optional ModelProvider instance (defaults to OpenAI)
        """
        self.provider = provider
        if self.provider is None:
            try:
                from ..orchestrator.providers.factory import get_provider

                self.provider = get_provider()
                logger.info("Emotion service initialized with default provider")
            except Exception as e:
                logger.warning(f"Could not initialize provider: {e}")

        logger.info("EmotionService initialized")

    async def detect_emotion(
        self, text: str, context: dict[str, Any] | None = None
    ) -> EmotionResult:
        """
        Detect emotion from text using OpenAI sentiment analysis.

        This method analyzes the text to determine:
        - Overall emotional tone (negative/neutral/positive)
        - Emotion intensity score (0.0-1.0)
        - Specific emotions present
        - Whether escalation is needed

        Args:
            text: Text to analyze for emotion
            context: Optional context (previous messages, customer history)

        Returns:
            EmotionResult with complete emotion analysis

        Example:
            ```python
            result = await service.detect_emotion(
                "This is terrible! I want a refund immediately!",
                context={"channel": "webchat", "is_repeat_customer": True}
            )
            # result.score = 0.12 (very negative)
            # result.label = "negative"
            # result.should_escalate = True
            # result.detected_emotions = ["anger", "frustration"]
            ```
        """
        try:
            # Build analysis prompt
            analysis_prompt = self._build_emotion_prompt(text, context)

            # Call OpenAI for emotion analysis
            response = await self.provider.complete(
                messages=[
                    {"role": "system", "content": analysis_prompt},
                    {"role": "user", "content": f"Analyze the emotion in this text: {text}"},
                ],
                temperature=0.3,  # Low temperature for consistent analysis
                max_tokens=300,
            )

            # Parse response to extract emotion data
            # OpenAI provider returns dict with 'content' key
            content = response.get("content", "")
            emotion_data = self._parse_emotion_response(content)

            # Create EmotionResult
            score = emotion_data.get("score", 0.5)
            label = self._score_to_label(score)
            should_escalate = score < self.ESCALATION_THRESHOLD

            result = EmotionResult(
                score=score,
                label=label,
                confidence=emotion_data.get("confidence", 0.8),
                should_escalate=should_escalate,
                detected_emotions=emotion_data.get("emotions", []),
                reasoning=emotion_data.get("reasoning", ""),
            )

            logger.info(
                f"Emotion detected: {label} (score: {score:.2f}, " f"escalate: {should_escalate})"
            )

            return result

        except Exception as e:
            logger.error(f"Emotion detection failed: {e}", exc_info=True)
            # Return neutral fallback
            return EmotionResult(
                score=0.5,
                label="neutral",
                confidence=0.0,
                should_escalate=False,
                detected_emotions=[],
                reasoning=f"Detection failed: {e!s}",
            )

    def _build_emotion_prompt(self, text: str, context: dict[str, Any] | None = None) -> str:
        """Build specialized prompt for emotion analysis"""

        base_prompt = """You are an expert emotion analyst for customer service interactions.

Analyze the customer's emotional state from their message and provide:

1. **Emotion Score** (0.0-1.0):
   - 0.0-0.2: Very negative (anger, extreme frustration)
   - 0.2-0.4: Negative (disappointment, dissatisfaction)
   - 0.4-0.6: Neutral (factual inquiry, no strong emotion)
   - 0.6-0.8: Positive (satisfaction, interest)
   - 0.8-1.0: Very positive (delight, enthusiasm)

2. **Specific Emotions**: Identify specific emotions present (anger, joy, frustration, etc.)

3. **Confidence**: How confident are you in this analysis? (0.0-1.0)

4. **Reasoning**: Brief explanation of why you rated it this way

**Response Format**:
Score: [0.0-1.0]
Confidence: [0.0-1.0]
Emotions: [comma-separated list]
Reasoning: [brief explanation]

**Important**:
- Consider context: repeat customers may express frustration differently
- Look for intensity words: "terrible", "awful", "amazing", "love"
- Detect sarcasm and frustration masked as politeness
- Escalate (score < 0.3) for genuine anger or extreme dissatisfaction
"""

        # Add context if available
        if context:
            context_info = []
            if context.get("is_repeat_customer"):
                context_info.append("This is a repeat customer")
            if context.get("previous_issue"):
                context_info.append("Customer has had previous issues")
            if context.get("channel"):
                context_info.append(f"Channel: {context['channel']}")

            if context_info:
                base_prompt += f"\n\n**Context**: {', '.join(context_info)}"

        return base_prompt

    def _parse_emotion_response(self, response: str) -> dict[str, Any]:
        """Parse OpenAI response to extract emotion data"""

        emotion_data = {"score": 0.5, "confidence": 0.8, "emotions": [], "reasoning": ""}

        try:
            lines = response.strip().split("\n")

            for line in lines:
                line = line.strip()

                if line.startswith("Score:"):
                    score_str = line.split(":", 1)[1].strip()
                    emotion_data["score"] = float(score_str)

                elif line.startswith("Confidence:"):
                    conf_str = line.split(":", 1)[1].strip()
                    emotion_data["confidence"] = float(conf_str)

                elif line.startswith("Emotions:"):
                    emotions_str = line.split(":", 1)[1].strip()
                    emotions = [e.strip().lower() for e in emotions_str.split(",")]
                    emotion_data["emotions"] = [e for e in emotions if e]

                elif line.startswith("Reasoning:"):
                    reasoning = line.split(":", 1)[1].strip()
                    emotion_data["reasoning"] = reasoning

        except Exception as e:
            logger.warning(f"Failed to parse emotion response: {e}")

        return emotion_data

    def _score_to_label(self, score: float) -> str:
        """Convert emotion score to label"""
        if score < self.NEGATIVE_THRESHOLD:
            return "negative"
        elif score > self.POSITIVE_THRESHOLD:
            return "positive"
        else:
            return "neutral"

    def adjust_agent_tone(self, agent_prompt: str, emotion_result: EmotionResult) -> str:
        """
        Adjust agent system prompt based on detected emotion.

        This adds empathy instructions and tone adjustments to the agent's
        system prompt based on the customer's emotional state.

        Args:
            agent_prompt: Original agent system prompt
            emotion_result: Detected emotion from customer message

        Returns:
            Modified system prompt with tone adjustments

        Example:
            ```python
            original = "You are a helpful customer service agent."
            emotion = EmotionResult(score=0.2, label="negative", ...)

            adjusted = service.adjust_agent_tone(original, emotion)
            # Adds empathy instructions for negative emotion
            ```
        """

        # No adjustment needed for neutral/positive emotions
        if emotion_result.label in ["neutral", "positive"]:
            return agent_prompt

        # Add empathy instructions for negative emotions
        if emotion_result.label == "negative":
            empathy_instructions = """

**CRITICAL TONE ADJUSTMENT**:
The customer is expressing negative emotions (frustration, disappointment, or anger).

**Adjust your tone**:
1. **Lead with empathy**: "I understand your frustration..." or "I'm sorry to hear that..."
2. **Validate feelings**: Acknowledge their concern is legitimate
3. **Take ownership**: Even if not directly at fault, show you're here to help
4. **Be solution-focused**: Move quickly to resolving the issue
5. **Avoid defensive language**: No "but", "actually", or "technically"

**Example opening**:
"I completely understand your frustration, and I sincerely apologize for the inconvenience.
Let me help resolve this right away."

**Escalation note**: If you cannot fully resolve the issue, offer to connect them with
a supervisor or manager immediately. Do not make them repeat their story.
"""

            # Add specific guidance for very negative emotions (escalation threshold)
            if emotion_result.should_escalate:
                empathy_instructions += """

**ESCALATION RECOMMENDED**:
This customer is experiencing significant frustration. Consider:
1. Offering immediate connection to a supervisor/manager
2. Providing direct phone number for faster resolution
3. Expressing urgency in resolving their concern
4. Offering compensation or goodwill gesture if appropriate
"""

            return agent_prompt + empathy_instructions

        return agent_prompt

    def should_escalate(self, emotion_result: EmotionResult) -> bool:
        """
        Determine if conversation should be escalated to human agent.

        Escalation criteria:
        - Emotion score < 0.3 (very negative)
        - Specific emotions: anger, extreme frustration
        - Low confidence in AI's ability to handle

        Args:
            emotion_result: Emotion detection result

        Returns:
            True if escalation is recommended
        """
        return emotion_result.should_escalate

    async def detect_emotion_batch(
        self, texts: list[str], context: dict[str, Any] | None = None
    ) -> list[EmotionResult]:
        """
        Detect emotions for multiple texts in batch.

        Useful for analyzing conversation history or multiple messages.

        Args:
            texts: List of texts to analyze
            context: Optional shared context

        Returns:
            List of EmotionResult objects
        """
        results = []

        for text in texts:
            result = await self.detect_emotion(text, context)
            results.append(result)

        return results

    def get_emotion_trend(self, emotion_results: list[EmotionResult]) -> dict[str, Any]:
        """
        Analyze emotion trend over a conversation.

        Useful for understanding if customer emotion is improving or
        deteriorating over the course of interaction.

        Args:
            emotion_results: List of emotion results from conversation

        Returns:
            Dict with trend analysis (improving, declining, stable)
        """
        if not emotion_results:
            return {"trend": "unknown", "direction": None}

        scores = [r.score for r in emotion_results]

        # Calculate trend
        if len(scores) < 2:
            return {
                "trend": "insufficient_data",
                "average_score": scores[0] if scores else 0.5,
                "direction": None,
            }

        # Simple linear trend
        first_half_avg = sum(scores[: len(scores) // 2]) / (len(scores) // 2)
        second_half_avg = sum(scores[len(scores) // 2 :]) / (len(scores) - len(scores) // 2)

        diff = second_half_avg - first_half_avg

        if abs(diff) < 0.1:
            trend = "stable"
            direction = None
        elif diff > 0:
            trend = "improving"
            direction = "positive"
        else:
            trend = "declining"
            direction = "negative"

        return {
            "trend": trend,
            "direction": direction,
            "average_score": sum(scores) / len(scores),
            "latest_score": scores[-1],
            "change": diff,
            "data_points": len(scores),
        }


# =========================================================================
# Factory Function
# =========================================================================

_emotion_service_instance: EmotionService | None = None


def get_emotion_service() -> EmotionService:
    """
    Get or create the singleton EmotionService instance.

    Returns:
        EmotionService: The singleton emotion service instance
    """
    global _emotion_service_instance

    if _emotion_service_instance is None:
        _emotion_service_instance = EmotionService()
        logger.info("EmotionService singleton instance created")

    return _emotion_service_instance
