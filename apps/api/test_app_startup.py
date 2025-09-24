#!/usr/bin/env python3
"""Test FastAPI application startup."""

try:
    from app.main import app
    print("✅ FastAPI application loaded successfully!")

    # Check available routes
    print("📊 Available routes:")
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if methods:
            methods_str = ", ".join(sorted(methods))
        else:
            methods_str = "N/A"
        print(f"  - {route.path} ({methods_str})")

    print(f"\n📋 Total routes: {len(app.routes)}")

except Exception as e:
    print(f"❌ Application startup failed: {e}")
    import traceback
    traceback.print_exc()
