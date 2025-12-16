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

**CRITICAL: Be detail-oriented when writing code to prevent syntax errors.**

### Before Submitting Code Changes:

| Check                      | Action                                          |
| -------------------------- | ----------------------------------------------- |
| **Matching brackets**      | Every `{` has `}`, every `(` has `)`            |
| **Matching tags**          | Every `<tag>` has `</tag>`, no duplicates       |
| **Complete statements**    | No missing semicolons, commas, or terminators   |
| **Proper nesting**         | JSX elements properly nested and closed         |
| **String literals**        | All quotes and backticks properly closed        |
| **Import statements**      | All imports syntactically correct               |
| **Arrow functions**        | Proper `=>` syntax with correct parentheses     |
| **Template literals**      | Backticks closed, `${}` expressions valid       |
| **Object/Array literals**  | Proper comma separation, no trailing issues     |

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

## 📋 Common Paths Quick Reference

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
