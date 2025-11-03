"""
Progressive router testing to isolate OpenAPI schema generation issue.
"""
import sys
sys.path.insert(0, "./src")

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(title="Test API")

routers_to_test = [
    ("health", "api.app.routers.health", "/api/health"),
    ("auth", "api.app.routers.auth", "/api/auth"),
    ("station_auth", "api.app.routers.station_auth", "/api/station"),
    ("station_admin", "api.app.routers.station_admin", "/api/admin/stations"),
    ("crm", "api.app.crm.endpoints", "/api"),
    ("stripe", "api.app.routers.stripe", "/api/stripe"),
    ("payments", "api.app.routers.payments", "/api/payments"),
    ("leads", "api.app.routers.leads", "/api"),
    ("newsletter", "api.app.routers.newsletter", "/api"),
    ("ringcentral", "api.app.routers.ringcentral_webhooks", "/api"),
    ("admin_analytics", "api.app.routers.admin_analytics", "/api"),
]

for name, module_path, prefix in routers_to_test:
    try:
        module = __import__(module_path, fromlist=["router"])
        router = getattr(module, "router")
        app.include_router(router, prefix=prefix, tags=[name])
        print(f"[OK] Added {name} router")
        
        # Try generating schema after each router
        try:
            schema = get_openapi(title="Test", version="1.0.0", routes=app.routes)
            path_count = len(schema.get('paths', {}))
            print(f"     Schema OK: {path_count} total paths")
        except Exception as e:
            print(f"[ERROR] SCHEMA FAILED AFTER ADDING {name.upper()}: {e}")
            import traceback
            traceback.print_exc()
            break
            
    except Exception as e:
        print(f"[ERROR] Failed to load {name} router: {e}")

print("\n=== FINAL TEST ===")
try:
    schema = get_openapi(title="Final Test", version="1.0.0", routes=app.routes)
    print(f"[OK] Final schema generation succeeded with {len(schema.get('paths', {}))} paths")
except Exception as e:
    print(f"[ERROR] Final schema generation failed: {e}")
