---
applyTo: 'apps/backend/src/services/ai/**'
---

# My Hibachi – Multi-LLM AI Architecture & Smart Router

**Version:** 1.0.0 **Created:** 2024-12-21 **Priority:** REFERENCE –
Use for all AI service development.

---

## 🎯 Executive Summary

My Hibachi uses a **Multi-LLM Ensemble** architecture with 3 providers
working together for optimal quality and cost:

| Tier       | LLM                    | Use For                                       | Why                              |
| ---------- | ---------------------- | --------------------------------------------- | -------------------------------- |
| **Tier 1** | GPT-4o (OpenAI)        | Complex bookings, negotiations, tool calling  | Best reasoning, function calling |
| **Tier 2** | Claude 3.5 (Anthropic) | Complaints, empathy-needed cases, brand voice | Best emotional intelligence      |
| **Tier 3** | Mistral Large/Small    | FAQ, menu questions, simple queries           | 5-10x cheaper, good for simple   |

**Why This Combo:**

- **GPT-4o**: Best at function calling (booking actions, chef
  assignment)
- **Claude 3.5**: Better at empathy, excellent at maintaining brand
  voice
- **Mistral**: 5-10x cheaper than GPT-4, can fine-tune later (open
  weights)

Plus a **Smart Router** that selects the right model based on query
complexity to optimize costs.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MY HIBACHI AI ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Customer Query                                                    │
│        │                                                            │
│        ▼                                                            │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    SMART AI ROUTER                           │   │
│   │                                                              │   │
│   │   Analyze Query Complexity:                                  │   │
│   │   • Query length & keywords                                  │   │
│   │   • Detected intent                                          │   │
│   │   • Customer sentiment                                       │   │
│   │   • Conversation history depth                               │   │
│   │   • Tool calling required?                                   │   │
│   │                                                              │   │
│   │   Complexity Score: SIMPLE | MEDIUM | COMPLEX                │   │
│   └──────────────┬────────────────┬────────────────┬────────────┘   │
│                  │                │                │                │
│          SIMPLE  │        MEDIUM  │        COMPLEX │                │
│          ~$0.001 │        ~$0.005 │        ~$0.050 │                │
│                  │                │                │                │
│                  ▼                ▼                ▼                │
│          ┌───────────┐    ┌───────────┐    ┌───────────────────┐   │
│          │  MISTRAL  │    │  MISTRAL  │    │   FULL ENSEMBLE   │   │
│          │   SMALL   │    │  LARGE 2  │    │                   │   │
│          │   (22B)   │    │  (123B)   │    │  GPT-4o + Claude  │   │
│          │           │    │           │    │  + Mistral Large  │   │
│          │  Fast,    │    │  Balance  │    │                   │   │
│          │  Cheap    │    │  Quality  │    │  Consensus Vote   │   │
│          └───────────┘    └───────────┘    └───────────────────┘   │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    SHADOW LEARNING                           │   │
│   │                                                              │   │
│   │   All responses logged for training your own model:         │   │
│   │   • Llama 3 fine-tuning                                     │   │
│   │   • LoRA training on Colab/Kaggle                           │   │
│   │   • 90% similarity → promote to production                  │   │
│   │                                                              │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 LLM Provider Specifications

### Provider 1: OpenAI (GPT-4)

| Property        | Value                                         |
| --------------- | --------------------------------------------- |
| **Model**       | gpt-4-turbo / gpt-4o                          |
| **Context**     | 128K tokens                                   |
| **Strengths**   | Best overall reasoning, coding, complex tasks |
| **Cost**        | ~$10-30/M tokens                              |
| **When to Use** | Complex queries, tool calling, consensus      |
| **API Key GSM** | `OPENAI_API_KEY`                              |

### Provider 2: Anthropic (Claude)

| Property        | Value                                   |
| --------------- | --------------------------------------- |
| **Model**       | claude-3-5-sonnet                       |
| **Context**     | 200K tokens                             |
| **Strengths**   | Nuanced responses, safety, long context |
| **Cost**        | ~$15/M tokens                           |
| **When to Use** | Customer complaints, sensitive topics   |
| **API Key GSM** | `ANTHROPIC_API_KEY`                     |

### Provider 3: Mistral AI

| Property        | Value                                                   |
| --------------- | ------------------------------------------------------- |
| **Model**       | mistral-large-2 (flagship)                              |
| **Context**     | 128K tokens                                             |
| **Strengths**   | Human-level reasoning, function calling, cost-effective |
| **Cost**        | ~$8/M tokens (input) / $24/M (output)                   |
| **When to Use** | Tool calling, medium complexity, consensus              |
| **API Key GSM** | `MISTRAL_API_KEY`                                       |
| **MMLU Score**  | 84.0 (vs GPT-4's 86.4)                                  |

#### Mistral Model Hierarchy

| Model               | Parameters    | Best For                    | Cost |
| ------------------- | ------------- | --------------------------- | ---- |
| **Mistral Large 2** | 123B          | Complex reasoning, tool use | $8/M |
| **Mixtral 8x22B**   | 141B (sparse) | Balance quality/speed       | $2/M |
| **Mistral Small**   | 22B           | Simple queries, fast        | $1/M |
| **Mistral Nemo**    | 12B           | Edge/local deployment       | Free |

---

## 🔀 Smart AI Router Implementation

### Complexity Classification

```python
# apps/backend/src/services/ai/smart_router.py

from enum import Enum
from typing import Literal
from pydantic import BaseModel

class QueryComplexity(str, Enum):
    SIMPLE = "simple"      # FAQ, hours, basic info
    MEDIUM = "medium"      # Booking details, menu questions
    COMPLEX = "complex"    # Complaints, booking changes, multi-step

class ComplexityScore(BaseModel):
    level: QueryComplexity
    score: float  # 0.0 - 1.0
    reasoning: str
    recommended_provider: str

class SmartAIRouter:
    """Route queries to optimal LLM based on complexity."""

    # Keywords indicating complexity levels
    SIMPLE_KEYWORDS = {
        "hours", "open", "close", "location", "address", "phone",
        "website", "menu", "price", "cost", "how much", "what is",
        "do you", "can you", "available"
    }

    COMPLEX_KEYWORDS = {
        "complaint", "frustrated", "angry", "problem", "issue",
        "cancel", "refund", "change", "reschedule", "manager",
        "supervisor", "lawyer", "attorney", "dispute", "disappointed"
    }

    TOOL_CALLING_KEYWORDS = {
        "book", "schedule", "reserve", "create", "update", "modify",
        "change date", "change time", "add guest", "remove guest"
    }

    async def classify_query(
        self,
        query: str,
        conversation_history: list = None,
        customer_sentiment: float = 0.5
    ) -> ComplexityScore:
        """Classify query complexity for optimal routing."""

        query_lower = query.lower()
        word_count = len(query.split())
        history_depth = len(conversation_history or [])

        # Score components
        length_score = min(word_count / 50, 1.0)  # Longer = more complex

        # Keyword scoring
        simple_matches = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in query_lower)
        complex_matches = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in query_lower)
        tool_matches = sum(1 for kw in self.TOOL_CALLING_KEYWORDS if kw in query_lower)

        # Sentiment impact (negative = more complex)
        sentiment_score = 1.0 - customer_sentiment  # 0.0-1.0

        # History impact (deeper = more complex)
        history_score = min(history_depth / 10, 1.0)

        # Calculate final complexity
        complexity_score = (
            length_score * 0.15 +
            (complex_matches / 5) * 0.30 +
            (tool_matches / 3) * 0.20 +
            sentiment_score * 0.20 +
            history_score * 0.15
        )

        # Determine level
        if complexity_score < 0.3:
            level = QueryComplexity.SIMPLE
            provider = "mistral_small"
        elif complexity_score < 0.6:
            level = QueryComplexity.MEDIUM
            provider = "mixtral_8x22b"
        else:
            level = QueryComplexity.COMPLEX
            provider = "ensemble"

        # Override: tool calling always needs capable model
        if tool_matches > 0:
            level = QueryComplexity.MEDIUM
            provider = "mistral_large"  # Best function calling

        # Override: negative sentiment escalates complexity
        if complex_matches >= 2 or customer_sentiment < 0.3:
            level = QueryComplexity.COMPLEX
            provider = "ensemble"

        return ComplexityScore(
            level=level,
            score=complexity_score,
            reasoning=f"Length: {length_score:.2f}, Complex keywords: {complex_matches}, "
                      f"Tool keywords: {tool_matches}, Sentiment: {sentiment_score:.2f}",
            recommended_provider=provider
        )

    async def route_query(
        self,
        query: str,
        conversation_history: list = None,
        customer_sentiment: float = 0.5
    ) -> str:
        """Route query and return response from optimal provider."""

        complexity = await self.classify_query(
            query, conversation_history, customer_sentiment
        )

        if complexity.recommended_provider == "mistral_small":
            return await self.mistral_small.generate(query)
        elif complexity.recommended_provider == "mixtral_8x22b":
            return await self.mixtral.generate(query)
        elif complexity.recommended_provider == "mistral_large":
            return await self.mistral_large.generate(query)
        else:  # ensemble
            return await self.ensemble.generate_with_consensus(query)
```

### Cost Tracking

```python
# apps/backend/src/services/ai/cost_tracker.py

from datetime import datetime
from decimal import Decimal

class AICostTracker:
    """Track AI API costs per conversation and aggregate."""

    COST_PER_1K_TOKENS = {
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
        "mistral-large-2": {"input": 0.008, "output": 0.024},
        "mixtral-8x22b": {"input": 0.002, "output": 0.006},
        "mistral-small": {"input": 0.001, "output": 0.003},
    }

    async def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        conversation_id: str
    ) -> dict:
        """Track token usage and cost for a request."""

        costs = self.COST_PER_1K_TOKENS.get(model, {"input": 0.01, "output": 0.03})

        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        total_cost = input_cost + output_cost

        # Store in database
        await self.db.execute(
            """
            INSERT INTO ai.usage_tracking
            (conversation_id, model, input_tokens, output_tokens,
             input_cost, output_cost, total_cost, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            conversation_id, model, input_tokens, output_tokens,
            input_cost, output_cost, total_cost, datetime.utcnow()
        )

        return {
            "model": model,
            "tokens": {"input": input_tokens, "output": output_tokens},
            "cost_usd": round(total_cost, 6)
        }

    async def get_monthly_summary(self) -> dict:
        """Get monthly cost summary by model."""

        result = await self.db.fetch(
            """
            SELECT
                model,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_cost) as total_cost,
                COUNT(*) as request_count
            FROM ai.usage_tracking
            WHERE created_at >= date_trunc('month', CURRENT_DATE)
            GROUP BY model
            ORDER BY total_cost DESC
            """
        )

        return {
            "period": "current_month",
            "by_model": [dict(row) for row in result],
            "total_cost": sum(row["total_cost"] for row in result)
        }
```

---

## 🌟 Mistral Provider Implementation

```python
# apps/backend/src/services/ai/providers/mistral.py

import httpx
from typing import Optional, List
from pydantic import BaseModel


class MistralMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str


class MistralProvider:
    """Mistral AI provider for the Multi-LLM ensemble."""

    BASE_URL = "https://api.mistral.ai/v1"

    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.default_model = "mistral-large-latest"  # Mistral Large 2

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[List[dict]] = None
    ) -> dict:
        """Generate a response from Mistral."""

        model = model or self.default_model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add function calling if tools provided
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        usage = data["usage"]

        return {
            "content": choice["message"]["content"],
            "tool_calls": choice["message"].get("tool_calls"),
            "model": model,
            "usage": {
                "input_tokens": usage["prompt_tokens"],
                "output_tokens": usage["completion_tokens"]
            },
            "finish_reason": choice["finish_reason"]
        }

    async def generate_with_function_calling(
        self,
        prompt: str,
        functions: List[dict],
        model: str = "mistral-large-latest"
    ) -> dict:
        """Generate with function/tool calling support."""

        # Convert functions to Mistral tool format
        tools = [
            {
                "type": "function",
                "function": func
            }
            for func in functions
        ]

        response = await self.generate(
            prompt=prompt,
            model=model,
            tools=tools
        )

        # Parse tool calls if any
        if response.get("tool_calls"):
            tool_calls = []
            for tc in response["tool_calls"]:
                tool_calls.append({
                    "id": tc["id"],
                    "function": tc["function"]["name"],
                    "arguments": json.loads(tc["function"]["arguments"])
                })
            response["parsed_tool_calls"] = tool_calls

        return response


# Convenience instances for different model sizes
class MistralSmall(MistralProvider):
    """Fast, cheap Mistral for simple queries."""
    def __init__(self):
        super().__init__()
        self.default_model = "mistral-small-latest"


class MistralMixtral(MistralProvider):
    """Balanced Mixtral 8x22B for medium complexity."""
    def __init__(self):
        super().__init__()
        self.default_model = "open-mixtral-8x22b"


class MistralLarge(MistralProvider):
    """Full Mistral Large 2 for complex reasoning."""
    def __init__(self):
        super().__init__()
        self.default_model = "mistral-large-latest"
```

---

## 🤝 Ensemble Consensus Engine

```python
# apps/backend/src/services/ai/ensemble.py

from typing import List, Dict
import asyncio
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class EnsembleConsensusEngine:
    """Multi-LLM ensemble with consensus voting (3 providers)."""

    def __init__(self):
        self.providers = {
            "gpt4o": OpenAIProvider(),
            "claude": AnthropicProvider(),
            "mistral": MistralLarge()
        }
        self.embedding_model = OpenAIEmbeddings()  # For similarity

    async def generate_with_consensus(
        self,
        prompt: str,
        system_prompt: str = None,
        min_agreement: float = 0.7
    ) -> dict:
        """Generate responses from all providers and find consensus."""

        # Parallel generation from all providers
        tasks = [
            provider.generate(prompt, system_prompt=system_prompt)
            for provider in self.providers.values()
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        valid_responses = []
        for name, response in zip(self.providers.keys(), responses):
            if isinstance(response, Exception):
                logger.warning(f"Provider {name} failed: {response}")
            else:
                valid_responses.append({
                    "provider": name,
                    "content": response["content"],
                    "usage": response.get("usage", {})
                })

        if len(valid_responses) < 2:
            # Fallback to single response
            return valid_responses[0] if valid_responses else {
                "content": "I'm sorry, I couldn't process that request.",
                "provider": "fallback"
            }

        # Calculate consensus
        consensus = await self._calculate_consensus(valid_responses)

        return {
            "content": consensus["best_response"],
            "provider": "ensemble",
            "consensus_score": consensus["agreement_score"],
            "individual_responses": valid_responses,
            "voting_details": consensus["votes"]
        }

    async def _calculate_consensus(
        self,
        responses: List[Dict]
    ) -> dict:
        """Calculate consensus among responses using embeddings."""

        # Get embeddings for all responses
        contents = [r["content"] for r in responses]
        embeddings = await self.embedding_model.embed_batch(contents)

        # Calculate pairwise similarity
        similarity_matrix = cosine_similarity(embeddings)

        # Score each response by average similarity to others
        scores = []
        for i in range(len(responses)):
            avg_similarity = np.mean([
                similarity_matrix[i][j]
                for j in range(len(responses))
                if i != j
            ])
            scores.append({
                "provider": responses[i]["provider"],
                "agreement_score": avg_similarity,
                "response": responses[i]["content"]
            })

        # Sort by agreement score
        scores.sort(key=lambda x: x["agreement_score"], reverse=True)

        # Best response is the one most similar to others (consensus)
        best = scores[0]

        return {
            "best_response": best["response"],
            "best_provider": best["provider"],
            "agreement_score": best["agreement_score"],
            "votes": scores
        }
```

---

## 📊 Cost Optimization Targets

| Scenario          | Before (All GPT-4) | After (Smart Router)   | Savings |
| ----------------- | ------------------ | ---------------------- | ------- |
| Simple FAQ        | $0.05              | $0.001 (Mistral Small) | **98%** |
| Menu question     | $0.05              | $0.005 (Mixtral)       | **90%** |
| Booking change    | $0.05              | $0.008 (Mistral Large) | **84%** |
| Complex complaint | $0.05              | $0.050 (Ensemble)      | **0%**  |
| **Monthly Avg**   | ~$500              | ~$150                  | **70%** |

---

## 🔧 Environment Configuration

```env
# AI Provider API Keys (in GSM)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
XAI_API_KEY=xai-...
MISTRAL_API_KEY=...

# Smart Router Configuration
AI_ROUTER_ENABLED=true
AI_ROUTER_DEFAULT_PROVIDER=mistral_small
AI_ROUTER_COMPLEX_THRESHOLD=0.6
AI_ROUTER_ENSEMBLE_THRESHOLD=0.8

# Cost Tracking
AI_COST_TRACKING_ENABLED=true
AI_COST_ALERT_THRESHOLD_DAILY=50
AI_COST_ALERT_THRESHOLD_MONTHLY=500

# Shadow Learning
AI_SHADOW_LEARNING_ENABLED=true
AI_SHADOW_MODEL=llama3:8b
AI_SHADOW_SIMILARITY_THRESHOLD=0.9
```

---

## 📁 File Structure

```
apps/backend/src/services/ai/
├── __init__.py
├── providers/
│   ├── __init__.py
│   ├── base.py              # Base provider interface
│   ├── openai.py            # GPT-4o provider (Tier 1)
│   ├── anthropic.py         # Claude 3.5 provider (Tier 2)
│   └── mistral.py           # Mistral provider (Tier 3)
├── smart_router.py          # Query complexity router
├── ensemble.py              # Multi-LLM consensus engine (3 models)
├── cost_tracker.py          # Usage and cost tracking
├── shadow_learning.py       # Train your own model
└── agents/
    ├── __init__.py
    ├── base_agent.py
    ├── lead_nurturing.py
    ├── customer_care.py
    ├── operations.py
    ├── knowledge.py
    ├── distance.py
    ├── menu.py
    └── allergen.py
```

---

## 🚀 Implementation Timeline

| Phase     | Task                      | Effort     | Batch   |
| --------- | ------------------------- | ---------- | ------- |
| 1         | Add MistralProvider class | 2 hrs      | Batch 3 |
| 2         | Add to ensemble           | 1 hr       | Batch 3 |
| 3         | Implement SmartRouter     | 4 hrs      | Batch 3 |
| 4         | Add cost tracking         | 3 hrs      | Batch 3 |
| 5         | Build cost dashboard UI   | 4 hrs      | Batch 5 |
| 6         | Optimize routing rules    | 2 hrs      | Batch 5 |
| **Total** |                           | **16 hrs** |         |

---

## 🎓 Free-Tier Training Strategy (Post Batch 6)

### Overview

Before investing in GPU servers, use **FREE** cloud GPU platforms to
train custom LoRA adapters for local models.

### Free GPU Platforms for Training

| Platform         | GPU          | Free Hours       | VRAM | Best For               |
| ---------------- | ------------ | ---------------- | ---- | ---------------------- |
| **Kaggle**       | P100 or T4x2 | 30 hrs/week      | 16GB | LoRA training          |
| **Google Colab** | T4           | Limited sessions | 16GB | Quick experiments      |
| **HF ZeroGPU**   | H200         | Dynamic          | 70GB | Inference testing      |
| **Colab Pro**    | A100         | 100 units        | 40GB | Full training ($10/mo) |

### Target Models for Fine-Tuning

| Model           | Parameters | License       | Use Case                       | Laptop OK?    |
| --------------- | ---------- | ------------- | ------------------------------ | ------------- |
| **Qwen3**       | 32B        | Apache 2.0 ✅ | General chat, function calling | ❌ GPU needed |
| **DeepSeek R1** | 32B        | MIT ✅        | Complex reasoning              | ❌ GPU needed |
| **Phi-4**       | 14B        | MIT ✅        | Fast FAQ responses             | ✅ Quantized  |
| **Qwen3**       | 8B         | Apache 2.0 ✅ | Smaller tasks                  | ✅ 16GB RAM   |
| **DeepSeek R1** | 7B         | MIT ✅        | Light reasoning                | ✅ 8GB RAM    |

### Training Workflow (FREE TIER + LAPTOP)

```
1. COLLECT DATA (Batch 3-6)
   └─ Shadow learning collects 50,000+ teacher-student pairs
   └─ API-based LLMs (OpenAI, Mistral) handle production

2. PREPARE DATA
   └─ Export conversations
   └─ Remove PII (names, phones, addresses)
   └─ Format as instruction/response pairs

3. TRAIN LOCALLY ON LAPTOP (for small models)
   └─ Phi-4 14B Q4, Qwen3 8B, DeepSeek R1 7B
   └─ Use Unsloth or PEFT for LoRA training
   └─ 16GB RAM minimum, GPU optional

4. OR UPLOAD TO KAGGLE (for large models)
   └─ Create Kaggle dataset from cleaned data
   └─ 30 hrs/week free GPU time
   └─ Train LoRA adapter for 32B models

5. DOWNLOAD ADAPTER
   └─ Download LoRA weights (~100-500MB)

6. TEST LOCALLY
   └─ Load base model + LoRA in Ollama on laptop
   └─ Compare responses to GPT-4

7. EVALUATE
   └─ If 90%+ similarity → deploy to VPS
   └─ If <90% → collect more data, retrain
```

### $300/Month API Cost Threshold Rule

```
IF monthly API costs < $300:
   └─ STAY ON API (OpenAI, Mistral, Claude)
   └─ Continue shadow learning data collection
   └─ Train locally on laptop for testing

IF monthly API costs > $300:
   └─ Consider renting GPU server (~$223/mo)
   └─ Deploy fine-tuned model for production
   └─ Savings = API costs - GPU rental = PROFIT

BREAK-EVEN MATH:
   $300 API costs - $223 GPU rental = $77/mo savings
   PLUS: Unlimited local inference (no per-token cost)
```

### When to Upgrade to Paid GPU

Only invest in GPU server ($200-300/mo) when:

| Trigger                    | Description                            |
| -------------------------- | -------------------------------------- |
| **API costs > $300/mo**    | Break-even point for GPU rental        |
| **Free tier insufficient** | Training runs exceed 30 hrs/week       |
| **Production inference**   | Need 24/7 local model for cost savings |
| **Training volume**        | Dataset exceeds 100K pairs             |

### Cost Comparison: Training Options

| Option           | Monthly Cost | Best For                       |
| ---------------- | ------------ | ------------------------------ |
| Your Laptop      | $0           | Small models (7B-14B), testing |
| Kaggle Free      | $0           | LoRA training (30 hrs/week)    |
| Colab Pro        | $10          | More GPU time, A100 access     |
| Vast.ai RTX 4090 | $223         | 24/7 inference + training      |
| RunPod A100      | $857         | Enterprise training            |

**Recommendation:** Laptop testing → Kaggle FREE → Colab Pro ($10) →
Vast.ai ($223) when API costs > $300/mo.

---

## 🔗 Related Documentation

- [17-SMART_SCHEDULING_SYSTEM.instructions.md](./17-SMART_SCHEDULING_SYSTEM.instructions.md)
- [16-INFRASTRUCTURE_DEPLOYMENT.instructions.md](./16-INFRASTRUCTURE_DEPLOYMENT.instructions.md)
  – GPU migration plan
- [Mistral AI Documentation](https://docs.mistral.ai/)
- [OpenAI Documentation](https://platform.openai.com/docs)
- [Anthropic Documentation](https://docs.anthropic.com/)

---

**Document Status:** ✅ READY FOR IMPLEMENTATION
