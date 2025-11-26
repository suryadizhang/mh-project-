"""
Enhanced NLP Service with spaCy + sentence-transformers
Provides better tone detection, entity extraction, and semantic search
With performance monitoring and metrics tracking
"""

import spacy
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple, Any
import re
import logging
import time
from functools import wraps
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ========== Performance Monitoring ==========


class PerformanceMonitor:
    """
    Track performance metrics for NLP operations
    - Execution time per method
    - Call counts
    - Average/min/max latencies
    - Resource usage patterns
    """

    def __init__(self):
        self.metrics = defaultdict(
            lambda: {
                "total_calls": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "errors": 0,
                "last_called": None,
            }
        )
        self.start_time = datetime.now(timezone.utc)

    def record_call(
        self, method_name: str, execution_time: float, success: bool = True
    ):
        """Record a method call with its execution time"""
        metrics = self.metrics[method_name]
        metrics["total_calls"] += 1
        metrics["total_time"] += execution_time
        metrics["min_time"] = min(metrics["min_time"], execution_time)
        metrics["max_time"] = max(metrics["max_time"], execution_time)
        metrics["last_called"] = datetime.now(timezone.utc)

        if not success:
            metrics["errors"] += 1

    def get_metrics(self, method_name: str = None) -> Dict[str, Any]:
        """Get performance metrics for a specific method or all methods"""
        if method_name:
            if method_name not in self.metrics:
                return {}

            m = self.metrics[method_name]
            avg_time = (
                m["total_time"] / m["total_calls"]
                if m["total_calls"] > 0
                else 0
            )

            return {
                "method": method_name,
                "total_calls": m["total_calls"],
                "average_time_ms": round(avg_time * 1000, 2),
                "min_time_ms": (
                    round(m["min_time"] * 1000, 2)
                    if m["min_time"] != float("inf")
                    else 0
                ),
                "max_time_ms": round(m["max_time"] * 1000, 2),
                "total_time_s": round(m["total_time"], 2),
                "errors": m["errors"],
                "error_rate": (
                    round(m["errors"] / m["total_calls"] * 100, 2)
                    if m["total_calls"] > 0
                    else 0
                ),
                "last_called": (
                    m["last_called"].isoformat() if m["last_called"] else None
                ),
            }

        # Return all metrics
        return {
            "uptime_seconds": (
                datetime.now(timezone.utc) - self.start_time
            ).total_seconds(),
            "methods": {
                method: self.get_metrics(method)
                for method in self.metrics.keys()
            },
        }

    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.start_time = datetime.now(timezone.utc)


def monitor_performance(method):
    """Decorator to monitor method performance"""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        success = True

        try:
            result = method(self, *args, **kwargs)
            return result
        except Exception:
            success = False
            raise
        finally:
            execution_time = time.time() - start_time
            if hasattr(self, "performance_monitor"):
                self.performance_monitor.record_call(
                    method.__name__, execution_time, success
                )

    return wrapper


class EnhancedNLPService:
    """
    Lightweight NLP enhancement layer using spaCy + sentence-transformers
    No GPU required, <50ms inference time
    With performance monitoring
    """

    def __init__(self):
        self.nlp = None
        self.semantic_model = None
        self._initialized = False
        self.performance_monitor = PerformanceMonitor()

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
            start_time = time.time()
            self.nlp = spacy.load("en_core_web_sm")
            logger.info(f"✅ spaCy loaded in {time.time() - start_time:.2f}s")

            # Load sentence-transformer (80MB, for semantic search)
            logger.info("Loading sentence-transformer model...")
            start_time = time.time()
            self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info(
                f"✅ sentence-transformer loaded in {time.time() - start_time:.2f}s"
            )

            self._initialized = True
            logger.info("✅ Enhanced NLP models loaded successfully")

        except Exception as e:
            logger.error(f"❌ Failed to load NLP models: {e}")
            logger.info("Falling back to rule-based system")
            self._initialized = False

    @monitor_performance
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

    @monitor_performance
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
                token.text.lower()
                in ["hi", "hello", "hey", "good morning", "good afternoon"]
                for token in doc
            ),
            "has_question": "?" in text,
            "has_exclamation": "!" in text,
            "word_count": len([token for token in doc if not token.is_punct]),
            "avg_word_length": sum(
                len(token.text) for token in doc if not token.is_punct
            )
            / max(len([token for token in doc if not token.is_punct]), 1),
            "has_emoji": bool(re.search(r"[😀-🙏]", text)),
            "has_formal_words": any(
                token.text.lower()
                in [
                    "inquiring",
                    "regarding",
                    "kindly",
                    "please",
                    "sir",
                    "madam",
                ]
                for token in doc
            ),
            "has_casual_words": any(
                token.text.lower()
                in ["wanna", "gonna", "yeah", "cool", "awesome", "hey"]
                for token in doc
            ),
            "has_anxiety_markers": any(
                token.text.lower()
                in [
                    "nervous",
                    "worried",
                    "anxious",
                    "scared",
                    "unsure",
                    "help",
                ]
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

    @monitor_performance
    def semantic_search_faqs(
        self, query: str, faq_list: List[Dict], top_k: int = 3
    ) -> List[Dict]:
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
                        "confidence": (
                            "high" if similarities[idx] > 0.7 else "medium"
                        ),
                    }
                )

        return results

    @monitor_performance
    def extract_booking_details(self, text: str) -> Dict[str, any]:
        """
        Extract comprehensive booking-related information from text

        Returns: {
            'guest_count': int | None,
            'date': str | None,
            'time': str | None,
            'locations': List[str],
            'proteins': List[str],
            'add_ons': List[str],
            'contact_phone': str | None,
            'contact_email': str | None,
            'special_requests': List[str],
            'dietary_restrictions': List[str],
            'confidence': float (0.0-1.0)
        }

        Examples:
        - "50 people Friday at 6pm" → {guest_count: 50, date: "Friday", time: "6pm"}
        - "chicken and steak for 30 guests" → {guest_count: 30, proteins: ["Chicken", "Steak"]}
        - "call me at 555-1234" → {contact_phone: "555-1234"}
        """
        if not self._initialized:
            self.initialize()

        entities = self.extract_entities(text)
        text_lower = text.lower()

        # Track confidence factors
        confidence_factors = []

        # ===== GUEST COUNT EXTRACTION =====
        guest_count = None
        if "CARDINAL" in entities:
            for num in entities["CARDINAL"]:
                if num.isdigit():
                    count = int(num)
                    # Check context for party size indicators
                    if 5 <= count <= 200:
                        # Look for party size keywords nearby
                        party_keywords = [
                            "people",
                            "person",
                            "guest",
                            "pax",
                            "folks",
                            "attendees",
                        ]
                        if any(
                            keyword in text_lower for keyword in party_keywords
                        ):
                            guest_count = count
                            confidence_factors.append(0.3)
                            break
                        # Even without keywords, numbers in this range are likely party sizes
                        elif not guest_count:
                            guest_count = count
                            confidence_factors.append(0.2)

        # ===== DATE EXTRACTION (Enhanced) =====
        date = None
        date_entities = entities.get("DATE", [])

        # Also check for relative date keywords
        from datetime import datetime, timedelta

        relative_dates = {
            "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "tomorrow": (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).strftime("%Y-%m-%d"),
            "next week": (
                datetime.now(timezone.utc) + timedelta(days=7)
            ).strftime("%Y-%m-%d"),
            "this weekend": "this weekend",
            "this friday": "this Friday",
            "this saturday": "this Saturday",
            "this sunday": "this Sunday",
            "next friday": "next Friday",
            "next saturday": "next Saturday",
            "next sunday": "next Sunday",
        }

        for keyword, date_value in relative_dates.items():
            if keyword in text_lower:
                date = date_value
                confidence_factors.append(0.25)
                break

        if not date and date_entities:
            date = date_entities[0]
            confidence_factors.append(0.25)

        # ===== TIME EXTRACTION =====
        time = None
        time_patterns = [
            r"(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)",  # 6:30 PM
            r"(\d{1,2})\s*(am|pm|AM|PM)",  # 6 PM
            r"(\d{1,2})\s*o['\']?clock",  # 6 o'clock
            r"at\s+(\d{1,2})",  # at 6
        ]

        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                time = match.group(0)
                confidence_factors.append(0.2)
                break

        # ===== LOCATION EXTRACTION =====
        locations = entities.get("GPE", []) + entities.get("LOC", [])

        # Add CA cities not caught by NER
        ca_cities = [
            "sacramento",
            "san francisco",
            "san jose",
            "oakland",
            "palo alto",
            "mountain view",
            "santa clara",
            "sunnyvale",
            "fremont",
            "roseville",
            "folsom",
            "davis",
            "berkeley",
            "hayward",
            "milpitas",
            "elk grove",
            "citrus heights",
            "rancho cordova",
        ]

        for city in ca_cities:
            if city in text_lower and city.title() not in locations:
                locations.append(city.title())
                confidence_factors.append(0.15)

        # ===== PROTEIN EXTRACTION =====
        proteins = []
        protein_keywords = {
            "chicken": "Chicken",
            "steak": "Steak",
            "beef": "Beef",
            "shrimp": "Shrimp",
            "scallops": "Scallops",
            "scallop": "Scallops",
            "salmon": "Salmon",
            "tofu": "Tofu",
            "lobster": "Lobster",
            "filet mignon": "Filet Mignon",
            "filet": "Filet Mignon",
            "ribeye": "Ribeye",
            "ny strip": "NY Strip",
        }

        for keyword, protein_name in protein_keywords.items():
            if keyword in text_lower and protein_name not in proteins:
                proteins.append(protein_name)
                confidence_factors.append(0.1)

        # ===== ADD-ONS EXTRACTION =====
        add_ons = []
        addon_keywords = {
            "noodles": "Noodles",
            "yakisoba": "Yakisoba",
            "fried rice": "Fried Rice",
            "gyoza": "Gyoza",
            "edamame": "Edamame",
            "vegetables": "Vegetables",
            "veggies": "Vegetables",
            "salad": "Salad",
            "miso soup": "Miso Soup",
        }

        for keyword, addon_name in addon_keywords.items():
            if keyword in text_lower and addon_name not in add_ons:
                add_ons.append(addon_name)
                confidence_factors.append(0.05)

        # ===== CONTACT INFO EXTRACTION =====
        contact_phone = None
        contact_email = None

        # Phone patterns
        phone_patterns = [
            r"\b(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b",  # 555-123-4567
            r"\b\((\d{3})\)\s*(\d{3})-(\d{4})\b",  # (555) 123-4567
        ]

        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                contact_phone = match.group(0)
                confidence_factors.append(0.2)
                break

        # Email pattern
        email_match = re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", text)
        if email_match:
            contact_email = email_match.group(0)
            confidence_factors.append(0.2)

        # ===== SPECIAL REQUESTS EXTRACTION =====
        special_requests = []
        request_keywords = [
            "outdoor",
            "indoor",
            "private",
            "surprise",
            "birthday",
            "anniversary",
            "proposal",
            "corporate",
            "team building",
            "celebration",
        ]

        for keyword in request_keywords:
            if keyword in text_lower:
                special_requests.append(keyword.title())
                confidence_factors.append(0.05)

        # ===== DIETARY RESTRICTIONS =====
        dietary_restrictions = []
        dietary_keywords = {
            "vegetarian": "Vegetarian",
            "vegan": "Vegan",
            "gluten free": "Gluten-Free",
            "gluten-free": "Gluten-Free",
            "dairy free": "Dairy-Free",
            "dairy-free": "Dairy-Free",
            "nut allergy": "Nut Allergy",
            "shellfish allergy": "Shellfish Allergy",
            "kosher": "Kosher",
            "halal": "Halal",
        }

        for keyword, restriction in dietary_keywords.items():
            if (
                keyword in text_lower
                and restriction not in dietary_restrictions
            ):
                dietary_restrictions.append(restriction)
                confidence_factors.append(0.1)

        # ===== CALCULATE OVERALL CONFIDENCE =====
        # Confidence based on how many fields we successfully extracted
        confidence = min(sum(confidence_factors), 1.0)

        # Boost confidence if we got the critical booking fields
        if guest_count and (date or time):
            confidence = min(confidence + 0.2, 1.0)

        return {
            "guest_count": guest_count,
            "date": date,
            "time": time,
            "locations": locations,
            "proteins": proteins,
            "add_ons": add_ons,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "special_requests": special_requests,
            "dietary_restrictions": dietary_restrictions,
            "confidence": round(confidence, 2),
            "entities_found": len(
                [
                    x
                    for x in [
                        guest_count,
                        date,
                        time,
                        contact_phone,
                        contact_email,
                    ]
                    if x
                ]
            )
            + len(proteins)
            + len(add_ons)
            + len(locations),
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

    # ========== Performance & Monitoring Methods ==========

    def get_performance_metrics(
        self, method_name: str = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for NLP operations

        Args:
            method_name: Specific method to get metrics for, or None for all methods

        Returns:
            Dictionary with performance metrics including:
            - Call counts
            - Average/min/max execution times
            - Error rates
            - Uptime
        """
        return self.performance_monitor.get_metrics(method_name)

    def reset_metrics(self):
        """Reset all performance metrics"""
        self.performance_monitor.reset()
        logger.info("Performance metrics reset")

    def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for NLP service

        Returns:
            {
                'status': 'healthy' | 'degraded' | 'unhealthy',
                'models_loaded': bool,
                'spacy_available': bool,
                'semantic_model_available': bool,
                'uptime_seconds': float,
                'total_requests': int,
                'average_response_time_ms': float,
                'error_rate': float
            }
        """
        metrics = self.get_performance_metrics()

        # Calculate aggregate statistics
        total_calls = sum(
            m["total_calls"] for m in metrics.get("methods", {}).values()
        )

        total_errors = sum(
            m["errors"] for m in metrics.get("methods", {}).values()
        )

        error_rate = (
            (total_errors / total_calls * 100) if total_calls > 0 else 0
        )

        # Calculate average response time across all methods
        all_times = [
            m["average_time_ms"]
            for m in metrics.get("methods", {}).values()
            if m.get("average_time_ms", 0) > 0
        ]
        avg_response_time = sum(all_times) / len(all_times) if all_times else 0

        # Determine health status
        status = "healthy"
        if not self._initialized:
            status = "degraded"  # Running on fallback
        elif error_rate > 10:
            status = "unhealthy"  # >10% error rate
        elif avg_response_time > 100:
            status = "degraded"  # Slow responses (>100ms avg)

        return {
            "status": status,
            "models_loaded": self._initialized,
            "spacy_available": self.nlp is not None,
            "semantic_model_available": self.semantic_model is not None,
            "uptime_seconds": metrics.get("uptime_seconds", 0),
            "total_requests": total_calls,
            "average_response_time_ms": round(avg_response_time, 2),
            "error_rate": round(error_rate, 2),
            "performance_target": "<50ms per request",
            "performance_status": (
                "good"
                if avg_response_time < 50
                else "acceptable" if avg_response_time < 100 else "slow"
            ),
        }

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
            for word in [
                "inquiring",
                "regarding",
                "kindly",
                "please sir",
                "please madam",
            ]
        ):
            return "formal", 0.70

        # Anxious indicators
        if any(
            word in text_lower
            for word in ["nervous", "worried", "anxious", "scared", "help me"]
        ):
            return "anxious", 0.75

        # Casual indicators
        if any(
            word in text_lower
            for word in ["hey", "wanna", "gonna", "yeah", "😊", "🎉"]
        ):
            return "casual", 0.70

        # Default
        return "casual", 0.60

    def _fallback_keyword_search(
        self, query: str, faq_list: List[Dict], top_k: int
    ) -> List[Dict]:
        """Simple keyword-based FAQ search"""
        query_words = set(query.lower().split())

        scored_faqs = []
        for faq in faq_list:
            question_words = set(faq["question"].lower().split())
            overlap = len(query_words & question_words)
            if overlap > 0:
                scored_faqs.append(
                    {
                        **faq,
                        "similarity_score": overlap / len(query_words),
                        "confidence": "medium",
                    }
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
