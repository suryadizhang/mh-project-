# VS Code Configuration Guide

This document explains the VS Code workspace configuration for the My
Hibachi monorepo.

## Why .vscode/ is Gitignored

The `.vscode/` directory is excluded from version control (see
`.gitignore` line 48) because:

1. **Local Python Paths**: Each developer may have different virtual
   environment locations
2. **Personal Preferences**: Editor settings vary by developer
   (themes, keybindings, etc.)
3. **OS Differences**: Windows vs Mac/Linux paths differ
   (`Scripts/python.exe` vs `bin/python`)
4. **Security**: Prevents accidental commit of local secrets or
   sensitive paths

## Setting Up Your Local VS Code

### Step 1: Copy the Template

The `.vscode/settings.json` file contains the recommended
configuration. It's already created but not committed to git.

### Step 2: Verify Python Interpreter Path

Update this line based on your OS:

**Windows**:

```json
"python.defaultInterpreterPath": "${workspaceFolder}/apps/backend/.venv/Scripts/python.exe"
```

**Mac/Linux**:

```json
"python.defaultInterpreterPath": "${workspaceFolder}/apps/backend/.venv/bin/python"
```

### Step 3: Install Required VS Code Extensions

**Python Development**:

- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Fast Python language server
- `ms-python.debugpy` - Python debugger

**Frontend Development**:

- `esbenp.prettier-vscode` - Code formatter
- `dbaeumer.vscode-eslint` - ESLint integration
- `bradlc.vscode-tailwindcss` - Tailwind CSS IntelliSense

**Database**:

- `ms-mssql.mssql` - SQL Server tools (for PostgreSQL syntax)

**Optional**:

- `eamodio.gitlens` - Git history and blame
- `ms-vscode.vscode-js-debug` - JavaScript debugger

### Step 4: Configure Backend Python Environment

1. Open `apps/backend/` in terminal
2. Create virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate it:
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 5: Test Configuration

1. Open `apps/backend/src/db/models/core.py`
2. Imports should NOT show red squiggles
3. Ctrl+Click on `from ..base_class import Base` should jump to file
4. Hover over `Booking` class - should show type info

## Key Configuration Explanations

### Python Analysis Extra Paths

```json
"python.analysis.extraPaths": [
  "${workspaceFolder}/apps/backend/src",
  "${workspaceFolder}/apps/backend"
]
```

This tells Pylance where to find Python modules, fixing import errors
like:

- ✅ `from db.models.core import Booking` now resolves
- ✅ `from src.core.config import settings` now resolves

### Diagnostic Severity Overrides

```json
"python.analysis.diagnosticSeverityOverrides": {
  "reportMissingImports": "none",
  "reportMissingModuleSource": "none"
}
```

Suppresses false-positive import errors caused by:

- Dynamic `sys.path` manipulation in backend
- Conditional imports for optional dependencies
- Runtime-generated modules

### File/Search Exclusions

```json
"files.exclude": {
  "**/__pycache__": true,
  "**/*.pyc": true,
  "**/.pytest_cache": true,
  "**/.mypy_cache": true,
  "**/node_modules": true,
  "**/.next": true
}
```

Hides build artifacts and cache directories from:

- File explorer (cleaner view)
- Search results (faster searches)
- File watchers (better performance)

## CI/CD Configuration Exclusions

The `.gitignore` file now excludes CI/CD configs that may show errors
due to non-hardcoded secrets:

```
.github/workflows/*.secrets.yml
.circleci/config.yml
azure-pipelines.yml
deployment-secrets/
*.secrets.yaml
```

**Why**: These files reference environment variables or secret
managers instead of hardcoding values. VS Code may show errors like
"undefined variable" - this is **intentional** for security.

**Examples of secure practices**:

```yaml
# ❌ BAD (hardcoded)
- name: Deploy
  env:
    API_KEY: sk_live_abc123...

# ✅ GOOD (from GitHub Secrets)
- name: Deploy
  env:
    API_KEY: ${{ secrets.API_KEY }}
```

## Troubleshooting

### Imports Still Show Errors

1. Reload VS Code: `Ctrl+Shift+P` → "Reload Window"
2. Restart Pylance: `Ctrl+Shift+P` → "Pylance: Restart Server"
3. Check Python interpreter: Bottom-left corner should show `.venv`
4. Verify `python.analysis.extraPaths` in settings

### "Module not found" Errors

1. Ensure virtual environment is activated
2. Install dependencies: `pip install -r requirements.txt`
3. Check import path matches file structure:

   ```python
   # Correct:
   from db.models.core import Booking

   # Wrong (missing 'db'):
   from models.core import Booking
   ```

### Performance Issues

1. Exclude large directories from file watcher:
   ```json
   "files.watcherExclude": {
     "**/.venv/**": true,
     "**/node_modules/**": true
   }
   ```
2. Disable unused language servers (e.g., `"mssql.enabled": false`)

### GitHub Actions Showing Errors

If `.github/workflows/*.yml` files show errors about undefined
secrets:

1. This is **expected behavior** (secrets come from GitHub UI)
2. To suppress: Add to `.gitignore` or use:
   ```json
   "yaml.validate": false
   ```
   (Not recommended - loses validation for other YAML files)

## Team Onboarding Checklist

- [ ] Clone repository
- [ ] Create `.vscode/settings.json` (copy from this guide)
- [ ] Update Python interpreter path for your OS
- [ ] Install VS Code extensions (see list above)
- [ ] Create backend virtual environment
- [ ] Install Python dependencies
- [ ] Verify imports resolve correctly
- [ ] Run tests: `pytest apps/backend/tests/`
- [ ] Read `00-BOOTSTRAP.instructions.md` for coding standards

## Additional Resources

- **Project Structure**: See `apps/backend/src/db/models/README.md`
- **Coding Standards**: See
  `.github/instructions/01-AGENT_RULES.instructions.md`
- **Database Schema**: See
  `COMPREHENSIVE_DATABASE_FOUNDATION_AUDIT.md`
- **Testing**: See `apps/backend/tests/README.md`

---

**Last Updated**: 2025-01-14 **Maintained By**: Development Team
