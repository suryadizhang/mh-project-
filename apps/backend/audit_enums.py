"""Complete Enum Audit Script - Check all enum mismatches between Python models and database"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL_SYNC"))

print("=" * 80)
print("COMPLETE ENUM AUDIT - Database vs SQLAlchemy Models")
print("=" * 80)

# Get all enum types from database
with engine.connect() as conn:
    result = conn.execute(
        text(
            """
        SELECT 
            t.typname as enum_name,
            n.nspname as schema_name,
            array_agg(e.enumlabel ORDER BY e.enumsortorder) as values
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        JOIN pg_namespace n ON t.typnamespace = n.oid
        WHERE n.nspname IN ('public', 'lead', 'newsletter', 'core', 'identity')
        GROUP BY t.typname, n.nspname
        ORDER BY n.nspname, t.typname
    """
        )
    )

    db_enums = {}
    for row in result:
        enum_name = row[0]
        schema = row[1]
        values = row[2]
        db_enums[f"{schema}.{enum_name}"] = values

    print(f"\nFound {len(db_enums)} enum types in database:\n")

    for full_name, values in sorted(db_enums.items()):
        print(f"- {full_name}")
        print(
            f"   Values ({len(values)}): {', '.join(values[:5])}"
            + (f" ... +{len(values)-5} more" if len(values) > 5 else "")
        )

# Now check Python enums
print("\n" + "=" * 80)
print("CHECKING SQLALCHEMY MODEL ENUMS")
print("=" * 80)

from models.legacy_lead_newsletter import (
    LeadSource,
    LeadStatus,
    LeadQuality,
    ContactChannel,
    SocialPlatform,
    ThreadStatus,
    CampaignChannel,
    CampaignStatus,
    CampaignEventType,
)

python_enums = {
    "LeadSource": LeadSource,
    "LeadStatus": LeadStatus,
    "LeadQuality": LeadQuality,
    "ContactChannel": ContactChannel,
    "SocialPlatform": SocialPlatform,
    "ThreadStatus": ThreadStatus,
    "CampaignChannel": CampaignChannel,
    "CampaignStatus": CampaignStatus,
    "CampaignEventType": CampaignEventType,
}

print(f"\n📊 Found {len(python_enums)} Python Enum classes:\n")

mismatches = []

for name, enum_class in python_enums.items():
    values = [e.value for e in enum_class]
    print(f"🔹 {name}")
    print(f"   Values ({len(values)}): {', '.join(values)}")

    # Try to find matching database enum
    possible_db_names = [
        f"lead.{name.lower()}",
        f"lead.{name.lower().replace('source', '_source').replace('status', '_status')}",
        f"newsletter.{name.lower()}",
        f"public.{name.lower()}",
    ]

    found_in_db = None
    for db_name in possible_db_names:
        if db_name in db_enums:
            found_in_db = db_name
            break

    if found_in_db:
        db_values = db_enums[found_in_db]
        python_values = set(values)
        db_values_set = set(db_values)

        missing_in_db = python_values - db_values_set
        extra_in_db = db_values_set - python_values

        if missing_in_db or extra_in_db:
            mismatches.append(
                {
                    "python_enum": name,
                    "db_enum": found_in_db,
                    "missing_in_db": missing_in_db,
                    "extra_in_db": extra_in_db,
                    "python_values": python_values,
                    "db_values": db_values_set,
                }
            )
            print(f"   ⚠️  MISMATCH with {found_in_db}")
            if missing_in_db:
                print(f"      Missing in DB: {missing_in_db}")
            if extra_in_db:
                print(f"      Extra in DB: {extra_in_db}")
        else:
            print(f"   ✅ Matches {found_in_db}")
    else:
        print("   ❌ NOT FOUND in database")
        mismatches.append(
            {
                "python_enum": name,
                "db_enum": None,
                "missing_in_db": set(values),
                "extra_in_db": set(),
                "python_values": set(values),
                "db_values": set(),
            }
        )

# Check Column definitions
print("\n" + "=" * 80)
print("CHECKING COLUMN ENUM REFERENCES")
print("=" * 80)

from models.legacy_lead_newsletter import (
    Lead,
    LeadContact,
    SocialThread,
    Subscriber,
)

models_to_check = [
    ("Lead", Lead),
    ("LeadContact", LeadContact),
    ("SocialThread", SocialThread),
    ("Subscriber", Subscriber),
]

print("\n🔍 Checking Column() enum name parameters:\n")

import sqlalchemy as sa

for model_name, model_class in models_to_check:
    print(f"📋 {model_name}:")
    for col_name, col in model_class.__table__.columns.items():
        if isinstance(col.type, sa.Enum):
            enum_type = col.type
            python_enum = enum_type.enum_class
            db_type_name = (
                enum_type.name
                if hasattr(enum_type, "name") and enum_type.name
                else "NOT SPECIFIED"
            )
            create_type = (
                enum_type.create_type
                if hasattr(enum_type, "create_type")
                else True
            )

            print(f"   • {col_name}: Enum({python_enum.__name__})")
            print(f"     DB type name: {db_type_name}")
            print(f"     create_type: {create_type}")

            if db_type_name == "NOT SPECIFIED":
                print(
                    "     ⚠️  WARNING: No explicit 'name' parameter - SQLAlchemy will auto-generate"
                )

# Summary
print("\n" + "=" * 80)
print("SUMMARY & RECOMMENDATIONS")
print("=" * 80)

if mismatches:
    print(f"\n❌ Found {len(mismatches)} enum mismatches:\n")

    for i, mismatch in enumerate(mismatches, 1):
        print(f"{i}. {mismatch['python_enum']}")
        if mismatch["db_enum"]:
            print(f"   Database: {mismatch['db_enum']}")
        else:
            print("   Database: NOT FOUND")

        if mismatch["missing_in_db"]:
            print(f"   ⚠️  Add to DB: {mismatch['missing_in_db']}")
        if mismatch["extra_in_db"]:
            print(f"   ⚠️  Remove or keep in DB: {mismatch['extra_in_db']}")
else:
    print("\n✅ All enums match!")

print("\n" + "=" * 80)
print("RECOMMENDED ACTIONS:")
print("=" * 80)
print(
    """
1. Create Alembic migration to add missing enum values
2. Update Column() definitions with explicit name= parameter
3. Set create_type=False to prevent auto-creation
4. Run migration on all environments
5. Re-run tests to verify
"""
)
