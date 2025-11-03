"""
Pricing Configuration for OpenAI Models

Tracks current pricing per 1,000 tokens for accurate cost monitoring.
Update these values if OpenAI changes pricing or you switch models.
"""

from typing import Dict, Tuple

# Pricing as of October 2025 (USD per 1,000 tokens)
# Format: "model": (input_per_1k, output_per_1k)
PRICES_USD_PER_1K_TOKENS: Dict[str, Tuple[float, float]] = {
    # GPT-4o models (current flagship)
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-2024-08-06": (2.50, 10.00),
    
    # GPT-4o-mini models (recommended for production)
    "gpt-4o-mini": (0.150, 0.600),
    "gpt-4o-mini-2024-07-18": (0.150, 0.600),
    
    # GPT-4 Turbo (legacy)
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4-turbo-2024-04-09": (10.00, 30.00),
    
    # GPT-4 (legacy)
    "gpt-4": (30.00, 60.00),
    "gpt-4-0613": (30.00, 60.00),
    
    # GPT-3.5 Turbo (legacy)
    "gpt-3.5-turbo": (0.50, 1.50),
    "gpt-3.5-turbo-0125": (0.50, 1.50),
    
    # Fine-tuned models (custom pricing)
    "ft:gpt-4o-mini": (0.300, 1.200),  # Fine-tuning doubles the cost
    "ft:gpt-3.5-turbo": (3.00, 6.00),
    
    # Embeddings models
    "text-embedding-3-small": (0.020, 0.0),  # No output cost for embeddings
    "text-embedding-3-large": (0.130, 0.0),
    "text-embedding-ada-002": (0.100, 0.0),
}

# Default pricing if model not found (conservative estimate)
DEFAULT_PRICING: Tuple[float, float] = (0.150, 0.600)  # gpt-4o-mini pricing


def get_model_pricing(model: str) -> Tuple[float, float]:
    """
    Get pricing for a specific model.
    
    Args:
        model: Model identifier (e.g., "gpt-4o-mini")
    
    Returns:
        Tuple of (input_price_per_1k, output_price_per_1k)
    
    Examples:
        >>> get_model_pricing("gpt-4o-mini")
        (0.150, 0.600)
        
        >>> get_model_pricing("unknown-model")
        (0.150, 0.600)  # Falls back to default
    """
    # Try exact match
    if model in PRICES_USD_PER_1K_TOKENS:
        return PRICES_USD_PER_1K_TOKENS[model]
    
    # Try prefix match (for fine-tuned models with unique IDs)
    for known_model, pricing in PRICES_USD_PER_1K_TOKENS.items():
        if model.startswith(known_model):
            return pricing
    
    # Fall back to default
    return DEFAULT_PRICING


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost for a single API call.
    
    Args:
        model: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Cost in USD
    
    Examples:
        >>> calculate_cost("gpt-4o-mini", 1000, 500)
        0.45  # (1000/1000)*0.150 + (500/1000)*0.600
    """
    input_price, output_price = get_model_pricing(model)
    
    input_cost = (input_tokens / 1000.0) * input_price
    output_cost = (output_tokens / 1000.0) * output_price
    
    return round(input_cost + output_cost, 4)


# Cost thresholds (USD)
MONTHLY_ALERT_THRESHOLD = 500.00  # Alert when monthly spend hits $500
DAILY_ALERT_THRESHOLD = 50.00     # Alert when daily spend hits $50 (projects to $1,500/month)

# Expected conversation costs (for projections)
EXPECTED_COST_PER_CONVERSATION = {
    "gpt-4o-mini": 0.009,      # ~600 input + 200 output tokens
    "gpt-4o": 0.045,           # Same tokens, 5x more expensive
    "ft:gpt-4o-mini": 0.018,   # Fine-tuned = 2x base cost
}
