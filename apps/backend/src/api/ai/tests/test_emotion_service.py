"""
Emotion Detection Service Tests

Tests for emotion detection, sentiment analysis, and agent tone adjustment.

Author: MyHibachi Development Team
Created: October 31, 2025
Phase: 1B - Intelligence Layer
"""

import pytest
import asyncio
from datetime import datetime
from api.ai.services.emotion_service import EmotionService, EmotionResult


class TestEmotionService:
    """Test suite for EmotionService"""
    
    @pytest.fixture
    def emotion_service(self):
        """Create emotion service instance for testing"""
        return EmotionService()
    
    def test_emotion_result_model(self):
        """Test EmotionResult data model"""
        result = EmotionResult(
            score=0.25,
            label="negative",
            confidence=0.9,
            should_escalate=True,
            detected_emotions=["anger", "frustration"],
            reasoning="Customer expressed strong dissatisfaction"
        )
        
        assert result.score == 0.25
        assert result.label == "negative"
        assert result.should_escalate is True
        assert "anger" in result.detected_emotions
        assert isinstance(result.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_detect_very_negative_emotion(self, emotion_service):
        """Test detection of very negative emotion (should escalate)"""
        text = "This is absolutely terrible! I'm furious and want a refund immediately!"
        
        result = await emotion_service.detect_emotion(text)
        
        print(f"\n[TEST] Very Negative Emotion")
        print(f"  Text: {text}")
        print(f"  Score: {result.score:.2f}")
        print(f"  Label: {result.label}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Should Escalate: {result.should_escalate}")
        print(f"  Emotions: {result.detected_emotions}")
        print(f"  Reasoning: {result.reasoning}")
        
        # Very negative should have low score
        assert result.score < 0.4, f"Expected negative score, got {result.score}"
        assert result.label == "negative"
        
        # Very negative should trigger escalation
        if result.score < EmotionService.ESCALATION_THRESHOLD:
            assert result.should_escalate is True
    
    @pytest.mark.asyncio
    async def test_detect_neutral_emotion(self, emotion_service):
        """Test detection of neutral emotion (factual inquiry)"""
        text = "What's your cancellation policy?"
        
        result = await emotion_service.detect_emotion(text)
        
        print(f"\n[TEST] Neutral Emotion")
        print(f"  Text: {text}")
        print(f"  Score: {result.score:.2f}")
        print(f"  Label: {result.label}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Should Escalate: {result.should_escalate}")
        
        # Neutral should have mid-range score
        assert 0.4 <= result.score <= 0.6, f"Expected neutral score, got {result.score}"
        assert result.label == "neutral"
        assert result.should_escalate is False
    
    @pytest.mark.asyncio
    async def test_detect_positive_emotion(self, emotion_service):
        """Test detection of positive emotion"""
        text = "This sounds amazing! I'm so excited to book with you!"
        
        result = await emotion_service.detect_emotion(text)
        
        print(f"\n[TEST] Positive Emotion")
        print(f"  Text: {text}")
        print(f"  Score: {result.score:.2f}")
        print(f"  Label: {result.label}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Emotions: {result.detected_emotions}")
        
        # Positive should have high score
        assert result.score > 0.6, f"Expected positive score, got {result.score}"
        assert result.label == "positive"
        assert result.should_escalate is False
    
    def test_score_to_label_conversion(self, emotion_service):
        """Test emotion score to label conversion"""
        assert emotion_service._score_to_label(0.2) == "negative"
        assert emotion_service._score_to_label(0.5) == "neutral"
        assert emotion_service._score_to_label(0.8) == "positive"
    
    def test_agent_tone_adjustment_negative(self, emotion_service):
        """Test agent tone adjustment for negative emotion"""
        original_prompt = "You are a helpful customer service agent."
        
        negative_emotion = EmotionResult(
            score=0.25,
            label="negative",
            confidence=0.9,
            should_escalate=True,
            detected_emotions=["anger", "frustration"]
        )
        
        adjusted_prompt = emotion_service.adjust_agent_tone(
            original_prompt,
            negative_emotion
        )
        
        print(f"\n[TEST] Tone Adjustment for Negative Emotion")
        print(f"  Original length: {len(original_prompt)} chars")
        print(f"  Adjusted length: {len(adjusted_prompt)} chars")
        
        # Adjusted prompt should be longer (added empathy instructions)
        assert len(adjusted_prompt) > len(original_prompt)
        
        # Should contain empathy keywords
        assert "empathy" in adjusted_prompt.lower()
        assert "apologize" in adjusted_prompt.lower() or "sorry" in adjusted_prompt.lower()
        
        # Should contain escalation notice if should_escalate is True
        if negative_emotion.should_escalate:
            assert "ESCALATION" in adjusted_prompt
    
    def test_agent_tone_adjustment_neutral(self, emotion_service):
        """Test agent tone adjustment for neutral emotion (no change)"""
        original_prompt = "You are a helpful customer service agent."
        
        neutral_emotion = EmotionResult(
            score=0.5,
            label="neutral",
            confidence=0.9,
            should_escalate=False,
            detected_emotions=["curiosity"]
        )
        
        adjusted_prompt = emotion_service.adjust_agent_tone(
            original_prompt,
            neutral_emotion
        )
        
        # Neutral emotion should not modify prompt
        assert adjusted_prompt == original_prompt
    
    def test_should_escalate_logic(self, emotion_service):
        """Test escalation logic"""
        very_negative = EmotionResult(
            score=0.15,
            label="negative",
            confidence=0.9,
            should_escalate=True,
            detected_emotions=["anger"]
        )
        
        neutral = EmotionResult(
            score=0.5,
            label="neutral",
            confidence=0.9,
            should_escalate=False,
            detected_emotions=[]
        )
        
        assert emotion_service.should_escalate(very_negative) is True
        assert emotion_service.should_escalate(neutral) is False
    
    @pytest.mark.asyncio
    async def test_detect_emotion_with_context(self, emotion_service):
        """Test emotion detection with additional context"""
        text = "I'm disappointed again. This keeps happening."
        
        context = {
            "is_repeat_customer": True,
            "previous_issue": True,
            "channel": "webchat"
        }
        
        result = await emotion_service.detect_emotion(text, context)
        
        print(f"\n[TEST] Emotion with Context")
        print(f"  Text: {text}")
        print(f"  Context: {context}")
        print(f"  Score: {result.score:.2f}")
        print(f"  Label: {result.label}")
        
        # With context of repeat issues, should be more negative
        assert result.score < 0.5
        assert result.label == "negative"
    
    def test_emotion_trend_improving(self, emotion_service):
        """Test emotion trend analysis - improving conversation"""
        emotions = [
            EmotionResult(score=0.2, label="negative", confidence=0.9, should_escalate=True, detected_emotions=[]),
            EmotionResult(score=0.3, label="negative", confidence=0.9, should_escalate=False, detected_emotions=[]),
            EmotionResult(score=0.5, label="neutral", confidence=0.9, should_escalate=False, detected_emotions=[]),
            EmotionResult(score=0.7, label="positive", confidence=0.9, should_escalate=False, detected_emotions=[])
        ]
        
        trend = emotion_service.get_emotion_trend(emotions)
        
        print(f"\n[TEST] Emotion Trend - Improving")
        print(f"  Trend: {trend['trend']}")
        print(f"  Direction: {trend['direction']}")
        print(f"  Average: {trend['average_score']:.2f}")
        print(f"  Change: {trend['change']:.2f}")
        
        assert trend["trend"] == "improving"
        assert trend["direction"] == "positive"
        assert trend["change"] > 0
    
    def test_emotion_trend_declining(self, emotion_service):
        """Test emotion trend analysis - declining conversation"""
        emotions = [
            EmotionResult(score=0.7, label="positive", confidence=0.9, should_escalate=False, detected_emotions=[]),
            EmotionResult(score=0.5, label="neutral", confidence=0.9, should_escalate=False, detected_emotions=[]),
            EmotionResult(score=0.3, label="negative", confidence=0.9, should_escalate=False, detected_emotions=[]),
            EmotionResult(score=0.2, label="negative", confidence=0.9, should_escalate=True, detected_emotions=[])
        ]
        
        trend = emotion_service.get_emotion_trend(emotions)
        
        print(f"\n[TEST] Emotion Trend - Declining")
        print(f"  Trend: {trend['trend']}")
        print(f"  Direction: {trend['direction']}")
        print(f"  Average: {trend['average_score']:.2f}")
        print(f"  Change: {trend['change']:.2f}")
        
        assert trend["trend"] == "declining"
        assert trend["direction"] == "negative"
        assert trend["change"] < 0


async def run_emotion_tests():
    """Run emotion service tests"""
    print("=" * 80)
    print("EMOTION SERVICE TESTS")
    print("=" * 80)
    
    service = EmotionService()
    
    # Test 1: Very negative emotion
    print("\n[TEST 1] Detecting Very Negative Emotion...")
    result1 = await service.detect_emotion(
        "This is absolutely terrible! I'm furious and want my money back!"
    )
    print(f"✓ Score: {result1.score:.2f}, Label: {result1.label}, Escalate: {result1.should_escalate}")
    
    # Test 2: Neutral emotion
    print("\n[TEST 2] Detecting Neutral Emotion...")
    result2 = await service.detect_emotion(
        "What's your cancellation policy?"
    )
    print(f"✓ Score: {result2.score:.2f}, Label: {result2.label}, Escalate: {result2.should_escalate}")
    
    # Test 3: Positive emotion
    print("\n[TEST 3] Detecting Positive Emotion...")
    result3 = await service.detect_emotion(
        "This sounds amazing! I can't wait to book!"
    )
    print(f"✓ Score: {result3.score:.2f}, Label: {result3.label}, Escalate: {result3.should_escalate}")
    
    # Test 4: Tone adjustment
    print("\n[TEST 4] Testing Tone Adjustment...")
    original_prompt = "You are a helpful assistant."
    adjusted = service.adjust_agent_tone(original_prompt, result1)
    print(f"✓ Original: {len(original_prompt)} chars")
    print(f"✓ Adjusted: {len(adjusted)} chars (added empathy instructions)")
    
    # Test 5: Emotion trend
    print("\n[TEST 5] Testing Emotion Trend...")
    trend = service.get_emotion_trend([result1, result2, result3])
    print(f"✓ Trend: {trend['trend']}, Direction: {trend['direction']}")
    
    print("\n" + "=" * 80)
    print("ALL EMOTION TESTS COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_emotion_tests())
