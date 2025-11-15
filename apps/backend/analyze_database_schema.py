"""Analyze actual database schema from models and migrations."""

import re
from pathlib import Path
from collections import defaultdict


def analyze_models():
    """Analyze SQLAlchemy models to understand business entities."""
    models_dir = Path("src/models")
    entities = {}

    for file in models_dir.glob("*.py"):
        if file.name.startswith("__"):
            continue

        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find class definitions
        class_matches = re.findall(r"class (\w+)\(Base\):", content)

        # Find relationships
        relationships = re.findall(
            r'(\w+)\s*=\s*relationship\(["\'](\w+)["\']', content
        )

        for cls in class_matches:
            if cls not in entities:
                entities[cls] = {"file": file.name, "relationships": []}

            for rel_name, rel_target in relationships:
                entities[cls]["relationships"].append(
                    {"name": rel_name, "target": rel_target}
                )

    return entities


def analyze_migrations():
    """Analyze migration files to understand actual database tables."""
    migrations_dir = Path("src/db/migrations/alembic/versions")
    tables = defaultdict(lambda: {"foreign_keys": [], "columns": []})

    for file in migrations_dir.glob("*.py"):
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find table creations with better regex
        table_pattern = r"op\.create_table\(\s*['\"]([^'\"]+)['\"]"
        table_matches = re.findall(table_pattern, content)

        for table in table_matches:
            tables[table]["migration_file"] = file.name

            # Find columns for this table
            # Look for sa.Column patterns after create_table
            column_pattern = r"sa\.Column\(['\"]([^'\"]+)['\"]"
            columns = re.findall(column_pattern, content)
            tables[table]["columns"].extend(
                columns[:20]
            )  # Limit to avoid duplicates

    return dict(tables)


def main():
    print("=" * 80)
    print("DATABASE SCHEMA & BUSINESS MODEL ANALYSIS")
    print("=" * 80)
    print()

    # Analyze models
    print("📊 ANALYZING SQLALCHEMY MODELS...")
    entities = analyze_models()

    print(f"\n✅ Found {len(entities)} business entities\n")

    # Group by domain
    domains = {
        "Core": [
            "Customer",
            "Booking",
            "Payment",
            "Message",
            "MessageThread",
            "Event",
        ],
        "Lead Management": [
            "Lead",
            "LeadContact",
            "Subscriber",
            "Campaign",
            "CampaignEvent",
        ],
        "Social": [
            "SocialAccount",
            "SocialIdentity",
            "SocialThread",
            "SocialMessage",
            "Review",
            "SocialInbox",
        ],
        "Payments": [
            "StripeCustomer",
            "StripePayment",
            "Invoice",
            "Product",
            "Price",
            "WebhookEvent",
            "Refund",
            "Dispute",
        ],
        "CateringPayments": [
            "CateringBooking",
            "CateringPayment",
            "PaymentNotification",
        ],
        "Reviews": ["CustomerReview", "DiscountCoupon", "ReviewEscalation"],
        "Notifications": [
            "NotificationGroup",
            "NotificationGroupMember",
            "NotificationGroupEvent",
        ],
        "QR/Tracking": ["QRCode", "QRScan"],
        "Knowledge Base": [
            "BusinessRule",
            "FAQItem",
            "TrainingData",
            "UpsellRule",
            "SeasonalOffer",
            "AvailabilityCalendar",
            "CustomerTonePreference",
            "MenuItem",
            "PricingTier",
            "SyncHistory",
        ],
        "Auth/RBAC": ["User", "Role", "Permission", "Station"],
        "AI/System": [
            "SystemEvent",
            "Escalation",
            "CallRecording",
            "Business",
        ],
        "Event Sourcing": [
            "DomainEvent",
            "OutboxEntry",
            "Snapshot",
            "ProjectionPosition",
            "IdempotencyKey",
        ],
        "Legacy": [
            "LegacyUser",
            "LegacyBooking",
            "TimeSlotConfiguration",
            "BookingAvailability",
        ],
    }

    for domain, entity_list in domains.items():
        found = [e for e in entity_list if e in entities]
        if found:
            print(f"\n🏢 {domain} Domain ({len(found)} entities)")
            for entity in found:
                info = entities[entity]
                rel_count = len(info["relationships"])
                rel_str = (
                    f" → {rel_count} relationships" if rel_count > 0 else ""
                )
                print(f"   ├── {entity}{rel_str}")

                # Show key relationships
                if rel_count > 0 and rel_count <= 5:
                    for rel in info["relationships"][:3]:
                        print(f"   │   └─> {rel['name']} → {rel['target']}")

    # Analyze migrations
    print("\n" + "=" * 80)
    print("📊 ANALYZING DATABASE TABLES FROM MIGRATIONS...")
    tables = analyze_migrations()

    print(f"\n✅ Found {len(tables)} database tables\n")

    # Group by schema
    schemas = defaultdict(list)
    for table in sorted(tables.keys()):
        if "." in table:
            schema, table_name = table.split(".", 1)
        else:
            schema = "public"
            table_name = table
        schemas[schema].append(table_name)

    for schema, table_list in sorted(schemas.items()):
        print(f"\n📁 Schema: {schema} ({len(table_list)} tables)")
        for table in sorted(table_list)[:15]:  # Limit display
            print(f"   ├── {table}")
        if len(table_list) > 15:
            print(f"   └── ... and {len(table_list) - 15} more")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Business Entities: {len(entities)}")
    print(f"Total Database Tables: {len(tables)}")
    print(f"Total Schemas: {len(schemas)}")


if __name__ == "__main__":
    main()
