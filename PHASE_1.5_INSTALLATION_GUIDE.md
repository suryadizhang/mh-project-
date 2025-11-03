# 🚀 Phase 1.5: Shadow Learning - Installation & Testing Guide

## ✅ What's Been Completed

**Commit: cceb84a**

### Infrastructure Created:
1. **Shadow Learning Module** (`apps/backend/src/api/ai/shadow/`)
   - ✅ `local_model.py` - Ollama/Llama-3 integration
   - ✅ `models.py` - Database models (AITutorPair, AIRLHFScore, AIExportJob)
   - ✅ `tutor_logger.py` - Records teacher-student pairs
   - ✅ `similarity_evaluator.py` - Compares responses using embeddings

2. **API Endpoints** (`apps/backend/src/api/v1/endpoints/shadow_learning.py`)
   - ✅ GET `/api/v1/ai/shadow/health` - System health check
   - ✅ GET `/api/v1/ai/shadow/model-info` - Llama-3 details
   - ✅ POST `/api/v1/ai/shadow/test-generate` - Test local model
   - ✅ GET `/api/v1/ai/shadow/stats` - Training statistics
   - ✅ GET `/api/v1/ai/shadow/training-data` - Preview pairs
   - ✅ GET `/api/v1/ai/shadow/readiness` - Deployment check

3. **Test Suite**
   - ✅ `test_cost_monitoring_api.py` - Tests all 6 cost monitoring endpoints

---

## 📋 Next Steps (Manual Actions Required)

### Step 1: Install Ollama ⏳ IN PROGRESS

**Download & Install:**

1. Visit: https://ollama.ai/download/windows
2. Download `OllamaSetup.exe`
3. Run the installer
4. Follow installation wizard
5. Ollama will be added to PATH automatically

**Verify Installation:**

Open a **NEW** PowerShell window (to refresh PATH):
```powershell
ollama --version
```

Expected output: `ollama version 0.x.x`

---

### Step 2: Download Llama-3 Model

Once Ollama is installed, download the model:

```powershell
# Download Llama-3-8B-Instruct (4.7 GB)
ollama pull llama3
```

**Verify Download:**
```powershell
# List installed models
ollama list
```

**Test Inference:**
```powershell
# Quick test
ollama run llama3 "What is your pricing?"
```

Expected: Llama-3 should respond that it's free and open-source.

---

### Step 3: Start Backend Server

Make sure your backend is running:

```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"

# Activate virtual environment if needed
# .venv\Scripts\Activate.ps1

# Start FastAPI server
python -m uvicorn src.main:app --reload --port 8000
```

---

### Step 4: Test Shadow Learning Health

Once Ollama is installed and backend is running:

**Test Health Check:**
```powershell
curl http://localhost:8000/api/v1/ai/shadow/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "ollama_url": "http://localhost:11434",
  "models_available": ["llama3"],
  "llama3_installed": true,
  "timestamp": "2025-01-15T..."
}
```

**If Unhealthy:**
```json
{
  "status": "unhealthy",
  "error": "Ollama service not reachable",
  "recommendation": "Please install Ollama and run 'ollama pull llama3'"
}
```

---

### Step 5: Test Local Model Generation

**Test via API:**
```powershell
curl -X POST http://localhost:8000/api/v1/ai/shadow/test-generate `
  -H "Content-Type: application/json" `
  -d '{\"prompt\": \"What are your business hours?\"}'
```

**Expected Response:**
```json
{
  "success": true,
  "response": "Our business hours are...",
  "model": "llama3",
  "total_duration_ms": 1234,
  "response_time_ms": 1250,
  "eval_count": 50,
  "prompt_eval_count": 20,
  "error": null
}
```

---

### Step 6: Test Cost Monitoring Dashboard

**Run Test Suite:**
```powershell
cd "c:\Users\surya\projects\MH webapps"
python test_cost_monitoring_api.py
```

**Expected Output:**
```
🧪 AI COST MONITORING API TEST SUITE
====================================
Testing against: http://localhost:8000/api/v1

✅ PASS - Cost Summary
✅ PASS - Cost Trend
✅ PASS - Hourly Costs
✅ PASS - Cost Alerts
✅ PASS - Top Expensive Queries
✅ PASS - Set Budget

6/6 tests passed (100.0%)
🎉 All tests passed!
```

**Manual API Tests:**

```powershell
# 1. Cost Summary
curl http://localhost:8000/api/v1/ai/costs/summary

# 2. Cost Trend (last 7 days)
curl http://localhost:8000/api/v1/ai/costs/trend?days=7

# 3. Hourly Breakdown (today)
curl http://localhost:8000/api/v1/ai/costs/hourly

# 4. Cost Alerts
curl http://localhost:8000/api/v1/ai/costs/alerts

# 5. Top Expensive Queries
curl "http://localhost:8000/api/v1/ai/costs/top-expensive?limit=10"

# 6. Set Budget
curl -X POST "http://localhost:8000/api/v1/ai/costs/set-budget?budget_usd=150"
```

---

### Step 7: Create Database Migration

**Generate Migration:**
```powershell
cd apps/backend

# Generate migration file
alembic revision -m "add_shadow_learning_tables"
```

**Edit Migration File:**

Location: `apps/backend/alembic/versions/xxx_add_shadow_learning_tables.py`

Add upgrade:
```python
def upgrade():
    # Import models
    from api.ai.shadow.models import AITutorPair, AIRLHFScore, AIExportJob
    
    # Create tables
    AITutorPair.__table__.create(op.get_bind())
    AIRLHFScore.__table__.create(op.get_bind())
    AIExportJob.__table__.create(op.get_bind())
```

**Run Migration:**
```powershell
alembic upgrade head
```

---

### Step 8: Check Deployment Readiness

**Test Readiness Endpoint:**
```powershell
curl http://localhost:8000/api/v1/ai/shadow/readiness
```

**Expected Response:**
```json
{
  "ready_for_deployment": false,
  "checklist": {
    "ollama_installed": true,
    "sufficient_training_data": false,
    "high_quality_responses": false
  },
  "details": {
    "ollama_status": "healthy",
    "llama3_installed": true,
    "total_pairs_collected": 0,
    "minimum_pairs_required": 100,
    "average_similarity": 0.0,
    "target_similarity": 0.85
  },
  "next_steps": [
    "Collect 100 more training pairs"
  ]
}
```

---

## 🎯 Success Criteria

### Phase 1.5.1: Infrastructure (✅ Complete)
- ✅ Shadow Learning module created
- ✅ Database models defined
- ✅ Local model service implemented
- ✅ API endpoints created
- ✅ Test suite written

### Phase 1.5.2: Ollama Setup (⏳ In Progress)
- ⏳ Ollama installed
- ⏳ Llama-3 model downloaded
- ⏳ Health check passing
- ⏳ Test generation working

### Phase 1.5.3: Data Collection (🔜 Next)
- 🔜 Database migration run
- 🔜 Start collecting teacher-student pairs
- 🔜 Reach 100+ pairs
- 🔜 Achieve ≥0.85 average similarity

---

## 📊 Cost Monitoring Dashboard

### Endpoints Available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ai/costs/summary` | GET | Monthly/daily costs + projections |
| `/api/v1/ai/costs/trend` | GET | Historical trends (7/30/90 days) |
| `/api/v1/ai/costs/hourly` | GET | Hour-by-hour breakdown |
| `/api/v1/ai/costs/alerts` | GET | Real-time budget alerts |
| `/api/v1/ai/costs/top-expensive` | GET | Most expensive queries |
| `/api/v1/ai/costs/set-budget` | POST | Update monthly budget |

### Budget Thresholds:

| Level | Threshold | Severity |
|-------|-----------|----------|
| Hourly | $2 | Critical |
| Daily | $10 | Warning |
| Monthly | $100 | Warning (80%) / Critical (100%) |

---

## 🔧 Troubleshooting

### Ollama Not Found
**Problem:** `ollama: command not found`

**Solution:**
1. Make sure you installed Ollama
2. Open a **NEW** PowerShell window
3. Try: `C:\Users\<username>\AppData\Local\Programs\Ollama\ollama.exe --version`
4. If found, PATH might not be refreshed

### Ollama Service Not Running
**Problem:** `Ollama service not reachable`

**Solution:**
1. Check if Ollama is running: Task Manager → Services
2. Restart Ollama: `ollama serve`
3. Verify: `curl http://localhost:11434/api/tags`

### Model Not Installed
**Problem:** `llama3_installed: false`

**Solution:**
```powershell
ollama pull llama3
ollama list  # Verify
```

### Cost Monitoring Returns Empty Data
**Problem:** All costs show $0.00

**Solution:**
- This is normal if you haven't made any OpenAI API calls yet
- Make some AI chat requests first
- Check AIUsage table in database

---

## 📈 Next Development Steps

Once Ollama is set up:

1. **Integrate Shadow Mode into Chat Service**
   - Modify `chat_service.py` to call both OpenAI and Llama-3
   - Log responses to AITutorPair table
   - Calculate similarity scores

2. **Start Collecting Training Data**
   - Run for 1-2 weeks in shadow mode
   - Target: 1,000+ pairs
   - Monitor similarity scores

3. **Implement RLHF Dashboard**
   - Admin interface to review responses
   - Score responses (1-5 scale)
   - Approve for production use

4. **Export Training Data**
   - Generate JSONL files for fine-tuning
   - Filter high-quality pairs (≥0.85 similarity)
   - Prepare for model training

5. **Deploy to Production**
   - When similarity ≥ 0.85 consistently
   - Gradually route traffic to local model
   - Monitor customer satisfaction

---

## 🎉 Current Status

✅ **Infrastructure**: 100% Complete  
⏳ **Ollama Installation**: Awaiting manual installation  
🔜 **Data Collection**: Ready to start  
🔜 **Production Deployment**: Pending data collection

**Ready to continue?** Install Ollama now and test the system!
