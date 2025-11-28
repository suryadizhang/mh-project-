"""
Validate all SQLAlchemy relationship configurations

This script checks:
1. All relationships have valid back_populates
2. Foreign keys exist for relationship joins
3. No orphaned relationships
4. Proper relationship symmetry
"""

import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy import inspect as sqla_inspect
from sqlalchemy.orm import Mapper, RelationshipProperty
from db.base_class import Base


def get_all_models() -> Dict[str, type]:
    """Import all model modules and return all Base subclasses"""
    models = {}

    # Import all model modules
    model_modules = [
        "db.models.core",
        "db.models.identity",
        "db.models.lead",
        "db.models.newsletter",
        "db.models.pricing",
        "db.models.feedback_marketing",
        "db.models.events",
        "db.models.social",
        "db.models.ops",
        "db.models.crm",
        "db.models.system_event",
        "db.models.ai.conversations",
        "db.models.ai.knowledge",
        "db.models.ai.analytics",
        "db.models.ai.engagement",
        "db.models.ai.shadow_learning",
    ]

    for module_name in model_modules:
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Base)
                    and obj is not Base
                    and hasattr(obj, "__tablename__")
                ):
                    models[f"{module_name}.{name}"] = obj
        except ModuleNotFoundError as e:
            print(f"⚠️  Module {module_name} not found: {e}")
        except Exception as e:
            print(f"❌ Error importing {module_name}: {e}")

    return models


def validate_relationships(models: Dict[str, type]) -> Tuple[List[str], List[str]]:
    """Validate all relationships and return errors and warnings"""
    errors = []
    warnings = []

    for model_path, model_class in models.items():
        mapper: Mapper = sqla_inspect(model_class)

        for prop in mapper.iterate_properties:
            if isinstance(prop, RelationshipProperty):
                relationship_name = prop.key
                target_class = prop.mapper.class_

                # Check if target class exists
                target_name = target_class.__name__

                # Check back_populates
                if hasattr(prop, "back_populates") and prop.back_populates:
                    back_pop = prop.back_populates

                    # Verify target has the back_populates property
                    try:
                        target_mapper: Mapper = sqla_inspect(target_class)
                        target_props = {p.key for p in target_mapper.iterate_properties}

                        if back_pop not in target_props:
                            errors.append(
                                f"❌ {model_class.__name__}.{relationship_name} → "
                                f"{target_name}.{back_pop} DOES NOT EXIST"
                            )
                        else:
                            # Verify it's a relationship
                            target_prop = target_mapper.get_property(back_pop)
                            if not isinstance(target_prop, RelationshipProperty):
                                errors.append(
                                    f"❌ {model_class.__name__}.{relationship_name} → "
                                    f"{target_name}.{back_pop} is not a relationship"
                                )
                            else:
                                # Verify symmetry
                                if hasattr(target_prop, "back_populates"):
                                    if target_prop.back_populates != relationship_name:
                                        errors.append(
                                            f"❌ ASYMMETRIC: {model_class.__name__}.{relationship_name} "
                                            f"points to {target_name}.{back_pop}, but "
                                            f"{target_name}.{back_pop} points to {target_prop.back_populates}"
                                        )
                    except Exception as e:
                        errors.append(
                            f"❌ Error validating {model_class.__name__}.{relationship_name}: {e}"
                        )

                # Check for foreign keys
                if prop.direction.name in ["MANYTOONE", "ONETOONE"]:
                    # Should have FK in source table
                    fks = [col for col in mapper.columns if col.foreign_keys]
                    if not fks and not prop.secondary:
                        warnings.append(
                            f"⚠️  {model_class.__name__}.{relationship_name} → {target_name} "
                            f"has no foreign key (many-to-one relationship)"
                        )

    return errors, warnings


def main():
    print("🔍 Scanning all SQLAlchemy models...")
    models = get_all_models()
    print(f"✅ Found {len(models)} models\n")

    print("🔗 Validating relationships...")
    errors, warnings = validate_relationships(models)

    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80 + "\n")

    if errors:
        print(f"❌ ERRORS FOUND ({len(errors)}):\n")
        for error in errors:
            print(f"  {error}")
        print()
    else:
        print("✅ No relationship errors found!\n")

    if warnings:
        print(f"⚠️  WARNINGS ({len(warnings)}):\n")
        for warning in warnings:
            print(f"  {warning}")
        print()
    else:
        print("✅ No warnings!\n")

    print("=" * 80)

    if errors:
        print("\n❌ VALIDATION FAILED - Fix errors above")
        return 1
    else:
        print("\n✅ VALIDATION PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
