"""
Tone Analyzer - Customer Communication Style Detection

Detects customer tone from messages to adapt AI responses for better hospitality.

Supported Tones:
- FORMAL: Professional, corporate, detailed inquiries
- CASUAL: Friendly, emoji-rich, conversational
- DIRECT: Short, efficient, fact-focused
- WARM: Enthusiastic, emotional, celebratory
- ANXIOUS: Worried, uncertain, needs reassurance
"""

from enum import Enum
from typing import Dict
import re
from dataclasses import dataclass


class CustomerTone(Enum):
    """Customer communication tone categories"""

    FORMAL = "formal"
    CASUAL = "casual"
    DIRECT = "direct"
    WARM = "warm"
    ANXIOUS = "anxious"


@dataclass
class ToneAnalysisResult:
    """Result of tone analysis"""

    detected_tone: CustomerTone
    confidence: float
    scores: Dict[str, float]
    reasoning: str


class ToneAnalyzer:
    """
    Rule-based tone detection using pattern matching
    Target accuracy: 85-90%

    Uses keyword patterns, emoji detection, message length, and punctuation
    to classify customer communication style.
    """

    # Tone-specific patterns
    FORMAL_PATTERNS = [
        r"\b(Good (morning|afternoon|evening))\b",
        r"\b(I would like to|Could you please|May I)\b",
        r"\b(inquiry|request|regarding|appreciate|grateful)\b",
        r"\b(professional|corporate|business|event)\b",
        r"\b(kindly|sincerely|respectfully)\b",
    ]

    CASUAL_PATTERNS = [
        r"\b(Hey|Hi|Yo|Sup|Heyyy)\b",
        r"😊|😁|🔥|✨|👍|🎉|💯|❤️",  # Casual emojis
        r"!{2,}",  # Multiple exclamation marks
        r"\b(yeah|yup|nah|gonna|wanna|gotta)\b",
        r"\b(lol|haha|omg|btw)\b",
    ]

    DIRECT_PATTERNS = [
        r"^\s*(how much|price|cost|available|date)\??$",  # One-word questions
        r"^[^.!?]{1,30}$",  # Very short messages
        r"^\s*\d+\s+(guests?|people|ppl)\??$",  # "10 guests?"
        r"^\s*(yes|no|ok|sure)\s*$",  # Single-word responses
    ]

    WARM_PATTERNS = [
        r"\b(excited|thrilled|love|can\'t wait|amazing|wonderful)\b",
        r"❤️|💕|💖|🥰|😍|🎊|🎉|🎈",  # Warm emojis
        r"!{3,}",  # Lots of exclamation marks
        r"\b(celebrate|celebration|special|milestone|birthday|anniversary)\b",
        r"\b(family|friends|loved ones|kids|children)\b",
    ]

    ANXIOUS_PATTERNS = [
        r"\b(worried|nervous|unsure|confused|help|don\'t know)\b",
        r"\?{2,}",  # Multiple question marks
        r"\b(never done|first time|not sure|afraid|concern)\b",
        r"\b(what if|is it okay|will it|should I)\b",
        r"😟|😰|😅|🤔|😕",  # Anxious emojis
    ]

    def __init__(self):
        """Initialize tone analyzer with pattern matchers"""
        self.patterns = {
            CustomerTone.FORMAL: [re.compile(p, re.IGNORECASE) for p in self.FORMAL_PATTERNS],
            CustomerTone.CASUAL: [re.compile(p, re.IGNORECASE) for p in self.CASUAL_PATTERNS],
            CustomerTone.DIRECT: [re.compile(p, re.IGNORECASE) for p in self.DIRECT_PATTERNS],
            CustomerTone.WARM: [re.compile(p, re.IGNORECASE) for p in self.WARM_PATTERNS],
            CustomerTone.ANXIOUS: [re.compile(p, re.IGNORECASE) for p in self.ANXIOUS_PATTERNS],
        }

    def detect_tone(self, message: str) -> ToneAnalysisResult:
        """
        Detect customer tone from message

        Args:
            message: Customer's message text

        Returns:
            ToneAnalysisResult with detected tone and confidence
        """
        if not message or not message.strip():
            return ToneAnalysisResult(
                detected_tone=CustomerTone.CASUAL,
                confidence=0.5,
                scores={},
                reasoning="Empty message, defaulting to casual",
            )

        # Calculate scores for each tone
        scores = {}
        for tone, patterns in self.patterns.items():
            score = self._calculate_tone_score(message, patterns)
            scores[tone.value] = score

        # Find highest scoring tone
        max_tone = max(scores.items(), key=lambda x: x[1])
        detected_tone = CustomerTone(max_tone[0])
        confidence = max_tone[1]

        # If confidence is too low, default to casual (safest fallback)
        if confidence < 0.2:
            detected_tone = CustomerTone.CASUAL
            confidence = 0.5
            reasoning = "Low confidence, defaulting to casual tone"
        else:
            reasoning = self._generate_reasoning(detected_tone, message, scores)

        return ToneAnalysisResult(
            detected_tone=detected_tone, confidence=confidence, scores=scores, reasoning=reasoning
        )

    def _calculate_tone_score(self, message: str, patterns: list) -> float:
        """
        Calculate tone score based on pattern matches

        Args:
            message: Customer message
            patterns: List of compiled regex patterns

        Returns:
            Score between 0.0 and 1.0
        """
        matches = 0
        for pattern in patterns:
            if pattern.search(message):
                matches += 1

        # Normalize score by number of patterns
        if not patterns:
            return 0.0

        return min(1.0, matches / len(patterns) * 2)  # Multiply by 2 to boost strong matches

    def _generate_reasoning(
        self, detected_tone: CustomerTone, message: str, scores: Dict[str, float]
    ) -> str:
        """Generate human-readable reasoning for tone detection"""

        reasoning_map = {
            CustomerTone.FORMAL: "Professional language detected (corporate vocabulary, polite phrasing)",
            CustomerTone.CASUAL: "Casual communication detected (friendly tone, emojis, informal language)",
            CustomerTone.DIRECT: "Direct communication detected (short message, fact-focused)",
            CustomerTone.WARM: "Warm/enthusiastic tone detected (celebration words, excitement markers)",
            CustomerTone.ANXIOUS: "Anxious tone detected (uncertainty markers, multiple questions)",
        }

        # Get top 3 tones
        top_tones = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

        reasoning = reasoning_map.get(detected_tone, "Tone detected based on message analysis")

        # Add confidence breakdown
        if len(top_tones) > 1:
            reasoning += f" | Top scores: {', '.join([f'{t}: {s:.2f}' for t, s in top_tones])}"

        return reasoning

    def get_response_guidelines(self, tone: CustomerTone) -> Dict[str, str]:
        """
        Get response guidelines for a given tone

        Args:
            tone: Detected customer tone

        Returns:
            Dictionary with response guidelines
        """
        guidelines = {
            CustomerTone.FORMAL: {
                "greeting": "Good morning/afternoon",
                "style": "Professional, detailed, polished",
                "length": "Medium-long (3-5 sentences)",
                "emoji_usage": "Minimal or none",
                "example": "Good afternoon, and thank you for your inquiry. I would be delighted to assist you with your event planning.",
            },
            CustomerTone.CASUAL: {
                "greeting": "Hey! / Hi there!",
                "style": "Friendly, conversational, warm",
                "length": "Medium (2-4 sentences)",
                "emoji_usage": "Moderate (2-3 per message)",
                "example": "Hey there! 🔥 So excited to help you plan this! Let's make it epic! 🎉",
            },
            CustomerTone.DIRECT: {
                "greeting": "Hi",
                "style": "Concise, efficient, fact-focused",
                "length": "Short (1-3 sentences)",
                "emoji_usage": "Minimal",
                "example": "For 10 guests: $550 total (party minimum). This includes your choice of 2 proteins...",
            },
            CustomerTone.WARM: {
                "greeting": "Oh my gosh!",
                "style": "Enthusiastic, celebratory, personal",
                "length": "Medium-long (3-5 sentences)",
                "emoji_usage": "Heavy (3-5 per message)",
                "example": "Oh my gosh, a sweet 16 — what an incredible milestone! 🎉✨ I LOVE this idea!",
            },
            CustomerTone.ANXIOUS: {
                "greeting": "I completely understand",
                "style": "Reassuring, patient, step-by-step",
                "length": "Long (4-6 sentences)",
                "emoji_usage": "Light (1-2 calming emojis)",
                "example": "I completely understand — planning something new can feel overwhelming, but I promise you're in great hands!",
            },
        }

        return guidelines.get(tone, guidelines[CustomerTone.CASUAL])

    def should_escalate_to_human(self, message: str, tone: CustomerTone) -> bool:
        """
        Determine if message should be escalated to human based on complexity

        Args:
            message: Customer message
            tone: Detected tone

        Returns:
            True if should escalate, False otherwise
        """
        # Escalation triggers
        escalation_keywords = [
            r"\b(cancel|refund|complaint|problem|issue|wrong|mistake)\b",
            r"\b(speak to|talk to|manager|supervisor)\b",
            r"\b(unhappy|disappointed|upset|frustrated)\b",
            r"\b(urgent|emergency|asap)\b",
        ]

        for pattern in escalation_keywords:
            if re.search(pattern, message, re.IGNORECASE):
                return True

        # Anxious tone with long message (might need personal attention)
        if tone == CustomerTone.ANXIOUS and len(message) > 200:
            return True

        return False

    def adapt_prompt_for_tone(self, base_prompt: str, tone: CustomerTone) -> str:
        """
        Adapt system prompt based on detected tone

        Args:
            base_prompt: Base system prompt
            tone: Detected customer tone

        Returns:
            Adapted system prompt
        """
        tone_adaptations = {
            CustomerTone.FORMAL: """
**TONE ADAPTATION - FORMAL CUSTOMER**:
- Use professional, polished language
- Address as "you" or "your company"
- Provide detailed explanations with all relevant information
- Use complete sentences, proper punctuation
- Minimal or no emojis
- Structure responses with clear sections
- Example: "Good afternoon, and thank you for your inquiry..."
""",
            CustomerTone.CASUAL: """
**TONE ADAPTATION - CASUAL CUSTOMER**:
- Use friendly, conversational language
- Include 2-3 emojis per message (🔥, ✨, 🎉)
- Keep it warm and approachable
- Use contractions ("you're", "let's", "we'll")
- Add excitement and energy
- Example: "Hey there! 🔥 Great question! For 12 people..."
""",
            CustomerTone.DIRECT: """
**TONE ADAPTATION - DIRECT CUSTOMER**:
- Be concise and fact-focused
- Lead with the answer immediately
- Keep it professional but efficient
- Minimal emojis (optional: checkmark ✅)
- One short paragraph maximum
- Example: "For 10 guests: $550 total (party minimum)..."
""",
            CustomerTone.WARM: """
**TONE ADAPTATION - WARM CUSTOMER**:
- Match their high energy and excitement
- Use 3-5 emojis per message (🎉, ✨, ❤️, 🥰)
- Celebrate with them
- Show genuine enthusiasm
- Build emotional connection
- Example: "Oh my gosh, a sweet 16 — what an incredible milestone! 🎉✨"
""",
            CustomerTone.ANXIOUS: """
**TONE ADAPTATION - ANXIOUS CUSTOMER**:
- Be extra reassuring and supportive
- Use calming language ("I promise", "Don't worry")
- Break down information step-by-step
- Address concerns proactively
- 1-2 calming emojis (✨, 💙)
- Example: "I completely understand — planning something new can feel overwhelming..."
""",
        }

        adaptation = tone_adaptations.get(tone, tone_adaptations[CustomerTone.CASUAL])

        return base_prompt + "\n" + adaptation

    def get_tone_statistics(self, messages: list[str]) -> Dict[str, any]:
        """
        Analyze tone distribution across multiple messages

        Args:
            messages: List of customer messages

        Returns:
            Dictionary with tone statistics
        """
        tone_counts = {tone.value: 0 for tone in CustomerTone}
        total_confidence = 0.0

        for message in messages:
            result = self.detect_tone(message)
            tone_counts[result.detected_tone.value] += 1
            total_confidence += result.confidence

        total_messages = len(messages)
        avg_confidence = total_confidence / total_messages if total_messages > 0 else 0

        return {
            "total_messages": total_messages,
            "tone_distribution": {
                tone: count / total_messages if total_messages > 0 else 0
                for tone, count in tone_counts.items()
            },
            "average_confidence": avg_confidence,
            "dominant_tone": (
                max(tone_counts.items(), key=lambda x: x[1])[0] if tone_counts else None
            ),
        }


# ============================================================================
# Utility Functions
# ============================================================================


def analyze_customer_tone(message: str) -> ToneAnalysisResult:
    """
    Convenience function for quick tone analysis

    Args:
        message: Customer message

    Returns:
        ToneAnalysisResult
    """
    analyzer = ToneAnalyzer()
    return analyzer.detect_tone(message)


def get_tone_adapted_prompt(base_prompt: str, message: str) -> str:
    """
    Convenience function to get tone-adapted prompt

    Args:
        base_prompt: Base system prompt
        message: Customer message

    Returns:
        Adapted system prompt
    """
    analyzer = ToneAnalyzer()
    result = analyzer.detect_tone(message)
    return analyzer.adapt_prompt_for_tone(base_prompt, result.detected_tone)
