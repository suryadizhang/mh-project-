---
applyTo: '**'
---

# My Hibachi Enterprise Audit Standards (A–H Deep Audit)

This file defines the **mandatory deep audit methodology** the agent
MUST use when the user requests:

- auditing
- checking logic
- verifying correctness
- finding bugs
- stress testing
- “check deeper”
- “is this correct?”

All 8 layers MUST be applied in every audit.

---

# 0. Principles

1. Never use incremental audits → apply ALL A–H together.
2. Never assume code is safe → verify everything.
3. Always test edge cases and failures.
4. Classify findings: Critical / High / Medium / Low.

---

# A. Static Analysis (line-by-line)

Check for:

- Syntax correctness
- Type mismatches
- Missing imports
- Dead code
- Shadowed variables
- Bad naming
- Missing validation
- Hidden side effects
- Improper async
- Unreachable code
- Debug leftovers

---

# B. Runtime Simulation

Simulate execution:

- Datetime/timezone problems
- None/null propagation
- Type coercion
- String formatting bugs
- Precision loss
- Uncaught exceptions
- Missing returns
- Control flow errors

---

# C. Concurrency & Transaction Safety

Check for:

- Race conditions (TOCTOU - Time Of Check, Time Of Use)
  - Example: `check_availability()` → 80ms gap → `create_booking()` =
    RACE CONDITION
- Shared state without locks
- Missing database transactions
- Missing SELECT FOR UPDATE
- Missing optimistic locking (version columns)
- Non-idempotent behavior (running twice causes problems)
- Concurrent writes to same resource

---

# D. Data Flow Tracing

Trace:

**input → processing → output**

Check:

- Type preservation
- Shape/format consistency
- Value ranges
- Mutations
- Missing validation

---

# E. Error Path & Exception Handling

Validate:

- try/except correctness
- Specific exceptions (not broad)
- Logging (no sensitive info)
- Good fallback behavior
- No silent failures

---

# F. Dependency & Enum Validation

Confirm:

- Imported symbols exist (e.g.,
  `from models import CustomerTonePreference` - does it exist?)
- Enum/constant values exist (e.g.,
  `ErrorCode.PAYMENT_AMOUNT_INVALID` - is it defined?)
- No magic strings where enums should exist
- All environment variables required are documented
- Version compatibility (Python 3.11+, Node 18+, etc.)
- No AttributeError risks from undefined enum values

---

# G. Business Logic Validation (Critical)

Check:

- Pricing
- Travel fee
- Booking logic
- Scheduling
- Deposits
- Cancellation
- Guest counts
- Time slot logic
- Admin flows

Look for:

- Wrong formulas
- Missing edge cases
- Over/under charging
- Double-booking
- Invalid states

---

# H. Helper/Utility Analysis

Check private/utility methods that are often overlooked:

- Parameter validation (especially in `_private_methods()`)
- Error handling (try-except around operations like `.split()`,
  `.parse()`)
- Hidden side effects (modifies global state? database calls?)
- Naming clarity (`_slots_overlap` is clear, `_process` is not)
- Testability (can it be unit tested?)
- Reusability (DRY principle)
- Edge cases (empty strings, None values, invalid formats)

---

# Required Audit Output Format

Every audit MUST include:

1. **Techniques applied (A–H)** with checkboxes:
   - [ ] A. Static Analysis (line-by-line)
   - [ ] B. Runtime Simulation
   - [ ] C. Concurrency & Transaction Safety
   - [ ] D. Data Flow Tracing
   - [ ] E. Error Path & Exception Handling
   - [ ] F. Dependency & Enum Validation
   - [ ] G. Business Logic Validation
   - [ ] H. Helper/Utility Analysis

2. **Findings by severity:**
   - 🔴 CRITICAL: Production-breaking, data loss, security issues
   - 🟠 HIGH: Major functionality broken, bad UX, data corruption risk
   - 🟡 MEDIUM: Minor bugs, edge cases, non-critical paths
   - 🟢 LOW: Code quality, optimization, nice-to-have fixes

3. **Why each issue matters** (business impact, technical debt, risk)

4. **Exact recommended fix** (code examples, not just descriptions)

5. **Final readiness classification:**
   - ✅ production-ready (all 8 techniques passed, tests passing)
   - ⚠️ dev-only (missing tests, has TODOs, needs review)
   - 🔴 dangerous (race conditions, data loss, security issues)
   - 🛑 needs rewrite (architectural problems, tech debt)

---

# Re-Audit Rules

If user requests:

- “check again”
- “go deeper”
- "are you sure?"

You MUST:

- Re-run ALL A–H
- Re-check previous safe areas
- Update severity levels
- Explain changes

---

# Real-World Bug Examples (From My Hibachi Project)

These bugs were found using A–H methodology:

**Bug #13 (Technique C - Concurrency)**:

- Race condition between `check_availability()` and `create_booking()`
- 80ms window allows double bookings
- Fix: Add database locking or optimistic locking

**Bug #14 (Technique H - Helper Methods)**:

- `_slots_overlap()` helper had no error handling
- `slot1_start.split(":")` could crash with ValueError
- Fix: Add try-except and validate time ranges

**Bug #15 (Technique F - Enum Validation)**:

- `ErrorCode.PAYMENT_AMOUNT_INVALID` doesn't exist
- Runtime AttributeError crashes deposit confirmation
- Fix: Use existing `ErrorCode.BAD_REQUEST`

**Bug #11 (Technique G - Business Logic)**:

- Time overlap check used hours only, ignored minutes
- `7:45 PM` and `8:00 PM` treated as overlapping
- Fix: Include minute-precision in overlap calculation

**Bug #9 (Technique B - Runtime Simulation)**:

- `datetime.now()` returns timezone-naive datetime
- Comparison with timezone-aware DB value crashes
- Fix: Use `datetime.now(timezone.utc)`

---

# Summary

If unsure:

> **Not safe. Dev-only. Keep behind feature flag.**
