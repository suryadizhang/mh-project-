"""Check what classes are registered in SQLAlchemy Base registry."""
import sys
sys.path.insert(0, 'src')

from models.base import Base

print("Classes in Base registry:")
for mapper in Base.registry.mappers:
    print(f"  - {mapper.class_.__name__} (from {mapper.class_.__module__})")
    print(f"    Table: {mapper.mapped_table.name if hasattr(mapper, 'mapped_table') else 'N/A'}")
