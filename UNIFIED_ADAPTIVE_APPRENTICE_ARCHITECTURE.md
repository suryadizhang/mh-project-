# 🚀 UNIFIED ADAPTIVE APPRENTICE AI ARCHITECTURE
## My Hibachi Chef - Next-Generation AI System

**Date:** October 31, 2025  
**Status:** Architecture Design - Ready for Implementation  
**Combines:** Original Phases 1-5 + Interactive Apprentice (Phase 8)

---

## 🎯 EXECUTIVE SUMMARY

This unified architecture merges:
- **Multi-Agent specialization** (4 domain expert agents)
- **Teacher-Student apprenticeship** (Llama 3 8B learns from GPT-4o)
- **Confidence-based routing** (adaptive fallback system)
- **RLHF-Lite** (booking-driven rewards)
- **Cross-channel memory** (unified customer context)
- **Human oversight** (dashboard for corrections)

**Result:** A cost-efficient, self-improving AI that handles 80% of inquiries locally while maintaining GPT-4o quality.

---

## 📐 SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                  CUSTOMER INQUIRY (Multi-Channel)                │
│              Email │ SMS │ Instagram │ Phone │ Live Chat         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    INTENT DETECTION LAYER                        │
│  - Classify: pricing, booking, complaint, info, complex          │
│  - Emotion detection: happy, neutral, frustrated, angry          │
│  - Extract: customer_id, channel, conversation_history           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              CROSS-CHANNEL MEMORY GRAPH (Neo4j)                  │
│  - Fetch customer context across all channels                   │
│  - Previous bookings, preferences, issues                        │
│  - Return: unified_customer_profile                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT ROUTER (Intent-Based)                   │
│  pricing → Lead Nurturing Agent                                  │
│  booking → Operations Agent                                      │
│  complaint → Customer Care Agent                                 │
│  info → Knowledge Agent                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│             SPECIALIZED AGENT (Domain Expert)                    │
│  - Agent-specific tools & prompts                                │
│  - RAG knowledge retrieval                                       │
│  - Generates: draft_response + confidence_score                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              STUDENT MODEL (Llama 3 8B - Local)                  │
│  - Generates response using agent prompt                         │
│  - Computes confidence score (entropy-based)                     │
│  - Output: student_response + confidence                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  CONFIDENCE ROUTER (Adaptive)                    │
│  confidence ≥ 0.75 → USE STUDENT (cost: $0.001)                 │
│  0.40 - 0.75 → ASK TEACHER (OpenAI GPT-4o)                      │
│  < 0.40 → ESCALATE TO HUMAN                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                           ↓
┌──────────────────────┐              ┌──────────────────────────┐
│   HIGH CONFIDENCE    │              │    LOW CONFIDENCE        │
│   Student Response   │              │   Teacher (GPT-4o)       │
│   (Direct Delivery)  │              │   + Log for Training     │
└──────────────────────┘              └──────────────────────────┘
        ↓                                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   RESPONSE DELIVERY                              │
│  - Deliver to customer via channel                               │
│  - Track: response_time, channel, confidence_route               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  FEEDBACK COLLECTION                             │
│  👍 Positive │ 👎 Negative │ ⚡ Booking Success                  │
│  + Star rating + text comment                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RLHF-LITE SCORER                              │
│  reward = 1.0 * booking_success                                  │
│         + 0.5 * positive_feedback                                │
│         - 0.3 * escalation                                       │
│         - 0.5 * negative_feedback                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              TUTOR FEEDBACK COLLECTOR                            │
│  - Store: student_output, teacher_output, confidence, reward     │
│  - Table: ai_tutor_pairs                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│             AUTO-LABELING PIPELINE (Nightly)                     │
│  - GPT-4o batch classification                                   │
│  - Labels: intent, sentiment, outcome, quality_score             │
│  - Table: conversation_labels                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           WEEKLY RETRAINING LOOP (APScheduler)                   │
│  1. Fetch high-reward teacher pairs (reward ≥ 0.7)              │
│  2. PII scrubbing (existing Phase 0)                             │
│  3. Generate training JSONL                                      │
│  4. Fine-tune Llama 3 8B (LoRA adapter)                          │
│  5. Evaluate: BLEU score, cosine similarity vs teacher           │
│  6. Shadow deploy: 10% traffic test                              │
│  7. Auto-promote if accuracy ≥ 95%                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           HUMAN-IN-THE-LOOP DASHBOARD (Next.js)                  │
│  - View: AI responses, confidence, fallback route                │
│  - Correct: Manual override → saved as gold training data        │
│  - Analytics: Fallback %, accuracy trend, cost savings           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 CORE COMPONENTS

### **1. Multi-Agent System (4 Specialized Agents)**

#### **A. Lead Nurturing Agent**
**Purpose:** Convert inquiries to bookings with sales psychology

**Personality:**
- Enthusiastic, premium-focused, FOMO-driven
- "Only 3 dates available in December!"
- Upsells: dessert chef, bartender, photographer

**Tools:**
```python
- create_lead(contact_info, event_details)
- calculate_quote(guests, proteins, zip_code)
- schedule_followup(lead_id, hours_delay)
- suggest_upsells(event_type, budget)
- get_availability(date_range, zip_code)
```

**Training Focus:**
- High-reward responses (booking conversions)
- Urgency language patterns
- Objection handling

---

#### **B. Customer Care Agent**
**Purpose:** Resolve complaints with empathy

**Personality:**
- Apologetic, understanding, solution-focused
- "I sincerely apologize for the inconvenience..."
- Proactive compensation offers

**Tools:**
```python
- escalate_to_manager(issue_summary, priority)
- issue_refund(booking_id, amount, reason)
- create_support_ticket(customer_id, issue)
- check_policy(policy_name)
- schedule_callback(customer_id, datetime)
```

**Training Focus:**
- De-escalation language
- Apology templates
- Resolution speed

---

#### **C. Operations Agent**
**Purpose:** Logistics, scheduling, chef assignment

**Personality:**
- Professional, detail-oriented, logistics-focused
- "I've assigned Chef Carlos—he specializes in teppanyaki..."
- Travel time calculations

**Tools:**
```python
- check_chef_availability(date, zip_code)
- assign_chef(booking_id, chef_id)
- calculate_travel_logistics(origin, destination)
- get_chef_skills(chef_id)
- block_calendar(chef_id, date_range)
```

**Training Focus:**
- Accurate distance calculations
- Chef expertise matching
- Schedule optimization

---

#### **D. Knowledge Agent**
**Purpose:** Answer questions using RAG

**Personality:**
- Informative, detailed, policy expert
- "According to our menu, we offer 12 protein options..."
- Cites sources (menu, FAQ, policies)

**Tools:**
```python
- search_kb(query, top_k=5)
- get_menu_details(protein_type)
- get_policy(policy_name)
- get_faq_answer(question)
- search_reviews(topic)
```

**Training Focus:**
- Accurate retrieval
- Source citation
- Policy consistency

---

### **2. Teacher-Student Architecture**

#### **Teacher Model: GPT-4o (OpenAI)**
- **Role:** Gold standard responses
- **Cost:** ~$0.015 per query
- **When used:**
  - Student confidence < 0.75
  - Complex multi-step queries
  - High-stakes bookings
  - Legal/policy questions

#### **Student Model: Llama 3 8B (Local - Ollama/vLLM)**
- **Role:** Primary responder (80% of queries)
- **Cost:** ~$0.001 per query (compute only)
- **Training:** Weekly LoRA fine-tuning on teacher pairs
- **Deployment:** Shadow → A/B test → gradual rollout

**Cost Savings:**
- Baseline (100% GPT-4o): $15/day × 1,000 queries = $15,000/day
- Hybrid (80% Llama, 20% GPT-4o): $0.80 + $3 = $3.80/day
- **Savings: 75% ($11.20/day, $336/month, $4,032/year)**

---

### **3. Confidence-Based Router**

```python
class ConfidenceRouter:
    """Route queries based on student confidence"""
    
    THRESHOLDS = {
        "high": 0.75,      # Use student directly
        "medium": 0.40,    # Ask teacher for help
        "low": 0.40        # Escalate to human
    }
    
    async def route(
        self,
        student_response: str,
        confidence_score: float,
        intent: str,
        emotion: str
    ) -> RouteDecision:
        """
        Determine routing path
        
        Logic:
        - High confidence (≥0.75) → Student
        - Medium (0.40-0.75) + simple intent → Student with teacher log
        - Medium + complex intent → Teacher
        - Low (<0.40) → Human escalation
        - Angry emotion → Always escalate
        """
        
        # Always escalate angry customers
        if emotion == "angry":
            return RouteDecision(
                path="human",
                reason="Customer emotion: angry"
            )
        
        # High confidence → use student
        if confidence_score >= self.THRESHOLDS["high"]:
            return RouteDecision(
                path="student",
                reason=f"High confidence: {confidence_score:.2f}"
            )
        
        # Low confidence → escalate
        if confidence_score < self.THRESHOLDS["medium"]:
            return RouteDecision(
                path="human",
                reason=f"Low confidence: {confidence_score:.2f}"
            )
        
        # Medium confidence → check complexity
        complex_intents = ["complaint", "refund", "legal", "policy"]
        if intent in complex_intents:
            return RouteDecision(
                path="teacher",
                reason=f"Complex intent: {intent}, confidence: {confidence_score:.2f}"
            )
        else:
            return RouteDecision(
                path="student_with_log",
                reason=f"Simple intent: {intent}, medium confidence: {confidence_score:.2f}"
            )
```

---

### **4. RLHF-Lite Reward System**

```python
class RewardScorer:
    """Calculate reward scores for training prioritization"""
    
    WEIGHTS = {
        "booking_success": 1.0,      # Highest priority
        "positive_feedback": 0.5,
        "high_rating": 0.3,          # 4-5 stars
        "fast_resolution": 0.2,
        "no_escalation": 0.1,
        "negative_feedback": -0.5,
        "escalation": -0.3,
        "complaint": -0.2
    }
    
    def calculate_reward(
        self,
        conversation: Dict[str, Any]
    ) -> float:
        """
        Calculate reward score (0.0 to 1.0+)
        
        High rewards prioritized for training
        """
        reward = 0.0
        
        # Booking success = jackpot
        if conversation.get("booking_created"):
            reward += self.WEIGHTS["booking_success"]
        
        # Positive feedback
        feedback = conversation.get("feedback", {})
        if feedback.get("vote") == "up":
            reward += self.WEIGHTS["positive_feedback"]
        
        # High rating
        if feedback.get("rating", 0) >= 4:
            reward += self.WEIGHTS["high_rating"]
        
        # Fast resolution (< 5 minutes)
        if conversation.get("resolution_time_seconds", 999) < 300:
            reward += self.WEIGHTS["fast_resolution"]
        
        # No escalation needed
        if not conversation.get("escalated"):
            reward += self.WEIGHTS["no_escalation"]
        
        # Penalties
        if feedback.get("vote") == "down":
            reward += self.WEIGHTS["negative_feedback"]
        
        if conversation.get("escalated"):
            reward += self.WEIGHTS["escalation"]
        
        if conversation.get("intent") == "complaint":
            reward += self.WEIGHTS["complaint"]
        
        return max(0.0, reward)  # No negative rewards
```

---

### **5. Cross-Channel Memory Graph**

**Technology:** Neo4j (graph database) or PostgreSQL with JSONB

**Schema:**
```cypher
// Neo4j schema
(Customer)-[:HAD_CONVERSATION]->(Conversation)
(Conversation)-[:VIA_CHANNEL]->(Channel)
(Conversation)-[:ABOUT_TOPIC]->(Topic)
(Conversation)-[:LED_TO]->(Booking)
(Customer)-[:PREFERS]->(Protein)
(Customer)-[:COMPLAINED_ABOUT]->(Issue)
```

**API:**
```python
class CrossChannelMemory:
    """Unified customer context across all channels"""
    
    async def get_customer_context(
        self,
        customer_id: str,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Retrieve unified customer profile
        
        Returns:
        {
            "customer_id": "cust_123",
            "total_bookings": 3,
            "total_spent": "$2,450",
            "preferred_proteins": ["filet mignon", "lobster"],
            "last_event": {
                "date": "2024-08-15",
                "type": "wedding",
                "guests": 45,
                "location": "Sonoma"
            },
            "recent_conversations": [
                {
                    "channel": "email",
                    "date": "2024-10-20",
                    "topic": "pricing",
                    "sentiment": "positive"
                },
                {
                    "channel": "phone",
                    "date": "2024-10-25",
                    "topic": "complaint",
                    "sentiment": "frustrated",
                    "resolved": True
                }
            ],
            "open_issues": [],
            "vip_status": True,
            "lifetime_value": "$2,450"
        }
        ```
    
    async def add_conversation(
        self,
        customer_id: str,
        channel: str,
        conversation_data: Dict
    ):
        """Add new conversation to graph"""
        # Neo4j MERGE query or PostgreSQL INSERT
```

---

### **6. Auto-Labeling Pipeline**

**Purpose:** Nightly batch classification using GPT-4o

**Process:**
```python
class AutoLabeler:
    """Batch label conversations for training"""
    
    async def label_batch(
        self,
        conversations: List[Dict],
        batch_size: int = 100
    ):
        """
        Use GPT-4o to classify conversations
        
        Labels:
        - intent: pricing, booking, complaint, info, complex
        - sentiment: positive, neutral, negative, angry
        - outcome: resolved, escalated, booking, no_action
        - quality_score: 0.0 - 1.0
        - channel: email, sms, instagram, facebook, phone, chat
        """
        
        for batch in self._chunk(conversations, batch_size):
            # GPT-4o function call
            response = await openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{
                    "role": "system",
                    "content": """You are a conversation classifier.
                    For each conversation, return:
                    {
                        "intent": "pricing|booking|complaint|info|complex",
                        "sentiment": "positive|neutral|negative|angry",
                        "outcome": "resolved|escalated|booking|no_action",
                        "quality_score": 0.0-1.0
                    }"""
                }, {
                    "role": "user",
                    "content": f"Classify these {len(batch)} conversations:\n{batch}"
                }],
                functions=[{
                    "name": "classify_conversations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "intent": {"type": "string"},
                                        "sentiment": {"type": "string"},
                                        "outcome": {"type": "string"},
                                        "quality_score": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }]
            )
            
            # Save labels to database
            await self._save_labels(response)
```

**Schedule:** Daily at 2 AM (after training collector)

---

### **7. Weekly Retraining Pipeline**

**Process:**
```python
class ApprenticeTrainer:
    """Weekly fine-tuning of Llama 3 8B student model"""
    
    async def weekly_training_job(self):
        """
        Sunday 3 AM: Retrain student model
        
        Steps:
        1. Fetch high-reward teacher pairs (reward ≥ 0.7)
        2. PII scrubbing (reuse Phase 0 scrubber)
        3. Generate training JSONL (teacher responses)
        4. Fine-tune Llama 3 8B with LoRA
        5. Evaluate: BLEU, cosine similarity vs teacher
        6. Shadow deploy (10% traffic)
        7. A/B test for 24 hours
        8. Auto-promote if accuracy ≥ 95%
        """
        
        # 1. Fetch high-quality pairs
        pairs = await self._fetch_training_pairs(
            min_reward=0.7,
            days_back=7
        )
        
        logger.info(f"Fetched {len(pairs)} high-reward pairs")
        
        # 2. PII scrubbing
        from api.ai.ml import get_pii_scrubber
        scrubber = get_pii_scrubber()
        
        clean_pairs = []
        for pair in pairs:
            scrubbed_input, _ = scrubber.scrub_text(pair["input"])
            scrubbed_output, _ = scrubber.scrub_text(pair["teacher_output"])
            clean_pairs.append({
                "input": scrubbed_input,
                "output": scrubbed_output,
                "reward": pair["reward"]
            })
        
        # 3. Generate JSONL
        jsonl_path = await self._generate_training_file(clean_pairs)
        
        # 4. Fine-tune with LoRA
        from transformers import AutoModelForCausalLM, TrainingArguments
        from peft import LoraConfig, get_peft_model
        
        model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8b")
        
        lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05
        )
        
        model = get_peft_model(model, lora_config)
        
        # Train for 3 epochs
        trainer = Trainer(
            model=model,
            args=TrainingArguments(
                output_dir="./llama3_mhc_lora",
                num_train_epochs=3,
                per_device_train_batch_size=4,
                learning_rate=2e-4
            ),
            train_dataset=dataset
        )
        
        trainer.train()
        
        # 5. Evaluate
        accuracy = await self._evaluate_model(model, validation_set)
        
        logger.info(f"New model accuracy: {accuracy:.2%}")
        
        # 6-8. Deploy if good
        if accuracy >= 0.95:
            await self._shadow_deploy(model)
        else:
            logger.warning(f"Accuracy {accuracy:.2%} below threshold, skipping deploy")
```

**Schedule:** Every Sunday 3 AM (after KB refresh)

---

### **8. Human-in-the-Loop Dashboard**

**Technology:** Next.js + shadcn UI + TanStack Query

**Features:**

#### **A. Real-Time Monitoring**
```tsx
// apps/admin/src/components/ai/AIInsightsDashboard.tsx

export function AIInsightsDashboard() {
  const { data: metrics } = useQuery({
    queryKey: ['ai-metrics'],
    queryFn: () => fetch('/api/ai/insights').then(r => r.json()),
    refetchInterval: 5000 // 5 seconds
  });

  return (
    <div className="grid grid-cols-4 gap-4">
      <MetricCard
        title="Student Coverage"
        value={`${metrics?.student_coverage_percent}%`}
        target="80%"
        trend={metrics?.coverage_trend}
      />
      
      <MetricCard
        title="Fallback Rate"
        value={`${metrics?.teacher_fallback_percent}%`}
        target="<20%"
        trend={metrics?.fallback_trend}
      />
      
      <MetricCard
        title="Human Escalation"
        value={`${metrics?.human_escalation_percent}%`}
        target="<5%"
        trend={metrics?.escalation_trend}
      />
      
      <MetricCard
        title="Cost Savings"
        value={`$${metrics?.cost_savings_today}`}
        target="$11/day"
        trend={metrics?.savings_trend}
      />
    </div>
  );
}
```

#### **B. Correction Interface**
```tsx
// apps/admin/src/components/ai/AIResponseReview.tsx

export function AIResponseReview() {
  const { data: pendingReviews } = useQuery({
    queryKey: ['pending-reviews'],
    queryFn: () => fetch('/api/ai/reviews/pending').then(r => r.json())
  });

  return (
    <div className="space-y-4">
      {pendingReviews?.map(review => (
        <Card key={review.id}>
          <CardHeader>
            <div className="flex justify-between">
              <Badge>{review.channel}</Badge>
              <Badge variant={review.confidence >= 0.75 ? 'success' : 'warning'}>
                Confidence: {review.confidence.toFixed(2)}
              </Badge>
            </div>
          </CardHeader>
          
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label>Customer Query:</Label>
                <p className="text-sm">{review.user_message}</p>
              </div>
              
              <div>
                <Label>Student Response:</Label>
                <p className="text-sm">{review.student_response}</p>
              </div>
              
              {review.teacher_response && (
                <div>
                  <Label>Teacher Response:</Label>
                  <p className="text-sm">{review.teacher_response}</p>
                </div>
              )}
              
              <div className="flex gap-2">
                <Button
                  variant="success"
                  onClick={() => approveResponse(review.id)}
                >
                  ✅ Approve
                </Button>
                
                <Button
                  variant="warning"
                  onClick={() => openCorrectionModal(review.id)}
                >
                  ✏️ Correct
                </Button>
                
                <Button
                  variant="destructive"
                  onClick={() => rejectResponse(review.id)}
                >
                  ❌ Reject
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

#### **C. Analytics Charts**
```tsx
// apps/admin/src/components/ai/AccuracyTrendChart.tsx

export function AccuracyTrendChart() {
  const { data } = useQuery({
    queryKey: ['accuracy-trend'],
    queryFn: () => fetch('/api/ai/analytics/accuracy-trend?days=30').then(r => r.json())
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Student Accuracy Trend (30 Days)</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data?.daily_accuracy}>
            <XAxis dataKey="date" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="accuracy"
              stroke="#8884d8"
              name="Accuracy %"
            />
            <Line
              type="monotone"
              dataKey="teacher_fallback"
              stroke="#82ca9d"
              name="Teacher Fallback %"
            />
            <ReferenceLine
              y={95}
              stroke="red"
              strokeDasharray="3 3"
              label="Target: 95%"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

---

## 📊 DATABASE SCHEMA ADDITIONS

```sql
-- Tutor feedback pairs (student vs teacher)
CREATE TABLE ai_tutor_pairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    input_text TEXT NOT NULL,
    student_output TEXT NOT NULL,
    teacher_output TEXT,
    confidence_score FLOAT NOT NULL,
    reward_score FLOAT,
    route_decision VARCHAR(50), -- student, teacher, human
    agent_type VARCHAR(50), -- lead_nurturing, customer_care, operations, knowledge
    corrected_by UUID REFERENCES users(id),
    corrected_output TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_reward (reward_score DESC),
    INDEX idx_confidence (confidence_score),
    INDEX idx_created (created_at DESC)
);

-- Conversation labels (auto-labeled by GPT-4o)
CREATE TABLE conversation_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    intent VARCHAR(50), -- pricing, booking, complaint, info, complex
    sentiment VARCHAR(50), -- positive, neutral, negative, angry
    outcome VARCHAR(50), -- resolved, escalated, booking, no_action
    quality_score FLOAT, -- 0.0 - 1.0
    labeled_by VARCHAR(50) DEFAULT 'gpt-4o',
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_intent (intent),
    INDEX idx_sentiment (sentiment),
    INDEX idx_quality (quality_score DESC)
);

-- RLHF rewards
CREATE TABLE ai_rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    booking_success BOOLEAN DEFAULT FALSE,
    positive_feedback BOOLEAN DEFAULT FALSE,
    high_rating BOOLEAN DEFAULT FALSE,
    fast_resolution BOOLEAN DEFAULT FALSE,
    no_escalation BOOLEAN DEFAULT FALSE,
    negative_feedback BOOLEAN DEFAULT FALSE,
    escalation BOOLEAN DEFAULT FALSE,
    complaint BOOLEAN DEFAULT FALSE,
    reward_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_reward (reward_score DESC)
);

-- Model versions (track student model improvements)
CREATE TABLE ai_model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100), -- llama-3-8b-mhc
    version_tag VARCHAR(50), -- v1.0, v1.1, etc.
    training_date TIMESTAMP,
    training_pairs_count INT,
    avg_reward_score FLOAT,
    accuracy_vs_teacher FLOAT, -- 0.0 - 1.0
    bleu_score FLOAT,
    cosine_similarity FLOAT,
    deployment_status VARCHAR(50), -- shadow, active, retired
    deployed_at TIMESTAMP,
    metrics JSONB, -- {coverage: 0.82, fallback: 0.15, escalation: 0.03}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Cross-channel customer graph (if not using Neo4j)
CREATE TABLE customer_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    interaction_type VARCHAR(50), -- conversation, booking, review, complaint
    channel VARCHAR(50), -- email, sms, instagram, facebook, phone, chat
    related_id UUID, -- conversation_id or booking_id
    sentiment VARCHAR(50),
    outcome VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_customer (customer_id),
    INDEX idx_channel (channel),
    INDEX idx_created (created_at DESC)
);
```

---

## 🔧 IMPLEMENTATION ROADMAP

### **Phase 1A: Foundation (Week 1-2) - 16 hours**

#### **Week 1: Multi-Agent Core**
1. ✅ Create base agent class (1 hour)
2. ✅ Build Lead Nurturing Agent (2 hours)
3. ✅ Build Customer Care Agent (1.5 hours)
4. ✅ Build Operations Agent (1.5 hours)
5. ✅ Build Knowledge Agent (1 hour)
6. ✅ Agent router integration (1 hour)
**Subtotal: 8 hours**

#### **Week 2: Teacher-Student Setup**
7. Setup Llama 3 8B (Ollama) (2 hours)
8. Confidence estimator (2 hours)
9. Confidence router middleware (2 hours)
10. Tutor pair logging (2 hours)
**Subtotal: 8 hours**

---

### **Phase 1B: Intelligence (Week 3-4) - 14 hours**

#### **Week 3: Memory & Emotion**
11. Cross-channel memory service (4 hours)
12. Emotion detection (3 hours)
13. Conversation memory (Redis) (3 hours)
**Subtotal: 10 hours**

#### **Week 4: RLHF-Lite**
14. Reward scorer (2 hours)
15. Auto-labeling pipeline (2 hours)
**Subtotal: 4 hours**

---

### **Phase 1C: Training Loop (Week 5) - 12 hours**

16. Weekly retraining pipeline (6 hours)
17. LoRA fine-tuning setup (3 hours)
18. Shadow deployment system (3 hours)
**Subtotal: 12 hours**

---

### **Phase 1D: Dashboard (Week 6-7) - 20 hours**

19. AI Insights Dashboard (React) (6 hours)
20. Response review interface (6 hours)
21. Analytics charts (4 hours)
22. Correction workflow (4 hours)
**Subtotal: 20 hours**

---

### **Phase 2: Voice Integration (Week 8-9) - 12 hours**

23. RingCentral webhook handlers (4 hours)
24. Speech-to-text (Whisper) (3 hours)
25. Text-to-speech (OpenAI TTS) (2 hours)
26. Voice emotion detection (3 hours)
**Subtotal: 12 hours**

---

### **Phase 3: Business Intelligence (Week 10-11) - 12 hours**

27. CRM sync (HubSpot/Airtable) (4 hours)
28. Predictive lead scoring (4 hours)
29. Demand forecasting (4 hours)
**Subtotal: 12 hours**

---

### **Phase 4: Expansion (Week 12) - 8 hours**

30. Multi-language support (DeepL) (4 hours)
31. AI chef assignment (4 hours)
**Subtotal: 8 hours**

---

## 📈 **TOTAL IMPLEMENTATION:**

| Phase | Duration | Components |
|-------|----------|------------|
| **Phase 1A: Foundation** | 16 hours | Agents + Teacher-Student |
| **Phase 1B: Intelligence** | 14 hours | Memory + Emotion + RLHF |
| **Phase 1C: Training** | 12 hours | Retraining pipeline |
| **Phase 1D: Dashboard** | 20 hours | Admin UI |
| **Phase 2: Voice** | 12 hours | RingCentral |
| **Phase 3: Business** | 12 hours | CRM + Predictive |
| **Phase 4: Expansion** | 8 hours | Multi-language |
| **TOTAL** | **94 hours** | **~12 weeks** |

---

## 💰 COST ANALYSIS

### **Development Costs:**
- **94 hours @ $32/hr** = **$3,008**

### **Operational Costs (Monthly):**

**Current (100% GPT-4o):**
- 1,000 queries/day × $0.015 = $15/day
- Monthly: $450

**After Implementation (80% Local, 20% GPT-4o):**
- Student (800 queries): $0.80/day (compute only)
- Teacher (150 queries): $2.25/day
- Human (50 queries): $0 (handled by team)
- **Total: $3.05/day = $91.50/month**

**Savings: $358.50/month = $4,302/year**

**ROI: $4,302 savings / $3,008 investment = 143% in Year 1**

---

## 🎯 SUCCESS METRICS

| Metric | Baseline | 3-Month Target | 6-Month Target |
|--------|----------|----------------|----------------|
| **Student Coverage** | 0% | 50% | 80% |
| **Teacher Fallback** | 100% | 35% | 15% |
| **Human Escalation** | 20% | 10% | 5% |
| **Accuracy vs Teacher** | N/A | 90% | 95% |
| **Booking Conversion** | 18% | 22% | 25% |
| **Cost per Query** | $0.015 | $0.008 | $0.003 |
| **Response Time** | 2.5s | 2.0s | 1.5s |
| **Customer Satisfaction** | 4.2/5 | 4.4/5 | 4.6/5 |

---

## ✅ ACCEPTANCE CRITERIA

### **Phase 1A (Foundation):**
- [ ] 4 specialized agents operational
- [ ] Llama 3 8B serving responses locally
- [ ] Confidence router directing traffic correctly
- [ ] Tutor pairs logging to database

### **Phase 1B (Intelligence):**
- [ ] Cross-channel memory retrieving unified customer context
- [ ] Emotion detection classifying sentiment accurately
- [ ] Reward scores calculating correctly
- [ ] Auto-labeling pipeline running nightly

### **Phase 1C (Training):**
- [ ] Weekly retraining job running successfully
- [ ] LoRA adapters training on high-reward pairs
- [ ] Shadow deployments A/B testing new models
- [ ] Accuracy ≥ 95% vs teacher validation set

### **Phase 1D (Dashboard):**
- [ ] Real-time metrics displaying correctly
- [ ] Correction interface functional
- [ ] Analytics charts showing trends
- [ ] Manual corrections saving as training data

---

## 🚀 DEPLOYMENT STRATEGY

### **Progressive Rollout:**

**Week 1-2:** Build foundation (agents + teacher-student)  
**Week 3-4:** Add intelligence (memory + emotion)  
**Week 5:** Implement training loop  
**Week 6-7:** Build dashboard  

**Week 8: Shadow Deploy (10% traffic)**
- Student handles 10% of queries
- Compare metrics vs GPT-4o
- Collect tutor pairs

**Week 10: Gradual Rollout (25% → 50% → 80%)**
- Phase 1: 25% student coverage (1 week)
- Phase 2: 50% coverage (1 week)
- Phase 3: 80% coverage (ongoing)

**Week 12: Full Production**
- 80% queries handled by student
- 15% teacher fallback
- 5% human escalation
- Weekly retraining active
- Dashboard monitoring live

---

## 🎉 EXPECTED OUTCOMES

### **Business Impact:**
1. **75% cost reduction** ($358/month savings)
2. **20%+ booking conversion increase** (better sales psychology)
3. **50% faster response times** (local inference)
4. **95% accuracy** (maintains GPT-4o quality)
5. **24/7 learning** (continuous improvement)

### **Technical Excellence:**
1. **Modular architecture** (4 specialized agents)
2. **Cost-efficient** (80% local inference)
3. **Safe deployments** (shadow testing + A/B)
4. **Self-improving** (weekly retraining)
5. **Human-supervised** (dashboard oversight)

### **Customer Experience:**
1. **Personalized responses** (cross-channel memory)
2. **Emotion-aware** (escalates angry customers)
3. **Faster service** (1.5s response time)
4. **Consistent quality** (95% teacher accuracy)
5. **Multi-channel continuity** (unified context)

---

**Status:** ✅ **ARCHITECTURE DESIGN COMPLETE - READY FOR IMPLEMENTATION**

**Next Step:** Begin Phase 1A (Foundation) - Build 4 specialized agents + teacher-student setup

**Estimated Completion:** 12 weeks (March 2026)

---

*Document Version: 1.0*  
*Created: October 31, 2025*  
*Owner: MyHibachi Development Team*
