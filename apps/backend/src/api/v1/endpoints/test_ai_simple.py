"""
Simple AI test endpoint - bypasses all dependencies
"""

from fastapi import APIRouter
import sys

sys.path.insert(0, "/app/src")

from api.ai.endpoints.services.openai_service import OpenAIService
from config.ai_booking_config import AI_BOOKING_CONFIG

router = APIRouter()


@router.post("/test-ai-simple")
async def test_ai_simple(message: str):
    """Simple AI test that bypasses all dependencies"""
    try:
        # Create OpenAI service directly
        openai_svc = OpenAIService()

        # Simple system prompt
        system_prompt = f"""You are a helpful assistant for My Hibachi Chef.
        
Pricing: Adults ${AI_BOOKING_CONFIG['pricing']['adult_price']}, Children ${AI_BOOKING_CONFIG['pricing']['child_price']}
Brand Voice: {', '.join(AI_BOOKING_CONFIG['brand_voice'])}

Answer the customer's question about pricing."""

        # Generate response
        response_tuple = await openai_svc.generate_response(message=message, context=system_prompt)

        return {
            "success": True,
            "response": response_tuple[0],
            "model": response_tuple[2],
            "pricing_used": {
                "adult": AI_BOOKING_CONFIG["pricing"]["adult_price"],
                "child": AI_BOOKING_CONFIG["pricing"]["child_price"],
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e), "type": type(e).__name__}
