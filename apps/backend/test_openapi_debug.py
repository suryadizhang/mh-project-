"""
Debug script to test OpenAPI schema generation and find the problematic model
"""
import sys
sys.path.insert(0, 'src')

from fastapi import FastAPI
from api.main import app

print("Testing OpenAPI schema generation...")
print("=" * 60)

try:
    # This will trigger the schema generation
    schema = app.openapi()
    paths_count = len(schema.get("paths", {}))
    print(f"✅ SUCCESS! Generated schema with {paths_count} endpoints")
    
    # Print first 10 endpoints
    if paths_count > 0:
        print("\nFirst 10 endpoints:")
        for i, path in enumerate(list(schema["paths"].keys())[:10]):
            print(f"  {i+1}. {path}")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
