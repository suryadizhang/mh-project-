# 🚀 EXECUTION PLAN - Tool Calling Implementation Phase

**Date:** October 31, 2025  
**Strategy:** Hybrid Phased Approach (Smart + ChatGPT-ready)  
**Timeline:** Week 1-2 (Tool Calling + Admin Dashboard)  
**Investment:** $5-7K (Phase 1) → Data Collection → $20-40K (Phase 3, if validated)

---

## 📋 PRE-EXECUTION CHECKLIST

### ✅ Phase 0: Safety & Organization (TODAY - 2-3 hours)

**CURRENT STATUS:** In Progress

```
[████████████░░░░░░░░░░░░░░░░░░░░] 40% Complete

✅ 1. Current State Audit
✅ 2. Todo List Updated
⏳ 3. Documentation Consolidation (Next)
⏳ 4. File Structure Analysis
⏳ 5. Git Safety Commit
⏳ 6. Execution Roadmap Finalization
```

---

## 🎯 EXECUTION STRATEGY

### Core Philosophy: **"Build Foundation, Collect Intelligence, Expand Smartly"**

```
Phase 1 (Week 1-2): Build Foundation + ChatGPT-Ready Architecture
├── Tool Calling Implementation (3-4 days)
├── Admin Dashboard Frontend (2-3 days)
├── Extension Points for Phase 3
└── Production Deployment

Phase 2 (Month 1-2): Intelligence Gathering
├── Send 50-100 quotes with manual review
├── Track: channels, follow-ups, errors, conversions
├── Decision Dashboard (Google Sheets)
└── Validate Phase 3 priorities

Phase 3 (Month 2+): Selective Feature Build
├── Build ONLY validated features (data-driven)
├── Voice AI (IF phone_call_rate >30%)
├── Threading (IF follow_up_rate >50%)
├── RAG (IF ai_error_rate >30%)
└── Analytics (IF total_inquiries >100)
```

**Estimated Savings:** $30-60K (avoid building unused features)

---

## 📁 CURRENT PROJECT STRUCTURE

### Monorepo Layout (3 Separate Deployments)

```
mh-project-/
├── apps/
│   ├── backend/              → VPS (Plesk) - API Server
│   │   ├── src/
│   │   │   ├── api/
│   │   │   │   ├── ai/       → AI Services (multi_channel, protein, etc.)
│   │   │   │   ├── v1/       → REST API endpoints
│   │   │   │   ├── admin/    → Admin APIs
│   │   │   │   ├── webhooks/ → Payment webhooks
│   │   │   │   └── websockets/
│   │   │   ├── core/         → Database, auth, config
│   │   │   └── shared/       → Utilities
│   │   └── main.py           → FastAPI entry point
│   │
│   ├── customer/             → Vercel - Customer Frontend
│   │   ├── src/
│   │   │   ├── app/          → Next.js 14 App Router
│   │   │   ├── components/   → React components
│   │   │   ├── lib/          → Client utilities
│   │   │   └── styles/       → Tailwind CSS
│   │   └── package.json
│   │
│   ├── admin/                → Vercel (Different Domain) - Admin Panel
│   │   ├── src/
│   │   │   ├── app/          → Next.js 14 App Router
│   │   │   ├── components/   → React admin components
│   │   │   ├── lib/          → Admin utilities
│   │   │   └── styles/       → Tailwind CSS
│   │   └── package.json
│   │
│   └── frontend/             → Legacy? (needs verification)
│
├── packages/                 → Shared libraries (if any)
├── docs/                     → Documentation
└── [100+ MD files]          → NEEDS CONSOLIDATION ⚠️
```

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     3 DOMAINS                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Domain 1: api.myhibachi.com                                 │
│  ├── VPS (Plesk)                                            │
│  ├── FastAPI Backend                                        │
│  └── PostgreSQL + Redis                                     │
│                                                               │
│  Domain 2: myhibachi.com                                     │
│  ├── Vercel                                                  │
│  ├── Next.js Customer Frontend                              │
│  └── API calls → api.myhibachi.com                          │
│                                                               │
│  Domain 3: admin.myhibachi.com                               │
│  ├── Vercel (separate project)                              │
│  ├── Next.js Admin Panel                                    │
│  └── API calls → api.myhibachi.com                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ DOCUMENTATION CONSOLIDATION PLAN

### Current State: **100+ Markdown Files** (Needs Organization) ⚠️

#### Categories Identified:

1. **Architecture & Planning** (15 files)
2. **Implementation Complete** (25 files)
3. **Backend Documentation** (20 files)
4. **Frontend Documentation** (10 files)
5. **Deployment Guides** (15 files)
6. **Testing & Audit** (15 files)
7. **Feature Specific** (25 files)
8. **Quick References** (10 files)
9. **Session Summaries** (15 files)

#### Consolidation Strategy:

```
docs/
├── 01-ARCHITECTURE/
│   ├── SYSTEM_ARCHITECTURE.md (consolidated)
│   ├── DECISION_MATRIX.md
│   └── DEPLOYMENT_ARCHITECTURE.md
│
├── 02-IMPLEMENTATION/
│   ├── PHASE_1_COMPLETE.md
│   ├── PHASE_2_PLAN.md
│   └── PHASE_3_PLAN.md
│
├── 03-FEATURES/
│   ├── AI_SYSTEM.md
│   ├── PROTEIN_CALCULATOR.md
│   ├── PAYMENT_SYSTEM.md
│   └── NOTIFICATION_SYSTEM.md
│
├── 04-DEPLOYMENT/
│   ├── VPS_DEPLOYMENT.md
│   ├── VERCEL_DEPLOYMENT.md
│   └── ENV_SETUP.md
│
├── 05-TESTING/
│   ├── TESTING_GUIDE.md
│   └── AUDIT_REPORTS.md
│
├── 06-QUICK_REFERENCE/
│   ├── API_REFERENCE.md
│   ├── COMMANDS.md
│   └── TROUBLESHOOTING.md
│
└── archives/
    └── [Old MD files - timestamped]
```

**Action:** Create consolidation script (move + update imports)

---

## 🔧 TOOL CALLING IMPLEMENTATION PLAN

### Phase 1A: ChatGPT-Ready Architecture (Day 1-2)

**Goal:** Build tool calling with extension points for Phase 3 expansion

#### New Files to Create:

```
apps/backend/src/api/ai/orchestrator/
├── __init__.py
├── ai_orchestrator.py           ✨ NEW - Main orchestrator
├── tools/
│   ├── __init__.py
│   ├── base_tool.py             ✨ NEW - Abstract tool interface
│   ├── pricing_tool.py          ✨ NEW - calculate_party_quote
│   ├── travel_fee_tool.py       ✨ NEW - calculate_travel_fee
│   ├── protein_tool.py          ✨ NEW - calculate_protein_costs
│   └── [Phase 3 tools here]     📦 Placeholders
│
├── services/
│   ├── __init__.py
│   ├── conversation_service.py   ✨ NEW - Basic now, full in Phase 3
│   ├── identity_resolver.py      ✨ NEW - Placeholder for Phase 3
│   ├── rag_service.py            ✨ NEW - Placeholder for Phase 3
│   └── voice_handler.py          ✨ NEW - Placeholder for Phase 3
│
└── schemas/
    ├── __init__.py
    ├── tool_schemas.py           ✨ NEW - OpenAI function schemas
    └── orchestrator_schemas.py   ✨ NEW - Request/response models
```

#### Modified Files:

```
apps/backend/src/api/ai/endpoints/services/
├── multi_channel_ai_handler.py   🔧 MODIFY - Integrate orchestrator
└── customer_booking_ai.py        🔧 MODIFY - Add tool calling support
```

---

### Phase 1B: OpenAI Function Calling (Day 2-3)

#### Tool Schema Example:

```python
# apps/backend/src/api/ai/orchestrator/schemas/tool_schemas.py

PRICING_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate_party_quote",
        "description": "Calculate accurate hibachi party quote with travel fees and protein upgrades",
        "parameters": {
            "type": "object",
            "properties": {
                "adults": {
                    "type": "integer",
                    "description": "Number of adult guests (12+ years old)"
                },
                "children": {
                    "type": "integer",
                    "description": "Number of children aged 6-12 years"
                },
                "protein_selections": {
                    "type": "object",
                    "description": "Protein choices mapping protein names to quantities",
                    "additionalProperties": {"type": "integer"}
                },
                "customer_zipcode": {
                    "type": "string",
                    "description": "Customer's zip code for travel fee calculation"
                },
                "event_date": {
                    "type": "string",
                    "description": "Event date in YYYY-MM-DD format (for holiday pricing)"
                }
            },
            "required": ["adults"]
        }
    }
}

TRAVEL_FEE_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate_travel_fee",
        "description": "Calculate travel fee based on distance from base location",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_zipcode": {
                    "type": "string",
                    "description": "Customer's zip code or full address"
                }
            },
            "required": ["customer_zipcode"]
        }
    }
}

# Phase 3 Tools (Placeholders)
VOICE_TRANSCRIBE_TOOL = {...}  # For RingCentral integration
RAG_RETRIEVE_TOOL = {...}      # For knowledge base queries
BOOKING_CREATE_TOOL = {...}    # For automatic booking creation
```

---

### Phase 1C: AI Orchestrator Implementation (Day 3-4)

```python
# apps/backend/src/api/ai/orchestrator/ai_orchestrator.py

from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Multi-channel AI orchestrator with ChatGPT-ready architecture
    
    Phase 1: Tool calling (pricing, travel fees)
    Phase 3 Ready: Voice AI, RAG, threading, identity resolution
    """
    
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        enable_rag: bool = False,
        enable_voice: bool = False,
        enable_threading: bool = False,
        enable_identity_resolution: bool = False
    ):
        self.openai_client = openai_client
        
        # Phase 1: Active tools
        from .tools import PricingTool, TravelFeeTool, ProteinTool
        self.active_tools = {
            "calculate_party_quote": PricingTool(),
            "calculate_travel_fee": TravelFeeTool(),
            "calculate_protein_costs": ProteinTool()
        }
        
        # Phase 3: Service placeholders (ready to activate)
        self.rag_service = None
        self.voice_handler = None
        self.conversation_service = ConversationService()
        self.identity_resolver = None
        
        # Feature flags (Phase 3)
        self.enable_rag = enable_rag
        self.enable_voice = enable_voice
        self.enable_threading = enable_threading
        self.enable_identity_resolution = enable_identity_resolution
        
        logger.info(f"🤖 AI Orchestrator initialized (Phase 1 mode)")
        logger.info(f"   Active tools: {list(self.active_tools.keys())}")
    
    async def process_inquiry(
        self,
        message: str,
        channel: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process multi-channel inquiry with tool calling
        
        Workflow:
        1. [Phase 3] Resolve customer identity
        2. [Phase 3] Get conversation history
        3. [Phase 3] Retrieve RAG knowledge
        4. [Phase 1] Execute tool calls
        5. Generate AI response
        """
        
        # Step 1: Identity resolution (Phase 3)
        customer_id = await self._resolve_identity(message, channel, context)
        
        # Step 2: Conversation history (Phase 3)
        conversation_history = await self._get_conversation_history(customer_id)
        
        # Step 3: RAG retrieval (Phase 3)
        knowledge_context = await self._retrieve_knowledge(message)
        
        # Step 4: Build AI context
        ai_context = self._build_ai_context(
            message=message,
            channel=channel,
            context=context,
            history=conversation_history,
            knowledge=knowledge_context
        )
        
        # Step 5: Call OpenAI with tool calling
        response = await self._call_openai_with_tools(ai_context)
        
        # Step 6: Execute tools if requested
        if response.get("tool_calls"):
            tool_results = await self._execute_tools(response["tool_calls"])
            
            # Feed tool results back to AI
            final_response = await self._call_openai_with_tool_results(
                ai_context, 
                response, 
                tool_results
            )
        else:
            final_response = response
        
        # Step 7: Format and return
        return self._format_response(final_response, context)
    
    async def _resolve_identity(
        self, 
        message: str, 
        channel: str, 
        context: Dict
    ) -> Optional[str]:
        """
        Resolve customer identity across channels
        
        Phase 1: Basic (email/phone from context)
        Phase 3: Full cross-channel merge (email + Instagram + phone)
        """
        if self.enable_identity_resolution and self.identity_resolver:
            return await self.identity_resolver.resolve(message, channel, context)
        
        # Phase 1: Simple extraction
        return context.get("customer_email") or context.get("customer_phone")
    
    async def _get_conversation_history(
        self, 
        customer_id: Optional[str]
    ) -> List[Dict]:
        """
        Get conversation history for threading
        
        Phase 1: Empty list (no history)
        Phase 3: Full conversation tracking with thread_id
        """
        if self.enable_threading and customer_id:
            return await self.conversation_service.get_history(customer_id)
        
        return []
    
    async def _retrieve_knowledge(self, message: str) -> Optional[str]:
        """
        Retrieve relevant knowledge from RAG
        
        Phase 1: None (uses system prompt only)
        Phase 3: Vector DB semantic search (Pinecone/Weaviate)
        """
        if self.enable_rag and self.rag_service:
            return await self.rag_service.retrieve(message)
        
        return None
    
    async def _call_openai_with_tools(
        self, 
        ai_context: Dict
    ) -> Dict[str, Any]:
        """
        Call OpenAI with function calling enabled
        """
        from .schemas.tool_schemas import PRICING_TOOL, TRAVEL_FEE_TOOL
        
        tools = [PRICING_TOOL, TRAVEL_FEE_TOOL]
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=ai_context["messages"],
            tools=tools,
            tool_choice="auto",
            temperature=0.7
        )
        
        return {
            "message": response.choices[0].message,
            "tool_calls": response.choices[0].message.tool_calls,
            "model_used": response.model,
            "usage": response.usage
        }
    
    async def _execute_tools(
        self, 
        tool_calls: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute requested tool calls
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_params = json.loads(tool_call.function.arguments)
            
            if tool_name in self.active_tools:
                try:
                    tool = self.active_tools[tool_name]
                    result = await tool.execute(tool_params)
                    
                    results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result)
                    })
                    
                    logger.info(f"✅ Tool executed: {tool_name}")
                except Exception as e:
                    logger.error(f"❌ Tool error ({tool_name}): {str(e)}")
                    results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps({"error": str(e)})
                    })
        
        return results
    
    async def _call_openai_with_tool_results(
        self,
        ai_context: Dict,
        previous_response: Dict,
        tool_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        Feed tool results back to AI for final response
        """
        messages = ai_context["messages"] + [
            previous_response["message"]
        ] + tool_results
        
        final_response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0.7
        )
        
        return {
            "message": final_response.choices[0].message,
            "model_used": final_response.model,
            "usage": final_response.usage
        }
    
    def _format_response(
        self, 
        response: Dict, 
        context: Dict
    ) -> Dict[str, Any]:
        """
        Format final response for API
        """
        return {
            "response_text": response["message"].content,
            "model_used": response["model_used"],
            "channel": context.get("channel"),
            "tool_calls_used": [
                call.function.name 
                for call in (response.get("tool_calls") or [])
            ],
            "metadata": {
                "tokens_used": response["usage"].total_tokens,
                "customer_id": context.get("customer_id")
            }
        }


# Singleton instance
_orchestrator_instance = None


def get_ai_orchestrator() -> AIOrchestrator:
    """Get singleton AI orchestrator instance"""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        from openai import AsyncOpenAI
        from core.config import settings
        
        _orchestrator_instance = AIOrchestrator(
            openai_client=AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        )
    
    return _orchestrator_instance
```

---

### Phase 1D: Integration with Existing System (Day 4)

**Modify:** `apps/backend/src/api/ai/endpoints/services/multi_channel_ai_handler.py`

```python
# Add import
from api.ai.orchestrator import get_ai_orchestrator

class MultiChannelAIHandler:
    def __init__(self):
        self.orchestrator = get_ai_orchestrator()  # ✨ NEW
        # ... existing code
    
    async def process_multi_channel_inquiry(
        self, 
        message: str, 
        channel: str, 
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process inquiry with AI orchestrator (tool calling enabled)
        """
        
        # Step 1: Extract inquiry details (existing)
        inquiry_details = await self.extract_inquiry_details(message, channel)
        
        # Step 1.5: Calculate protein costs (existing - Phase 1A complete)
        protein_info = None
        if inquiry_details.get("protein_selections") and inquiry_details.get("party_size"):
            from .protein_calculator_service import get_protein_calculator_service
            protein_calc = get_protein_calculator_service()
            protein_info = protein_calc.calculate_protein_costs(
                guest_count=inquiry_details["party_size"],
                protein_selections=inquiry_details["protein_selections"]
            )
        
        # Step 2: Build context for orchestrator
        orchestrator_context = {
            "channel": channel,
            "inquiry_details": inquiry_details,
            "protein_info": protein_info,
            "customer_email": context.get("customer_email"),
            "customer_phone": context.get("customer_phone")
        }
        
        # Step 3: Call orchestrator with tool calling ✨ NEW
        ai_response = await self.orchestrator.process_inquiry(
            message=message,
            channel=channel,
            context=orchestrator_context
        )
        
        # Step 4: Format response (existing logic)
        formatted_response = self._format_response(
            ai_response, 
            inquiry_details, 
            protein_info
        )
        
        return formatted_response
```

---

## 🎨 ADMIN DASHBOARD IMPLEMENTATION PLAN

### Phase 1E: Admin Dashboard Frontend (Day 5-7)

#### New Files to Create:

```
apps/admin/src/app/emails/
├── pending/
│   ├── page.tsx                 ✨ NEW - Email review dashboard
│   └── [id]/
│       └── page.tsx             ✨ NEW - Individual email detail view
│
apps/admin/src/components/emails/
├── EmailReviewDashboard.tsx     ✨ NEW - Main dashboard component
├── EmailList.tsx                ✨ NEW - List of pending emails
├── EmailCard.tsx                ✨ NEW - Email preview card
├── EmailDetailView.tsx          ✨ NEW - Side-by-side comparison
├── ProteinBreakdown.tsx         ✨ NEW - Protein cost display
├── ApprovalActions.tsx          ✨ NEW - Approve/Edit/Reject buttons
└── EmailFilters.tsx             ✨ NEW - Priority/Channel filters
```

#### Implementation Details:

```tsx
// apps/admin/src/components/emails/EmailReviewDashboard.tsx

'use client';

import { useState, useEffect } from 'react';
import { EmailList } from './EmailList';
import { EmailDetailView } from './EmailDetailView';
import { EmailFilters } from './EmailFilters';

export function EmailReviewDashboard() {
  const [pendingEmails, setPendingEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [filters, setFilters] = useState({
    priority: 'all',
    channel: 'all',
    status: 'pending'
  });
  
  useEffect(() => {
    fetchPendingEmails();
  }, [filters]);
  
  async function fetchPendingEmails() {
    const response = await fetch(
      `/api/admin/emails/pending?${new URLSearchParams(filters)}`
    );
    const data = await response.json();
    setPendingEmails(data.emails);
  }
  
  async function handleApprove(emailId: string) {
    await fetch(`/api/admin/emails/${emailId}/approve`, {
      method: 'POST'
    });
    fetchPendingEmails();
    setSelectedEmail(null);
  }
  
  async function handleEdit(emailId: string, editedContent: string) {
    await fetch(`/api/admin/emails/${emailId}/edit`, {
      method: 'PUT',
      body: JSON.stringify({ content: editedContent })
    });
    fetchPendingEmails();
  }
  
  async function handleReject(emailId: string, reason: string) {
    await fetch(`/api/admin/emails/${emailId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
    fetchPendingEmails();
    setSelectedEmail(null);
  }
  
  return (
    <div className="email-review-dashboard">
      <div className="dashboard-header">
        <h1>Email Review Dashboard</h1>
        <EmailFilters 
          filters={filters} 
          onFilterChange={setFilters} 
        />
      </div>
      
      <div className="dashboard-content">
        <EmailList
          emails={pendingEmails}
          selectedEmail={selectedEmail}
          onSelectEmail={setSelectedEmail}
        />
        
        {selectedEmail && (
          <EmailDetailView
            email={selectedEmail}
            onApprove={handleApprove}
            onEdit={handleEdit}
            onReject={handleReject}
          />
        )}
      </div>
    </div>
  );
}
```

---

## 📊 PHASE 2: DATA COLLECTION SYSTEM

### Data Collection Tools (Month 1-2)

#### Create Tracking System:

```python
# apps/backend/src/api/ai/analytics/customer_behavior_tracker.py

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CustomerBehaviorTracker:
    """
    Track customer behavior during Phase 2 to inform Phase 3 decisions
    
    Metrics:
    - Channel usage (email, phone, Instagram, Facebook)
    - Follow-up patterns (multi-turn conversations)
    - AI accuracy (approval rate, edit rate, error types)
    - Conversion funnel (inquiry → quote → booking)
    - Protein upsell rates
    - Multi-channel usage (identity resolution need)
    """
    
    def __init__(self, db_session, sheets_client=None):
        self.db = db_session
        self.sheets = sheets_client
    
    async def track_inquiry(self, inquiry_data: Dict[str, Any]) -> None:
        """
        Track comprehensive inquiry metrics
        """
        metrics = {
            # Channel Analysis
            "channel": inquiry_data["channel"],
            "timestamp": datetime.utcnow(),
            
            # Customer Identity
            "customer_id": inquiry_data.get("customer_id"),
            "customer_email": inquiry_data.get("customer_email"),
            "customer_phone": inquiry_data.get("customer_phone"),
            
            # Conversation Analysis
            "is_follow_up": await self._detect_follow_up(inquiry_data),
            "conversation_depth": await self._count_messages(inquiry_data),
            "message_count": inquiry_data.get("message_count", 1),
            
            # AI Quality Analysis
            "ai_response_generated": inquiry_data.get("ai_response") is not None,
            "admin_approval_status": None,  # Will be updated later
            "edit_percentage": None,  # Will be calculated on approval
            "response_time_seconds": inquiry_data.get("response_time"),
            
            # Tool Calling Analysis
            "tools_used": inquiry_data.get("tool_calls_used", []),
            "pricing_tool_called": "calculate_party_quote" in inquiry_data.get("tool_calls_used", []),
            
            # Quote Details
            "party_size": inquiry_data.get("party_size"),
            "quote_total": inquiry_data.get("quote_total"),
            "protein_upgrades": inquiry_data.get("protein_info", {}).get("total_protein_cost", 0),
            
            # Multi-Channel Detection
            "multi_channel_user": await self._check_multi_channel(inquiry_data.get("customer_id")),
            "channels_used_count": await self._count_channels(inquiry_data.get("customer_id")),
            
            # Metadata
            "raw_message": inquiry_data.get("message"),
            "inquiry_type": inquiry_data.get("inquiry_type")
        }
        
        # Save to database
        await self._save_to_db(metrics)
        
        # Sync to Google Sheets (if enabled)
        if self.sheets:
            await self._sync_to_sheets(metrics)
        
        logger.info(f"📊 Tracked inquiry: {metrics['channel']} | Customer: {metrics['customer_id']}")
    
    async def track_approval(
        self, 
        inquiry_id: str, 
        approval_data: Dict[str, Any]
    ) -> None:
        """
        Track admin approval decision
        """
        approval_metrics = {
            "inquiry_id": inquiry_id,
            "approval_status": approval_data["status"],  # approved, edited, rejected
            "edit_percentage": self._calculate_edit_distance(
                approval_data.get("original"),
                approval_data.get("edited")
            ) if approval_data["status"] == "edited" else 0,
            "admin_time_seconds": approval_data.get("time_spent"),
            "approval_timestamp": datetime.utcnow()
        }
        
        await self._update_inquiry_metrics(inquiry_id, approval_metrics)
    
    async def track_booking(
        self, 
        inquiry_id: str, 
        booking_data: Dict[str, Any]
    ) -> None:
        """
        Track booking conversion
        """
        conversion_metrics = {
            "inquiry_id": inquiry_id,
            "booked": True,
            "booking_id": booking_data["booking_id"],
            "time_to_booking": self._calculate_time_to_booking(inquiry_id),
            "final_amount": booking_data["total"],
            "protein_upsell_included": booking_data.get("protein_upgrades", 0) > 0,
            "booking_timestamp": datetime.utcnow()
        }
        
        await self._update_inquiry_metrics(inquiry_id, conversion_metrics)
    
    async def generate_decision_dashboard(self) -> Dict[str, Any]:
        """
        Generate Phase 3 decision dashboard after 50-100 inquiries
        
        Returns decision criteria for each potential Phase 3 feature
        """
        total_inquiries = await self._count_total_inquiries()
        
        if total_inquiries < 50:
            return {
                "ready_for_analysis": False,
                "message": f"Need {50 - total_inquiries} more inquiries for analysis"
            }
        
        # Channel Analysis
        channel_stats = await self._analyze_channels()
        
        # Conversation Analysis
        follow_up_rate = await self._calculate_follow_up_rate()
        avg_messages = await self._calculate_avg_messages()
        
        # AI Quality Analysis
        approval_rate = await self._calculate_approval_rate()
        edit_rate = await self._calculate_edit_rate()
        error_rate = 100 - approval_rate
        
        # Identity Analysis
        multi_channel_rate = await self._calculate_multi_channel_rate()
        
        # Conversion Analysis
        conversion_rate = await self._calculate_conversion_rate()
        protein_upsell_rate = await self._calculate_protein_upsell_rate()
        
        # Phase 3 Decisions
        decisions = {
            "voice_ai": {
                "build": channel_stats.get("phone", 0) > 30,
                "metric": f"{channel_stats.get('phone', 0)}% phone calls",
                "threshold": "30%",
                "cost": "$12,000",
                "timeline": "3-4 weeks",
                "recommendation": "BUILD" if channel_stats.get("phone", 0) > 30 else "SKIP"
            },
            "conversation_threading": {
                "build": follow_up_rate > 50,
                "metric": f"{follow_up_rate}% follow-up rate",
                "threshold": "50%",
                "cost": "$3,000",
                "timeline": "1 week",
                "recommendation": "BUILD" if follow_up_rate > 50 else "SKIP"
            },
            "rag_knowledge_base": {
                "build": error_rate > 30,
                "metric": f"{error_rate}% AI error rate",
                "threshold": "30%",
                "cost": "$5,000 + $20-50/mo",
                "timeline": "1-2 weeks",
                "recommendation": "BUILD" if error_rate > 30 else "IMPROVE PROMPT"
            },
            "identity_resolution": {
                "build": multi_channel_rate > 30,
                "metric": f"{multi_channel_rate}% multi-channel users",
                "threshold": "30%",
                "cost": "$2,000",
                "timeline": "3-4 days",
                "recommendation": "BUILD" if multi_channel_rate > 30 else "SKIP"
            },
            "analytics_dashboard": {
                "build": total_inquiries > 100,
                "metric": f"{total_inquiries} total inquiries",
                "threshold": "100",
                "cost": "$3,000",
                "timeline": "1-2 weeks",
                "recommendation": "BUILD" if total_inquiries > 100 else "USE SHEETS"
            }
        }
        
        # Calculate total Phase 3 investment
        features_to_build = [
            feature for feature, data in decisions.items() 
            if data["recommendation"] == "BUILD"
        ]
        
        total_cost = sum(
            int(decisions[feature]["cost"].replace("$", "").replace(",", "").split()[0])
            for feature in features_to_build
        )
        
        return {
            "ready_for_analysis": True,
            "total_inquiries": total_inquiries,
            "channel_stats": channel_stats,
            "conversation_stats": {
                "follow_up_rate": follow_up_rate,
                "avg_messages": avg_messages
            },
            "ai_quality_stats": {
                "approval_rate": approval_rate,
                "edit_rate": edit_rate,
                "error_rate": error_rate
            },
            "conversion_stats": {
                "conversion_rate": conversion_rate,
                "protein_upsell_rate": protein_upsell_rate
            },
            "phase_3_decisions": decisions,
            "features_to_build": features_to_build,
            "estimated_investment": f"${total_cost:,}",
            "savings_from_skipped": f"${50000 - total_cost:,}"
        }
```

#### Google Sheets Template:

```
PHASE 2 DATA COLLECTION TRACKER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Date | Customer | Channel | Party Size | Quote $ | Proteins |
Response Time | Follow-up? | AI Error? | Admin Edit? | Booked? | Revenue | Notes

[Auto-populated from backend tracking system]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DECISION DASHBOARD (Auto-calculated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Inquiries: [COUNT]
Phase 3 Ready: [Yes/No - Need 50 minimum]

CHANNEL USAGE:
├── Email: [X]%
├── Phone: [X]% → Voice AI? [Yes/No]
├── Instagram: [X]%
└── Facebook: [X]%

CONVERSATION PATTERNS:
├── Follow-up rate: [X]% → Threading? [Yes/No]
├── Avg messages: [X]
└── Multi-channel: [X]% → Identity Resolution? [Yes/No]

AI QUALITY:
├── Approval rate: [X]%
├── Edit rate: [X]%
├── Error rate: [X]% → RAG? [Yes/No]
└── Avg admin time: [X] seconds

CONVERSION:
├── Booking rate: [X]%
├── Protein upsell: [X]%
└── Avg revenue: $[X]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 RECOMMENDATION: [Features to build]
ESTIMATED INVESTMENT: $[X]
SAVINGS: $[X] (avoided unnecessary features)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📐 PHASE 3 ARCHITECTURE PLAN (READY TO ACTIVATE)

### Feature: Voice AI (RingCentral Integration)

**Build ONLY if:** phone_call_rate > 30%

**Architecture:**

```python
# apps/backend/src/api/ai/orchestrator/services/voice_handler.py

from ringcentral import SDK
import asyncio

class VoiceHandler:
    """
    RingCentral voice call handling with real-time transcription
    
    Features:
    - Incoming call webhook
    - Real-time transcription (RingCentral API)
    - AI response generation
    - Text-to-speech (ElevenLabs or RingCentral TTS)
    - Auto-transfer to human (low confidence or complaint)
    - Call summary and transcript storage
    """
    
    def __init__(self, ringcentral_client, orchestrator):
        self.rc = ringcentral_client
        self.orchestrator = orchestrator
    
    async def handle_incoming_call(self, call_data: Dict) -> None:
        """
        Handle incoming customer call
        """
        # 1. Start call recording
        await self.rc.start_recording(call_data["call_id"])
        
        # 2. Stream transcription
        transcript_stream = self.rc.transcribe_realtime(call_data["call_id"])
        
        # 3. Process with AI orchestrator
        async for transcript_chunk in transcript_stream:
            ai_response = await self.orchestrator.process_inquiry(
                message=transcript_chunk,
                channel="phone",
                context={"call_id": call_data["call_id"]}
            )
            
            # 4. Synthesize and play response
            audio = await self.text_to_speech(ai_response["response_text"])
            await self.rc.play_audio(call_data["call_id"], audio)
            
            # 5. Check for transfer conditions
            if self._should_transfer(ai_response):
                await self.transfer_to_agent(call_data["call_id"])
                break
        
        # 6. Save call summary
        await self._save_call_summary(call_data["call_id"])
```

**Cost:** $12,000 development + $0.02/min transcription  
**Timeline:** 3-4 weeks  
**Dependencies:** RingCentral API, ElevenLabs or RingCentral TTS

---

### Feature: Conversation Threading

**Build ONLY if:** follow_up_rate > 50%

**Architecture:**

```python
# apps/backend/src/api/ai/orchestrator/services/conversation_service.py

class ConversationService:
    """
    Track multi-turn conversations with thread_id and history
    
    Phase 1 (Current): Basic conversation tracking
    Phase 3 (If needed): Full threading with context window management
    """
    
    async def create_thread(
        self, 
        customer_id: str, 
        channel: str
    ) -> str:
        """Create new conversation thread"""
        thread = await self.db.conversations.create({
            "customer_id": customer_id,
            "channel": channel,
            "created_at": datetime.utcnow(),
            "status": "active"
        })
        return thread.id
    
    async def add_message(
        self, 
        thread_id: str, 
        message: Dict
    ) -> None:
        """Add message to thread history"""
        await self.db.conversation_messages.create({
            "thread_id": thread_id,
            "role": message["role"],  # user or assistant
            "content": message["content"],
            "timestamp": datetime.utcnow()
        })
    
    async def get_history(
        self, 
        thread_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """Get conversation history for context"""
        messages = await self.db.conversation_messages.find({
            "thread_id": thread_id
        }).sort("timestamp", -1).limit(limit)
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(list(messages))
        ]
```

**Cost:** $3,000  
**Timeline:** 1 week  
**Dependencies:** Conversation table schema, thread_id tracking

---

### Feature: RAG Knowledge Base

**Build ONLY if:** ai_error_rate > 30%

**Architecture:**

```python
# apps/backend/src/api/ai/orchestrator/services/rag_service.py

from pinecone import Pinecone
from openai import AsyncOpenAI

class RAGService:
    """
    Vector database RAG for knowledge retrieval
    
    Knowledge Sources:
    - Company FAQ
    - Menu details
    - Policies (refund, cancellation, allergens)
    - Pricing rules
    - Script examples
    - Seasonal offers
    """
    
    def __init__(self, pinecone_client, openai_client):
        self.pc = pinecone_client
        self.openai = openai_client
        self.index = self.pc.Index("myhibachi-knowledge")
    
    async def index_document(
        self, 
        doc_id: str, 
        content: str, 
        metadata: Dict
    ) -> None:
        """Index document for semantic search"""
        # Generate embedding
        embedding = await self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=content
        )
        
        # Store in Pinecone
        self.index.upsert(vectors=[{
            "id": doc_id,
            "values": embedding.data[0].embedding,
            "metadata": {
                "content": content,
                **metadata
            }
        }])
    
    async def retrieve(
        self, 
        query: str, 
        top_k: int = 3
    ) -> str:
        """Retrieve relevant knowledge"""
        # Generate query embedding
        query_embedding = await self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        
        # Search Pinecone
        results = self.index.query(
            vector=query_embedding.data[0].embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Format results
        knowledge_context = "\n\n".join([
            match.metadata["content"]
            for match in results.matches
        ])
        
        return knowledge_context
```

**Cost:** $5,000 + $20-50/month (Pinecone)  
**Timeline:** 1-2 weeks  
**Dependencies:** Pinecone account, knowledge base content

---

### Feature: Identity Resolution

**Build ONLY if:** multi_channel_rate > 30%

**Architecture:**

```python
# apps/backend/src/api/ai/orchestrator/services/identity_resolver.py

class IdentityResolver:
    """
    Merge customer identity across multiple channels
    
    Match criteria:
    - Email address
    - Phone number
    - Name similarity
    - Social media handles
    """
    
    async def resolve(
        self, 
        message: str, 
        channel: str, 
        context: Dict
    ) -> Optional[str]:
        """
        Resolve customer ID from multiple potential identifiers
        """
        # Extract identifiers
        identifiers = {
            "email": context.get("customer_email"),
            "phone": context.get("customer_phone"),
            "instagram_handle": context.get("instagram_handle"),
            "facebook_id": context.get("facebook_id")
        }
        
        # Search existing customers
        matches = await self._find_matches(identifiers)
        
        if len(matches) == 1:
            return matches[0].id
        elif len(matches) > 1:
            # Merge duplicate profiles
            primary_customer = await self._merge_customers(matches)
            return primary_customer.id
        else:
            # Create new customer profile
            new_customer = await self._create_customer(identifiers)
            return new_customer.id
```

**Cost:** $2,000  
**Timeline:** 3-4 days  
**Dependencies:** Customer merge logic, duplicate detection

---

## 🔒 GIT SAFETY & BACKUP STRATEGY

### Pre-Execution Commit Plan

```bash
# 1. Create feature branch
git checkout -b feature/tool-calling-phase-1

# 2. Commit current state (before any changes)
git add -A
git commit -m "📸 CHECKPOINT: Pre-Tool-Calling State

Current Status:
- ✅ Protein integration complete (Phase 1A)
- ✅ Multi-channel AI working (6 channels)
- ✅ Test suite passing (3/4 protein tests)
- ✅ 100+ MD files (needs consolidation)

Next Steps:
- Tool calling implementation
- Admin dashboard frontend
- Documentation consolidation

Tracked Changes:
- apps/backend/src/api/ai/endpoints/services/multi_channel_ai_handler.py (protein integration)
- test_protein_integration.py (test suite)
- PROTEIN_INTEGRATION_COMPLETE.md
- PHASE_1_PROGRESS_TRACKER.md
- SESSION_SUMMARY.md
"

# 3. Push safety checkpoint
git push origin feature/tool-calling-phase-1

# 4. Tag checkpoint
git tag -a v0.1-pre-tool-calling -m "Checkpoint before tool calling implementation"
git push origin v0.1-pre-tool-calling
```

### During Development Commits

```bash
# Commit after each major step:

# After orchestrator structure
git commit -m "🔧 Add AI orchestrator structure (Phase 1B)"

# After tool implementations
git commit -m "✨ Implement pricing and travel fee tools (Phase 1B)"

# After multi_channel integration
git commit -m "🔗 Integrate orchestrator with multi_channel_ai_handler (Phase 1C)"

# After admin dashboard
git commit -m "🎨 Add admin email review dashboard (Phase 1D)"

# After testing
git commit -m "✅ Tool calling tests passing (Phase 1E)"
```

### Rollback Plan

```bash
# If something breaks, rollback to checkpoint:
git reset --hard v0.1-pre-tool-calling

# Or revert specific commits:
git revert <commit-hash>

# Or create new branch from checkpoint:
git checkout -b feature/tool-calling-attempt-2 v0.1-pre-tool-calling
```

---

## ✅ EXECUTION CHECKLIST

### Phase 0: Pre-Execution (TODAY - 2-3 hours) ⏳ IN PROGRESS

- [x] Update todo list with hybrid strategy
- [x] Create EXECUTION_PLAN document
- [ ] Consolidate MD files (organize into docs/)
- [ ] Analyze file structure (imports, dependencies)
- [ ] Git commit safety checkpoint
- [ ] Create Phase 3 architecture document
- [ ] Create Phase 2 tracking guide

### Phase 1A: Tool Calling Foundation (Day 1-2)

- [ ] Create ai_orchestrator.py structure
- [ ] Create tool base classes
- [ ] Implement pricing_tool.py
- [ ] Implement travel_fee_tool.py
- [ ] Create conversation_service.py (basic)
- [ ] Create placeholder services (RAG, voice, identity)
- [ ] Write unit tests for tools

### Phase 1B: OpenAI Integration (Day 2-3)

- [ ] Define tool schemas
- [ ] Implement OpenAI function calling
- [ ] Implement tool execution logic
- [ ] Implement tool result feedback loop
- [ ] Error handling and logging
- [ ] Integration tests

### Phase 1C: System Integration (Day 3-4)

- [ ] Update multi_channel_ai_handler.py
- [ ] Update customer_booking_ai.py
- [ ] Test with existing protein integration
- [ ] Verify no regressions
- [ ] End-to-end testing

### Phase 1D: Admin Dashboard (Day 5-7)

- [ ] Create EmailReviewDashboard component
- [ ] Create EmailList and EmailCard
- [ ] Create EmailDetailView
- [ ] Create ApprovalActions
- [ ] API integration (connect to email_review.py)
- [ ] Test approve/edit/reject workflow

### Phase 1E: Testing & Deployment (Day 8-9)

- [ ] Comprehensive integration tests
- [ ] Load testing (simulate 50 inquiries)
- [ ] Security audit (tool calling permissions)
- [ ] Documentation update
- [ ] Deployment to staging
- [ ] Production deployment

### Phase 2: Data Collection Setup (Day 10)

- [ ] Create CustomerBehaviorTracker
- [ ] Create Google Sheets template
- [ ] Set up tracking webhooks
- [ ] Create decision dashboard
- [ ] Train admin on tracking

---

## 📊 SUCCESS METRICS

### Phase 1 (Week 2):
- ✅ Tool calling working (0% pricing errors)
- ✅ Admin dashboard deployed
- ✅ Response time <4 hours
- ✅ Admin edit rate <5%

### Phase 2 (Month 2):
- ✅ 50-100 quotes sent and tracked
- ✅ Data collected for all metrics
- ✅ Decision dashboard generated
- ✅ Phase 3 priorities validated

### Phase 3 (Month 3+):
- ✅ Build ONLY validated features
- ✅ ROI >5x for all features
- ✅ Total savings: $30-60K

---

## 🎯 NEXT IMMEDIATE ACTION

**Once you confirm, I will:**

1. ✅ Consolidate MD files (organize docs/)
2. ✅ Create Git safety commit
3. ✅ Create detailed Phase 3 architecture doc
4. ✅ Create Phase 2 tracking guide
5. ✅ Start tool calling implementation

**Estimated Time:** 
- Documentation consolidation: 1 hour
- Git safety: 15 minutes
- Phase 3 doc: 1 hour
- Phase 2 guide: 30 minutes
- **Total: 2-3 hours**

Then we proceed with tool calling implementation (3-4 days).

---

**Ready to proceed?** Say "✅ Yes, execute plan" and I'll start immediately.
