"""
OpenAI service for AI lead management integration.
Simple wrapper around the OpenAI client to match existing architecture.
"""
import openai
from typing import Dict, List, Any, Optional
from core.config import get_settings

settings = get_settings()
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    """Simple OpenAI service wrapper for lead management AI features."""
    
    def __init__(self):
        """Initialize OpenAI client with API key from settings."""
        if not settings.openai_api_key:
            logger.warning("openai_api_key not found in settings. AI features will be disabled.")
            self.client = None
        else:
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a chat completion using OpenAI API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: OpenAI model to use
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
            
        Returns:
            Response dictionary with 'content' field
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Check openai_api_key setting.")
            return {"content": "AI service unavailable"}
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": model,
                "usage": response.usage.dict() if response.usage else None
            }
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return {"content": "AI service temporarily unavailable"}
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI service: {e}")
            return {"content": "AI service error"}


# Global instance for dependency injection
_openai_service: Optional[OpenAIService] = None

def get_openai_service() -> OpenAIService:
    """Get global OpenAI service instance."""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service