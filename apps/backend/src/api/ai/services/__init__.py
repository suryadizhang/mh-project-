"""
AI Services Module

This module contains intelligence layer services for the AI system:
- Emotion Detection: Sentiment analysis from text/voice
- Memory Management: Cross-channel conversation persistence
- Follow-Up Scheduling: Automated customer engagement

Author: MyHibachi Development Team
Created: October 31, 2025
Phase: 1B - Intelligence Layer
"""

from .emotion_service import EmotionResult, EmotionService, get_emotion_service

__all__ = [
    "EmotionResult",
    "EmotionService",
    "get_emotion_service",
]
