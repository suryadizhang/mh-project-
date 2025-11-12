"""
Enhanced NLP Service with spaCy + sentence-transformers
Provides better tone detection, entity extraction, and semantic search
"""

import spacy
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class EnhancedNLPService:
    """
    Lightweight NLP enhancement layer using spaCy + sentence-transformers
    No GPU required, <50ms inference time
    """

    def __init__(self):
        self.nlp = None
        self.semantic_model = None
        self._initialized = False

    def initialize(self):
        """
        Lazy initialization - load models on first use
        This prevents blocking app startup
        """
        if self._initialized:
            return

        try:
            # Load spaCy model (40MB, fast loading)
            logger.info("Loading spaCy model...")
            self.nlp = spacy.load("en_core_web_sm")

            # Load sentence-transformer (80MB, for semantic search)
            logger.info("Loading sentence-transformer model...")
            self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")

            self._initialized = True
            logger.info("✅ Enhanced NLP models loaded successfully")

        except Exception as e:
            logger.error(f"❌ Failed to load NLP models: {e}")
            logger.info("Falling back to rule-based system")
            self._initialized = False

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities: dates, numbers, names, locations

        Examples:
        - "50 people on December 15th" → {"CARDINAL": ["50"], "DATE": ["December 15th"]}
        - "John Smith at 123 Main St" → {"PERSON": ["John Smith"], "ADDRESS": ["123 Main St"]}
        """
        if not self._initialized:
            self.initialize()

        if not self.nlp:
            return self._fallback_entity_extraction(text)

        doc = self.nlp(text)
        entities = {}

        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)

        return entities

    def detect_tone_enhanced(self, text: str) -> Tuple[str, float]:
        """
        Enhanced tone detection using spaCy sentiment + linguistic features

        Returns: (tone, confidence)
        Tones: formal, casual, anxious, warm, direct
        """
        if not self._initialized:
            self.initialize()

        if not self.nlp:
            return self._fallback_tone_detection(text)

        doc = self.nlp(text)

        # Feature extraction
        features = {
            "has_greeting": any(
                token.text.lower() in ["hi", "hello", "hey", "good morning", "good afternoon"]
                for token in doc
            ),
            "has_question": "?" in text,
            "has_exclamation": "!" in text,
            "word_count": len([token for token in doc if not token.is_punct]),
            "avg_word_length": sum(len(token.text) for token in doc if not token.is_punct)
            / max(len([token for token in doc if not token.is_punct]), 1),
            "has_emoji": bool(re.search(r"[😀-🙏]", text)),
            "has_formal_words": any(
                token.text.lower() in ["inquiring", "regarding", "kindly", "please", "sir", "madam"]
                for token in doc
            ),
            "has_casual_words": any(
                token.text.lower() in ["wanna", "gonna", "yeah", "cool", "awesome", "hey"]
                for token in doc
            ),
            "has_anxiety_markers": any(
                token.text.lower() in ["nervous", "worried", "anxious", "scared", "unsure", "help"]
                for token in doc
            ),
            "sentence_count": len(list(doc.sents)),
            "has_capitals": sum(1 for c in text if c.isupper())
            > len(text) * 0.3,  # >30% caps = shouting
        }

        # Tone classification with confidence
        confidence = 0.0
        tone = "casual"  # default

        # Formal detection
        if features["has_formal_words"] or (
            features["avg_word_length"] > 5 and not features["has_emoji"]
        ):
            tone = "formal"
            confidence = 0.85 if features["has_formal_words"] else 0.70

        # Anxious detection (high priority)
        elif features["has_anxiety_markers"] or (
            features["sentence_count"] > 3 and features["has_question"]
        ):
            tone = "anxious"
            confidence = 0.90 if features["has_anxiety_markers"] else 0.75

        # Warm detection
        elif features["has_emoji"] and features["has_exclamation"]:
            tone = "warm"
            confidence = 0.80

        # Casual detection
        elif features["has_casual_words"] or features["has_emoji"]:
            tone = "casual"
            confidence = 0.85 if features["has_casual_words"] else 0.70

        # Direct detection
        elif features["word_count"] < 10 and not features["has_question"]:
            tone = "direct"
            confidence = 0.75

        return tone, confidence

    def semantic_search_faqs(self, query: str, faq_list: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        Semantic search for FAQs - finds similar questions even if worded differently

        Example:
        - Query: "How much for 50 peeps?"
        - Matches: "How much does My Hibachi Chef cost?" (even though words are different)
        """
        if not self._initialized:
            self.initialize()

        if not self.semantic_model:
            return self._fallback_keyword_search(query, faq_list, top_k)

        # Encode query
        query_embedding = self.semantic_model.encode(query)

        # Encode all FAQ questions
        faq_questions = [faq["question"] for faq in faq_list]
        faq_embeddings = self.semantic_model.encode(faq_questions)

        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity

        similarities = cosine_similarity([query_embedding], faq_embeddings)[0]

        # Get top-k results
        top_indices = similarities.argsort()[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0.3:  # Threshold for relevance
                results.append(
                    {
                        **faq_list[idx],
                        "similarity_score": float(similarities[idx]),
                        "confidence": "high" if similarities[idx] > 0.7 else "medium",
                    }
                )

        return results

    def extract_booking_details(self, text: str) -> Dict[str, any]:
        """
        Extract booking-related information from text

        Returns: {
            'guest_count': int,
            'date': str,
            'time': str,
            'location': str,
            'proteins': List[str],
            'add_ons': List[str]
        }
        """
        if not self._initialized:
            self.initialize()

        entities = self.extract_entities(text)

        # Extract guest count
        guest_count = None
        if "CARDINAL" in entities:
            for num in entities["CARDINAL"]:
                if num.isdigit() and 5 <= int(num) <= 200:  # Reasonable party size
                    guest_count = int(num)
                    break

        # Extract dates
        dates = entities.get("DATE", [])

        # Extract locations
        locations = entities.get("GPE", []) + entities.get("LOC", [])

        # Extract proteins (keyword matching)
        proteins = []
        protein_keywords = [
            "chicken",
            "steak",
            "shrimp",
            "scallops",
            "salmon",
            "tofu",
            "lobster",
            "filet",
        ]
        for keyword in protein_keywords:
            if keyword in text.lower():
                proteins.append(keyword.capitalize())

        # Extract add-ons
        add_ons = []
        addon_keywords = ["noodles", "yakisoba", "fried rice", "gyoza", "edamame", "vegetables"]
        for keyword in addon_keywords:
            if keyword in text.lower():
                add_ons.append(keyword.capitalize())

        return {
            "guest_count": guest_count,
            "dates": dates,
            "locations": locations,
            "proteins": proteins,
            "add_ons": add_ons,
            "confidence": "high" if guest_count else "low",
        }

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for better matching
        - Fix common typos
        - Expand contractions
        - Standardize slang
        """
        if not self._initialized:
            self.initialize()

        # Common substitutions
        replacements = {
            "wanna": "want to",
            "gonna": "going to",
            "gotta": "got to",
            "lemme": "let me",
            "gimme": "give me",
            "ppl": "people",
            "peeps": "people",
            "thx": "thanks",
            "tho": "though",
            "ur": "your",
            "rn": "right now",
        }

        normalized = text.lower()
        for old, new in replacements.items():
            normalized = re.sub(r"\b" + old + r"\b", new, normalized)

        return normalized

    # ========== Fallback Methods (if models fail to load) ==========

    def _fallback_entity_extraction(self, text: str) -> Dict[str, List[str]]:
        """Simple regex-based entity extraction"""
        entities = {}

        # Extract numbers
        numbers = re.findall(r"\b\d+\b", text)
        if numbers:
            entities["CARDINAL"] = numbers

        # Extract dates (simple patterns)
        date_patterns = [
            r"(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}",
            r"\d{1,2}/\d{1,2}/\d{2,4}",
            r"\d{1,2}-\d{1,2}-\d{2,4}",
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        if dates:
            entities["DATE"] = dates

        return entities

    def _fallback_tone_detection(self, text: str) -> Tuple[str, float]:
        """Rule-based tone detection (current system)"""
        text_lower = text.lower()

        # Formal indicators
        if any(
            word in text_lower
            for word in ["inquiring", "regarding", "kindly", "please sir", "please madam"]
        ):
            return "formal", 0.70

        # Anxious indicators
        if any(
            word in text_lower for word in ["nervous", "worried", "anxious", "scared", "help me"]
        ):
            return "anxious", 0.75

        # Casual indicators
        if any(word in text_lower for word in ["hey", "wanna", "gonna", "yeah", "😊", "🎉"]):
            return "casual", 0.70

        # Default
        return "casual", 0.60

    def _fallback_keyword_search(self, query: str, faq_list: List[Dict], top_k: int) -> List[Dict]:
        """Simple keyword-based FAQ search"""
        query_words = set(query.lower().split())

        scored_faqs = []
        for faq in faq_list:
            question_words = set(faq["question"].lower().split())
            overlap = len(query_words & question_words)
            if overlap > 0:
                scored_faqs.append(
                    {**faq, "similarity_score": overlap / len(query_words), "confidence": "medium"}
                )

        scored_faqs.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_faqs[:top_k]


# Singleton instance
_nlp_service = None


def get_nlp_service() -> EnhancedNLPService:
    """Get or create NLP service instance"""
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = EnhancedNLPService()
        _nlp_service.initialize()
    return _nlp_service
