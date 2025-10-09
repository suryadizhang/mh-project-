#!/usr/bin/env python3

import sys
import os

# Add backend source path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

print("Testing imports...")

try:
    from api.v1.endpoints.customers import router as customers_router
    print("✅ customers.py imported successfully")
except Exception as e:
    print(f"❌ customers.py import failed: {e}")

try:
    from api.v1.endpoints.leads import router as leads_router
    print("✅ leads.py imported successfully")
except Exception as e:
    print(f"❌ leads.py import failed: {e}")

try:
    from api.v1.endpoints.inbox import router as inbox_router
    print("✅ inbox.py imported successfully")
except Exception as e:
    print(f"❌ inbox.py import failed: {e}")

try:
    from api.v1.api import api_router
    print("✅ Main API router imported successfully")
except Exception as e:
    print(f"❌ Main API router import failed: {e}")

try:
    from api.deps import get_current_admin_user, AdminUser
    print("✅ Admin dependencies imported successfully")
except Exception as e:
    print(f"❌ Admin dependencies import failed: {e}")

print("\nAll import tests completed!")