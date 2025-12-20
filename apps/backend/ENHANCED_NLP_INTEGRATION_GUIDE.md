# Enhanced NLP Service - Quick Integration Guide

## 🚀 Quick Start

### **Import the Service**

```python
from services.enhanced_nlp_service import get_nlp_service

# Get singleton instance (lazy-loaded)
nlp = get_nlp_service()
```

---

## 📖 API Reference

### **1. detect_tone_enhanced(text: str) → (str, float)**

Enhanced tone detection with confidence scoring.

```python
tone, confidence = nlp.detect_tone_enhanced(
    "Hey! I wanna book hibachi for my birthday! 🎉"
)
# Returns: ("casual", 0.85)
```

**Supported Tones**:

- `formal` - Professional language, proper grammar
- `casual` - Informal, contractions, slang
- `anxious` - Nervous, worried, uncertain
- `warm` - Friendly, enthusiastic, emoji
- `direct` - Straight to the point, no-nonsense

**Confidence Levels**:

- `>0.8` - High confidence (trust the result)
- `0.6-0.8` - Medium confidence (probably correct)
- `<0.6` - Low confidence (consider escalating to human)

**Usage Example**:

```python
async def process_message(message: str):
    tone, confidence = nlp.detect_tone_enhanced(message)

    if confidence < 0.6:
        logger.warning(f"Low confidence: {confidence}")
        # Consider escalating to human agent

    # Use tone to customize response
    if tone == "anxious":
        return reassuring_response(message)
    elif tone == "formal":
        return professional_response(message)
    else:
        return casual_response(message)
```

---

### **2. extract_entities(text: str) → Dict[str, List[str]]**

Extract named entities (dates, numbers, names, locations).

```python
entities = nlp.extract_entities(
    "I want to book for 50 people on December 15th at 6pm"
)
# Returns: {
#     'CARDINAL': ['50'],
#     'DATE': ['December 15th'],
#     'TIME': ['6pm']
# }
```

**Entity Types**:

- `CARDINAL` - Numbers (50, 30, 100)
- `DATE` - Dates (December 15th, next Saturday, Nov 20)
- `TIME` - Times (6pm, evening, afternoon)
- `PERSON` - Names (Sarah Johnson, Mike Davis)
- `GPE` - Locations (cities, states, countries)
- `ORG` - Organizations (company names)

**Usage Example**:

```python
async def parse_booking_request(message: str):
    entities = nlp.extract_entities(message)

    guest_count = None
    if 'CARDINAL' in entities:
        # Get first number as guest count
        guest_count = int(entities['CARDINAL'][0])

    event_date = None
    if 'DATE' in entities:
        event_date = entities['DATE'][0]
        # Convert to datetime using dateparser or similar

    return {
        'guest_count': guest_count,
        'event_date': event_date
    }
```

---

### **3. semantic_search_faqs(query: str, faq_list: List[Dict], top_k: int = 3) → List[Dict]**

Find similar FAQs using semantic search (understands meaning, not just
keywords).

```python
faqs = [
    {
        "question": "How much does My Hibachi Chef cost?",
        "answer": "Adult pricing is $55 per person...",
        "category": "Pricing"
    },
    # ... more FAQs
]

results = nlp.semantic_search_faqs("How much for 50 peeps?", faqs, top_k=3)
# Returns: [
#     {
#         "question": "How much does My Hibachi Chef cost?",
#         "answer": "Adult pricing is $55 per person...",
#         "category": "Pricing",
#         "similarity_score": 0.72,
#         "confidence": "high"
#     },
#     # ... more results
# ]
```

**Parameters**:

- `query` - User's question (natural language)
- `faq_list` - List of FAQ dictionaries (must have 'question' field)
- `top_k` - Number of results to return (default: 3)

**Similarity Thresholds**:

- `>0.7` - High confidence match
- `0.5-0.7` - Medium confidence match
- `0.3-0.5` - Low confidence match
- `<0.3` - Not returned (filtered out)

**Usage Example**:

```python
async def search_faqs(query: str):
    # Get all FAQs from database
    all_faqs = await db.fetch("SELECT * FROM faq_items")

    # Convert to dict format
    faqs = [
        {
            "question": row['question'],
            "answer": row['answer'],
            "category": row['category']
        }
        for row in all_faqs
    ]

    # Semantic search
    results = nlp.semantic_search_faqs(query, faqs, top_k=3)

    if results and results[0]['similarity_score'] > 0.7:
        # High confidence match
        return results[0]['answer']
    elif results and results[0]['similarity_score'] > 0.5:
        # Medium confidence - return with disclaimer
        return f"I think you're asking about: {results[0]['question']}. {results[0]['answer']}"
    else:
        # No good match
        return "I'm not sure I understand. Could you rephrase?"
```

---

### **4. extract_booking_details(text: str) → Dict**

Extract booking-specific information (guest count, proteins, add-ons).

```python
details = nlp.extract_booking_details(
    "30 people with chicken and steak, plus noodles"
)
# Returns: {
#     'guest_count': 30,
#     'proteins': ['Chicken', 'Steak'],
#     'add_ons': ['Noodles'],
#     'confidence': 'high'
# }
```

**Extracted Fields**:

- `guest_count` - Number of guests (int or None)
- `proteins` - List of proteins (Chicken, Steak, Shrimp)
- `add_ons` - List of add-ons (Noodles, Gyoza, etc.)
- `confidence` - 'high', 'medium', or 'low'

**Handles Variations**:

- Guest count: "30 people", "30 ppl", "about 30", "~30"
- Proteins: "chicken", "Chicken", "CHICKEN", "all 3 proteins"
- Add-ons: "noodles", "yakisoba", "dumplings", "gyoza"

**Usage Example**:

```python
async def parse_booking(message: str):
    details = nlp.extract_booking_details(message)

    if details['confidence'] == 'low':
        # Ask for clarification
        return "Could you confirm the number of guests and protein choices?"

    # Calculate pricing
    guest_count = details['guest_count']
    base_price = guest_count * 55  # $55 per person

    # Add-on pricing
    addon_price = 0
    for addon in details['add_ons']:
        if addon in ['Gyoza', 'Extra Protein']:
            addon_price += guest_count * 10
        else:
            addon_price += guest_count * 5

    total = base_price + addon_price

    return {
        'guest_count': guest_count,
        'proteins': details['proteins'],
        'add_ons': details['add_ons'],
        'base_price': base_price,
        'addon_price': addon_price,
        'total': total
    }
```

---

### **5. normalize_text(text: str) → str**

Normalize slang and abbreviations to standard English.

```python
normalized = nlp.normalize_text("Wanna book for 30 ppl thx")
# Returns: "want to book for 30 people thanks"
```

**Normalizations**:

- `wanna` → `want to`
- `gonna` → `going to`
- `ppl` → `people`
- `thx` → `thanks`
- `ur` → `your`
- `plz` → `please`

**Usage Example**:

```python
async def process_message(message: str):
    # Normalize first for better entity extraction
    normalized = nlp.normalize_text(message)

    # Then extract entities
    entities = nlp.extract_entities(normalized)

    # Entities will be more accurate on normalized text
    return entities
```

---

## 🔄 Migration from Rule-Based

### **Before (Rule-Based Tone Detection)**

```python
# Old approach
from services.tone_analyzer import ToneAnalyzer

analyzer = ToneAnalyzer()
tone = analyzer.detect(message)  # Returns: str
```

### **After (Enhanced NLP)**

```python
# New approach
from services.enhanced_nlp_service import get_nlp_service

nlp = get_nlp_service()
tone, confidence = nlp.detect_tone_enhanced(message)  # Returns: (str, float)

# Handle confidence
if confidence < 0.6:
    # Low confidence - consider escalation
    pass
```

---

### **Before (Keyword FAQ Search)**

```python
# Old approach
def search_faqs(query: str, faqs: List):
    query_lower = query.lower()
    for faq in faqs:
        if query_lower in faq['question'].lower():
            return faq
    return None
```

### **After (Semantic FAQ Search)**

```python
# New approach
from services.enhanced_nlp_service import get_nlp_service

nlp = get_nlp_service()
results = nlp.semantic_search_faqs(query, faqs, top_k=3)

if results and results[0]['similarity_score'] > 0.7:
    return results[0]
else:
    return None
```

**Improvement**: Finds matches even if query uses different words!

---

## ⚡ Performance Tips

### **1. Lazy Initialization**

```python
# Service initializes models on first use, not at import
from services.enhanced_nlp_service import get_nlp_service

# This doesn't load models yet (fast)
nlp = get_nlp_service()

# Models load on first method call (1-2 seconds)
tone, conf = nlp.detect_tone_enhanced("Hello")  # Loads models here
```

### **2. Reuse the Instance**

```python
# ✅ GOOD - Reuse singleton instance
nlp = get_nlp_service()
for message in messages:
    tone, conf = nlp.detect_tone_enhanced(message)

# ❌ BAD - Don't create new instances
for message in messages:
    nlp = get_nlp_service()  # Unnecessary, uses same singleton anyway
    tone, conf = nlp.detect_tone_enhanced(message)
```

### **3. Batch Processing (Future)**

```python
# For future optimization - batch encode queries
queries = ["Query 1", "Query 2", "Query 3"]

# Instead of:
for query in queries:
    results = nlp.semantic_search_faqs(query, faqs)

# Could batch encode all queries at once (future improvement)
```

---

## 🛡️ Error Handling

### **Automatic Fallback**

```python
# Service automatically falls back to rule-based if models fail
try:
    tone, confidence = nlp.detect_tone_enhanced(message)
    # Uses spaCy + NLP features
except Exception as e:
    # Automatically falls back to rule-based
    # No error thrown, system keeps working
    pass
```

### **Check if Models Loaded**

```python
nlp = get_nlp_service()

if nlp._initialized:
    print("✅ NLP models loaded")
else:
    print("⚠️  Using rule-based fallback")
```

### **Handle Low Confidence**

```python
tone, confidence = nlp.detect_tone_enhanced(message)

if confidence < 0.6:
    logger.warning(f"Low confidence tone detection: {confidence}")
    # Consider:
    # 1. Escalate to human agent
    # 2. Ask clarifying question
    # 3. Use neutral/safe response
```

---

## 📊 Monitoring

### **Track Performance Metrics**

```python
import time
from services.enhanced_nlp_service import get_nlp_service

nlp = get_nlp_service()

# Time the inference
start = time.time()
tone, confidence = nlp.detect_tone_enhanced(message)
latency_ms = (time.time() - start) * 1000

# Log metrics
await db.execute("""
    INSERT INTO nlp_metrics
    (method, latency_ms, confidence, timestamp)
    VALUES ($1, $2, $3, NOW())
""", "detect_tone_enhanced", latency_ms, confidence)

# Alert if slow
if latency_ms > 100:  # Target: <50ms
    logger.warning(f"Slow NLP inference: {latency_ms}ms")
```

### **A/B Testing**

```python
import random

async def process_message(message: str):
    # 50% use new NLP, 50% use old rule-based
    variant = "nlp" if random.random() < 0.5 else "rule_based"

    if variant == "nlp":
        tone, confidence = nlp.detect_tone_enhanced(message)
    else:
        tone = old_tone_analyzer.detect(message)
        confidence = 1.0

    # Track variant used
    await track_conversation(variant=variant, tone=tone)

    return generate_response(message, tone)
```

---

## 🎯 Usage Patterns

### **Pattern 1: Full Pipeline**

```python
async def process_customer_message(message: str):
    nlp = get_nlp_service()

    # 1. Normalize text
    normalized = nlp.normalize_text(message)

    # 2. Extract entities
    entities = nlp.extract_entities(normalized)

    # 3. Detect tone
    tone, confidence = nlp.detect_tone_enhanced(normalized)

    # 4. Extract booking details
    details = nlp.extract_booking_details(normalized)

    # 5. Search FAQs if question
    if '?' in message:
        faq_results = nlp.semantic_search_faqs(message, all_faqs)

    return {
        'normalized': normalized,
        'entities': entities,
        'tone': tone,
        'confidence': confidence,
        'booking_details': details,
        'faq_match': faq_results[0] if faq_results else None
    }
```

### **Pattern 2: Conditional Enhancement**

```python
async def detect_tone_smart(message: str):
    nlp = get_nlp_service()

    # Try enhanced NLP first
    tone, confidence = nlp.detect_tone_enhanced(message)

    # If low confidence, ask follow-up
    if confidence < 0.6:
        return {
            'tone': 'unknown',
            'needs_clarification': True,
            'suggested_question': "Could you tell me a bit more about what you're looking for?"
        }

    return {
        'tone': tone,
        'confidence': confidence,
        'needs_clarification': False
    }
```

---

## ✅ Testing

### **Unit Tests**

```python
import pytest
from services.enhanced_nlp_service import get_nlp_service

def test_tone_detection():
    nlp = get_nlp_service()

    # Test casual tone
    tone, conf = nlp.detect_tone_enhanced("Hey! Wanna book for 30 ppl!")
    assert tone == "casual"
    assert conf > 0.8

    # Test formal tone
    tone, conf = nlp.detect_tone_enhanced("Good morning. I'm inquiring about catering.")
    assert tone == "formal"
    assert conf > 0.8

def test_entity_extraction():
    nlp = get_nlp_service()

    entities = nlp.extract_entities("Book for 50 people on December 15th")
    assert 'CARDINAL' in entities
    assert '50' in entities['CARDINAL']
    assert 'DATE' in entities
```

### **Integration Tests**

```python
async def test_full_booking_flow():
    nlp = get_nlp_service()

    message = "Hey! I want to book hibachi for 30 people with chicken and steak, plus noodles on December 15th at 6pm"

    # Extract all info
    normalized = nlp.normalize_text(message)
    tone, conf = nlp.detect_tone_enhanced(normalized)
    entities = nlp.extract_entities(normalized)
    details = nlp.extract_booking_details(normalized)

    # Assertions
    assert tone == "casual"
    assert details['guest_count'] == 30
    assert 'Chicken' in details['proteins']
    assert 'Steak' in details['proteins']
    assert 'Noodles' in details['add_ons']
    assert 'December 15th' in entities['DATE']
```

---

## 🚀 Production Checklist

Before deploying enhanced NLP to production:

- [ ] ✅ Models installed (spacy==3.8.8, en_core_web_sm)
- [ ] ✅ Test suite passing (python scripts/test_enhanced_nlp.py)
- [ ] ⏳ Integrated into AI service
- [ ] ⏳ Performance monitoring added
- [ ] ⏳ Fallback handling tested
- [ ] ⏳ A/B testing configured
- [ ] ⏳ Baseline metrics collected (for comparison)
- [ ] ⏳ Load testing completed (<50ms target)

---

## 📞 Support

**Models Not Loading?**

- Check: `python -m spacy download en_core_web_sm`
- Fallback: System automatically uses rule-based methods

**Slow Performance?**

- Target: <50ms average inference
- Check: `time python -m spacy info en_core_web_sm`
- Monitor: Add timing logs to all NLP calls

**Low Accuracy?**

- Collect: Edge cases for improvement
- Test: A/B against rule-based baseline
- Report: Specific examples where NLP fails

---

**Version**: 1.0 **Last Updated**: November 2025 **Dependencies**:
spacy==3.8.8, sentence-transformers==5.1.2, scikit-learn==1.3.2
