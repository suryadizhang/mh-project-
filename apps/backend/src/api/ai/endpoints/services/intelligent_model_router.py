"""
Intelligent AI Model Router
Selects optimal OpenAI model based on query complexity for cost optimization
"""

import logging
import re
from typing import Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class IntelligentModelRouter:
    """
    Routes queries to appropriate AI model:
    - GPT-3.5-turbo: Simple FAQ queries (80% cost savings vs GPT-4)
    - GPT-4-turbo: Complex reasoning, multi-step questions
    - GPT-4: High-stakes conversations, complaints, complex bookings
    """
    
    def __init__(self):
        # Model pricing (per 1K tokens, approximate)
        self.model_costs = {
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06}
        }
        
        # Simple question patterns (GPT-3.5)
        self.simple_patterns = [
            # Direct questions with clear answers
            r"\b(what|where|when|who)\s+(is|are|do|does)\b",
            r"\bhow much\b",
            r"\bprice|pricing|cost\b",
            r"\bhours|open|close\b",
            r"\baddress|location|phone|email\b",
            r"\bpayment methods?\b",
            r"\bdo you (accept|take|have)\b",
        ]
        
        # Complex question indicators (GPT-4)
        self.complex_patterns = [
            # Multi-part questions
            r"\b(and|also|additionally|furthermore)\b.*\?",
            r"\?.*\?",  # Multiple questions
            
            # Hypothetical/conditional
            r"\bif\b.*\bthen\b",
            r"\bwhat if\b",
            r"\bsuppose|assuming|hypothetically\b",
            
            # Comparison/analysis
            r"\bcompare|versus|vs\b",
            r"\bdifference between\b",
            r"\bbetter|best|recommend\b",
            
            # Planning/strategy
            r"\bplan|strategy|approach\b",
            r"\bhow (can|should|would) (i|we)\b",
            
            # Complaints/escalation
            r"\bcomplaint|problem|issue|wrong\b",
            r"\bnot (satisfied|happy|working)\b",
            r"\bdisappointed|frustrated|angry\b",
        ]
        
        # Context clues for complexity scoring
        self.complexity_indicators = {
            "high": [
                "customize", "special request", "dietary restriction",
                "corporate event", "large party", "multi-day",
                "complicated", "specific", "detailed", "explain why"
            ],
            "medium": [
                "options", "available", "alternatives", "which",
                "recommendations", "suggest", "help me choose"
            ],
            "low": [
                "yes", "no", "ok", "thanks", "got it",
                "simple", "basic", "standard", "regular"
            ]
        }
        
        # Conversation context tracking
        self.conversation_complexity = {}
        
        logger.info("Intelligent Model Router initialized")
    
    def calculate_query_complexity(
        self, 
        message: str, 
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Calculate query complexity score (0-10)
        Returns model recommendation and reasoning
        """
        score = 5.0  # Start neutral
        factors = []
        
        message_lower = message.lower()
        word_count = len(message.split())
        
        # Factor 1: Message length
        if word_count < 5:
            score -= 2
            factors.append("short_query")
        elif word_count > 30:
            score += 2
            factors.append("long_query")
        
        # Factor 2: Simple patterns (lower score)
        simple_matches = sum(
            1 for pattern in self.simple_patterns 
            if re.search(pattern, message_lower)
        )
        if simple_matches > 0:
            score -= simple_matches * 1.5
            factors.append(f"simple_pattern_matches_{simple_matches}")
        
        # Factor 3: Complex patterns (higher score)
        complex_matches = sum(
            1 for pattern in self.complex_patterns 
            if re.search(pattern, message_lower)
        )
        if complex_matches > 0:
            score += complex_matches * 2
            factors.append(f"complex_pattern_matches_{complex_matches}")
        
        # Factor 4: Complexity indicators
        for level, keywords in self.complexity_indicators.items():
            matches = sum(1 for kw in keywords if kw in message_lower)
            if matches > 0:
                if level == "high":
                    score += matches * 1.5
                elif level == "medium":
                    score += matches * 0.5
                elif level == "low":
                    score -= matches * 1
                factors.append(f"{level}_indicators_{matches}")
        
        # Factor 5: Question marks (multiple questions = complex)
        question_marks = message.count("?")
        if question_marks > 1:
            score += question_marks * 1.5
            factors.append(f"multiple_questions_{question_marks}")
        
        # Factor 6: Conversation history
        if conversation_history and len(conversation_history) > 3:
            # Long conversation = context needed = more complex
            score += len(conversation_history) * 0.3
            factors.append(f"conversation_length_{len(conversation_history)}")
        
        # Factor 7: Technical/specific terms
        technical_terms = [
            "custom", "specific", "particular", "exactly", "precise",
            "allergies", "dietary", "restrictions", "requirements"
        ]
        tech_matches = sum(1 for term in technical_terms if term in message_lower)
        if tech_matches > 0:
            score += tech_matches * 1.5
            factors.append(f"technical_terms_{tech_matches}")
        
        # Clamp score between 0-10
        score = max(0, min(10, score))
        
        return {
            "complexity_score": round(score, 2),
            "factors": factors,
            "word_count": word_count,
            "question_marks": question_marks
        }
    
    def select_model(
        self,
        message: str,
        context: Dict[str, Any] = None,
        conversation_history: list = None,
        force_model: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Select optimal model based on query analysis
        
        Returns:
            (model_name, analysis_data)
        """
        if force_model:
            return force_model, {"reason": "forced", "forced_model": force_model}
        
        # Calculate complexity
        complexity_analysis = self.calculate_query_complexity(message, conversation_history)
        score = complexity_analysis["complexity_score"]
        
        # Check for escalation keywords (always use GPT-4)
        escalation_keywords = [
            "complaint", "manager", "supervisor", "refund", "lawsuit",
            "lawyer", "disappointed", "terrible", "worst"
        ]
        if any(kw in message.lower() for kw in escalation_keywords):
            return "gpt-4", {
                **complexity_analysis,
                "model_reason": "escalation_detected",
                "estimated_cost": "high"
            }
        
        # Model selection based on score
        if score <= 3.5:
            # Simple query → GPT-3.5-turbo
            model = "gpt-3.5-turbo"
            reason = "simple_faq_query"
            cost_level = "low"
        elif score <= 6.5:
            # Medium complexity → GPT-4-turbo
            model = "gpt-4-turbo"
            reason = "moderate_complexity"
            cost_level = "medium"
        else:
            # High complexity → GPT-4
            model = "gpt-4"
            reason = "high_complexity"
            cost_level = "high"
        
        # Check user role (admins get better models)
        if context and context.get("user_role") in ["admin", "super_admin", "manager"]:
            if model == "gpt-3.5-turbo":
                model = "gpt-4-turbo"
                reason = "admin_user_upgrade"
        
        logger.info(
            f"Model selected: {model} (score: {score:.1f}, reason: {reason})"
        )
        
        return model, {
            **complexity_analysis,
            "model_reason": reason,
            "estimated_cost": cost_level,
            "selected_model": model
        }
    
    def estimate_cost(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """Estimate cost for a request"""
        if model not in self.model_costs:
            return 0.0
        
        input_cost = (input_tokens / 1000) * self.model_costs[model]["input"]
        output_cost = (output_tokens / 1000) * self.model_costs[model]["output"]
        
        return input_cost + output_cost
    
    def get_savings_report(self, requests_data: list) -> Dict[str, Any]:
        """
        Generate savings report comparing intelligent routing vs always using GPT-4
        
        requests_data: List of {"model": str, "input_tokens": int, "output_tokens": int}
        """
        total_actual_cost = 0
        total_gpt4_cost = 0
        
        model_usage = {}
        
        for req in requests_data:
            model = req["model"]
            input_tokens = req["input_tokens"]
            output_tokens = req["output_tokens"]
            
            # Actual cost
            actual_cost = self.estimate_cost(model, input_tokens, output_tokens)
            total_actual_cost += actual_cost
            
            # Cost if we used GPT-4
            gpt4_cost = self.estimate_cost("gpt-4", input_tokens, output_tokens)
            total_gpt4_cost += gpt4_cost
            
            # Track model usage
            model_usage[model] = model_usage.get(model, 0) + 1
        
        savings = total_gpt4_cost - total_actual_cost
        savings_percent = (savings / total_gpt4_cost * 100) if total_gpt4_cost > 0 else 0
        
        return {
            "total_requests": len(requests_data),
            "actual_cost": round(total_actual_cost, 4),
            "gpt4_cost": round(total_gpt4_cost, 4),
            "savings": round(savings, 4),
            "savings_percent": round(savings_percent, 1),
            "model_distribution": model_usage,
            "avg_cost_per_request": round(total_actual_cost / len(requests_data), 6) if requests_data else 0
        }


# Global instance
model_router = IntelligentModelRouter()


def get_model_router() -> IntelligentModelRouter:
    """Get global model router instance"""
    return model_router
