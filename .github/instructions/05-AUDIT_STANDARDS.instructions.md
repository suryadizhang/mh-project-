---
applyTo: '**/audit/**,**/test*/**'
---

# My Hibachi – Audit Standards

> **Load On-Demand:** This file only loads for audit/test files. For
> manual audit, reference this file explicitly. (A–H Deep Audit)

**Priority: HIGH** – Use when auditing, checking, or verifying code.

---

## 🎯 When to Use This

Apply A–H audit when user asks to:

- Audit code
- Check logic
- Verify correctness
- Find bugs
- Stress test
- "Check deeper"
- "Is this correct?"
- "Are you sure?"

---

## 🔴 Core Principles

1. **Never incremental** → Apply ALL A–H together
2. **Never assume safe** → Verify everything
3. **Always test edges** → Edge cases break production
4. **Classify findings** → Critical / High / Medium / Low

---

## 📋 The 8 Audit Techniques

### A. Static Analysis (Line-by-Line)

Check for:

| Issue               | Example                                |
| ------------------- | -------------------------------------- |
| Syntax errors       | Missing brackets, typos                |
| Type mismatches     | `string` vs `number`                   |
| Missing imports     | `from models import X` – does X exist? |
| Dead code           | Unreachable branches                   |
| Shadowed variables  | Same name in nested scope              |
| Bad naming          | `x`, `data`, `temp`                    |
| Missing validation  | User input not checked                 |
| Hidden side effects | Function modifies global state         |
| Improper async      | Missing await, race conditions         |
| Debug leftovers     | `console.log`, `print()` statements    |

---

### B. Runtime Simulation

Mentally execute the code:

| Issue                 | Example                            |
| --------------------- | ---------------------------------- |
| Datetime/timezone     | `datetime.now()` without timezone  |
| None/null propagation | `user.name` when user is None      |
| Type coercion         | `"5" + 5` in JavaScript            |
| String formatting     | f-string with missing variable     |
| Precision loss        | Float arithmetic errors            |
| Uncaught exceptions   | Division by zero                   |
| Missing returns       | Function returns None unexpectedly |
| Control flow errors   | Wrong if/else logic                |

---

### C. Concurrency & Transaction Safety

Check for:

| Issue                      | Example                                   |
| -------------------------- | ----------------------------------------- |
| Race conditions (TOCTOU)   | Check availability → Gap → Create booking |
| Shared state without locks | Multiple writers to same variable         |
| Missing DB transactions    | Partial writes on error                   |
| Missing SELECT FOR UPDATE  | Concurrent booking creation               |
| Missing optimistic locking | No version column                         |
| Non-idempotent operations  | Running twice causes problems             |

**Real Example:**

```python
# 🔴 RACE CONDITION
available = check_availability(date, time)  # Check
# ... 80ms gap ...
if available:
    create_booking(date, time)  # Use (another request may have booked)
```

---

### D. Data Flow Tracing

Trace: **input → processing → output**

| Check              | Question                       |
| ------------------ | ------------------------------ |
| Type preservation  | Does type change unexpectedly? |
| Shape consistency  | Is data structure maintained?  |
| Value ranges       | Are bounds checked?            |
| Mutations          | Is data modified in place?     |
| Missing validation | Is input sanitized?            |

---

### E. Error Path & Exception Handling

Validate:

| Check                  | Requirement                  |
| ---------------------- | ---------------------------- |
| try/except correctness | Catches right exceptions     |
| Specific exceptions    | Not broad `except Exception` |
| Logging                | No sensitive info logged     |
| Fallback behavior      | Graceful degradation         |
| No silent failures     | Errors are visible           |

---

### F. Dependency & Enum Validation

Confirm:

| Check                 | Example                                     |
| --------------------- | ------------------------------------------- |
| Imports exist         | `from models import CustomerTonePreference` |
| Enums defined         | `ErrorCode.PAYMENT_AMOUNT_INVALID` exists?  |
| No magic strings      | Use enums, not `"pending"`                  |
| Env vars documented   | All required vars listed                    |
| Version compatibility | Python 3.11+, Node 18+                      |

---

### G. Business Logic Validation (CRITICAL)

Check these high-risk areas:

| Area          | What to Verify                    |
| ------------- | --------------------------------- |
| Pricing       | Formulas, discounts, fees         |
| Travel fee    | Distance calculation, thresholds  |
| Booking logic | Availability, conflicts, capacity |
| Scheduling    | Time slots, chef assignment       |
| Deposits      | Amounts, timing, refunds          |
| Cancellation  | Policies, fees, notifications     |
| Guest counts  | Min/max, pricing impact           |

Look for:

- Wrong formulas
- Missing edge cases
- Over/under charging
- Double-booking
- Invalid states

---

### H. Helper/Utility Analysis

Check private/utility methods:

| Check                | Why                                      |
| -------------------- | ---------------------------------------- |
| Parameter validation | `_private_method(None)` handled?         |
| Error handling       | try-except around `.split()`, `.parse()` |
| Hidden side effects  | Does it modify global state?             |
| Naming clarity       | `_slots_overlap` vs `_process`           |
| Testability          | Can it be unit tested?                   |
| Edge cases           | Empty strings, None, invalid formats     |

---

## 📊 Required Audit Output Format

Every audit MUST include:

### 1. Techniques Applied

```
- [x] A. Static Analysis
- [x] B. Runtime Simulation
- [x] C. Concurrency & Transaction Safety
- [x] D. Data Flow Tracing
- [x] E. Error Path & Exception Handling
- [x] F. Dependency & Enum Validation
- [x] G. Business Logic Validation
- [x] H. Helper/Utility Analysis
```

### 2. Findings by Severity

| Severity    | Criteria                                 |
| ----------- | ---------------------------------------- |
| 🔴 CRITICAL | Production-breaking, data loss, security |
| 🟠 HIGH     | Major functionality broken, bad UX       |
| 🟡 MEDIUM   | Minor bugs, edge cases                   |
| 🟢 LOW      | Code quality, optimization               |

### 3. For Each Finding:

- **What:** Description of issue
- **Why:** Business/technical impact
- **Where:** File and line number
- **Fix:** Exact code solution

### 4. Readiness Classification:

| Status              | Meaning                         |
| ------------------- | ------------------------------- |
| ✅ Production-ready | All A–H passed, tests passing   |
| ⚠️ Dev-only         | Missing tests, has TODOs        |
| 🔴 Dangerous        | Race conditions, data loss risk |
| 🛑 Needs rewrite    | Architectural problems          |

---

## 🔄 Re-Audit Rules

If user says "check again" or "go deeper":

1. Re-run ALL A–H
2. Re-check previously "safe" areas
3. Update severity levels
4. Explain any changes

---

## 📝 Summary

> **Never skip techniques. Never assume safe. Always verify.**
