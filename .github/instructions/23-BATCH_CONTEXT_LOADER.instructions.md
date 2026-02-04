---
applyTo: '.github/instructions/**,CURRENT_BATCH_STATUS.md,docs/04-DEPLOYMENT/**'
---

# My Hibachi – Batch Context Loader

**Priority: REFERENCE** – Check this file when starting work on any
batch. **Purpose:** Maps project batches to required instruction files
for efficient context loading.

---

## 🎯 How to Use This Loader

**Before starting work on any batch:**

1. Find your current batch in the table below
2. Load ONLY the instruction files listed for that batch
3. Use the "Quick Load" section for copy-paste file list
4. Check the "Phase Improvements" for optimization tips

---

## 📊 Batch-to-Instruction Mapping

### Always Load (Core - Every Session)

These files are essential for ANY work:

| File                     | Lines | Purpose                       |
| ------------------------ | ----- | ----------------------------- |
| `00-BOOTSTRAP`           | 450   | System bootstrap, quick start |
| `01-CORE_PRINCIPLES`     | 653   | Non-negotiable rules          |
| `02-ARCHITECTURE`        | ~200  | System structure              |
| `03-BRANCH_GIT_WORKFLOW` | ~300  | Git rules                     |
| `22-QUALITY_CONTROL`     | ~400  | Pre-commit checklist          |

**Estimated Core Load: ~2,000 lines (~20K tokens)**

---

### Batch 0: Repository Cleanup

**Status:** ✅ COMPLETE

| Required Files     | Why              |
| ------------------ | ---------------- |
| Core files (above) | Base rules       |
| `06-DOCUMENTATION` | Doc organization |

---

### Batch 1: Core Booking + Security

**Status:** 🟡 IN PROGRESS (Pending DevOps)

| Required Files                  | Why               |
| ------------------------------- | ----------------- |
| Core files (above)              | Base rules        |
| `04-BATCH_DEPLOYMENT`           | Batch context     |
| `07-TESTING_QA`                 | Test requirements |
| `08-FEATURE_FLAGS`              | Flag rules        |
| `19-DATABASE_SCHEMA_MANAGEMENT` | DB migrations     |
| `20-SINGLE_SOURCE_OF_TRUTH`     | SSoT architecture |
| `21-BUSINESS_MODEL`             | Business rules    |

**Optional (load if needed):** | File | Load When |
|------|-----------| | `16-INFRASTRUCTURE_DEPLOYMENT` | Working on
server/deployment | | `09-ROLLBACK_SAFETY` | Working on production |

---

### Batch 2: Payment Processing

**Status:** ⬜ NOT STARTED

| Required Files                  | Why               |
| ------------------------------- | ----------------- |
| Core files (above)              | Base rules        |
| `04-BATCH_DEPLOYMENT`           | Batch context     |
| `07-TESTING_QA`                 | Test requirements |
| `08-FEATURE_FLAGS`              | Flag rules        |
| `19-DATABASE_SCHEMA_MANAGEMENT` | DB migrations     |
| `20-SINGLE_SOURCE_OF_TRUTH`     | SSoT architecture |
| `21-BUSINESS_MODEL`             | Pricing logic     |

**Additional Specs (read when needed):**

- `docs/specs/SMART_SCHEDULING_SYSTEM.md` - If working on scheduling

---

### Batch 3: Core AI

**Status:** ⬜ NOT STARTED

| Required Files              | Why                         |
| --------------------------- | --------------------------- |
| Core files (above)          | Base rules                  |
| `04-BATCH_DEPLOYMENT`       | Batch context               |
| `13-PYTHON_PERFORMANCE`     | Backend optimization        |
| `20-SINGLE_SOURCE_OF_TRUTH` | SSoT for AI responses       |
| `21-BUSINESS_MODEL`         | AI must know business rules |

**Additional Specs (read when needed):**

- `docs/specs/AI_MULTI_LLM_ARCHITECTURE.md` - Full AI architecture
  spec

---

### Batch 4: Communications

**Status:** ⬜ NOT STARTED

| Required Files                 | Why                  |
| ------------------------------ | -------------------- |
| Core files (above)             | Base rules           |
| `04-BATCH_DEPLOYMENT`          | Batch context        |
| `13-PYTHON_PERFORMANCE`        | Backend optimization |
| `16-INFRASTRUCTURE_DEPLOYMENT` | Webhook config       |

---

### Batch 5-6: Advanced AI & Training

**Status:** ⬜ FUTURE

| Required Files          | Why             |
| ----------------------- | --------------- |
| Core files (above)      | Base rules      |
| `04-BATCH_DEPLOYMENT`   | Batch context   |
| `13-PYTHON_PERFORMANCE` | ML optimization |

**Additional Specs (read when needed):**

- `docs/specs/AI_MULTI_LLM_ARCHITECTURE.md` - Multi-LLM ensemble
- `docs/specs/SMART_SCHEDULING_SYSTEM.md` - Chef optimization

---

## 🚀 Quick Load Commands

### For Batch 1 (Current):

```
Read these instruction files:
- 00-BOOTSTRAP
- 01-CORE_PRINCIPLES
- 02-ARCHITECTURE
- 03-BRANCH_GIT_WORKFLOW
- 04-BATCH_DEPLOYMENT
- 07-TESTING_QA
- 19-DATABASE_SCHEMA_MANAGEMENT
- 20-SINGLE_SOURCE_OF_TRUTH
- 21-BUSINESS_MODEL
- 22-QUALITY_CONTROL
```

### For Frontend Work:

```
Additional files for frontend:
- 11-REACT_PERFORMANCE
- 12-CSS_ARCHITECTURE
- 14-MEDIA_OPTIMIZATION
- 15-LIGHTHOUSE_WEB_VITALS
```

### For Backend Work:

```
Additional files for backend:
- 13-PYTHON_PERFORMANCE
```

### For DevOps/Deployment:

```
Additional files for DevOps:
- 16-INFRASTRUCTURE_DEPLOYMENT
- 09-ROLLBACK_SAFETY
```

---

## 📈 Phase Improvements Tracker

### Batch 1 Improvements (Applied)

| Improvement                      | Status         | Impact               |
| -------------------------------- | -------------- | -------------------- |
| Move future specs to docs/specs/ | ✅ Done        | -70KB from context   |
| Scope applyTo for large files    | ⏳ In Progress | -30% per interaction |
| Create batch loader (this file)  | ✅ Done        | Better navigation    |

### Batch 2 Improvements (Planned)

| Improvement                    | Status     | Impact                  |
| ------------------------------ | ---------- | ----------------------- |
| Archive Batch 1 detailed notes | ⬜ Pending | Keep context lean       |
| Add Stripe-specific patterns   | ⬜ Pending | Better payment guidance |

### Batch 3 Improvements (Planned)

| Improvement                  | Status     | Impact                |
| ---------------------------- | ---------- | --------------------- |
| Load AI specs on-demand only | ⬜ Pending | -40KB when not needed |
| Add AI-specific applyTo      | ⬜ Pending | Only for ai/ folder   |

---

## 📊 Context Budget Tracking

**Current Instruction Load:**

| Category              | Files | Est. Lines | Est. Tokens |
| --------------------- | ----- | ---------- | ----------- |
| **Core (always)**     | 5     | ~2,000     | ~20K        |
| **Batch-specific**    | 5-7   | ~2,500     | ~25K        |
| **Optional**          | 2-4   | ~1,500     | ~15K        |
| **TOTAL per session** | 12-16 | ~6,000     | ~60K        |

**Optimization Results:**

- Before: 23 files, 9,081 lines, ~94K tokens
- After: 12-16 files, ~6,000 lines, ~60K tokens
- **Savings: ~36% reduction per session**

---

## 🔄 When Transitioning Batches

When you complete a batch and move to the next:

1. **Update `CURRENT_BATCH_STATUS.md`** with new batch number
2. **Check this file** for new batch's required files
3. **Archive completed batch notes** to `docs/04-DEPLOYMENT/batches/`
4. **Review Phase Improvements** for the new batch
5. **Update this loader** if you discover new patterns

---

## 📁 Archived Specs Location

These files are NOT loaded automatically. Read when needed:

| Spec             | Location                                  | Load When                 |
| ---------------- | ----------------------------------------- | ------------------------- |
| Smart Scheduling | `docs/specs/SMART_SCHEDULING_SYSTEM.md`   | Batch 2+, scheduling work |
| AI Multi-LLM     | `docs/specs/AI_MULTI_LLM_ARCHITECTURE.md` | Batch 3+, AI work         |

---

## 🔧 File ApplyTo Optimization Status

| File                           | Current                           | Optimized To                      | Status              |
| ------------------------------ | --------------------------------- | --------------------------------- | ------------------- |
| `00-BOOTSTRAP`                 | `**`                              | `**`                              | ✅ Keep (essential) |
| `01-CORE_PRINCIPLES`           | `**`                              | `**`                              | ✅ Keep (essential) |
| `11-REACT_PERFORMANCE`         | `apps/customer/**,apps/admin/**`  | Same                              | ✅ Already scoped   |
| `12-CSS_ARCHITECTURE`          | `apps/customer/**,apps/admin/**`  | Same                              | ✅ Already scoped   |
| `13-PYTHON_PERFORMANCE`        | `apps/backend/**`                 | Same                              | ✅ Already scoped   |
| `16-INFRASTRUCTURE_DEPLOYMENT` | `**`                              | `scripts/**,docker/**,.github/**` | ⏳ Pending          |
| `17-SMART_SCHEDULING`          | `**`                              | MOVED to docs/specs/              | ✅ Done             |
| `18-AI_MULTI_LLM`              | `apps/backend/src/services/ai/**` | MOVED to docs/specs/              | ✅ Done             |

---

**Last Updated:** 2025-01-27 **Maintained By:** AI Agent during batch
transitions
