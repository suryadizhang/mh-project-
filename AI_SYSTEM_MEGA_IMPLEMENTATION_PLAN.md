# 🚀 AI SYSTEM MEGA IMPLEMENTATION PLAN

**Date:** November 16, 2025  
**Scope:** Complete AI-first transformation (v3.0 → v5.0)  
**Timeline:** 24 weeks (6 months)  
**Status:** 🎯 READY FOR EXECUTION

---

## 📋 EXECUTION PRINCIPLES

### ✅ OPERATIONAL LOGIC PRIORITY ORDER:

1. **Foundation First** - Fix critical infrastructure gaps
2. **Safety Layer** - Complete test coverage (prevents production
   incidents)
3. **Core Features** - Deploy revenue-generating features
4. **Intelligence Layer** - Add AI enhancements
5. **Advanced Features** - Implement competitive advantages

### 🎯 DEPENDENCY CHAIN:

```
Critical Tests → v3.0 Production → Data Collection → Self-Healing →
Customer Memory → Analytics → Auto-Tagging → Cost Tracking →
Hybrid Training System → Voice Integration
```

---

## 🧠 COPILOT/CLAUDE MEGA PROMPT

Copy everything below into your AI coding agent:

---

# 🧠 **"MY HIBACHI CHEF – AI SYSTEM ENGINEER MODE"**

## 📌 _Full Implementation Copilot Prompt (v3.0 → v5.0)_

### **Execute EVERYTHING in this roadmap unless told otherwise.**

---

## 🟦 **SYSTEM ROLE – DO NOT BREAK**

You are the **Lead AI Engineer + CTO Assistant** for My Hibachi Chef.
Your job is to implement the entire AI Booking + Analytics + Memory +
Voice + Self-Healing ecosystem according to the provided roadmap.

Follow these rules:

### ✔ ALWAYS:

- Follow my project structure exactly
- Write production-ready code (no placeholders)
- Create missing folders automatically
- Write Alembic migration files
- Write comprehensive tests (pytest)
- Write inline documentation + docstrings
- Validate before generating code
- Ask clarifying questions only when absolutely necessary
- Keep context of business logic from existing codebase
- Follow secure patterns (OWASP, SQL injection safe, JWT validation)
- Follow all safety rules from v3.0 spec (strict tool enforcement,
  price sanity checks)
- Integrate with **FastAPI backend + PostgreSQL DB + Redis +
  TypeScript admin panel**

### ❌ NEVER:

- Invent new pricing logic (use pricing_tool.calculate_party_quote)
- Skip validation layers (AIResponseValidator required)
- Skip logging (all AI interactions logged)
- Skip tests (80%+ coverage required)
- Break existing APIs (backward compatibility)
- Hallucinate database fields (check existing schema first)
- Output partial code without full file paths
- Remove existing features
- Deploy without human approval
- Bypass security checks

---

# 🟥 IMPORTANT CONTEXT (LOAD INTO MEMORY)

## Project Structure:

```
apps/
├── backend/
│   ├── src/
│   │   ├── api/            # FastAPI routes
│   │   ├── config/         # AI configs (ai_booking_config_v2.py)
│   │   ├── services/       # Business logic
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── utils/          # Helpers
│   │   └── ai/             # AI systems (orchestrator, tools, validators)
│   ├── tests/              # Pytest test suites
│   └── alembic/            # Database migrations
├── admin/                  # Next.js TypeScript admin panel
└── customer/               # Next.js TypeScript customer app

docs/                       # Documentation
scripts/                    # Deployment scripts
ai_versions/                # AI version snapshots
```

## Tech Stack:

**Backend**

- FastAPI (async/await)
- PostgreSQL 14+
- SQLAlchemy ORM (async)
- Alembic migrations
- Redis (caching, rate limiting)
- Celery or FastAPI BackgroundTasks
- OpenAI API (gpt-4o, gpt-4o-mini)
- RingCentral (SMS, Voice, WebRTC)
- Stripe (payments)
- Google Maps API (travel fees)

**Frontend**

- Next.js 14+ (App Router)
- TypeScript (strict mode)
- Tailwind CSS
- shadcn/ui components
- Recharts (analytics)
- React Query (data fetching)
- Zustand (state management)

**AI Layer (Existing)**

- `pricing_tool.calculate_party_quote()` - MANDATORY for all pricing
- `AIResponseValidator` - Validates all AI responses
- Conversation storage (conversations table)
- Multi-channel support (SMS, Web, Instagram)
- v3.0 safety architecture (tool enforcement, sanity checks,
  escalation rules)

**Existing Database Tables:**

- customers, bookings, conversations, messages
- leads, reviews, referrals, newsletters
- proteins, addons, pricing_rules
- users, roles, permissions (RBAC)

**CRITICAL: Project Architecture Rules (MUST FOLLOW):**

1. **Service Layer Pattern** - All business logic in `services/`
   - Use existing services when possible (ringcentral_service,
     ai_booking_assistant_service, etc.)
   - New services follow naming: `{domain}_{purpose}_service.py`
   - Services are stateless, dependency-injected

2. **Repository Pattern** - All data access in `repositories/`
   - Use SQLAlchemy async sessions
   - Never write SQL directly in services
   - Repository methods return domain objects

3. **API Layer** - FastAPI routes in `api/v1/`
   - Routes only handle HTTP concerns (validation, serialization)
   - Delegate all logic to services
   - Use Pydantic schemas for validation

4. **Clean Architecture Layers:**

   ```
   api/ → services/ → repositories/ → models/
   (HTTP)  (Business)  (Data Access)  (Entities)
   ```

5. **Existing Services to Leverage:**
   - `ringcentral_service.py` - SMS, call management
   - `ringcentral_voice_service.py` - WebRTC, voice
   - `ai_booking_assistant_service.py` - AI orchestration
   - `conversation_history_service.py` - Conversation storage
   - `booking_service.py` - Booking operations
   - `notification_service.py` - Multi-channel notifications

6. **Testing Structure:**
   - Unit tests: `tests/unit/test_{service_name}.py`
   - Integration tests: `tests/integration/test_{feature}_flow.py`
   - Use pytest fixtures for dependencies
   - Mock external APIs (OpenAI, RingCentral)

7. **Configuration:**
   - All configs in `config/` directory
   - Environment variables for secrets
   - Never hardcode credentials

8. **Modularity:**
   - Each feature is a self-contained module
   - Minimal coupling between modules
   - Use dependency injection
   - Follow SOLID principles

---

# 🟨 **PRIMARY OBJECTIVE (START IMMEDIATELY)**

## 🔥 Implement ALL features listed below in correct operational order:

---

# 🟦 **PHASE 0 — CRITICAL FOUNDATION (Week 1-2)**

**Priority:** 🔴 BLOCKING - Must complete before v3.0 production

## 0.1 Complete Missing Test Suites (22 hours)

**Location:** `apps/backend/tests/services/`

### Implementation Order:

```python
# 1. payment_email_monitor tests (CRITICAL ⭐) - 3 hours
apps/backend/tests/services/test_payment_email_monitor.py
- test_email_parsing
- test_booking_matching
- test_payment_confirmation
- test_error_handling
- test_webhook_processing
(25 tests total)

# 2. booking_service tests - 5 hours
apps/backend/tests/services/test_booking_service.py
- test_create_booking
- test_update_booking
- test_cancel_booking
- test_availability_check
- test_conflict_detection
- test_pricing_calculation
- test_travel_fee_integration
(40 tests total)

# 3. lead_service tests - 4 hours
apps/backend/tests/services/test_lead_service.py
- test_create_lead
- test_failed_booking_capture
- test_lead_followup
- test_lead_conversion
(30 tests total)

# 4. referral_service tests - 3 hours
apps/backend/tests/services/test_referral_service.py
- test_create_referral
- test_track_conversion
- test_payout_calculation
(20 tests total)

# 5. newsletter_service tests - 4 hours
apps/backend/tests/services/test_newsletter_service.py
- test_generate_newsletter
- test_send_newsletter
- test_subscriber_management
- test_analytics_tracking
(30 tests total)

# 6. review_service tests - 3 hours
apps/backend/tests/services/test_review_service.py
- test_create_review
- test_moderation
- test_sentiment_analysis
(20 tests total)
```

**Success Criteria:**

- [ ] All 165 tests passing
- [ ] 80%+ code coverage
- [ ] No production blockers

---

## 0.2 Calendar Backend - Phase 2 Security (4 hours)

**Location:** `apps/backend/src/api/admin/calendar.py`

### Implementation:

```python
# 1. Add admin role check
from src.middleware.auth import require_roles

@router.get("/admin/weekly")
@require_roles(["admin", "manager"])
async def get_weekly_calendar(...):
    """Admin-only endpoint"""
    pass

# 2. Add request logging
from src.utils.audit_logger import log_admin_action

@router.patch("/admin/{booking_id}")
async def update_booking(booking_id: UUID, ...):
    log_admin_action(
        user_id=current_user.id,
        action="booking_update",
        resource_id=booking_id,
        changes={"field": "old_value → new_value"}
    )

# 3. Add unit tests (50+ tests)
apps/backend/tests/api/admin/test_calendar.py

# 4. Fix timezone handling (PST/PDT)
from datetime import timezone
import pytz

PST = pytz.timezone('America/Los_Angeles')
```

---

## 0.3 AI SMS System - Testing & Integration (10 hours)

**Location:** `apps/backend/src/services/` (use existing RingCentral
services)

### Implementation:

```python
# 1. End-to-end SMS testing (3 hours)
apps/backend/tests/integration/test_ai_sms_booking_flow.py
- test_full_booking_via_sms_ringcentral
- test_error_handling_sms
- test_ringcentral_webhook_verification

# LEVERAGE EXISTING SERVICES:
# - services/ringcentral_service.py (already has send_sms)
# - services/ringcentral_sms.py (existing SMS functionality)
# - api/v1/webhooks/ringcentral.py (webhook handler)

# 2. AI SMS Orchestrator Integration (2 hours)
class AISMSOrchestrator:
    """Integrate AI with existing RingCentral SMS service"""

    def __init__(self):
        self.ringcentral = RingCentralService()  # Use existing service
        self.ai_orchestrator = AIBookingOrchestrator()
        self.conversation_service = ConversationHistoryService()

    async def handle_incoming_sms(self, from_phone: str, message: str, metadata: dict):
        """Process incoming SMS through AI system"""

        # Load conversation history
        context = await self.conversation_service.get_context(phone=from_phone)

        # Generate AI response
        ai_response = await self.ai_orchestrator.generate_response(
            user_message=message,
            context=context,
            channel='sms'
        )

        # Send via RingCentral (existing service)
        await self.ringcentral.send_sms(
            to_phone=from_phone,
            message=ai_response['content'],
            metadata={'conversation_id': context['id']}
        )

# 3. RingCentral webhook integration testing (2 hours)
- Real RingCentral number testing
- Webhook signature verification (already in ringcentral_service.py)
- Rate limiting integration

# 4. SMS Analytics & Monitoring (2 hours)
class SMSConversationAnalytics:
    async def track_sms_metrics(self):
        """Track SMS delivery, response time, conversion"""
        # Integrate with existing conversation_history_service

# 5. Staff training materials (1 hour)
docs/AI_SMS_BOOKING_GUIDE.md
```

**IMPORTANT: Follow existing architecture patterns:**

- Use `services/` for business logic (already have
  ringcentral_service.py)
- Use `api/v1/webhooks/` for webhook endpoints
- Use `repositories/` for data access
- Use `schemas/` for Pydantic validation
- Use `core/` for shared utilities
- Tests in `tests/integration/` and `tests/unit/`

---

## 0.4 Admin UI Components - Tests (8 hours)

**Location:** `apps/admin/src/`

### Implementation:

```typescript
// 1. Admin UI Sync Dashboard Tests (4 hours)
__tests__ / components / AdminSyncDashboard.test.tsx -
  test_sync_status_display -
  test_force_sync_button -
  test_rollback_feature -
  test_config_comparison;

// 2. Integration tests (4 hours)
__tests__ / integration / admin -
  ui -
  sync.test.tsx -
  test_full_sync_workflow -
  test_error_handling -
  test_rollback_workflow;
```

---

# 🟩 **PHASE 1 — v3.0 PRODUCTION DEPLOYMENT (Week 2-3)**

## 1.1 Integration Testing Suite

**Location:** `apps/backend/tests/integration/`

```python
# test_ai_booking_flow.py
import pytest
from src.ai.orchestrator import AIBookingOrchestrator

class TestAIBookingFlow:
    """Full end-to-end AI booking scenarios"""

    async def test_standard_pricing_flow(self):
        """Customer asks price → AI calls pricing_tool → validator approves"""

    async def test_dietary_restriction_flow(self):
        """Customer has allergies → AI handles → books successfully"""

    async def test_objection_handling_flow(self):
        """Customer objects to minimum → AI uses OBJECTION_HANDLING → converts"""

    async def test_upsell_flow(self):
        """AI suggests lobster → customer accepts → revenue increases"""

    async def test_human_escalation_flow(self):
        """Custom menu request → AI escalates → human takes over"""

    async def test_validation_failure_flow(self):
        """AI generates bad response → validator blocks → AI retries"""

    async def test_multi_turn_conversation(self):
        """10-turn conversation → maintains context → books successfully"""

    async def test_sms_channel_booking(self):
        """Booking via SMS → same logic → successful"""

    async def test_instagram_channel_booking(self):
        """Booking via Instagram DM → successful"""

    async def test_web_chat_booking(self):
        """Booking via web chat widget → successful"""

# Run: pytest tests/integration/test_ai_booking_flow.py -v
```

---

## 1.2 Backup + Versioning System

**Location:** `ai_versions/`, `scripts/`

```bash
# scripts/create_version_snapshot.sh
#!/bin/bash
VERSION=$1
DATE=$(date +%Y-%m-%d)

echo "📸 Creating AI version snapshot for v${VERSION}..."

# 1. Create version folder
mkdir -p ai_versions/v${VERSION}

# 2. Copy current config
cp apps/backend/src/config/ai_booking_config_v2.py \
   ai_versions/v${VERSION}/ai_booking_config_v${VERSION}.py

# 3. Copy validator
cp apps/backend/src/config/ai_response_validator.py \
   ai_versions/v${VERSION}/ai_response_validator_v${VERSION}.py

# 4. Run tests and save results
python -m pytest apps/backend/tests/ -v > \
   ai_versions/v${VERSION}/test_results.txt

# 5. Generate release notes
cat > ai_versions/v${VERSION}/RELEASE_NOTES.md <<EOF
# AI Booking System v${VERSION}

**Released:** ${DATE}
**Status:** Production

## Features
- [ ] List features

## Performance
- Conversion rate: [X]%
- Avg response time: [X]s
- Customer satisfaction: [X]/10

## Breaking Changes
- [ ] None

## Migration Steps
1. Backup current config
2. Deploy new version
3. Monitor for 24 hours
EOF

echo "✅ Version v${VERSION} snapshot created!"
```

```bash
# scripts/rollback_ai_version.sh
#!/bin/bash
VERSION=$1

echo "⏪ Rolling back to AI v${VERSION}..."

# 1. Backup current version
cp apps/backend/src/config/ai_booking_config_v2.py \
   ai_versions/backup_before_rollback_$(date +%Y%m%d).py

# 2. Restore old version
cp ai_versions/v${VERSION}/ai_booking_config_v${VERSION}.py \
   apps/backend/src/config/ai_booking_config_v2.py

# 3. Restart backend
echo "🔄 Restarting backend..."
systemctl restart mh-backend

# 4. Verify
echo "✅ Rollback complete. Verify AI responses."
```

---

## 1.3 Production Validator Integration

**Location:** `apps/backend/src/ai/orchestrator/`

```python
# orchestrator.py - Ensure validator is always called

class AIBookingOrchestrator:
    def __init__(self):
        self.validator = AIResponseValidator()
        self.strict_mode = os.getenv("AI_STRICT_MODE", "true") == "true"

    async def generate_response(self, user_message: str, context: dict) -> dict:
        """Generate AI response with mandatory validation"""

        # Generate response
        response = await self._call_openai(user_message, context)

        # MANDATORY VALIDATION - CANNOT SKIP
        validation_result = self.validator.validate_response(
            response=response,
            tools_used=context.get("tools_used", []),
            conversation_history=context.get("history", [])
        )

        if not validation_result["is_valid"]:
            # Log validation failure
            logger.error(f"AI response blocked: {validation_result['errors']}")

            if self.strict_mode:
                # Retry with error feedback
                return await self._regenerate_with_feedback(
                    user_message,
                    context,
                    validation_errors=validation_result["errors"]
                )
            else:
                # Escalate to human
                await self.escalate_to_human(
                    reason="validation_failure",
                    details=validation_result["errors"]
                )

        return response
```

---

## 1.4 Staging Deployment

**Location:** `scripts/deploy_staging.sh`

```bash
#!/bin/bash

echo "🚀 Deploying to STAGING..."

# 1. Run tests (follow existing test structure)
echo "1/7 Running tests..."
cd apps/backend
python -m pytest tests/unit/ tests/integration/ -v --cov=src --cov-report=term
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi

# 2. Validate architecture (use existing validator)
echo "2/7 Validating architecture..."
python src/test_enterprise_architecture.py
if [ $? -ne 0 ]; then
    echo "⚠️ Architecture validation failed. Review warnings."
fi

# 3. Backup production config
echo "3/7 Backing up production..."
./scripts/create_version_snapshot.sh 3.0

# 4. Deploy to staging
echo "4/7 Deploying to staging..."
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' \
    apps/backend/src/ staging:/var/www/mh-backend/src/

# 5. Run migrations (Alembic)
echo "5/7 Running migrations..."
ssh staging "cd /var/www/mh-backend && source venv/bin/activate && alembic upgrade head"

# 6. Restart services (FastAPI + Celery workers)
echo "6/7 Restarting services..."
ssh staging "systemctl restart mh-backend mh-celery-worker"

# 7. Health checks
echo "7/7 Running health checks..."
sleep 10
curl -f https://staging.myhibachichef.com/api/health || exit 1
curl -f https://staging.myhibachichef.com/api/v1/health/ai || exit 1

echo "✅ Staging deployment complete!"
echo "🔗 API: https://staging.myhibachichef.com/api/v1/"
echo "🔗 Docs: https://staging.myhibachichef.com/docs"
```

---

# 🟦 **PHASE 2 — v4.0 CORE (Week 4-14)**

## 2.1 Self-Healing Mode (Week 4-6)

**Location:** `apps/backend/src/ai/self_healing/`

### File Structure:

```
apps/backend/src/ai/self_healing/
├── __init__.py
├── feedback_collector.py      # Collect failure patterns
├── pattern_detector.py         # Detect repeated issues
├── prompt_optimizer.py         # Auto-adjust prompts
├── healing_engine.py           # Orchestrate healing cycle
└── models.py                   # SQLAlchemy models
```

### Implementation:

```python
# feedback_collector.py
from typing import List, Dict
from datetime import datetime, timedelta

class FeedbackCollector:
    """Collect AI failures and patterns"""

    async def collect_validation_failures(self, hours: int = 24) -> List[Dict]:
        """Get all validation failures from last N hours"""

        failures = await db.query("""
            SELECT
                conversation_id,
                error_type,
                error_message,
                ai_response,
                user_query,
                COUNT(*) OVER (PARTITION BY error_type) as frequency
            FROM ai_validation_failures
            WHERE created_at > NOW() - INTERVAL :hours HOUR
            ORDER BY frequency DESC
        """, {"hours": hours})

        return failures

    async def collect_repeated_escalations(self) -> List[Dict]:
        """Find escalation patterns"""

        return await db.query("""
            SELECT
                escalation_reason,
                COUNT(*) as frequency,
                ARRAY_AGG(conversation_id) as examples
            FROM conversations
            WHERE escalated_to_human = TRUE
              AND created_at > NOW() - INTERVAL '7 days'
            GROUP BY escalation_reason
            HAVING COUNT(*) >= 5
            ORDER BY frequency DESC
        """)

    async def collect_repeated_confusion(self) -> List[Dict]:
        """Track when AI asks for clarification 3+ times"""

        return await db.query("""
            SELECT
                c.id as conversation_id,
                COUNT(m.id) as clarification_count,
                ARRAY_AGG(m.content) as messages
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE m.role = 'assistant'
              AND (
                  m.content ILIKE '%could you clarify%'
                  OR m.content ILIKE '%I need more information%'
                  OR m.content ILIKE '%can you tell me more%'
              )
              AND c.created_at > NOW() - INTERVAL '7 days'
            GROUP BY c.id
            HAVING COUNT(m.id) >= 3
        """)
```

```python
# pattern_detector.py
import openai
from typing import List, Dict

class PatternDetector:
    """Detect patterns in failures using GPT-4o"""

    async def analyze_failure_patterns(
        self,
        failures: List[Dict]
    ) -> Dict:
        """Use GPT-4o to find root causes"""

        prompt = f"""
Analyze these AI validation failures and identify root causes:

{failures}

For each pattern, provide:
1. Root cause (what's causing the failure)
2. Affected scenarios (when does it happen)
3. Suggested fix (how to prevent it)
4. Priority (critical/high/medium/low)

Return JSON:
{{
    "patterns": [
        {{
            "root_cause": "...",
            "frequency": 15,
            "scenarios": ["..."],
            "suggested_fix": "...",
            "priority": "critical"
        }}
    ]
}}
"""

        response = await openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return json.loads(response.choices[0].message.content)
```

```python
# prompt_optimizer.py
class PromptOptimizer:
    """Auto-adjust prompts to fix patterns"""

    async def apply_fix(
        self,
        pattern: Dict,
        current_config: str
    ) -> str:
        """Generate improved prompt"""

        fix_prompt = f"""
Current AI config section:
{current_config}

Problem detected:
{pattern['root_cause']}

Suggested fix:
{pattern['suggested_fix']}

Rewrite this config section to fix the problem.
Maintain all existing safety rules.
Return ONLY the improved config section.
"""

        response = await openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": fix_prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content
```

```python
# healing_engine.py
class HealingEngine:
    """Orchestrate daily healing cycle"""

    async def run_nightly_healing(self):
        """Runs at 2:00 AM daily"""

        logger.info("🔧 Starting self-healing cycle...")

        # 1. Collect feedback (2:00 - 2:15 AM)
        collector = FeedbackCollector()
        validation_failures = await collector.collect_validation_failures()
        escalations = await collector.collect_repeated_escalations()
        confusion = await collector.collect_repeated_confusion()

        # 2. Detect patterns (2:15 - 2:30 AM)
        detector = PatternDetector()
        patterns = await detector.analyze_failure_patterns({
            "validation_failures": validation_failures,
            "escalations": escalations,
            "confusion": confusion
        })

        # 3. Generate fixes (2:30 - 3:00 AM)
        optimizer = PromptOptimizer()
        fixes = []

        for pattern in patterns["patterns"]:
            if pattern["priority"] in ["critical", "high"]:
                fix = await optimizer.apply_fix(
                    pattern,
                    current_config=self.get_current_config()
                )
                fixes.append({
                    "pattern": pattern,
                    "fix": fix
                })

        # 4. Test fixes (3:00 - 4:00 AM)
        test_results = await self.test_fixes(fixes)

        # 5. Queue for human approval (4:00 AM)
        for fix, result in zip(fixes, test_results):
            if result["pass_rate"] >= 0.90:
                await self.queue_for_approval(fix, result)
            else:
                logger.warning(f"Fix failed tests: {fix['pattern']['root_cause']}")

        logger.info("✅ Self-healing cycle complete")
```

### Database Schema:

```sql
-- Migration: create_self_healing_tables.sql

CREATE TABLE ai_feedback_corpus (
    id SERIAL PRIMARY KEY,
    feedback_type VARCHAR(50),  -- 'validation_failure', 'escalation', 'confusion'
    pattern_description TEXT,
    occurrence_count INT DEFAULT 1,
    example_conversations JSONB,
    root_cause TEXT,
    suggested_fix TEXT,
    fix_applied BOOLEAN DEFAULT FALSE,
    fix_effectiveness FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ai_prompt_versions (
    id SERIAL PRIMARY KEY,
    component VARCHAR(100),  -- 'OBJECTION_HANDLING', 'SALES_OPTIMIZATION', etc.
    version INT,
    prompt_text TEXT,
    performance_score FLOAT,
    deployed_at TIMESTAMP,
    deprecated_at TIMESTAMP
);

CREATE TABLE self_healing_approvals (
    id SERIAL PRIMARY KEY,
    pattern_id INT REFERENCES ai_feedback_corpus(id),
    proposed_fix TEXT,
    test_results JSONB,
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    reviewed_by UUID REFERENCES users(id),
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);
```

---

## 2.2 Conversation Analytics Engine (Week 7-9)

**Location:** `apps/backend/src/analytics/`

### File Structure:

```
apps/backend/src/analytics/
├── __init__.py
├── collectors/
│   ├── __init__.py
│   ├── conversation_collector.py
│   ├── booking_collector.py
│   └── objection_collector.py
├── processors/
│   ├── __init__.py
│   ├── lost_booking_analyzer.py
│   ├── conversion_analyzer.py
│   └── location_analyzer.py
├── queries/
│   ├── __init__.py
│   └── analytics_queries.py
└── models.py
```

### Implementation:

```python
# models.py
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, UUID, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB

class BookingLossReason(Base):
    __tablename__ = "booking_loss_reasons"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(UUID, ForeignKey("conversations.id"))
    loss_category = Column(String(50))  # 'price_objection', 'availability', etc.
    loss_reason = Column(Text)
    customer_sentiment = Column(Float)  # -1.0 to 1.0
    recovery_attempted = Column(Boolean, default=False)
    recovery_successful = Column(Boolean, default=False)
    occurred_at = Column(TIMESTAMP)

class ConversationObjection(Base):
    __tablename__ = "conversation_objections"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(UUID, ForeignKey("conversations.id"))
    objection_type = Column(String(50))
    objection_text = Column(Text)
    ai_response = Column(Text)
    resolution_successful = Column(Boolean)
    time_to_resolution = Column(Integer)  # seconds
    occurred_at = Column(TIMESTAMP)
```

```python
# collectors/conversation_collector.py
class ConversationCollector:
    """Collect conversation data for analytics"""

    async def analyze_lost_booking(self, conversation_id: UUID):
        """Analyze why a booking was lost"""

        conversation = await self.get_conversation(conversation_id)
        messages = await self.get_messages(conversation_id)

        # Use GPT-4o to analyze
        analysis_prompt = f"""
Analyze why this customer didn't book:

Conversation:
{messages}

Provide:
1. Primary loss reason (price_objection, availability, requirements, competition)
2. Customer sentiment (-1.0 to 1.0)
3. Could it have been saved? (yes/no)

Return JSON:
{{
    "loss_category": "...",
    "loss_reason": "...",
    "customer_sentiment": 0.5,
    "recoverable": true
}}
"""

        response = await openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3
        )

        analysis = json.loads(response.choices[0].message.content)

        # Store in DB
        await db.execute("""
            INSERT INTO booking_loss_reasons (
                conversation_id, loss_category, loss_reason,
                customer_sentiment, recovery_attempted, occurred_at
            ) VALUES (
                :conv_id, :category, :reason, :sentiment, :attempted, NOW()
            )
        """, {
            "conv_id": conversation_id,
            "category": analysis["loss_category"],
            "reason": analysis["loss_reason"],
            "sentiment": analysis["customer_sentiment"],
            "attempted": analysis["recoverable"]
        })
```

```python
# queries/analytics_queries.py
class AnalyticsQueries:
    """Pre-built analytics queries"""

    async def get_top_loss_reasons(self, days: int = 30) -> List[Dict]:
        """Top 10 reasons bookings are lost"""

        return await db.query("""
            SELECT
                loss_category,
                COUNT(*) as frequency,
                AVG(customer_sentiment) as avg_sentiment,
                COUNT(CASE WHEN recovery_attempted THEN 1 END) as recovery_attempts,
                COUNT(CASE WHEN recovery_successful THEN 1 END) as recoveries,
                ROUND(100.0 * COUNT(CASE WHEN recovery_successful THEN 1 END) /
                      NULLIF(COUNT(CASE WHEN recovery_attempted THEN 1 END), 0), 2) as recovery_rate
            FROM booking_loss_reasons
            WHERE occurred_at > NOW() - INTERVAL :days DAY
            GROUP BY loss_category
            ORDER BY frequency DESC
            LIMIT 10
        """, {"days": days})

    async def get_objection_performance(self) -> List[Dict]:
        """Objection handling effectiveness"""

        return await db.query("""
            SELECT
                objection_type,
                COUNT(*) as total_objections,
                COUNT(CASE WHEN resolution_successful THEN 1 END) as resolved,
                ROUND(100.0 * COUNT(CASE WHEN resolution_successful THEN 1 END) / COUNT(*), 2) as resolution_rate,
                AVG(time_to_resolution) as avg_resolution_time
            FROM conversation_objections
            WHERE occurred_at > NOW() - INTERVAL '30 days'
            GROUP BY objection_type
            ORDER BY total_objections DESC
        """)

    async def get_conversion_by_event_type(self) -> List[Dict]:
        """Which event types convert best?"""

        return await db.query("""
            SELECT
                event_type,
                COUNT(DISTINCT conversation_id) as total_inquiries,
                COUNT(DISTINCT CASE WHEN booking_created THEN conversation_id END) as bookings,
                ROUND(100.0 * COUNT(DISTINCT CASE WHEN booking_created THEN conversation_id END) /
                      COUNT(DISTINCT conversation_id), 2) as conversion_rate,
                AVG(total_revenue) as avg_revenue,
                SUM(total_revenue) as total_revenue
            FROM conversations
            WHERE created_at > NOW() - INTERVAL '90 days'
            GROUP BY event_type
            ORDER BY total_revenue DESC
        """)
```

---

## 2.3 Customer Memory System (Week 10-11)

**Location:** `apps/backend/src/ai/customer_memory/`

### File Structure:

```
apps/backend/src/ai/customer_memory/
├── __init__.py
├── memory_retriever.py
├── memory_writer.py
├── reminder_service.py
└── models.py
```

### Implementation:

```python
# models.py
class CustomerMemory(Base):
    __tablename__ = "customer_memory"

    id = Column(Integer, primary_key=True)
    customer_id = Column(UUID, ForeignKey("customers.id"), unique=True)

    # Basic Info
    preferred_name = Column(String(100))

    # Party Preferences
    typical_party_size = Column(Integer)
    typical_adults = Column(Integer)
    typical_children = Column(Integer)
    typical_event_type = Column(String(50))

    # Booking History
    total_bookings = Column(Integer, default=0)
    last_booking_date = Column(Date)
    favorite_day_of_week = Column(String(20))
    favorite_time_of_day = Column(String(20))

    # Menu Preferences
    favorite_proteins = Column(JSONB)  # ["lobster_tail", "filet_mignon"]
    dietary_restrictions = Column(JSONB)  # ["peanut_allergy"]
    favorite_addons = Column(JSONB)

    # Location
    usual_location = Column(String(255))
    usual_zip = Column(String(10))
    typical_travel_fee = Column(Numeric(10, 2))

    # Special Notes
    special_requests = Column(Text)
    important_dates = Column(JSONB)  # [{"type": "birthday", "date": "2025-07-15"}]

    # Engagement
    preferred_contact_method = Column(String(20))
    response_speed = Column(String(20))

    updated_at = Column(TIMESTAMP, default=func.now())
```

```python
# memory_retriever.py
class CustomerMemoryRetriever:
    """Retrieve customer memory for personalization"""

    async def get_memory(self, customer_id: UUID) -> Optional[Dict]:
        """Get customer memory"""

        memory = await db.query(CustomerMemory).filter_by(
            customer_id=customer_id
        ).first()

        if not memory:
            return None

        return {
            "name": memory.preferred_name,
            "history": {
                "total_bookings": memory.total_bookings,
                "last_booking": memory.last_booking_date.isoformat() if memory.last_booking_date else None,
                "typical_party_size": memory.typical_party_size,
            },
            "preferences": {
                "proteins": memory.favorite_proteins or [],
                "dietary": memory.dietary_restrictions or [],
                "addons": memory.favorite_addons or [],
            },
            "location": {
                "usual": memory.usual_location,
                "zip": memory.usual_zip,
            },
            "important_dates": memory.important_dates or [],
        }

    def enhance_prompt_with_memory(self, base_prompt: str, memory: Dict) -> str:
        """Add customer context to AI prompt"""

        if not memory:
            return base_prompt

        memory_context = f"""

**RETURNING CUSTOMER DETECTED:**
- Name: {memory['name'] or 'Customer'}
- Previous bookings: {memory['history']['total_bookings']} times
- Last booking: {memory['history']['last_booking'] or 'Never'}
- Typical party: {memory['history']['typical_party_size'] or 'Unknown'} people
- Favorites: {', '.join(memory['preferences']['proteins']) or 'None'}

**PERSONALIZATION INSTRUCTIONS:**
1. Greet warmly by name
2. Reference their last booking naturally
3. Suggest their favorite proteins
4. Pre-fill their typical party size
5. Mention any upcoming important dates within 30 days
"""

        return base_prompt + memory_context
```

```python
# memory_writer.py
class CustomerMemoryWriter:
    """Update customer memory after bookings"""

    async def update_from_booking(self, booking: Booking):
        """Auto-update memory from completed booking"""

        memory = await db.query(CustomerMemory).filter_by(
            customer_id=booking.customer_id
        ).first()

        if not memory:
            memory = CustomerMemory(customer_id=booking.customer_id)
            db.add(memory)

        # Update booking history
        memory.total_bookings += 1
        memory.last_booking_date = booking.event_date

        # Update party preferences (moving average)
        if memory.typical_party_size:
            memory.typical_party_size = (memory.typical_party_size + booking.adults + booking.children) // 2
        else:
            memory.typical_party_size = booking.adults + booking.children

        # Update favorite proteins
        if booking.proteins:
            current_favorites = memory.favorite_proteins or []
            for protein in booking.proteins:
                if protein not in current_favorites:
                    current_favorites.append(protein)
            memory.favorite_proteins = current_favorites[:5]  # Keep top 5

        # Update location
        memory.usual_location = booking.location
        memory.usual_zip = booking.zip_code

        await db.commit()
```

```python
# reminder_service.py
class ReminderService:
    """Send birthday/anniversary reminders"""

    async def send_upcoming_date_reminders(self):
        """Check for important dates in next 14 days"""

        today = datetime.now().date()
        two_weeks = today + timedelta(days=14)

        memories = await db.query(CustomerMemory).filter(
            CustomerMemory.important_dates != None
        ).all()

        for memory in memories:
            for date_entry in memory.important_dates:
                event_date = datetime.strptime(date_entry['date'], '%Y-%m-%d').date()

                # Check if event is in next 14 days
                if today < event_date <= two_weeks:
                    await self.send_reminder_email(memory, date_entry)

    async def send_reminder_email(self, memory: CustomerMemory, event: Dict):
        """Send personalized reminder"""

        customer = await db.query(Customer).filter_by(id=memory.customer_id).first()

        await email_service.send(
            to=customer.email,
            subject=f"🎉 {event['name']}'s {event['type'].title()} is Coming Up!",
            body=f"""
Hi {memory.preferred_name or customer.first_name}!

{event['name']}'s {event['type']} is on {event['date']} - just 2 weeks away! 🎂

Last year you booked our hibachi chef and it was amazing.
Want to do it again?

[Book Now for {event['date']}]

P.S. Your guests loved the {', '.join(memory.favorite_proteins or [])}.
Want to add them again?
            """
        )
```

### Database Migration:

```sql
-- Migration: create_customer_memory_tables.sql

CREATE TABLE customer_memory (
    id SERIAL PRIMARY KEY,
    customer_id UUID UNIQUE REFERENCES customers(id),

    preferred_name VARCHAR(100),

    typical_party_size INT,
    typical_adults INT,
    typical_children INT,
    typical_event_type VARCHAR(50),

    total_bookings INT DEFAULT 0,
    last_booking_date DATE,
    favorite_day_of_week VARCHAR(20),
    favorite_time_of_day VARCHAR(20),

    favorite_proteins JSONB,
    dietary_restrictions JSONB,
    favorite_addons JSONB,

    usual_location VARCHAR(255),
    usual_zip VARCHAR(10),
    typical_travel_fee DECIMAL(10,2),

    special_requests TEXT,
    important_dates JSONB,

    preferred_contact_method VARCHAR(20),
    response_speed VARCHAR(20),

    updated_at TIMESTAMP DEFAULT NOW()
);

-- Auto-update trigger
CREATE OR REPLACE FUNCTION update_customer_memory() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO customer_memory (customer_id, typical_party_size, last_booking_date, total_bookings)
    VALUES (NEW.customer_id, NEW.adults + NEW.children, NEW.event_date, 1)
    ON CONFLICT (customer_id) DO UPDATE SET
        total_bookings = customer_memory.total_bookings + 1,
        last_booking_date = NEW.event_date,
        typical_party_size = (customer_memory.typical_party_size + NEW.adults + NEW.children) / 2,
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER booking_memory_update
AFTER INSERT ON bookings
FOR EACH ROW EXECUTE FUNCTION update_customer_memory();
```

---

## 2.4 AI Coach Prompts System (Week 12-13)

**Location:** `apps/backend/src/ai/coach/`

### File Structure:

```
apps/backend/src/ai/coach/
├── __init__.py
├── daily_optimizer.py
├── test_scenarios.py
├── tone_tuner.py
└── models.py
```

### Implementation:

```python
# daily_optimizer.py
class AICoachSystem:
    """Daily AI optimization cycle"""

    STANDARD_TEST_SCENARIOS = [
        {
            "name": "Standard pricing",
            "input": "How much for 20 people?",
            "expected": {
                "price_mentioned": True,
                "price_correct": 1100.00,
                "follow_up_asked": True,
            }
        },
        {
            "name": "Minimum objection",
            "input": "I only have 5 people",
            "expected": {
                "minimum_explained": True,
                "alternatives_offered": True,
                "tone": "empathetic",
            }
        },
        # ... 8 more scenarios
    ]

    async def run_daily_optimization(self):
        """Runs every 24 hours at 2:00 AM"""

        logger.info("🎓 Starting AI Coach daily optimization...")

        # 1. Collect metrics (2:00 - 2:30 AM)
        metrics = await self.collect_metrics()

        # 2. Tune tone if needed (2:30 - 3:00 AM)
        if metrics['customer_satisfaction'] < 8.5:
            await self.tune_tone(target_satisfaction=9.0)

        # 3. Run test scenarios (3:00 - 4:00 AM)
        test_results = await self.run_test_scenarios()

        # 4. Auto-adjust if failures (4:00 - 4:30 AM)
        if test_results['pass_rate'] < 0.90:
            await self.adjust_scripts(test_results)

        # 5. Generate report (4:30 - 5:00 AM)
        await self.send_report(metrics, test_results)

        logger.info("✅ AI Coach optimization complete")

    async def collect_metrics(self) -> Dict:
        """Collect last 24h performance"""

        return await db.query("""
            SELECT
                COUNT(*) as total_conversations,
                COUNT(CASE WHEN booking_created THEN 1 END) as bookings,
                ROUND(100.0 * COUNT(CASE WHEN booking_created THEN 1 END) / COUNT(*), 2) as conversion_rate,
                AVG(customer_satisfaction) as avg_satisfaction,
                COUNT(CASE WHEN escalated_to_human THEN 1 END) as escalations
            FROM conversations
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)

    async def run_test_scenarios(self) -> Dict:
        """Run 10 standard tests"""

        results = []

        for scenario in self.STANDARD_TEST_SCENARIOS:
            result = await self.test_scenario(scenario)
            results.append(result)

        pass_rate = sum(1 for r in results if r['passed']) / len(results)

        return {
            "pass_rate": pass_rate,
            "results": results
        }

    async def send_report(self, metrics: Dict, test_results: Dict):
        """Generate daily report"""

        report = f"""
AI Coach Daily Report - {datetime.now().date()}
==========================================

PERFORMANCE METRICS (Last 24 Hours):
- Conversations: {metrics['total_conversations']}
- Bookings: {metrics['bookings']} ({metrics['conversion_rate']}%)
- Avg Satisfaction: {metrics['avg_satisfaction']}/10
- Escalations: {metrics['escalations']}

TEST SCENARIOS ({len(test_results['results'])}/10 PASSED):
{"".join(['✅ ' + r['name'] if r['passed'] else '❌ ' + r['name'] for r in test_results['results']])}

RECOMMENDATIONS:
{self.generate_recommendations(metrics, test_results)}
"""

        await slack_service.send_message(
            channel="#ai-performance",
            text=report
        )
```

---

## 2.5 Voice Integration (Week 14)

**Location:** `apps/backend/src/services/realtime_voice/` (EXTEND
EXISTING)

### File Structure (Leverage Existing):

```
apps/backend/src/services/
├── ringcentral_voice_service.py       # EXISTING - WebRTC, call management
├── ringcentral_voice_ai.py           # EXISTING - AI voice integration
├── realtime_voice/                   # EXISTING directory
│   ├── __init__.py
│   ├── gpt4o_audio_handler.py       # NEW - GPT-4o native audio
│   ├── booking_voice_agent.py       # NEW - Voice booking orchestrator
│   └── call_transcription_service.py # NEW - Post-call transcription
└── speech_service.py                 # EXISTING
```

### Implementation:

```python
# realtime_voice/booking_voice_agent.py
from services.ringcentral_voice_service import RingCentralVoiceService
from services.ai_booking_assistant_service import AIBookingAssistantService

class VoiceBookingAgent:
    """GPT-4o audio for phone bookings - Integrates with existing services"""

    def __init__(self):
        self.ringcentral = RingCentralVoiceService()  # Use existing
        self.ai_booking = AIBookingAssistantService()  # Use existing

    async def handle_phone_call(self, call_session_id: str, call_metadata: dict):
        """Handle incoming phone call via RingCentral WebRTC"""

        # 1. Initialize GPT-4o audio session
        session = await openai.AudioSession.create(
            model="gpt-4o-audio",
            voice="shimmer",
            system_prompt=self.build_voice_prompt()
        )

        # 2. Stream bidirectional audio via RingCentral WebRTC
        async with session:
            async for audio_chunk in self.ringcentral.stream_audio_from_call(call_session_id):
                # Send customer audio to GPT-4o
                await session.send_audio(audio_chunk)

                # Get AI response audio
                ai_response_audio = await session.receive_audio()

                # Send AI audio back through RingCentral
                await self.ringcentral.stream_audio_to_call(
                    call_session_id,
                    ai_response_audio
                )

        # 3. Save conversation using existing conversation_history_service
        await self.save_voice_conversation(
            call_session_id=call_session_id,
            transcript=session.transcript,
            metadata=call_metadata
        )

    def build_voice_prompt(self) -> str:
        """Voice-optimized AI prompt"""

        return """
You are a friendly hibachi chef booking agent on the phone.

VOICE GUIDELINES:
- Speak naturally and warmly
- Keep responses under 30 seconds
- Use verbal affirmations ("uh-huh", "I see", "great!")
- Repeat key details back for confirmation
- Use pauses naturally

For pricing, say:
"Let me calculate that for you... [pause] ... For 20 people, that comes to $1,100 total, which is $55 per person."

All pricing logic same as text chat.
"""
```

---

# 🟩 **PHASE 3 — v4.5 ADVANCED (Week 15-18)**

## 3.1 Auto-Tagging System (Week 15-16)

**Location:** `apps/backend/src/ai/auto_tagging/`

```python
# conversation_tagger.py
class ConversationAutoTagger:
    """Auto-tag conversations with GPT-4o"""

    TAGGING_PROMPT = """
Analyze this conversation and apply ALL relevant tags:

**CUSTOMER INTENT:**
- high_intent, low_intent, price_shopping, upgrade_likely

**BUDGET:**
- price_sensitive, budget_constrained, budget_flexible, luxury_seeker

**OBJECTIONS:**
- objection_minimum, objection_travel, objection_price, etc.

**PARTY TYPE:**
- party_birthday, party_corporate, party_anniversary, etc.

**BEHAVIOR:**
- first_time_customer, returning_customer, urgency_high, etc.

**OUTCOME:**
- outcome_booked, outcome_lost, outcome_pending, outcome_escalated

Return JSON array: ["tag1", "tag2", "tag3"]
"""

    async def tag_conversation(self, conversation_id: UUID) -> List[str]:
        """Auto-tag with GPT-4o"""

        messages = await self.get_conversation_messages(conversation_id)

        response = await openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.TAGGING_PROMPT},
                {"role": "user", "content": json.dumps(messages)}
            ],
            temperature=0.3
        )

        tags = json.loads(response.choices[0].message.content)

        # Store tags
        for tag in tags:
            await db.execute("""
                INSERT INTO conversation_tags (conversation_id, tag, confidence)
                VALUES (:conv_id, :tag, 0.95)
                ON CONFLICT DO NOTHING
            """, {"conv_id": conversation_id, "tag": tag})

        return tags
```

### Database Schema:

```sql
CREATE TABLE conversation_tags (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    tag VARCHAR(50),
    confidence FLOAT DEFAULT 0.95,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(conversation_id, tag)
);

CREATE INDEX idx_conversation_tags_tag ON conversation_tags(tag);
```

---

## 3.2 Cost-to-Revenue Tracking (Week 16-17)

**Location:** `apps/backend/src/analytics/profitability/`

```python
# profitability_calculator.py
class ProfitabilityCalculator:
    """Calculate booking profitability"""

    COSTS = {
        "chef_base": 300.00,
        "protein_multiplier": 0.35,  # 35% of upgrade price
        "travel_per_mile": 0.75,
        "equipment_fixed": 50.00,
        "addon_multiplier": 0.30,
        "overhead_rate": 0.15  # 15% of revenue
    }

    async def calculate_profitability(self, booking: Booking) -> Dict:
        """Calculate all costs and profit"""

        # Revenue
        total_revenue = booking.total_amount

        # Costs
        chef_cost = self.COSTS["chef_base"]
        protein_cost = booking.protein_upgrade_cost * self.COSTS["protein_multiplier"]
        travel_cost = booking.travel_fee * 0.40  # 40% of travel fee is actual cost
        equipment_cost = self.COSTS["equipment_fixed"]
        addon_cost = booking.addon_cost * self.COSTS["addon_multiplier"]
        overhead_cost = total_revenue * self.COSTS["overhead_rate"]

        # Profit
        gross_profit = total_revenue - (chef_cost + protein_cost + travel_cost + equipment_cost + addon_cost)
        net_profit = gross_profit - overhead_cost
        profit_margin = (net_profit / total_revenue) * 100

        return {
            "revenue": total_revenue,
            "costs": {
                "chef": chef_cost,
                "protein": protein_cost,
                "travel": travel_cost,
                "equipment": equipment_cost,
                "addon": addon_cost,
                "overhead": overhead_cost,
                "total": chef_cost + protein_cost + travel_cost + equipment_cost + addon_cost + overhead_cost
            },
            "profit": {
                "gross": gross_profit,
                "net": net_profit,
                "margin": profit_margin
            }
        }
```

### Database Schema:

```sql
CREATE TABLE booking_profitability (
    id SERIAL PRIMARY KEY,
    booking_id UUID REFERENCES bookings(id),

    base_revenue DECIMAL(10,2),
    protein_upgrade_revenue DECIMAL(10,2),
    addon_revenue DECIMAL(10,2),
    total_revenue DECIMAL(10,2),

    chef_cost DECIMAL(10,2),
    protein_cost DECIMAL(10,2),
    travel_cost DECIMAL(10,2),
    equipment_cost DECIMAL(10,2),
    addon_cost DECIMAL(10,2),
    overhead_cost DECIMAL(10,2),

    gross_profit DECIMAL(10,2),
    net_profit DECIMAL(10,2),
    profit_margin FLOAT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Auto-calculate trigger
CREATE FUNCTION calculate_booking_costs() RETURNS TRIGGER AS $$
-- (implementation from earlier)
$$ LANGUAGE plpgsql;

CREATE TRIGGER booking_profitability_trigger
AFTER INSERT ON bookings
FOR EACH ROW EXECUTE FUNCTION calculate_booking_costs();
```

---

## 3.3 Per-Channel Performance (Week 17-18)

**Location:** `apps/backend/src/analytics/channels/`

```python
# channel_tracker.py
class ChannelPerformanceTracker:
    """Track performance by channel"""

    async def track_conversation_channel(
        self,
        conversation_id: UUID,
        channel: str  # 'sms', 'web_chat', 'instagram', 'phone_call'
    ):
        """Track channel metrics"""

        conversation = await db.query(Conversation).get(conversation_id)

        await db.execute("""
            INSERT INTO conversation_channels (
                conversation_id,
                channel,
                first_response_time,
                total_messages,
                conversation_duration,
                booking_created,
                total_revenue,
                customer_response_rate
            ) VALUES (
                :conv_id, :channel, :response_time, :messages,
                :duration, :booked, :revenue, :response_rate
            )
        """, {
            "conv_id": conversation_id,
            "channel": channel,
            # ... metrics
        })
```

### Database Schema:

```sql
CREATE TABLE conversation_channels (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    channel VARCHAR(50),

    first_response_time INT,
    total_messages INT,
    conversation_duration INT,
    booking_created BOOLEAN,
    total_revenue DECIMAL(10,2),
    customer_response_rate FLOAT,
    handoff_to_human BOOLEAN,
    customer_satisfaction FLOAT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance view
CREATE VIEW channel_performance AS
SELECT
    channel,
    COUNT(*) as total_conversations,
    COUNT(CASE WHEN booking_created THEN 1 END) as bookings,
    ROUND(100.0 * COUNT(CASE WHEN booking_created THEN 1 END) / COUNT(*), 2) as conversion_rate,
    AVG(total_revenue) as avg_revenue,
    SUM(total_revenue) as total_revenue,
    AVG(customer_satisfaction) as avg_satisfaction
FROM conversation_channels
GROUP BY channel
ORDER BY conversion_rate DESC;
```

---

# 🟥 **PHASE 4 — v5.0 HYBRID AI+HUMAN (Week 19-24)**

## 4.1 Human Feedback System (Week 19-22)

**Location:** `apps/backend/src/ai/human_feedback/`,
`apps/admin/src/pages/ai/`

### Backend:

```python
# feedback_processor.py
class HumanFeedbackProcessor:
    """Process human feedback and improve AI"""

    async def process_improved_response(
        self,
        feedback_id: UUID,
        original: str,
        improved: str,
        tags: List[str]
    ):
        """Learn from human-improved responses"""

        # Extract improvement pattern
        pattern = await self.extract_improvement_pattern(original, improved)

        # Update relevant prompt sections
        if 'objection_handling' in tags:
            await self.update_objection_template(pattern)

        # Add to training corpus
        await self.add_to_training_corpus({
            'bad_output': original,
            'good_output': improved,
            'tags': tags
        })
```

### Frontend (Next.js):

```typescript
// apps/admin/src/pages/ai/HumanFeedbackPanel.tsx

export function HumanFeedbackPanel() {
  const [conversations, setConversations] = useState([]);

  return (
    <div className="space-y-6">
      {/* Recent Conversations */}
      <Card>
        <CardHeader>AI Conversations Needing Review</CardHeader>
        {conversations.map(conv => (
          <ConversationCard
            key={conv.id}
            conversation={conv}
            onImprove={async (messageId, improved) => {
              await submitFeedback({
                conversation_id: conv.id,
                ai_message_id: messageId,
                feedback_type: 'improve_response',
                improved_response: improved
              });
            }}
          />
        ))}
      </Card>

      {/* Knowledge Base Editor */}
      <Card>
        <CardHeader>Knowledge Base</CardHeader>
        <KnowledgeBaseTable
          entries={knowledgeEntries}
          onAdd={addKnowledgeEntry}
          onEdit={editKnowledgeEntry}
        />
      </Card>

      {/* Custom Scripts Manager */}
      <Card>
        <CardHeader>Custom Scripts & Upsells</CardHeader>
        <CustomScriptsManager
          scripts={customScripts}
          onAdd={addScript}
        />
      </Card>

      {/* Self-Healing Approval Queue */}
      <Card>
        <CardHeader>🤖 Self-Healing Changes Awaiting Approval</CardHeader>
        <ApprovalQueue
          changes={pendingChanges}
          onApprove={approveChange}
          onReject={rejectChange}
        />
      </Card>
    </div>
  );
}
```

---

# 🟦 **PHASE 5 — ADMIN DASHBOARDS (Week 23-24)**

## 5.1 Analytics Dashboards

**Location:** `apps/admin/src/pages/analytics/`

```typescript
// ConversationAnalyticsPage.tsx
export function ConversationAnalyticsPage() {
  const { data: analytics } = useQuery('conversation-analytics');

  return (
    <div className="space-y-6">
      {/* Lost Booking Analysis */}
      <Card>
        <CardHeader>Top Reasons for Lost Bookings</CardHeader>
        <PieChart data={analytics.lostBookings} />
      </Card>

      {/* Objection Tracking */}
      <Card>
        <CardHeader>Objection Resolution Rate</CardHeader>
        <BarChart data={analytics.objections} />
      </Card>

      {/* Conversion by Event Type */}
      <Card>
        <CardHeader>Conversion Rate by Event Type</CardHeader>
        <BarChart data={analytics.conversionByEvent} />
      </Card>
    </div>
  );
}

// ProfitabilityDashboard.tsx
export function ProfitabilityDashboard() {
  return (
    <div className="space-y-6">
      {/* Monthly Profit Trend */}
      <Card>
        <CardHeader>Monthly Profitability</CardHeader>
        <LineChart data={profitByMonth} />
      </Card>

      {/* Low-Margin Bookings Alert */}
      <Card className="border-orange-500">
        <CardHeader>⚠️ Low-Margin Bookings</CardHeader>
        <LowMarginTable bookings={lowMarginBookings} />
      </Card>
    </div>
  );
}
```

---

# 🟨 **PHASE 6 — DOCUMENTATION (Week 24)**

Create comprehensive docs:

```
docs/
├── AI_SYSTEM_OVERVIEW.md
├── SELF_HEALING_DESIGN.md
├── CUSTOMER_MEMORY_DESIGN.md
├── ANALYTICS_DESIGN.md
├── VOICE_ARCHITECTURE.md
├── VERSIONING_GUIDE.md
├── TESTING_STRATEGY.md
├── DEPLOYMENT_GUIDE.md
└── TROUBLESHOOTING.md
```

---

# ⚙️ **AGENT EXECUTION COMMANDS**

## When you say:

### **"BEGIN IMPLEMENTATION FOR PHASE X"**

I will:

1. Generate all files with full paths
2. Include complete code (no placeholders)
3. Include migrations
4. Include tests
5. Add documentation

### **"CONTINUE"**

Continue exactly where I left off

### **"RUN DIAGNOSTIC"**

Summarize: what's built, what's missing, what's next

### **"DEPLOY"**

Generate deployment scripts and instructions

### **"TEST"**

Run all tests and show results

---

# ✅ **READY SIGNAL**

**AI SYSTEM ENGINEER READY — Awaiting Phase Instructions.**

Respond with phase number to begin (e.g., "BEGIN PHASE 0" or "BEGIN
PHASE 2.1")

---

**END OF MEGA PROMPT**
