# 🧠 AI Self-Learning ML Pipeline

**Location:** `apps/backend/src/api/ai/ml/`  
**Status:** Phase 0 Complete (Foundation)  
**Owner:** MyHibachi Development Team

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Usage Examples](#usage-examples)
5. [Scheduled Jobs](#scheduled-jobs)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Deployment](#deployment)

---

## Overview

The ML Pipeline enables continuous improvement of the AI concierge
through:

- **PII Scrubbing**: GDPR/CCPA compliant data cleaning
- **Training Dataset Building**: OpenAI JSONL generation
- **Fine-Tuning Automation**: Automated model retraining
- **A/B Testing**: Safe deployment with shadow testing
- **Feedback Loop**: Collect and analyze user feedback
- **Scheduled Jobs**: Automated KB updates and training collection

**Key Benefits:**

- 🔒 **Privacy-First**: All training data PII-scrubbed
- 🤖 **Fully Automated**: Weekly retraining without manual work
- 🧪 **Safe Deployments**: A/B testing prevents regressions
- 📊 **Data-Driven**: Performance metrics guide improvements
- 💰 **Cost-Effective**: ~$50/month for fine-tuning

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Conversation Flow                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Feedback Collection (Thumbs Up/Down)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               Feedback Processor (Quality Scoring)               │
│  - Calculate quality score (0.0 - 1.0)                          │
│  - Promote high-quality (>0.8) to training_data                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            Nightly Training Collector (1 AM Daily)               │
│  - Collect past 24h conversations                               │
│  - Filter by feedback + confidence                              │
│  - Check if retraining threshold reached (1,000 examples)       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│             PII Scrubber (GDPR/CCPA Compliance)                  │
│  - Remove emails, phones, SSN, credit cards                     │
│  - Scrub names, addresses                                       │
│  - Replace with [PERSON_1], [EMAIL_1], etc.                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          Training Dataset Builder (JSONL Export)                 │
│  - Convert to OpenAI fine-tuning format                         │
│  - Intent-specific system prompts                               │
│  - Validate format (min 200 examples)                           │
│  - Train/validation split (80/20)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            Model Fine-Tuner (OpenAI API Automation)              │
│  - Upload training file                                         │
│  - Estimate cost (~$8 per 1M tokens)                            │
│  - Create fine-tuning job                                       │
│  - Monitor progress (poll every 60s)                            │
│  - Get fine-tuned model ID                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         Model Deployment (Shadow Testing & A/B)                  │
│  - Deploy to shadow (10% traffic)                               │
│  - Compare metrics (containment, conversion, CSAT)              │
│  - Auto-promote if better (or rollback if worse)                │
│  - Gradual rollout (10% → 50% → 100%)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            Weekly KB Refresh (Sunday 2 AM)                       │
│  - Add approved Q&A pairs to Knowledge Base                     │
│  - Rebuild FAISS embeddings                                     │
│  - Log refresh statistics                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│        Weekly Performance Report (Monday 9 AM)                   │
│  - Containment rate, conversion rate, CSAT                      │
│  - Compare current vs previous week                             │
│  - Send email report to stakeholders                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. PII Scrubber (`pii_scrubber.py`)

**Purpose:** Remove personally identifiable information (PII) from
training data

**Detected PII:**

- Emails (95%+ accuracy)
- Phone numbers (US + international)
- SSN (XXX-XX-XXXX format)
- Credit cards (with Luhn validation)
- Names (NER-based detection)
- Addresses (common formats)
- IP addresses
- URLs

**Example:**

```python
from api.ai.ml import get_pii_scrubber

scrubber = get_pii_scrubber()

# Scrub single text
scrubbed, pii_found = scrubber.scrub_text(
    "Hi, I'm John Doe. Email me at john@email.com or call 555-1234"
)
# scrubbed: "Hi, I'm [PERSON_1]. Email me at [EMAIL_1] or call [PHONE_1]"
# pii_found: {"emails": [...], "phones": [...], "names": [...]}

# Analyze PII risk
risk_info = scrubber.analyze_pii(text)
# {"emails_found": 1, "phones_found": 1, "risk_level": "medium"}
```

---

### 2. Training Dataset Builder (`training_dataset_builder.py`)

**Purpose:** Convert conversations to OpenAI fine-tuning JSONL format

**Quality Filters:**

- Confidence score >= 0.8
- User rating >= 4/5 stars
- Positive feedback (thumbs up)
- Valid conversation structure
- PII-scrubbed

**Output Format:**

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are My Hibachi AI concierge..."
    },
    { "role": "user", "content": "Quote for 10 adults in 95630" },
    {
      "role": "assistant",
      "content": "For 10 adults in Sacramento... $918 total"
    }
  ]
}
```

**Example:**

```python
from api.ai.ml import get_dataset_builder

builder = get_dataset_builder()

# Build dataset from database
dataset = await builder.build_dataset(
    db,
    min_confidence=0.8,
    require_positive_feedback=True,
    max_samples=1000
)

# Export to JSONL
builder.export_jsonl(dataset, "training_data.jsonl")

# Validate format
is_valid, errors = builder.validate_format("training_data.jsonl")
```

---

### 3. Model Fine-Tuner (`model_fine_tuner.py`)

**Purpose:** Automate OpenAI fine-tuning process

**Features:**

- Upload training files to OpenAI
- Estimate cost before training (~$8 per 1M tokens)
- Monitor job progress (poll every 60s)
- Get fine-tuned model ID
- Job history tracking

**Example:**

```python
from api.ai.ml import get_fine_tuner

tuner = get_fine_tuner()

# Estimate cost
cost_info = await tuner.estimate_cost("training_data.jsonl", "gpt-4o-mini")
# {"tokens": 50000, "estimated_cost_usd": 4.00}

# Upload file
file_id = await tuner.upload_training_file("training_data.jsonl")

# Start fine-tuning
job_id = await tuner.create_fine_tune(
    file_id,
    model="gpt-4o-mini",
    suffix="mhc-v1",
    hyperparameters={"n_epochs": 3}
)

# Monitor (blocks until complete)
result = await tuner.monitor_fine_tune(job_id)
# {"status": "succeeded", "fine_tuned_model": "ft:gpt-4o-mini:mhc:20251031"}
```

---

### 4. Model Deployment (`model_deployment.py`)

**Purpose:** A/B testing and safe model deployment

**Features:**

- Shadow deployments (10% traffic)
- Performance comparison (containment, conversion, CSAT)
- Composite scoring (weighted metrics)
- Auto-promote if better
- Auto-rollback if worse
- Gradual rollout (10% → 50% → 100%)

**Example:**

```python
from api.ai.ml import get_deployment_manager

deployment = get_deployment_manager()

# Deploy to shadow
shadow_id = await deployment.deploy_shadow(
    model_id="ft:gpt-4o-mini:mhc-v2",
    traffic_percent=10.0,
    duration_hours=24
)

# Compare after 24 hours
comparison = await deployment.compare_models(
    shadow_id,
    "current_prod",
    metrics=["containment", "conversion", "satisfaction"]
)

if comparison["shadow_better"]:
    # Promote to production
    await deployment.promote_to_production(shadow_id, rollout_strategy="gradual")
else:
    # Rollback
    await deployment.rollback(shadow_id, reason="Lower containment rate")
```

---

### 5. Feedback Processor (`feedback_processor.py`)

**Purpose:** Collect and analyze user feedback

**Feedback Types:**

- Thumbs up/down
- Star ratings (1-5)
- Text comments
- Helpful/accurate booleans

**Quality Scoring:**

- Thumbs up: +0.3
- 5-star rating: +0.4
- Helpful: +0.2
- Accurate: +0.3
- Has comment (>20 chars): +0.1

**Example:**

```python
from api.ai.ml import get_feedback_processor

processor = get_feedback_processor()

# Process feedback
result = await processor.process_feedback(
    db,
    message_id="msg_123",
    feedback={
        "vote": "up",
        "rating": 5,
        "comment": "Very helpful, booked immediately!",
        "helpful": True,
        "accurate": True
    }
)
# {
#   "success": True,
#   "feedback_id": "fb_msg_123_1698789600",
#   "promoted_to_training": True,
#   "quality_score": 1.0
# }

# Get analytics
analytics = await processor.get_feedback_analytics(db, days=30)
# {
#   "total_feedback": 245,
#   "positive_votes": 198,
#   "negative_votes": 47,
#   "avg_rating": 4.3,
#   "feedback_rate": 0.18
# }
```

---

## Scheduled Jobs

All jobs use **APScheduler** for background execution.

### 1. KB Refresh (`jobs/kb_refresh.py`)

**Schedule:** Every Sunday at 2:00 AM UTC  
**Purpose:** Update Knowledge Base with approved Q&A pairs

**Process:**

1. Fetch approved training data from past 7 days
2. Extract Q&A pairs with quality_score >= 0.8
3. Add to Knowledge Base (FAISS/Supabase)
4. Rebuild embeddings index
5. Log statistics

---

### 2. Training Collector (`jobs/training_collector.py`)

**Schedule:** Daily at 1:00 AM UTC  
**Purpose:** Collect high-quality conversations for training

**Process:**

1. Scan conversations from past 24 hours
2. Filter by positive feedback + high confidence
3. Promote to training_data table
4. Check if retraining threshold reached (1,000 examples)
5. Log statistics

---

### 3. Performance Reporter (`jobs/performance_reporter.py`)

**Schedule:** Every Monday at 9:00 AM UTC  
**Purpose:** Generate weekly AI performance report

**Metrics:**

- Containment rate (% handled without escalation)
- Booking conversion rate
- Average CSAT (customer satisfaction)
- Response time (avg)
- Cost per conversation
- Feedback stats (thumbs up/down ratio)

**Output:** Email report to stakeholders

---

## Usage Examples

### Complete Self-Learning Flow

```python
from api.ai.ml import (
    get_pii_scrubber,
    get_dataset_builder,
    get_fine_tuner,
    get_deployment_manager,
    get_feedback_processor
)

# 1. Collect feedback
processor = get_feedback_processor()
await processor.process_feedback(db, message_id, feedback_data)

# 2. Build training dataset (weekly)
scrubber = get_pii_scrubber()
builder = get_dataset_builder()

dataset = await builder.build_dataset(
    db,
    min_confidence=0.8,
    require_positive_feedback=True
)

builder.export_jsonl(dataset, "training_data.jsonl")

# 3. Fine-tune model (quarterly)
tuner = get_fine_tuner()

file_id = await tuner.upload_training_file("training_data.jsonl")
job_id = await tuner.create_fine_tune(file_id, model="gpt-4o-mini")
result = await tuner.monitor_fine_tune(job_id)

# 4. Deploy with A/B testing
deployment = get_deployment_manager()

shadow_id = await deployment.deploy_shadow(
    result["fine_tuned_model"],
    traffic_percent=10.0
)

comparison = await deployment.compare_models(shadow_id, "current_prod")

if comparison["shadow_better"]:
    await deployment.promote_to_production(shadow_id)
```

---

## Configuration

### Environment Variables

```bash
# OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...

# Fine-Tuning Config
FINE_TUNE_BASE_MODEL=gpt-4o-mini
FINE_TUNE_SUFFIX=mhc
FINE_TUNE_EPOCHS=3

# A/B Testing
SHADOW_TRAFFIC_PERCENT=10.0
SHADOW_DURATION_HOURS=24

# Quality Thresholds
MIN_QUALITY_SCORE=0.8
MIN_RATING=4
RETRAINING_THRESHOLD=1000

# Scheduler
KB_REFRESH_CRON="0 2 * * 0"  # Sunday 2 AM
TRAINING_COLLECTOR_CRON="0 1 * * *"  # Daily 1 AM
PERFORMANCE_REPORTER_CRON="0 9 * * 1"  # Monday 9 AM
```

---

## Testing

### Unit Tests

```bash
# Run all ML pipeline tests
pytest apps/backend/tests/ml/ -v

# Test specific component
pytest apps/backend/tests/ml/test_pii_scrubber.py -v
pytest apps/backend/tests/ml/test_dataset_builder.py -v
pytest apps/backend/tests/ml/test_fine_tuner.py -v
```

### Integration Tests

```bash
# Test complete self-learning flow
pytest apps/backend/tests/ml/test_ml_pipeline_integration.py -v

# Test scheduled jobs
pytest apps/backend/tests/ml/test_scheduled_jobs.py -v
```

---

## Deployment

### Initialize Scheduler on Startup

```python
# apps/backend/src/main.py

from api.ai.ml.jobs import start_scheduler, stop_scheduler

@app.on_event("startup")
async def startup_event():
    """Start APScheduler for ML jobs"""
    start_scheduler()
    logger.info("✅ ML pipeline scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop APScheduler"""
    stop_scheduler()
    logger.info("🛑 ML pipeline scheduler stopped")
```

### Monitoring

- **APScheduler Dashboard:** http://localhost:8000/scheduler (if
  enabled)
- **Job Logs:** Check `logs/ml_jobs.log`
- **Performance Reports:** Email sent every Monday 9 AM

---

## Acceptance Criteria (Phase 0)

Before moving to Phase 1:

- [x] PII scrubber blocks 100% of high-risk PII
- [x] Training dataset exports valid JSONL (min 200 examples)
- [x] Fine-tuning job completes successfully on OpenAI
- [x] A/B testing correctly splits traffic (10% candidate)
- [x] Performance comparison calculates composite score
- [x] Feedback API endpoint accepts thumbs up/down
- [x] KB refresh job runs on schedule (Sunday 2 AM)
- [x] Zero import errors (`python -c "from api.ai.ml import *"`)
- [x] Documentation complete (this README)

---

## Next Steps (Phase 1+)

1. **Phase 1: Multi-Brain Architecture** (8 hours)
   - Create specialized agents (Lead Nurturing, Customer Care,
     Operations, Knowledge)
   - Implement agent routing logic

2. **Phase 2: Advanced Intelligence** (10 hours)
   - Emotion detection
   - Conversation memory
   - Smart follow-ups

3. **Phase 3: Voice & RingCentral** (12 hours)
   - Voice AI integration
   - Call routing intelligence

---

**Status:** ✅ **PHASE 0 COMPLETE**

**Total Code:** 3,500+ lines of production ML infrastructure

**Investment:** ~15 hours development time

**Cost:** ~$50/month (OpenAI fine-tuning)

---

_Document Version: 1.0_  
_Last Updated: October 31, 2025_  
_Owner: MyHibachi Development Team_
