# Security Files Consolidation Plan

## Files Being Consolidated

1. ✅ **core/security.py** (KEEP - Main security utilities)
2. ❌ **api/app/security.py** (MERGE → core/security.py)
3. ❌ **api/app/middleware/security.py** (MERGE → core/security.py)
4. ❌ **api/ai/endpoints/security.py** (MERGE → core/security.py)
5. ❌ **api/ai/endpoints/utils/security.py** (DELETE - Empty file)

## Current Import Usage

### Files importing from core/security:
- `api/deps.py` - Using: extract_user_from_token, is_admin_user, is_super_admin, get_public_business_info
- `api/deps_enhanced.py` - Using: extract_user_from_token, is_admin_user, is_super_admin
- `api/v1/endpoints/auth.py` - Using: verify_password, create_access_token

### Files importing from api/ai/endpoints/security:
- `api/ai/endpoints/main.py` - Using: setup_security_middleware, get_current_user

## Consolidation Strategy

### Phase 1: Enhance core/security.py ✅
Add missing functionality from other files:
- Middleware classes (SecurityHeadersMiddleware, RateLimitByIPMiddleware, etc.)
- Setup functions (setup_security_middleware)
- Additional security utilities (FieldEncryption, SecurityUtils, AuditLogger)
- Authentication helpers (get_current_user, require_auth)

### Phase 2: Update Imports 🔄
Update `api/ai/endpoints/main.py`:
```python
# OLD:
from api.ai.endpoints.security import setup_security_middleware, get_current_user

# NEW:
from core.security import setup_security_middleware, get_current_user
```

### Phase 3: Delete Duplicate Files 🗑️
- Remove: api/app/security.py
- Remove: api/app/middleware/security.py
- Remove: api/ai/endpoints/security.py
- Remove: api/ai/endpoints/utils/security.py (empty)

## Benefits
- **Single Source of Truth**: All security logic in one place
- **Easier Maintenance**: Update security in one location
- **Reduced Complexity**: ~500-800 lines removed
- **Better Testing**: Centralized security testing
- **Consistent Behavior**: Same security across all APIs

## Estimated Time
- Phase 1: 1 hour (merge all functionality)
- Phase 2: 30 minutes (update 1 import file)
- Phase 3: 10 minutes (delete 4 files)
- Testing: 30 minutes (verify no breaks)
- **Total**: ~2 hours
