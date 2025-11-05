"""Test OpenAPI schema generation directly"""

import sys

sys.path.insert(0, "src")

from main import app
from fastapi.openapi.utils import get_openapi
import traceback

print("Testing OpenAPI schema generation...")
print(f"App has {len(app.routes)} routes")

try:
    schema = get_openapi(title="Test", version="1.0", routes=app.routes)
    paths = schema.get("paths", {})
    print(f"\n✅ SUCCESS: Generated {len(paths)} endpoint paths")

    # Print first 10 endpoints
    for i, path in enumerate(list(paths.keys())[:10]):
        print(f"  {i+1}. {path}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"\nError type: {type(e).__name__}")
    print("\nFull traceback:")
    traceback.print_exc()

    # Try to find the specific model causing issues
    print("\n" + "=" * 80)
    print("Attempting to identify problematic model...")
    print("=" * 80)

    # Get the traceback object
    import sys

    tb = sys.exc_info()[2]

    # Walk through the stack
    if tb:
        frame = tb.tb_frame
        depth = 0
        while frame and depth < 20:
            local_vars = frame.f_locals
            code = frame.f_code

            # Look for model-related variables
            if (
                "model" in local_vars
                or "schema" in local_vars
                or "__pydantic" in str(local_vars.keys())
            ):
                print(f"\nFrame {depth}: {code.co_filename}:{code.co_name} (line {frame.f_lineno})")

                if "model" in local_vars and hasattr(local_vars["model"], "__name__"):
                    print(f"  Model: {local_vars['model'].__name__}")

                if "field_name" in local_vars:
                    print(f"  Field: {local_vars['field_name']}")

            frame = frame.f_back if hasattr(frame, "f_back") else None
            depth += 1
