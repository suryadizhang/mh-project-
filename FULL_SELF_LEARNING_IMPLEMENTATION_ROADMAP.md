# 🚀 FULL SELF-LEARNING PIPELINE + 20 AI IMPROVEMENTS
## Implementation Roadmap v2.0

**Project:** My Hibachi Chef AI Concierge  
**Start Date:** October 31, 2025  
**Architecture:** Monorepo (Backend VPS, Customer/Admin Vercel)  
**Status:** Phase 0 in Progress

---

## 📊 Progress Tracker

| Phase | Status | Components | Timeline | Investment |
|-------|--------|------------|----------|------------|
| **Phase 0: Foundation** | 🟡 In Progress | PII, Training, Fine-Tuning, Deployment | 15 hours | $480 |
| **Phase 1: Multi-Brain** | ⏳ Queued | Sub-agents (4x) | 8 hours | $256 |
| **Phase 2: Intelligence** | ⏳ Queued | Emotion, Memory, Follow-ups | 10 hours | $320 |
| **Phase 3: Voice & Ops** | ⏳ Queued | RingCentral, Call Routing | 12 hours | $384 |
| **Phase 4: Business** | ⏳ Queued | CRM, Analytics, Predictive | 15 hours | $480 |
| **Phase 5: Scale** | ⏳ Queued | Multi-language, Chef Matching | 10 hours | $320 |
| **Total** | **35% Complete** | **70 hours** | **4-6 weeks** | **$2,240** |

---

## 🎯 What We're Building

### Core Self-Learning Pipeline (Phase 0) ✅ **60% COMPLETE**

#### ✅ Completed Today:
1. **PII Scrubber** (`ml/pii_scrubber.py`) - 300 lines
   - Regex-based detection (email, phone, SSN, credit card, IP, URL)
   - Name detection (NER-ready)
   - Risk level calculation
   - Batch processing
   - Training validation

2. **Training Dataset Builder** (`ml/training_dataset_builder.py`) - 400 lines
   - JSONL export for OpenAI fine-tuning
   - Quality filtering (score >= 0.8, rating >= 4)
   - PII scrubbing integration
   - Intent-specific system prompts
   - Dataset validation (min 200 examples)
   - Human evaluation export

3. **Model Fine-Tuner** (`ml/model_fine_tuner.py`) - 350 lines
   - OpenAI API automation
   - File upload & job creation
   - Progress monitoring (poll every 60s)
   - Cost estimation (~$8 per 1M tokens)
   - Duration estimation
   - Job cancellation

4. **Model Deployment** (`ml/model_deployment.py`) - 400 lines
   - Shadow deployment (10% traffic)
   - Consistent hashing (same user → same model)
   - Performance comparison (containment, conversion, satisfaction)
   - Composite scoring (weighted metrics)
   - Auto-promotion/rollback
   - Deployment history tracking

#### ⏳ Remaining (Phase 0):
5. **Feedback Processor** (`ml/feedback_processor.py`) - 4 hours
   - Feedback API endpoint
   - Email/chat feedback widgets
   - Feedback analytics
   - Training data promotion

6. **Scheduled Jobs** (`ml/jobs/`) - 3 hours
   - Weekly KB refresh (Sunday 2 AM)
   - Nightly training data collection
   - Monthly fine-tuning automation
   - Performance report generation

---

## 🧠 20 AI Improvements Breakdown

### **Tier 1: Intelligence Core (Phase 1-2)**

#### Phase 1: Multi-Brain Architecture (8 hours)
**Goal:** Specialized sub-agents with domain expertise

**Components:**
1. **Lead Nurturing Agent** (`agents/lead_nurturing_agent.py`)
   - Sales psychology (upselling, FOMO, urgency)
   - Conversion optimization
   - Follow-up timing
   - **Tools:** `create_lead`, `schedule_followup`, `calc_lifetime_value`

2. **Customer Care Agent** (`agents/customer_care_agent.py`)
   - Empathy-first responses
   - Complaint resolution
   - Apology templates
   - **Tools:** `escalate_to_manager`, `issue_refund`, `create_ticket`

3. **Operations Agent** (`agents/operations_agent.py`)
   - Chef availability
   - Schedule optimization
   - Logistics coordination
   - **Tools:** `check_availability`, `assign_chef`, `calc_travel_logistics`

4. **Knowledge Agent** (`agents/knowledge_agent.py`)
   - RAG expert
   - Policy lookup
   - Menu details
   - **Tools:** `search_kb`, `get_policy`, `get_menu_details`

**Integration:**
```python
# ai_orchestrator.py (new agent routing)
class AIOrchestrator:
    def __init__(self):
        self.agents = {
            "lead_nurturing": LeadNurturingAgent(),
            "customer_care": CustomerCareAgent(),
            "operations": OperationsAgent(),
            "knowledge": KnowledgeAgent()
        }
    
    async def route_to_agent(self, intent: str, message: str):
        """Route inquiry to specialized agent"""
        agent_map = {
            "pricing": "lead_nurturing",
            "booking": "operations",
            "complaint": "customer_care",
            "info": "knowledge"
        }
        agent = self.agents[agent_map.get(intent, "knowledge")]
        return await agent.process(message)
```

**Deliverable:** Sub-agent architecture with intent-based routing

---

#### Phase 2: Advanced Intelligence (10 hours)
**Goal:** Emotion detection, memory, personality, smart follow-ups

**Components:**
1. **Emotion Detection** (`ml/emotion_detector.py`)
   - Sentiment analysis (OpenAI embeddings + HuggingFace)
   - Intent classification (pricing, booking, complaint, etc.)
   - Emotion state (happy, neutral, confused, angry)
   - Auto-escalation triggers
   
   ```python
   class EmotionDetector:
       async def detect(self, text: str) -> Dict:
           return {
               "emotion": "frustrated",
               "intensity": 0.8,
               "intent": "complaint",
               "should_escalate": True
           }
   ```

2. **Conversation Memory** (`ml/conversation_memory.py`)
   - Redis/PostgreSQL memory layer
   - Returning customer recognition
   - Context threading
   
   ```python
   class ConversationMemory:
       async def remember(self, customer_id: str):
           return {
               "last_event": "Sonoma wedding (May 2024)",
               "preferred_proteins": ["filet mignon", "lobster"],
               "total_spent": "$3,245"
           }
   ```

3. **Personality Fine-Tuning** (`ml/personality.py`)
   - Brand voice guide (friendly, premium, humorous)
   - Few-shot style anchors
   - Tone consistency validator

4. **Smart Follow-Ups** (`ml/followup_scheduler.py`)
   - 24h reminder if no booking
   - 48h incentive offer
   - 7-day re-engagement
   
   **APScheduler Integration:**
   ```python
   from apscheduler.schedulers.asyncio import AsyncIOScheduler
   
   scheduler = AsyncIOScheduler()
   scheduler.add_job(
       send_followup_reminders,
       'cron',
       hour=10,  # 10 AM daily
       minute=0
   )
   ```

**Deliverable:** Emotional AI + Memory + Follow-ups

---

### **Tier 2: Omnichannel & Voice (Phase 3)**

#### Phase 3: Voice & RingCentral Integration (12 hours)
**Goal:** AI voice concierge with emotion detection

**Components:**
1. **RingCentral Voice Handler** (`integrations/ringcentral_voice.py`)
   - Webhook endpoints for incoming calls
   - Speech-to-text (Whisper API)
   - AI reasoning (GPT-4o with voice context)
   - Text-to-speech (OpenAI TTS / ElevenLabs)
   - Call transfer logic

2. **Voice Emotion Detection** (`ml/voice_emotion.py`)
   - pyannote.audio for stress detection
   - Tone analysis
   - Escalation triggers

3. **Call Routing Intelligence** (`services/call_router.py`)
   - CRM tag checking (new lead, VIP, complaint)
   - Route to correct person
   - Slack/email call summaries

**API Endpoints:**
```python
# apps/backend/src/api/integrations/ringcentral.py

@app.post("/webhooks/ringcentral/inbound-call")
async def handle_inbound_call(call_data: RingCentralCallEvent):
    """Handle incoming phone call"""
    # 1. Transcribe audio → text
    transcript = await transcribe_audio(call_data.audio_url)
    
    # 2. Detect emotion
    emotion = await voice_emotion_detector.detect(call_data.audio_url)
    
    # 3. Process through orchestrator
    response = await orchestrator.process_inquiry(
        message=transcript,
        channel="phone",
        metadata={"emotion": emotion}
    )
    
    # 4. Convert to speech
    audio = await text_to_speech(response.response)
    
    # 5. Return audio to RingCentral
    return {"audio_url": audio.url}
```

**Deliverable:** Voice AI + Call routing + Transcripts

---

### **Tier 3: Business Intelligence (Phase 4)**

#### Phase 4: CRM, Analytics, Predictive AI (15 hours)
**Goal:** Transform AI from reactive → proactive business tool

**Components:**
1. **CRM Sync** (`integrations/crm_sync.py`)
   - Push leads to HubSpot/Airtable
   - Auto-tagging by source channel
   - Campaign triggering

2. **Analytics Dashboard** (`admin/dashboard/AIMetrics.tsx`)
   - Real-time KPIs
   - Conversion funnel
   - Containment rate
   - CSAT tracking
   - Cost per conversation

3. **Predictive Insights** (`ml/predictive.py`)
   - Lead scoring model (hot vs cold)
   - Demand forecasting (high-booking dates)
   - Chef assignment optimization

**Dashboard Components:**
```typescript
// apps/admin/src/components/ai/AIMetricsDashboard.tsx

export function AIMetricsDashboard() {
  return (
    <div className="grid grid-cols-4 gap-4">
      <MetricCard
        title="Containment Rate"
        value="87%"
        target="80%"
        status="success"
      />
      <MetricCard
        title="Booking Conversion"
        value="23%"
        target="20%"
        status="success"
      />
      <MetricCard
        title="Avg CSAT"
        value="4.6/5"
        target="4.0"
        status="success"
      />
      <MetricCard
        title="AI Cost per Conversation"
        value="$0.03"
        target="$0.05"
        status="success"
      />
    </div>
  );
}
```

**Deliverable:** CRM integration + Analytics + Predictive AI

---

### **Tier 4: Scale & Expansion (Phase 5)**

#### Phase 5: Multi-Language & Advanced Features (10 hours)
**Goal:** Global scale + chef automation

**Components:**
1. **Multi-Language Support** (`ml/translation.py`)
   - DeepL / GPT-4o multilingual
   - Language detection
   - Auto-translation middleware
   - Supported: Spanish, Chinese, Tagalog, Vietnamese

2. **AI Chef Assignment** (`ml/chef_matcher.py`)
   - Distance optimization
   - Skill matching (special menus)
   - Workload balancing
   - Customer rating consideration

3. **Dynamic Cross-Selling** (`agents/upsell_agent.py`)
   - Context-aware recommendations
   - Holiday bundle automation
   - Add-on suggestions (dessert chef, bartender)

**Deliverable:** Multi-language + Chef matching + Smart upsells

---

## 📂 Project Structure (Updated)

```
apps/
├── backend/ (VPS Deployment)
│   └── src/
│       └── api/
│           ├── ai/
│           │   ├── orchestrator/          # ✅ Phase 0 (Day 1-3)
│           │   │   ├── ai_orchestrator.py # Main orchestrator
│           │   │   ├── tools/             # 3 production tools
│           │   │   ├── schemas/           # Request/response models
│           │   │   └── services/          # Phase 3 placeholders
│           │   │
│           │   ├── ml/                    # 🟡 Phase 0 (NEW - 60% Complete)
│           │   │   ├── __init__.py        # ✅ Module exports
│           │   │   ├── pii_scrubber.py    # ✅ PII detection/removal
│           │   │   ├── training_dataset_builder.py  # ✅ JSONL export
│           │   │   ├── model_fine_tuner.py          # ✅ OpenAI fine-tuning
│           │   │   ├── model_deployment.py          # ✅ A/B testing
│           │   │   ├── feedback_processor.py        # ⏳ TODO (4 hours)
│           │   │   ├── emotion_detector.py          # ⏳ Phase 2
│           │   │   ├── conversation_memory.py       # ⏳ Phase 2
│           │   │   ├── personality.py               # ⏳ Phase 2
│           │   │   ├── followup_scheduler.py        # ⏳ Phase 2
│           │   │   ├── translation.py               # ⏳ Phase 5
│           │   │   ├── chef_matcher.py              # ⏳ Phase 5
│           │   │   └── jobs/                        # ⏳ Scheduled tasks
│           │   │       ├── kb_refresh.py
│           │   │       ├── training_collector.py
│           │   │       └── performance_reporter.py
│           │   │
│           │   ├── agents/                # ⏳ Phase 1 (NEW)
│           │   │   ├── __init__.py
│           │   │   ├── base_agent.py      # Abstract base class
│           │   │   ├── lead_nurturing_agent.py
│           │   │   ├── customer_care_agent.py
│           │   │   ├── operations_agent.py
│           │   │   ├── knowledge_agent.py
│           │   │   └── upsell_agent.py    # Phase 5
│           │   │
│           │   ├── endpoints/             # ✅ Existing
│           │   │   ├── main.py            # FastAPI routes
│           │   │   ├── models.py          # DB models
│           │   │   ├── schemas.py         # Pydantic schemas
│           │   │   └── services/          # Business logic
│           │   │       ├── self_learning_ai.py  # ✅ Existing
│           │   │       ├── knowledge_base.py    # ✅ RAG/FAISS
│           │   │       └── multi_channel_ai_handler.py  # ✅ Day 3
│           │   │
│           │   └── integrations/          # ⏳ Phase 3-4 (NEW)
│           │       ├── ringcentral_voice.py
│           │       ├── ringcentral_sms.py
│           │       ├── meta_graph.py      # FB/IG DMs
│           │       ├── gmail.py
│           │       ├── google_business.py # Reviews
│           │       └── crm_sync.py        # HubSpot/Airtable
│           │
│           └── app/                       # ✅ Existing core
│               ├── models/               # DB schemas
│               └── services/             # Business services
│
├── admin/ (Vercel Deployment)
│   └── src/
│       └── components/
│           └── ai/                        # ⏳ Phase 4 (NEW)
│               ├── AIMetricsDashboard.tsx
│               ├── FeedbackReviewPanel.tsx
│               ├── ModelComparisonView.tsx
│               └── TrainingDatasetManager.tsx
│
└── customer/ (Vercel Deployment)
    └── src/
        └── components/
            └── feedback/                  # ⏳ Phase 0 (NEW)
                ├── FeedbackWidget.tsx
                └── EmailFeedbackButtons.tsx
```

---

## 🔧 Implementation Steps (Phase by Phase)

### **PHASE 0: Self-Learning Foundation (15 hours)** 🟡 60% Complete

#### ✅ Completed (11 hours):
1. PII Scrubber (2 hours)
2. Training Dataset Builder (3 hours)
3. Model Fine-Tuner (3 hours)
4. Model Deployment (3 hours)

#### ⏳ Remaining (4 hours):

**Step 1: Feedback Processor (2 hours)**
```python
# apps/backend/src/api/ai/ml/feedback_processor.py

class FeedbackProcessor:
    async def process_feedback(
        self,
        message_id: str,
        feedback: Dict[str, Any]
    ):
        """
        Process user feedback:
        - Store in message.metadata
        - Analyze for quality score
        - Promote high-quality to training_data
        - Trigger KB update if needed
        """
        pass
```

**Step 2: Feedback API Endpoints (1 hour)**
```python
# apps/backend/src/api/ai/endpoints/feedback_routes.py

@router.post("/api/v1/ai/feedback")
async def submit_feedback(
    message_id: str,
    vote: str,  # "up" or "down"
    comment: Optional[str] = None
):
    """Public feedback endpoint"""
    processor = get_feedback_processor()
    return await processor.process_feedback(message_id, {
        "vote": vote,
        "comment": comment
    })
```

**Step 3: Scheduled Jobs (1 hour)**
```python
# apps/backend/src/api/ai/ml/jobs/kb_refresh.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def weekly_kb_refresh():
    """Every Sunday at 2 AM"""
    builder = get_dataset_builder()
    kb_service = get_kb_service()
    
    # Fetch new approved Q&A
    new_qa = await builder.fetch_approved_pairs(days=7)
    
    # Add to KB
    for qa in new_qa:
        await kb_service.add_chunk(qa)
    
    # Rebuild index
    await kb_service.rebuild_index()

scheduler = AsyncIOScheduler()
scheduler.add_job(weekly_kb_refresh, 'cron', day_of_week='sun', hour=2)
scheduler.start()
```

**Deliverable:** Complete self-learning pipeline with feedback loop

---

### **PHASE 1: Multi-Brain Architecture (8 hours)**

**Step 1: Base Agent Class (1 hour)**
```python
# apps/backend/src/api/ai/agents/base_agent.py

class BaseAgent(ABC):
    """Abstract base class for specialized agents"""
    
    @abstractmethod
    async def process(self, message: str, context: Dict) -> Dict:
        """Process inquiry with domain expertise"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """Get agent-specific tools"""
        pass
```

**Step 2-5: Specialized Agents (6 hours total)**
- Lead Nurturing Agent (2 hours)
- Customer Care Agent (1.5 hours)
- Operations Agent (1.5 hours)
- Knowledge Agent (1 hour)

**Step 6: Agent Router Integration (1 hour)**
```python
# Modify ai_orchestrator.py to route to agents
class AIOrchestrator:
    def __init__(self):
        self.agents = {
            "lead_nurturing": LeadNurturingAgent(),
            "customer_care": CustomerCareAgent(),
            "operations": OperationsAgent(),
            "knowledge": KnowledgeAgent()
        }
    
    async def process_inquiry(self, request: OrchestratorRequest):
        # Detect intent
        intent = await self.detect_intent(request.message)
        
        # Route to specialized agent
        agent = self.select_agent(intent)
        
        # Process with agent
        return await agent.process(request.message, request.customer_context)
```

**Deliverable:** 4 specialized agents with domain expertise

---

### **PHASE 2: Advanced Intelligence (10 hours)**

**Components to Build:**
1. Emotion Detector (3 hours)
2. Conversation Memory (3 hours)
3. Personality Fine-Tuning (2 hours)
4. Smart Follow-Ups (2 hours)

**Deliverable:** Emotionally intelligent AI with memory and follow-ups

---

### **PHASE 3: Voice & RingCentral (12 hours)**

**Components to Build:**
1. RingCentral Voice Handler (5 hours)
2. Voice Emotion Detection (3 hours)
3. Call Routing Intelligence (2 hours)
4. Transcription Pipeline (2 hours)

**Deliverable:** AI voice concierge with call routing

---

### **PHASE 4: Business Intelligence (15 hours)**

**Components to Build:**
1. CRM Sync (HubSpot/Airtable) (4 hours)
2. Analytics Dashboard (React) (6 hours)
3. Predictive Lead Scoring (3 hours)
4. Demand Forecasting (2 hours)

**Deliverable:** CRM integration + Analytics + Predictive AI

---

### **PHASE 5: Scale & Expansion (10 hours)**

**Components to Build:**
1. Multi-Language Support (4 hours)
2. AI Chef Assignment (4 hours)
3. Dynamic Cross-Selling (2 hours)

**Deliverable:** Global-ready AI with chef automation

---

## 🎯 Success Metrics by Phase

| Phase | Metric | Target | Measurement |
|-------|--------|--------|-------------|
| **Phase 0** | Feedback collection rate | >15% | % of conversations with feedback |
| | Training dataset size | 200+ examples | Approved Q&A pairs per month |
| | Fine-tune cost | <$50/month | OpenAI billing |
| **Phase 1** | Agent accuracy | >90% | Intent routing correctness |
| | Response relevance | >85% | User satisfaction |
| **Phase 2** | Emotion detection accuracy | >80% | Manual validation |
| | Follow-up conversion | >10% | Bookings from follow-ups |
| **Phase 3** | Call containment | >70% | % calls handled by AI |
| | Voice escalation rate | <20% | % calls escalated to human |
| **Phase 4** | Lead conversion lift | +15% | AI vs baseline |
| | Booking prediction accuracy | >75% | Predicted vs actual |
| **Phase 5** | Multi-language support | 5 languages | Spanish, Chinese, Tagalog, Vietnamese, Japanese |
| | Chef assignment time | <5 minutes | Automated matching |

---

## 💰 Cost Breakdown

| Component | One-Time | Monthly | Notes |
|-----------|----------|---------|-------|
| **Development** | $2,240 | - | 70 hours @ $32/hr |
| **OpenAI API** | - | $150 | GPT-4o-mini + embeddings |
| **Fine-Tuning** | - | $50 | Quarterly retraining |
| **RingCentral** | - | $40 | Voice API tier |
| **Vector DB** | - | $0 | Supabase free tier (or FAISS local) |
| **APScheduler** | - | $0 | Built into FastAPI |
| **Total** | **$2,240** | **$240** | **~$0.08 per conversation** |

**ROI Estimate:**
- Cost per conversation: $0.08
- Avg booking value: $750
- Conversion rate: 20%
- Revenue per 100 conversations: $15,000
- AI cost per 100 conversations: $8
- **ROI: 187,400%**

---

## 🚀 Next Immediate Actions

### Today (Phase 0 Completion - 4 hours):
1. ✅ Create `feedback_processor.py` (2 hours)
2. ✅ Add feedback API endpoints (1 hour)
3. ✅ Setup APScheduler for KB refresh (1 hour)

### Tomorrow (Phase 1 Start - 8 hours):
1. ✅ Create base agent class (1 hour)
2. ✅ Build Lead Nurturing Agent (2 hours)
3. ✅ Build Customer Care Agent (1.5 hours)
4. ✅ Build Operations Agent (1.5 hours)
5. ✅ Build Knowledge Agent (1 hour)
6. ✅ Integrate agent routing (1 hour)

### Week 2 (Phase 2 - 10 hours):
1. Emotion detection
2. Conversation memory
3. Personality fine-tuning
4. Smart follow-ups

---

## 📋 Acceptance Criteria (Phase 0)

Before moving to Phase 1, verify:

- [ ] PII scrubber blocks 100% of high-risk PII
- [ ] Training dataset exports valid JSONL (min 200 examples)
- [ ] Fine-tuning job completes successfully on OpenAI
- [ ] A/B testing correctly splits traffic (10% candidate)
- [ ] Performance comparison calculates composite score
- [ ] Feedback API endpoint accepts thumbs up/down
- [ ] KB refresh job runs on schedule (Sunday 2 AM)
- [ ] Zero import errors (`python -c "from api.ai.ml import *"`)
- [ ] Documentation complete (README.md in ml/)

---

## 📚 Documentation To-Do

1. **ML Pipeline README** (`apps/backend/src/api/ai/ml/README.md`)
2. **Agent Architecture Guide** (`apps/backend/src/api/ai/agents/README.md`)
3. **API Endpoints Reference** (update `API_DOCUMENTATION.md`)
4. **Deployment Guide** (update `DEPLOYMENT_CHECKLIST.md`)

---

**Status:** Phase 0 is 60% complete (11/15 hours). Remaining 4 hours to complete self-learning foundation.

**Next Step:** Complete Phase 0 (feedback processor + scheduled jobs) before proceeding to Phase 1 (multi-brain architecture).

---

*Document Version: 2.0*  
*Last Updated: October 31, 2025*  
*Owner: MyHibachi Development Team*
