---
applyTo: '**'
---

# My Hibachi – Copilot Agent Performance Guidelines

**Priority: REFERENCE** – Guidelines for efficient AI agent operation.

---

## 🎯 Purpose

This document provides guidelines for Copilot Agent to work
efficiently in the My Hibachi monorepo.

---

## 🎓 Interactive Teaching Mode (PREFERRED)

**When guiding through multi-step tasks, use mentor-student
approach:**

### How to Teach:

1. **One step at a time** – Don't overwhelm with all steps upfront
2. **Explain the "why"** – Help user understand, not just execute
3. **Run what you can** – Execute CLI commands on user's behalf
4. **Wait for confirmation** – Before proceeding to next step
5. **Provide context** – What we're doing, why it matters
6. **Celebrate progress** – Acknowledge completed steps

### Teaching Format:

```
## Step X of Y: [Step Name]

**What we're doing:** [Brief explanation]
**Why it matters:** [Business/technical reason]

[Action or command here]

**Expected result:** [What success looks like]

---
✅ Ready for next step? [Or ask clarifying question]
```

### When to Use This Mode:

- Infrastructure setup (Cloudflare, servers, databases)
- Database migrations
- Deployment procedures
- Complex debugging sessions
- Learning new systems
- Any multi-step task where user wants guidance

### When NOT to Use:

- Simple code fixes (just do them)
- Quick questions (just answer)
- User explicitly says "just do it"

---

## 📁 Monorepo Structure (Key Paths)

```
MH webapps/
├── apps/
│   ├── customer/      # Next.js public booking site
│   ├── admin/         # Next.js admin panel
│   └── backend/       # FastAPI Python API
├── packages/          # Shared npm packages
│   └── types/         # Shared TypeScript types
├── docs/              # Documentation hierarchy
├── database/          # SQL migrations
├── e2e/               # Playwright E2E tests
└── .github/           # CI/CD, instructions
```

---

## 🚀 Performance-Optimized Search Strategy

### 1. Know Where to Look

| Looking For         | Search In                               |
| ------------------- | --------------------------------------- |
| Frontend components | `apps/customer/src/`, `apps/admin/src/` |
| API endpoints       | `apps/backend/src/routers/`             |
| Business logic      | `apps/backend/src/services/`            |
| Database models     | `apps/backend/src/db/models/`           |
| Shared types        | `packages/types/`                       |
| Tests               | `**/tests/`, `**/__tests__/`, `e2e/`    |
| Documentation       | `docs/`, `.github/instructions/`        |

### 2. Avoid Searching In

These folders are large and contain generated/vendored code:

- `node_modules/` – npm packages
- `.next/` – Next.js build output
- `.venv/` – Python virtual environment
- `dist/` – Build output
- `coverage/` – Test coverage reports
- `__pycache__/` – Python bytecode
- `archives/` – Obsolete documentation

### 3. Use Targeted Queries

```
# Good - specific path
grep_search with includePattern="apps/backend/src/services/**"

# Bad - searches everything
grep_search without includePattern
```

---

## 📖 Context Gathering Efficiency

### Read Large Chunks

Instead of many small reads:

```
# Preferred - one large read
read_file lines 1-200

# Avoid - many small reads
read_file lines 1-20
read_file lines 21-40
read_file lines 41-60
...
```

### Use Parallel Reads When Possible

When files are independent, read them in parallel:

```
# Good - parallel independent reads
read_file(fileA)
read_file(fileB)
read_file(fileC)

# Not needed - waiting between independent reads
read_file(fileA)
wait
read_file(fileB)
wait
```

---

## 🗂️ File Modification Guidelines

### 1. Fix Existing Files (No Duplicates)

From Core Principles Rule 7:

> **Fix existing files** instead of creating new duplicates. Before
> creating any file, check if similar exists.

### 2. Use Targeted Edits

For small changes, use `replace_string_in_file` with sufficient
context (3+ lines before and after).

### 3. Batch Related Edits

When making multiple related changes, use
`multi_replace_string_in_file` to apply them in a single operation.

---

## ⚡ Quick Reference Commands

### Find Files

```
file_search "**/*.py" - Find Python files
file_search "**/test_*.py" - Find Python tests
file_search "**/page.tsx" - Find Next.js pages
```

### Search Code

```
grep_search "def booking" includePattern="apps/backend/**"
grep_search "useBooking" includePattern="apps/customer/**"
semantic_search "payment processing logic"
```

### Get Context

```
list_dir "apps/backend/src/services"
read_file "apps/backend/src/services/booking_service.py" 1-300
```

---

## 🎯 Task Prioritization

When working on tasks:

1. **Understand scope first** – Read relevant files before editing
2. **Check batch context** – See `CURRENT_BATCH_STATUS.md`
3. **Verify dependencies** – Check imports resolve correctly
4. **Test locally before PR** – Run tests before pushing

---

## 🔍 Code Quality & Syntax Verification

**CRITICAL: Be detail-oriented when writing code to prevent syntax
errors.**

### Before Submitting Code Changes:

| Check                     | Action                                        |
| ------------------------- | --------------------------------------------- |
| **Matching brackets**     | Every `{` has `}`, every `(` has `)`          |
| **Matching tags**         | Every `<tag>` has `</tag>`, no duplicates     |
| **Complete statements**   | No missing semicolons, commas, or terminators |
| **Proper nesting**        | JSX elements properly nested and closed       |
| **String literals**       | All quotes and backticks properly closed      |
| **Import statements**     | All imports syntactically correct             |
| **Arrow functions**       | Proper `=>` syntax with correct parentheses   |
| **Template literals**     | Backticks closed, `${}` expressions valid     |
| **Object/Array literals** | Proper comma separation, no trailing issues   |

### Common Syntax Errors to Avoid:

```tsx
// ❌ BAD - Duplicate closing tag
<button>Click</button>
</button>

// ✅ GOOD - Single closing tag
<button>Click</button>

// ❌ BAD - Missing closing bracket
const obj = { key: value

// ✅ GOOD - Complete object
const obj = { key: value };

// ❌ BAD - Unclosed string
const msg = "Hello world

// ✅ GOOD - Closed string
const msg = "Hello world";
```

### Multi-Edit Verification:

When making multiple edits in one operation:

1. **Review each edit independently** before submitting
2. **Count opening/closing tags** to ensure they match
3. **Check edit boundaries** don't cut off in middle of statements
4. **Verify context lines** are accurate and unique

---

## � Pre-Commit Code Review (MANDATORY)

**Before ANY commit, perform a Senior SWE-level code review.**

This is an enterprise-standard practice that catches bugs before they
reach CI/CD or production. Never skip this step.

### Pre-Commit Checklist (Run EVERY Time):

```bash
# 1. Build verification (catches compile/type errors)
cd apps/customer && npm run build
cd apps/admin && npm run build

# 2. Run tests (catches regressions)
cd apps/customer && npm test -- --run

# 3. Backend syntax check (catches Python errors)
cd apps/backend/src && python -c "from main import app; print('✅ Backend imports OK')"

# 4. Check for errors in changed files
# Use VS Code's Problems panel or run linters
```

### Manual Code Review Steps (Senior SWE Standard):

| Step                  | What to Check                         | Why                                  |
| --------------------- | ------------------------------------- | ------------------------------------ |
| **1. Diff Review**    | `git diff --staged` - Read every line | Catch accidental changes, debug code |
| **2. Import Check**   | All new imports exist and resolve     | Prevent runtime ModuleNotFoundError  |
| **3. Type Safety**    | No `any` types, proper generics       | Catch type errors before runtime     |
| **4. Error Handling** | All async ops have try/catch          | Prevent unhandled promise rejections |
| **5. Edge Cases**     | null, undefined, empty array, 0       | Prevent production crashes           |
| **6. API Contract**   | Request/response types match          | Prevent 422/500 errors               |
| **7. Security Scan**  | No secrets, no SQL injection          | Prevent security vulnerabilities     |
| **8. Console/Debug**  | Remove console.log, print()           | Clean production code                |

### Code Review Questions (Ask Before Every Commit):

1. **Does this break existing functionality?**
   - Check all usages of modified functions
   - Verify API contracts haven't changed unexpectedly

2. **Are all edge cases handled?**
   - What if the input is null/undefined?
   - What if the array is empty?
   - What if the API returns an error?

3. **Is the code testable and tested?**
   - Can this be unit tested?
   - Did I update existing tests if behavior changed?

4. **Is this the right abstraction?**
   - Is this in the right file/module?
   - Does it follow existing patterns in the codebase?

5. **Would another developer understand this?**
   - Are variable names descriptive?
   - Is complex logic commented?

### Enterprise Code Quality Gates:

| Gate                   | Command                            | Must Pass? |
| ---------------------- | ---------------------------------- | ---------- |
| TypeScript Build       | `npm run build`                    | ✅ YES     |
| Unit Tests             | `npm test -- --run`                | ✅ YES     |
| Python Imports         | `python -c "from main import app"` | ✅ YES     |
| ESLint (if configured) | `npm run lint`                     | ✅ YES     |
| Type Check             | `npx tsc --noEmit`                 | ✅ YES     |

### What Senior SWEs Look For:

**Correctness:**

- Logic errors, off-by-one bugs
- Race conditions in async code
- Missing error handling paths

**Maintainability:**

- Code duplication (DRY violations)
- Overly complex functions (should be split)
- Missing documentation on public APIs

**Performance:**

- N+1 query patterns
- Unnecessary re-renders (React)
- Memory leaks (unclosed resources)

**Security:**

- Input validation on all user data
- SQL injection prevention (parameterized queries)
- No sensitive data in logs

### Pre-Commit Self-Review Template:

Before committing, mentally answer:

```
□ I ran the build and it passes
□ I ran the tests and they pass
□ I reviewed the git diff line-by-line
□ I checked all imports resolve correctly
□ I handled all error cases
□ I removed all debug/console statements
□ I updated tests if behavior changed
□ I would approve this PR if I was reviewing it
```

### Common Mistakes to Catch:

| Mistake                 | How to Detect              | Fix                      |
| ----------------------- | -------------------------- | ------------------------ |
| Forgot to save file     | `git status` shows nothing | Save all files           |
| Wrong API response type | Build error                | Update TypeScript types  |
| Missing await           | Runtime error on Promise   | Add await keyword        |
| Circular import         | Python ImportError         | Reorganize imports       |
| Stale test assertion    | Test fails                 | Update test expectations |
| Hardcoded value         | Code review                | Use env var or config    |

---

## �📋 Common Paths Quick Reference

| Resource             | Path                                       |
| -------------------- | ------------------------------------------ |
| Customer app entry   | `apps/customer/src/app/page.tsx`           |
| Admin app entry      | `apps/admin/src/app/page.tsx`              |
| Backend main         | `apps/backend/src/main.py`                 |
| Backend config       | `apps/backend/src/core/config.py`          |
| Feature flags        | `apps/backend/src/core/config.py`          |
| Shared types         | `packages/types/src/`                      |
| CI workflow          | `.github/workflows/deployment-testing.yml` |
| Instruction files    | `.github/instructions/`                    |
| Current batch status | `CURRENT_BATCH_STATUS.md`                  |
| Customer tests       | `apps/customer/src/**/__tests__/`          |
| Backend tests        | `apps/backend/tests/`                      |
| E2E tests            | `e2e/tests/`                               |

---

## 🔗 Related Docs

- `00-BOOTSTRAP.instructions.md` – System bootstrap
- `02-ARCHITECTURE.instructions.md` – System structure
- `myhibachi.code-workspace` – Multi-root workspace file
