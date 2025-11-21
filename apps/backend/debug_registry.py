"""Debug SQLAlchemy registry to find duplicate CustomerTonePreference"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.base import Base

# Check the registry
registry = Base.registry._class_registry
print("=== Searching registry for CustomerTonePreference (after Customer import) ===\n")

count = 0
for key, value in registry.items():
    if "CustomerTonePreference" in str(key):
        count += 1
        print(f"#{count} Key: {key}")
        print(f"    Value: {value}")
        print(f"    Type: {type(value)}")
        if hasattr(value, "__module__"):
            print(f"    Module: {value.__module__}")
        print("-" * 80)

print(f"\nTotal CustomerTonePreference entries: {count}")

print("\n=== All registered model classes ===\n")
for key in sorted(registry.keys()):
    if isinstance(key, str) and key[0].isupper():
        print(f"  - {key}")
