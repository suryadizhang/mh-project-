# My Hibachi Chef CRM - File Migration Mapping

## Overview
This document maps the current disorganized file structure to the new enterprise-grade monorepo structure with unified API architecture.

## Migration Strategy
- **Phase 1**: Security cleanup (COMPLETED)
- **Phase 2**: Directory restructuring (IN PROGRESS)
- **Phase 3**: Backend API implementation
- **Phase 4**: Frontend implementation
- **Phase 5**: Deployment configuration
- **Phase 6**: Documentation & testing

## Directory Structure Changes

### OLD STRUCTURE → NEW STRUCTURE

#### Root Level Files (Moving/Organizing)
```
OLD LOCATION                          → NEW LOCATION
====================================================================
.secrets                             → REMOVED (config/environments/secrets/.secrets.local)
deep_production_audit.py             → scripts/monitoring/deep_audit.py
deploy.sh                           → scripts/deployment/deploy.sh
guard.py                            → apps/backend/src/utils/guard.py
organize_project.py                 → scripts/maintenance/organize_project.py
plesk_vercel_audit.py               → scripts/monitoring/plesk_audit.py
setup_enhanced_crm.py               → scripts/setup/setup_crm.py
simple_test_server.py               → apps/backend/tests/test_server.py
test_admin_quick.py                 → apps/backend/tests/integration/test_admin.py
test_station_rbac_simple.db         → DELETE (temporary test file)
requirements.txt                    → apps/backend/requirements.txt
pyproject.toml                      → apps/backend/pyproject.toml
pytest.ini                          → apps/backend/pytest.ini
```

#### Apps Directory (Reorganizing)
```
OLD LOCATION                          → NEW LOCATION
====================================================================
apps/api/                            → apps/backend/src/ (UNIFIED)
apps/ai-api/                         → apps/backend/src/api/v1/endpoints/ai/ (MERGED)
apps/customer/                       → apps/frontend/
apps/admin/                          → apps/admin/ (KEEP)
```

#### Backend/API Files
```
OLD LOCATION                          → NEW LOCATION
====================================================================
apps/api/*.py                        → apps/backend/src/api/v1/endpoints/
apps/ai-api/*.py                     → apps/backend/src/api/v1/endpoints/ai/
[scattered Python files]             → apps/backend/src/services/
[database files]                     → apps/backend/src/db/
[integration files]                  → apps/backend/src/integrations/
```

#### Frontend Files
```
OLD LOCATION                          → NEW LOCATION
====================================================================
apps/customer/                       → apps/frontend/
myhibachi-frontend/                  → apps/frontend/ (MERGE)
[marketing pages]                    → apps/frontend/src/app/(marketing)/
[booking flow]                       → apps/frontend/src/app/(booking)/
```

#### Configuration Files
```
OLD LOCATION                          → NEW LOCATION
====================================================================
.env*                                → config/environments/
docker/                             → infrastructure/docker/
systemd/                            → infrastructure/systemd/
[nginx configs]                      → infrastructure/nginx/
```

#### Documentation
```
OLD LOCATION                          → NEW LOCATION
====================================================================
*.md (reports)                       → archives/old-reports/ (CLEANUP)
docs/                               → docs/ (REORGANIZE)
verification/                       → archives/verification/
```

## Unified API Architecture Changes

### CRITICAL: AI API Merge
**OLD**: Separate AI API at different domain
**NEW**: AI endpoints integrated into main API

```
OLD ENDPOINTS:
- https://ai-api.myhibachichef.com/chat
- https://ai-api.myhibachichef.com/voice

NEW ENDPOINTS (UNIFIED):
- https://api.myhibachichef.com/v1/ai/chat
- https://api.myhibachichef.com/v1/ai/voice
- https://api.myhibachichef.com/v1/ai/embeddings
```

### Domain Architecture
**3 Domains Total (not 4):**
1. `myhibachichef.com` - Customer frontend (Next.js)
2. `admin.myhibachichef.com` - Admin dashboard (Next.js)  
3. `api.myhibachichef.com` - **Unified Backend API** (FastAPI)

## File Actions Required

### 1. REMOVE (Security/Cleanup)
- `.secrets` (DONE - moved to secure location)
- `test_station_rbac_simple.db` (temporary test file)
- Documentation bloat files (`*_COMPLETE.md`, `*_FINAL.md`, etc.)
- `__pycache__/` directories

### 2. MOVE (File Migration)
```bash
# Backend files
mv apps/api/ apps/backend/src/api/v1/endpoints/
mv apps/ai-api/ apps/backend/src/api/v1/endpoints/ai/

# Frontend files
mv apps/customer/ apps/frontend/
mv myhibachi-frontend/ apps/frontend/ # merge

# Scripts
mv deep_production_audit.py scripts/monitoring/
mv deploy.sh scripts/deployment/
mv guard.py apps/backend/src/utils/

# Configuration
mv docker/ infrastructure/docker/
mv systemd/ infrastructure/systemd/
```

### 3. MERGE (Consolidation)
- Combine `apps/customer/` and `myhibachi-frontend/` → `apps/frontend/`
- Merge `apps/api/` and `apps/ai-api/` → `apps/backend/` (unified)
- Consolidate documentation in `docs/`

### 4. CREATE (New Structure)
```
apps/backend/src/
├── api/v1/endpoints/ai/     # AI endpoints (merged from ai-api)
├── core/                    # Configuration, security, rate limiting
├── models/domain/           # Domain models
├── models/schemas/          # Pydantic schemas
├── services/                # Business logic
├── integrations/            # External APIs (RingCentral, Stripe, etc.)
├── db/repositories/         # Database layer
└── utils/                   # Utilities
```

## Migration Script Plan

### Phase 2.1: File Movement Script
```bash
#!/bin/bash
# Create script: scripts/migrate_files.sh

# Dry run mode
if [[ "$1" == "--dry-run" ]]; then
    echo "DRY RUN: Would move files..."
    # Show what would be moved without actually moving
fi

# Actual migration
# Move files according to mapping above
```

### Phase 2.2: Import Path Updates
After moving files, update all import statements:

```python
# OLD IMPORTS
from api.endpoints import bookings
from ai_api.chat import chatbot

# NEW IMPORTS (UNIFIED)
from api.v1.endpoints import bookings
from api.v1.endpoints.ai import chat
```

## Rate Limiting Implementation

### NEW: Tiered Rate Limiting
```python
RATE_LIMITS = {
    "public": "20 req/min, 1000 req/hour",
    "admin": "100 req/min, 5000 req/hour",        # 5x higher for admins
    "admin_super": "200 req/min, 10000 req/hour", # 10x higher for super admins
    "ai": "10 req/min, 300 req/hour",             # Strict for AI (cost control)
    "webhook": "100 req/min, 5000 req/hour"       # High for external services
}
```

## Dependencies Updates

### Backend Requirements
```python
# NEW: apps/backend/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
redis==5.0.1      # For rate limiting
openai==1.3.8     # AI integration
ringcentral==1.0.0
stripe==7.8.0
# ... (see full requirements file)
```

### Frontend Dependencies
```json
// apps/frontend/package.json
{
  "name": "@myhibachi/frontend",
  "dependencies": {
    "next": "14.0.0",
    "react": "18.2.0"
  }
}
```

## Database Schema Changes

### PostgreSQL Schemas (4 main + infrastructure)
```sql
-- Main business schemas
CREATE SCHEMA customer;    -- PII, addresses, consent
CREATE SCHEMA lead;        -- Prospect pipeline
CREATE SCHEMA booking;     -- Orders, chefs, messages
CREATE SCHEMA newsletter;  -- Subscribers, campaigns

-- Infrastructure schemas  
CREATE SCHEMA events;      -- Event sourcing
CREATE SCHEMA integra;     -- External system data
CREATE SCHEMA read;        -- CQRS read models
CREATE SCHEMA audit;       -- Audit trails
```

## Environment Variables Migration

### OLD: .secrets file (REMOVED)
### NEW: Environment templates + .env files

```bash
# Development
config/environments/.env.development.template

# Production  
config/environments/.env.production.template

# Actual values (gitignored)
.env
```

## Testing Strategy

### Migration Testing
1. **Dry run**: Test file moves without actually moving
2. **Import testing**: Verify all import paths work
3. **Endpoint testing**: Ensure API endpoints respond
4. **Rate limit testing**: Verify tiered rate limiting works
5. **Integration testing**: Test all external service integrations

### Rollback Plan
```bash
# If migration fails, restore from backup
mv /backup/mh-project-20251008/ .
systemctl restart myhibachi-api
```

## Success Criteria

### Phase 2 Complete When:
- [ ] All files moved to new structure
- [ ] No broken import statements
- [ ] API endpoints accessible at new paths
- [ ] Rate limiting working with admin tiers
- [ ] All tests pass
- [ ] Documentation updated

## Implementation Order

1. **Create new directory structure** ✅
2. **Move configuration files** ✅
3. **Move and merge backend files** (IN PROGRESS)
4. **Move frontend files**
5. **Update import paths**
6. **Test unified API**
7. **Update documentation**
8. **Deploy to staging**

## Notes

- **NEVER**: Show EIN (39-2675702) or full address publicly
- **ALWAYS**: Use business email (cs@myhibachichef.com)
- **UNIFIED API**: AI endpoints are part of main API, not separate service
- **RATE LIMITS**: Admins get 5-10x higher limits than public users
- **SECURITY**: All secrets in environment variables, never in code

---

**Last Updated**: 2025-10-08  
**Phase**: 2 - Directory Restructuring  
**Status**: In Progress