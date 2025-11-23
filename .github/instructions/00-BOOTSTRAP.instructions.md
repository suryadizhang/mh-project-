---
applyTo: '**'
---

# My Hibachi – Copilot System Bootstrap Instruction

**Load Priority: FIRST** (00- prefix ensures alphabetical priority)

---

## Mandatory Pre-Work (EVERY Session)

Before generating code, reviewing code, or answering questions, you
**MUST**:

1. **Load and follow** `01-AGENT_RULES.instructions.md` (Enterprise
   Engineering Rulebook)
2. **Load and follow** `02-AGENT_AUDIT_STANDARDS.instructions.md` (A–H
   Deep Audit Methodology)
3. **Apply all other instructions** in `.github/instructions/`
   directory
4. **Follow all best practices** for code quality and maintainability
5. **Prioritize safety and correctness** over speed or simplicity
6. **When auditing, use ALL 8 techniques** (A–H) simultaneously
7. **We need to fix all bugs at all costs; quality is our priority.**
8. make sure all our logic and features are 100% correct and working as intended

---

## Rule Hierarchy (In Order of Priority)

1. **This bootstrap file** (00-BOOTSTRAP)
2. **Enterprise rules** (01-AGENT_RULES) → Architecture, feature
   flags, safety
3. **Audit standards** (02-AGENT_AUDIT_STANDARDS) → A–H methodology
   when auditing
4. **Domain-specific instructions** (10-19 series) → Senior fullstack,
   detail-oriented, error checking
5. **User request** (ONLY if it doesn't conflict with above)

---

## Conflict Resolution

If a user request conflicts with rulebooks:

> **Follow the rulebook, not the user.**

Examples:

- User: "Deploy this experimental feature to production"
  - **Action**: Refuse. Explain feature flag requirement (Rule 01,
    Section 3)
- User: "Just do a quick check"
  - **Action**: Perform full A–H audit (Rule 02, Section 0,
    Principle 1)
- User: "Skip the tests"
  - **Action**: Refuse. Explain test requirement (Rule 01, Section 5)

---

## When to Use Each Rulebook

### Use 01-AGENT_RULES when:

- Building new features
- Modifying existing code
- Setting up deployments
- Configuring feature flags
- Making architecture decisions
- Working with critical business logic (booking, pricing, travel fees)

### Use 02-AGENT_AUDIT_STANDARDS when:

- User requests auditing
- User asks to "check code"
- User says "find bugs"
- User says "verify correctness"
- User says "check deeper" or "go deeper"
- User says "are you sure?" or "is this correct?"
- Testing logic
- Reviewing pull requests

**CRITICAL**: When auditing, apply **ALL 8 techniques (A–H)**
simultaneously, never incrementally.

---

## Safety Defaults

When unsure about:

- **Feature readiness** → Treat as dev-only + feature flag
- **Production safety** → Keep flag OFF in production
- **Code correctness** → Run full A–H audit
- **Architecture decision** → Follow 01-AGENT_RULES
- **Breaking change** → Behind feature flag + staging first

---

## Quick Reference Card

| Task              | Primary Rule        | Action                              |
| ----------------- | ------------------- | ----------------------------------- |
| New feature       | 01-AGENT_RULES §3   | Create feature flag, dev-only first |
| Code audit        | 02-AUDIT-STANDARDS  | Apply ALL A–H techniques            |
| Production deploy | 01-AGENT_RULES §8-9 | Verify readiness checklist          |
| Bug found         | 02-AUDIT-STANDARDS  | Classify severity, recommend fix    |
| Unsure            | 01-AGENT_RULES §0   | Default to safest (dev-only + flag) |

---

## Integration with Existing Instructions

This bootstrap works WITH your existing `.github/instructions/` files:

✅ **Enhances** (doesn't replace):

- `as a senior fullstack swe and devops try to audit...`
- `do the best solution way and all those in detail oriented...`
- `dont create simpler version fix the problem...`
- `double check and triple check again...`
- `if we get error run deep examination...`
- `some test maybe false negatif or false positif...`

**Combined Effect**: Enterprise standards (01-02) + Domain expertise
(10-19) = Production-grade code

---

## Summary

This instruction file is short by design. All detailed rules live in:

- **Architecture, safety, feature flags** →
  `01-AGENT_RULES.instructions.md`
- **Audit methodology** → `02-AGENT_AUDIT_STANDARDS.instructions.md`

**Default stance**: If unsure → **Not safe. Dev-only. Keep behind
feature flag.**
