# AI/ML Enhancement Analysis for MyHibachi

## Do You Need TensorFlow, PyTorch, or Keras?

**Date**: November 11, 2025  
**Current Status**: Rule-based AI system with tone detection and
knowledge base  
**Question**: Should we add deep learning frameworks
(TensorFlow/PyTorch/Keras)?

---

## 📊 Current AI System Architecture

### **What You Have Now:**

1. **Tone Detection System** (80% accuracy)
   - Rule-based pattern matching
   - Keyword analysis
   - Sentiment detection
2. **Knowledge Base** (100% accuracy)
   - Database-driven FAQ system
   - Real-time pricing calculations
   - Context-aware responses

3. **Upsell Engine** (100% accuracy)
   - Priority-based suggestion system
   - Party size filtering
   - Conversational flow logic

4. **Multi-Agent System**
   - Lead nurturing agent
   - Operations agent
   - Escalation handling

### **Tech Stack:**

- Python (AsyncIO)
- PostgreSQL (Knowledge Base)
- Deepgram (Voice STT/TTS)
- Rule-based AI logic

---

## 🤔 Analysis: Do You Need Deep Learning?

### **RECOMMENDATION: NOT YET - Here's Why**

| Aspect               | Current System     | With TensorFlow/PyTorch      | Verdict                       |
| -------------------- | ------------------ | ---------------------------- | ----------------------------- |
| **Accuracy**         | 80-100%            | 85-95% (with training)       | ✅ **Current is good**        |
| **Response Time**    | <100ms             | 200-500ms (inference)        | ✅ **Current is faster**      |
| **Complexity**       | Low (maintainable) | High (requires ML expertise) | ✅ **Current is simpler**     |
| **Training Data**    | None needed        | 10,000+ conversations needed | ✅ **Current wins**           |
| **Infrastructure**   | Standard CPU       | GPU required ($$$)           | ✅ **Current is cheaper**     |
| **Interpretability** | 100% explainable   | Black box                    | ✅ **Current is transparent** |

---

## 🎯 When Should You Consider ML Frameworks?

### **Scenarios Where TensorFlow/PyTorch Would Help:**

#### 1. **Complex Natural Language Understanding (NLU)**

**Use Case**: Customer asks "How much for 50 peeps with all the fancy
stuff?"

- **Current**: Struggles with slang, abbreviations, complex phrasing
- **With ML**: Better handles natural language variations
- **Need**: Named Entity Recognition (NER), Intent Classification
- **Framework**: SpaCy + Transformers (lighter than TensorFlow)

#### 2. **Predictive Analytics**

**Use Case**: "Predict which customers are likely to book based on
conversation"

- **Current**: No prediction capability
- **With ML**: Predict conversion probability, churn risk, upsell
  likelihood
- **Need**: Classification models (Random Forest, XGBoost)
- **Framework**: scikit-learn (no GPU needed!)

#### 3. **Voice Emotion Detection**

**Use Case**: Detect frustration/anger in customer's voice tone

- **Current**: Deepgram provides transcription only
- **With ML**: Analyze voice pitch, speed, volume for emotions
- **Need**: Audio emotion recognition models
- **Framework**: PyTorch + librosa

#### 4. **Conversation Summarization**

**Use Case**: Auto-generate booking summaries for agents

- **Current**: Manual templating
- **With ML**: LLM-based summarization
- **Framework**: Hugging Face Transformers + smaller models (BART, T5)

#### 5. **Personalization at Scale**

**Use Case**: Remember customer preferences across thousands of
bookings

- **Current**: Basic database lookups
- **With ML**: Recommendation engine for proteins, add-ons, timing
- **Need**: Collaborative filtering
- **Framework**: TensorFlow Recommenders

---

## 💡 Better Alternatives to Full ML Stack

### **Option 1: Hybrid Approach (RECOMMENDED)**

Instead of TensorFlow/PyTorch, use **specialized lightweight
libraries**:

```python
# Lightweight ML stack (no GPU needed)
pip install spacy            # NLP (40MB model)
pip install scikit-learn     # Predictive models
pip install sentence-transformers  # Semantic search (better than keywords)
```

**Benefits:**

- ✅ CPU-only (no GPU costs)
- ✅ Fast inference (<50ms)
- ✅ Easy to maintain
- ✅ Much smaller models (40MB vs 2GB+)

**Example Use Cases:**

```python
# 1. Better tone detection with spaCy
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp("I'm really nervous about this party...")
# Detect sentiment + entities automatically

# 2. Semantic search for FAQs
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB only!
# Find similar questions even if wording is different
```

---

### **Option 2: Managed AI Services**

Instead of building ML models, use **OpenAI API / Azure OpenAI**:

```python
# Use GPT-4 for complex queries only
import openai

# Fallback to GPT when rule-based system is uncertain
if confidence < 0.7:
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[...],
        temperature=0.3  # Consistent responses
    )
```

**Benefits:**

- ✅ No training needed
- ✅ No infrastructure
- ✅ State-of-the-art accuracy
- ❌ Costs $0.01 per 1K tokens (manageable at low volume)

---

### **Option 3: Edge ML with ONNX Runtime**

If you eventually need custom models, use **ONNX** (optimized
inference):

```python
# Convert any model to ONNX for 3-10x faster inference
import onnxruntime as ort

session = ort.InferenceSession("tone_classifier.onnx")
# Runs on CPU, 5-10ms latency
```

**Benefits:**

- ✅ Framework-agnostic (works with TF, PyTorch, scikit-learn)
- ✅ Optimized for production
- ✅ Cross-platform (works everywhere)

---

## 🚀 Recommended Implementation Plan

### **Phase 1: Enhance Current System (No ML Required) - Week 4-5**

Focus on improving what you have:

1. **Better Keyword Matching**

   ```python
   # Add fuzzy matching for typos
   from difflib import SequenceMatcher
   # "30 ppl" → "30 people"
   ```

2. **Context Memory**

   ```python
   # Remember last 3 messages for context
   conversation_history = []
   ```

3. **Confidence Scores**
   ```python
   # Add uncertainty detection
   if keywords_matched < 2:
       ask_clarifying_question()
   ```

**Cost**: $0 | **Time**: 1 week | **Accuracy gain**: +5-10%

---

### **Phase 2: Add Lightweight NLP (Month 2)**

Integrate spaCy for better understanding:

```python
# Install
pip install spacy
python -m spacy download en_core_web_sm

# Use for:
# - Entity extraction (dates, numbers, names)
# - Better sentiment analysis
# - Dependency parsing (understand complex sentences)
```

**Cost**: $0 | **Time**: 1 week | **Accuracy gain**: +10-15%

---

### **Phase 3: Predictive Analytics (Month 3)**

Use scikit-learn for business intelligence:

```python
# Predict booking likelihood
from sklearn.ensemble import RandomForestClassifier

# Features: time_on_chat, questions_asked, price_mentioned, etc.
# Target: did_book (yes/no)

# Train on your actual booking data (you'll have 100+ bookings by then)
```

**Cost**: $0 | **Time**: 2 weeks | **Accuracy**: 70-80%

---

### **Phase 4: Advanced NLU (Month 4-6, if needed)**

**Only if** you're getting 1000+ conversations/month:

```python
# Semantic search with sentence-transformers
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
# Better FAQ matching, even for rephrased questions
```

**Cost**: $0 | **Time**: 1 week | **Accuracy gain**: +15-20%

---

## 📈 When to Revisit Deep Learning

### **Triggers to Consider TensorFlow/PyTorch:**

1. **Scale Threshold**
   - ✅ > 10,000 conversations/month
   - ✅ > 1,000 bookings with labeled data
   - ✅ Need sub-50ms inference at scale

2. **Use Case Requirements**
   - ✅ Real-time voice emotion detection
   - ✅ Custom language models for industry jargon
   - ✅ Complex multi-modal inputs (text + voice + images)

3. **Resource Availability**
   - ✅ Dedicated ML engineer on team
   - ✅ GPU infrastructure ($500+/month)
   - ✅ 3-6 months for model development

---

## 💰 Cost Comparison

| Approach                    | Monthly Cost    | Setup Time | Maintenance |
| --------------------------- | --------------- | ---------- | ----------- |
| **Current Rule-Based**      | $50 (hosting)   | Done       | Low         |
| **+ spaCy/scikit-learn**    | $50             | 1 week     | Low         |
| **+ OpenAI API (fallback)** | $50-200         | 1 week     | Low         |
| **+ TensorFlow/PyTorch**    | $500-2000 (GPU) | 3-6 months | High        |

---

## 🎯 Final Recommendation

### **DO THIS NOW (Week 4):**

1. ✅ Add **spaCy** for better NLP (1 day setup)
2. ✅ Add **sentence-transformers** for semantic FAQ search (1 day)
3. ✅ Implement conversation context memory (2 days)

### **DO THIS LATER (Month 2-3):**

4. ⏳ Add **scikit-learn** for booking predictions (when you have 100+
   bookings)
5. ⏳ Consider **OpenAI API** as fallback for edge cases

### **DON'T DO YET:**

- ❌ TensorFlow/PyTorch (overkill for current scale)
- ❌ Custom deep learning models (insufficient training data)
- ❌ GPU infrastructure (unnecessary cost)

---

## 📚 Suggested Libraries (in priority order)

```bash
# Install these in order of priority:

# Priority 1: NLP Enhancement (Week 4)
pip install spacy==3.7.2
python -m spacy download en_core_web_sm
pip install sentence-transformers==2.2.2

# Priority 2: Predictive Analytics (Month 2, when data available)
pip install scikit-learn==1.3.2
pip install pandas==2.1.3

# Priority 3: Advanced Features (Month 3+)
pip install transformers==4.35.2  # For Hugging Face models
pip install onnxruntime==1.16.3   # For optimized inference

# Priority 4: If scale demands it (Month 6+)
# pip install tensorflow==2.15.0   # Only if truly needed
# pip install torch==2.1.0          # Only if truly needed
```

---

## 🔬 Testing the Enhancements

### **Benchmark Current System:**

```
✅ Phase 1: Tone Detection - 80% accuracy
✅ Phase 2: Knowledge Base - 100% accuracy
✅ Phase 3: Upsell Triggers - 100% accuracy
✅ Phase 4: E2E Flow - 100% accuracy
```

### **After spaCy/sentence-transformers:**

**Target Improvements:**

- Tone Detection: 80% → 90% (handle slang, typos)
- FAQ Matching: 100% → 100% (but faster, more flexible)
- Intent Recognition: New capability (classify user goals)
- Response Time: <100ms → <80ms (optimized)

---

## 💡 Alternative: "AI as a Service"

### **If budget allows, consider:**

**Option A: Rasa Open Source** (Rule + ML hybrid)

```bash
pip install rasa
# Get NLU + dialogue management without building from scratch
```

- ✅ Best of both worlds (rules + ML)
- ❌ Steeper learning curve

**Option B: Dialogflow CX / Azure Bot Service**

- ✅ Managed ML (Google/Microsoft handles it)
- ❌ Vendor lock-in
- ❌ $0.002 per request (affordable at low volume)

---

## 📊 Data Requirements for ML (if you go that route)

| Model Type                | Training Data Needed         | Time to Collect |
| ------------------------- | ---------------------------- | --------------- |
| **Tone Classifier**       | 5,000 labeled messages       | 3-6 months      |
| **Intent Classifier**     | 10,000 conversations         | 6-12 months     |
| **Upsell Predictor**      | 500 bookings (with outcomes) | 3 months        |
| **Recommendation Engine** | 1,000 bookings               | 6 months        |

**Current Data Available**: ~0 bookings (launching now)

**Verdict**: Not enough data for custom ML yet. Use rule-based +
lightweight NLP.

---

## 🎬 Conclusion

### **Your AI System is Already Excellent for Current Needs**

**What you have:**

- ✅ 80-100% accuracy across all phases
- ✅ Fast response times (<100ms)
- ✅ Real-time pricing and availability
- ✅ Conversational upsell flow
- ✅ Multi-agent architecture

**What you should add next:**

1. **spaCy** (better NLP, no GPU) - Week 4
2. **sentence-transformers** (semantic search) - Week 4
3. **scikit-learn** (predictions) - Month 2 when data available

**What to skip for now:**

- ❌ TensorFlow/PyTorch (wait 6-12 months)
- ❌ GPU infrastructure (not needed yet)
- ❌ Custom deep learning models (insufficient data)

**ROI Analysis:**

- Rule-based enhancements: $0 cost, 10-15% accuracy gain, 1 week
- TensorFlow/PyTorch: $500-2000/month, 5-10% gain, 3-6 months
- **Winner: Rule-based + lightweight NLP**

---

## 📞 Decision Time

**I recommend: Start with spaCy + sentence-transformers this week.**

This gives you:

- ✅ Better tone detection
- ✅ Semantic FAQ search
- ✅ Entity extraction (dates, numbers, names)
- ✅ Near-zero cost
- ✅ 1 week implementation

Then revisit deep learning in 6 months when you have:

- 1000+ conversations
- 500+ bookings
- Clear ML use cases

**What do you think? Want me to implement the spaCy enhancement now?**
