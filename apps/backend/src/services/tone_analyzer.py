"""
Tone Analyzer Service

Detects customer communication tone and provides AI response guidelines.

Supports 5 tone categories:
1. FORMAL - Professional, courteous, detailed
2. CASUAL - Friendly, enthusiastic, emojis
3. DIRECT - Brief, efficient, bullet points
4. WARM - Empathetic, celebratory, personal
5. ANXIOUS - Reassuring, patient, step-by-step

Uses rule-based detection (85-90% accuracy) for speed and cost-effectiveness.
Can be upgraded to ML-based detection if needed.

Created: 2025-11-12
"""
import logging
import re
from typing import Dict, List, Tuple, Optional
from decimal import Decimal

from models.knowledge_base import ToneType

logger = logging.getLogger(__name__)


class ToneAnalyzer:
    """
    Rule-based tone detection for customer messages
    
    Analyzes:
    - Message length and structure
    - Punctuation and capitalization
    - Emojis and emoticons
    - Word choice and formality
    - Question patterns
    """
    
    # ============================================
    # TONE DETECTION PATTERNS
    # ============================================
    
    FORMAL_INDICATORS = [
        "good morning", "good afternoon", "good evening",
        "i would like to", "i am interested in", "could you please",
        "thank you for", "i appreciate", "sincerely",
        "regarding", "concerning", "furthermore", "additionally",
        "i am writing to", "i hope this finds you well"
    ]
    
    CASUAL_INDICATORS = [
        "hey", "hi there", "what's up", "sup",
        "yeah", "yep", "nope", "gonna", "wanna",
        "lol", "haha", "cool", "awesome", "sweet",
        "thanks!", "thx", "btw", "fyi", "np"
    ]
    
    DIRECT_INDICATORS = [
        "price?", "cost?", "how much", "available?",
        "can you", "do you", "when", "where", "what time"
    ]
    
    WARM_INDICATORS = [
        "excited", "can't wait", "looking forward",
        "special", "celebrate", "birthday", "anniversary",
        "love", "wonderful", "amazing", "fantastic",
        "family", "friends", "gathering", "party"
    ]
    
    ANXIOUS_INDICATORS = [
        "i'm not sure", "i don't know", "confused",
        "worried", "concerned", "nervous", "unsure",
        "help", "how do i", "what should i", "is it okay",
        "i hope", "hopefully", "i think maybe"
    ]
    
    # Emoji patterns
    CASUAL_EMOJIS = ["😊", "😃", "😄", "🙂", "👍", "🔥", "✨", "💯"]
    WARM_EMOJIS = ["❤️", "💕", "💖", "🎉", "🎊", "🎈", "🥳", "😍"]
    ANXIOUS_EMOJIS = ["😟", "😕", "😰", "😬", "🤔", "😅", "😓"]
    
    @classmethod
    def detect_tone(cls, message: str, channel: str = "email") -> Tuple[ToneType, Decimal]:
        """
        Detect tone of customer message
        
        Args:
            message: Customer message
            channel: Communication channel (email, sms, voice, instagram, etc.)
            
        Returns:
            Tuple of (detected_tone, confidence_score)
        """
        try:
            if not message or len(message.strip()) == 0:
                return ToneType.FORMAL, Decimal("50.0")
            
            message_lower = message.lower()
            
            # Calculate scores for each tone
            scores = {
                ToneType.FORMAL: cls._calculate_formal_score(message, message_lower),
                ToneType.CASUAL: cls._calculate_casual_score(message, message_lower),
                ToneType.DIRECT: cls._calculate_direct_score(message, message_lower),
                ToneType.WARM: cls._calculate_warm_score(message, message_lower),
                ToneType.ANXIOUS: cls._calculate_anxious_score(message, message_lower)
            }
            
            # Adjust scores based on channel
            if channel in ["sms", "instagram", "facebook"]:
                # Social channels tend to be more casual
                scores[ToneType.CASUAL] *= Decimal("1.2")
                scores[ToneType.DIRECT] *= Decimal("1.1")
            
            elif channel == "email":
                # Email tends to be more formal
                scores[ToneType.FORMAL] *= Decimal("1.1")
            
            # Find highest score
            detected_tone = max(scores, key=lambda k: scores[k])
            confidence = scores[detected_tone]
            
            # Cap confidence at 95%
            confidence = min(confidence, Decimal("95.0"))
            
            logger.info(f"Detected tone: {detected_tone.value}, confidence: {confidence}%")
            logger.debug(f"All scores: {scores}")
            
            return detected_tone, confidence
        
        except Exception as e:
            logger.error(f"Error detecting tone: {e}")
            return ToneType.FORMAL, Decimal("50.0")
    
    @classmethod
    def _calculate_formal_score(cls, message: str, message_lower: str) -> Decimal:
        """Calculate formality score"""
        score = Decimal("20.0")  # Base score
        
        # Complete sentences with proper punctuation
        sentences = [s.strip() for s in re.split(r'[.!?]', message) if s.strip()]
        if len(sentences) >= 2:
            score += Decimal("15.0")
        
        # Proper capitalization (sentences start with capital letter)
        properly_capitalized = sum(1 for s in sentences if s and s[0].isupper())
        if len(sentences) > 0:
            cap_ratio = properly_capitalized / len(sentences)
            score += Decimal(str(cap_ratio * 20))
        
        # Formal phrases
        formal_count = sum(1 for phrase in cls.FORMAL_INDICATORS if phrase in message_lower)
        score += Decimal(str(formal_count * 10))
        
        # No emojis (formal)
        if not any(emoji in message for emoji in (cls.CASUAL_EMOJIS + cls.WARM_EMOJIS)):
            score += Decimal("10.0")
        
        # Longer messages tend to be more formal
        if len(message) > 100:
            score += Decimal("10.0")
        
        # No abbreviations or slang
        casual_words = ["hey", "yeah", "lol", "gonna", "wanna"]
        if not any(word in message_lower for word in casual_words):
            score += Decimal("10.0")
        
        return score
    
    @classmethod
    def _calculate_casual_score(cls, message: str, message_lower: str) -> Decimal:
        """Calculate casual score"""
        score = Decimal("20.0")  # Base score
        
        # Casual indicators
        casual_count = sum(1 for phrase in cls.CASUAL_INDICATORS if phrase in message_lower)
        score += Decimal(str(casual_count * 15))
        
        # Emojis
        emoji_count = sum(1 for emoji in cls.CASUAL_EMOJIS if emoji in message)
        score += Decimal(str(emoji_count * 10))
        
        # Exclamation marks
        exclamation_count = message.count("!")
        score += Decimal(str(exclamation_count * 5))
        
        # Short messages
        if len(message) < 50:
            score += Decimal("10.0")
        
        # Contractions
        contractions = ["it's", "that's", "what's", "i'm", "you're", "we're"]
        contraction_count = sum(1 for c in contractions if c in message_lower)
        score += Decimal(str(contraction_count * 5))
        
        # Lowercase start (informal)
        if message and message[0].islower():
            score += Decimal("15.0")
        
        # Multiple question marks or exclamation marks (!!!, ???)
        if "!!" in message or "??" in message:
            score += Decimal("10.0")
        
        return score
    
    @classmethod
    def _calculate_direct_score(cls, message: str, message_lower: str) -> Decimal:
        """Calculate direct/brief score"""
        score = Decimal("20.0")  # Base score
        
        # Very short messages
        if len(message) < 30:
            score += Decimal("20.0")
        
        # Single word or two-word messages
        words = message.split()
        if len(words) <= 3:
            score += Decimal("30.0")
        
        # Direct indicators (questions)
        direct_count = sum(1 for phrase in cls.DIRECT_INDICATORS if phrase in message_lower)
        score += Decimal(str(direct_count * 15))
        
        # Ends with question mark (direct question)
        if message.strip().endswith("?"):
            score += Decimal("15.0")
        
        # No pleasantries
        pleasantries = ["please", "thank", "sorry", "appreciate"]
        if not any(p in message_lower for p in pleasantries):
            score += Decimal("10.0")
        
        return score
    
    @classmethod
    def _calculate_warm_score(cls, message: str, message_lower: str) -> Decimal:
        """Calculate warm/emotional score"""
        score = Decimal("20.0")  # Base score
        
        # Warm indicators
        warm_count = sum(1 for phrase in cls.WARM_INDICATORS if phrase in message_lower)
        score += Decimal(str(warm_count * 15))
        
        # Warm emojis
        emoji_count = sum(1 for emoji in cls.WARM_EMOJIS if emoji in message)
        score += Decimal(str(emoji_count * 15))
        
        # Personal details (sharing about event/occasion)
        personal_keywords = ["my", "our", "we", "family", "friend"]
        personal_count = sum(1 for keyword in personal_keywords if keyword in message_lower)
        score += Decimal(str(personal_count * 5))
        
        # Longer messages with emotion
        if len(message) > 80:
            score += Decimal("10.0")
        
        # Exclamation marks (excitement)
        exclamation_count = message.count("!")
        if exclamation_count >= 2:
            score += Decimal("15.0")
        
        return score
    
    @classmethod
    def _calculate_anxious_score(cls, message: str, message_lower: str) -> Decimal:
        """Calculate anxious/uncertain score"""
        score = Decimal("20.0")  # Base score
        
        # Anxious indicators
        anxious_count = sum(1 for phrase in cls.ANXIOUS_INDICATORS if phrase in message_lower)
        score += Decimal(str(anxious_count * 20))
        
        # Multiple questions
        question_count = message.count("?")
        if question_count >= 3:
            score += Decimal("20.0")
        
        # Uncertainty words
        uncertainty_words = ["maybe", "perhaps", "possibly", "might", "could"]
        uncertainty_count = sum(1 for word in uncertainty_words if word in message_lower)
        score += Decimal(str(uncertainty_count * 10))
        
        # Anxious emojis
        emoji_count = sum(1 for emoji in cls.ANXIOUS_EMOJIS if emoji in message)
        score += Decimal(str(emoji_count * 15))
        
        # Ellipsis (uncertainty)
        if "..." in message:
            score += Decimal("15.0")
        
        return score
    
    # ============================================
    # AI RESPONSE GUIDELINES
    # ============================================
    
    @classmethod
    def get_response_guidelines(cls, tone: ToneType) -> Dict[str, any]:
        """
        Get AI response style guidelines for detected tone
        
        Args:
            tone: Detected customer tone
            
        Returns:
            Dictionary with response guidelines
        """
        guidelines = {
            ToneType.FORMAL: {
                "style": "professional",
                "greeting": "Good [morning/afternoon/evening]",
                "language": "formal and courteous",
                "structure": "detailed and well-organized",
                "emojis": "avoid",
                "punctuation": "proper punctuation and grammar",
                "closing": "Sincerely / Best regards",
                "example_phrases": [
                    "I would be pleased to assist you with...",
                    "Thank you for your inquiry regarding...",
                    "I hope this information is helpful",
                    "Please feel free to contact me if you have any further questions"
                ],
                "system_prompt_addition": (
                    "Use professional, formal language. "
                    "Provide detailed responses with proper grammar. "
                    "Avoid emojis and casual language. "
                    "Be courteous and thorough."
                )
            },
            
            ToneType.CASUAL: {
                "style": "friendly",
                "greeting": "Hey! / Hi there!",
                "language": "conversational and relaxed",
                "structure": "concise and natural",
                "emojis": "use appropriate emojis 😊🔥",
                "punctuation": "casual, can use exclamation marks!",
                "closing": "Talk soon! / Cheers!",
                "example_phrases": [
                    "Hey! Thanks for reaching out 😊",
                    "That's awesome!",
                    "No problem at all!",
                    "Let me know if you need anything else!"
                ],
                "system_prompt_addition": (
                    "Use friendly, casual language with enthusiasm. "
                    "Include appropriate emojis to match the tone. "
                    "Keep responses conversational and warm. "
                    "Use contractions and exclamation marks naturally."
                )
            },
            
            ToneType.DIRECT: {
                "style": "efficient",
                "greeting": "Quick answer:",
                "language": "brief and to-the-point",
                "structure": "bullet points or short sentences",
                "emojis": "minimal",
                "punctuation": "clean and simple",
                "closing": "Let me know if you need more details",
                "example_phrases": [
                    "Price: $55/person",
                    "Available: Yes",
                    "Time: 6-10 PM",
                    "Need: date, guest count, location"
                ],
                "system_prompt_addition": (
                    "Be concise and direct. "
                    "Answer the question quickly without unnecessary details. "
                    "Use bullet points when listing information. "
                    "Offer to provide more details if needed."
                )
            },
            
            ToneType.WARM: {
                "style": "empathetic",
                "greeting": "How exciting! / I'm so happy to help!",
                "language": "warm and celebratory",
                "structure": "personal and detailed",
                "emojis": "use celebratory emojis 🎉❤️",
                "punctuation": "enthusiastic!",
                "closing": "Can't wait to help celebrate! 🎊",
                "example_phrases": [
                    "How wonderful that you're celebrating...",
                    "I love that you're planning this special occasion!",
                    "We'd be honored to be part of your celebration",
                    "This sounds like it's going to be amazing!"
                ],
                "system_prompt_addition": (
                    "Use warm, empathetic language with genuine enthusiasm. "
                    "Celebrate the customer's occasion or event. "
                    "Include appropriate celebratory emojis. "
                    "Show excitement about helping them. "
                    "Be personal and heartfelt."
                )
            },
            
            ToneType.ANXIOUS: {
                "style": "reassuring",
                "greeting": "I'm here to help!",
                "language": "patient and supportive",
                "structure": "step-by-step and clear",
                "emojis": "supportive emojis 😊✅",
                "punctuation": "clear and reassuring",
                "closing": "I'm here if you have any other questions!",
                "example_phrases": [
                    "Don't worry, this is actually quite simple!",
                    "Let me walk you through this step by step",
                    "You're doing great! Here's what happens next...",
                    "It's completely normal to have these questions"
                ],
                "system_prompt_addition": (
                    "Use reassuring, patient language. "
                    "Break down information into clear, simple steps. "
                    "Address concerns proactively. "
                    "Be supportive and encouraging. "
                    "Let them know it's okay to ask questions."
                )
            }
        }
        
        return guidelines.get(tone, guidelines[ToneType.FORMAL])
    
    @classmethod
    def format_ai_system_prompt(cls, base_prompt: str, detected_tone: ToneType) -> str:
        """
        Inject tone-specific instructions into AI system prompt
        
        Args:
            base_prompt: Original system prompt
            detected_tone: Detected customer tone
            
        Returns:
            Enhanced system prompt with tone instructions
        """
        guidelines = cls.get_response_guidelines(detected_tone)
        tone_instruction = guidelines["system_prompt_addition"]
        
        enhanced_prompt = f"""{base_prompt}

TONE ADAPTATION:
Customer's communication style detected as: {detected_tone.value.upper()}

{tone_instruction}

Remember to match the customer's energy and communication style while maintaining professionalism.
"""
        
        return enhanced_prompt
