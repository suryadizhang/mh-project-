"""
Local LLM Service - Ollama Integration
Manages local Llama-3 model for Shadow Learning
"""

import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalLLMService:
    """
    Service for interacting with local Ollama-hosted Llama-3 model
    
    Provides methods to generate responses, check health, and get model info.
    Used in Shadow Learning to create student responses alongside teacher (OpenAI).
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Local LLM Service
        
        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
        """
        self.base_url = base_url
        self.model_name = "llama3"  # Can be configured
        self.timeout = 60.0  # 60 seconds for generation
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Ollama service is running and accessible
        
        Returns:
            dict: Health status with available models
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                response.raise_for_status()
                
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                
                return {
                    "status": "healthy",
                    "ollama_url": self.base_url,
                    "models_available": model_names,
                    "llama3_installed": any("llama3" in name for name in model_names),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            return {
                "status": "unhealthy",
                "error": "Ollama service not reachable",
                "ollama_url": self.base_url
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "ollama_url": self.base_url
            }
    
    async def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about the Llama-3 model
        
        Returns:
            dict: Model information or None if unavailable
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": self.model_name},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return None
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Generate a response from local Llama-3 model
        
        Args:
            prompt: User's question/prompt
            context: Optional conversation context
            system_prompt: Optional system instructions
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            dict: Response with text, tokens, and timing info
        """
        start_time = datetime.utcnow()
        
        try:
            # Build the full prompt with context
            full_prompt = ""
            if system_prompt:
                full_prompt += f"System: {system_prompt}\n\n"
            if context:
                full_prompt += f"Context: {context}\n\n"
            full_prompt += f"User: {prompt}\nAssistant:"
            
            # Call Ollama API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
            
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "response": result.get("response", "").strip(),
                "model": self.model_name,
                "total_duration_ms": result.get("total_duration", 0) // 1_000_000,
                "response_time_ms": response_time_ms,
                "eval_count": result.get("eval_count", 0),  # Output tokens
                "prompt_eval_count": result.get("prompt_eval_count", 0),  # Input tokens
                "error": None
            }
            
        except httpx.TimeoutException:
            logger.error(f"Ollama request timeout after {self.timeout}s")
            return {
                "success": False,
                "response": "",
                "error": "Request timeout - Ollama took too long to respond",
                "response_time_ms": int(self.timeout * 1000)
            }
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            return {
                "success": False,
                "response": "",
                "error": "Ollama service not reachable - is it running?",
                "response_time_ms": 0
            }
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            return {
                "success": False,
                "response": "",
                "error": str(e),
                "response_time_ms": response_time_ms
            }
    
    async def generate_parallel_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response optimized for parallel execution with teacher model
        
        This is used in Shadow Learning to get both teacher (OpenAI) and
        student (Llama-3) responses simultaneously.
        
        Args:
            prompt: User's question
            context: Conversation context
            system_prompt: System instructions
            
        Returns:
            dict: Response suitable for comparison with teacher
        """
        # Use slightly higher temperature for diversity
        result = await self.generate_response(
            prompt=prompt,
            context=context,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500
        )
        
        # Add metadata for shadow learning
        result["shadow_learning"] = True
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result


# Singleton instance
_local_llm_service: Optional[LocalLLMService] = None


def get_local_llm_service() -> LocalLLMService:
    """
    Get or create singleton LocalLLMService instance
    
    Returns:
        LocalLLMService: Configured service instance
    """
    global _local_llm_service
    if _local_llm_service is None:
        _local_llm_service = LocalLLMService()
    return _local_llm_service
