"""
Similarity Evaluator - Shadow Learning
Compares teacher and student responses using embeddings
"""

import logging
import numpy as np
from typing import Optional
import openai
import os

logger = logging.getLogger(__name__)


async def calculate_similarity(
    text1: str,
    text2: str,
    model: str = "text-embedding-3-small"
) -> float:
    """
    Calculate cosine similarity between two texts using OpenAI embeddings
    
    This measures how similar the student (Llama-3) response is to the
    teacher (GPT-4) response. Higher scores (0.85+) indicate the student
    is learning well.
    
    Args:
        text1: First text (usually teacher response)
        text2: Second text (usually student response)
        model: OpenAI embedding model to use
        
    Returns:
        float: Cosine similarity score between 0 and 1
    """
    
    try:
        # Get embeddings from OpenAI
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.embeddings.create(
            input=[text1, text2],
            model=model
        )
        
        # Extract embedding vectors
        embedding1 = np.array(response.data[0].embedding)
        embedding2 = np.array(response.data[1].embedding)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(embedding1, embedding2)
        
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Failed to calculate similarity: {e}")
        # Return None or 0.0 to indicate failure
        return 0.0


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        float: Cosine similarity (-1 to 1, usually 0 to 1 for text)
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


async def evaluate_response_quality(
    response: str,
    prompt: str,
    criteria: Optional[dict] = None
) -> dict:
    """
    Evaluate response quality using multiple criteria
    
    This can be enhanced with more sophisticated evaluation metrics.
    For now, it checks basic quality indicators.
    
    Args:
        response: The response to evaluate
        prompt: Original prompt
        criteria: Custom evaluation criteria
        
    Returns:
        dict: Quality scores and assessments
    """
    
    # Basic quality checks
    word_count = len(response.split())
    char_count = len(response)
    
    # Check for completeness (not too short)
    min_length_score = min(word_count / 20, 1.0)  # Expect at least 20 words
    
    # Check for coherence (basic heuristic)
    sentences = response.split('.')
    sentence_count = len([s for s in sentences if s.strip()])
    coherence_score = min(sentence_count / 3, 1.0)  # Expect at least 3 sentences
    
    # Check for relevance (contains key terms from prompt)
    prompt_words = set(prompt.lower().split())
    response_words = set(response.lower().split())
    common_words = prompt_words.intersection(response_words)
    relevance_score = len(common_words) / len(prompt_words) if prompt_words else 0.5
    
    # Overall quality (simple average)
    overall_quality = (min_length_score + coherence_score + relevance_score) / 3
    
    return {
        "word_count": word_count,
        "char_count": char_count,
        "sentence_count": sentence_count,
        "min_length_score": round(min_length_score, 3),
        "coherence_score": round(coherence_score, 3),
        "relevance_score": round(relevance_score, 3),
        "overall_quality": round(overall_quality, 3),
        "is_acceptable": overall_quality >= 0.6
    }
