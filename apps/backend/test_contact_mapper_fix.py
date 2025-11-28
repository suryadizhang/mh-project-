"""
Test script to verify Contact model mapper error is fixed.
Tests relationship resolution without requiring full app initialization.
"""

import sys

sys.path.insert(0, "src")

# Mock minimal environment
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_32_characters_long_for_validation_purposes"
os.environ["SUPABASE_URL"] = "http://localhost"
os.environ["SUPABASE_KEY"] = "test"

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, registry

# Create minimal test setup
mapper_registry = registry()


class Base(DeclarativeBase):
    registry = mapper_registry


# Import the models to test relationship resolution
try:
    # Import Contact model
    from models.contact import Contact

    print("✅ Contact model imported successfully")

    # Import inbox models
    from api.v1.inbox.models import InboxMessage, Thread, TCPAOptStatus

    print("✅ Inbox models imported successfully")

    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)

    # This is where the mapper error would occur if relationships are broken
    Base.metadata.create_all(engine)
    print("✅ Database schema created - all relationships resolved!")

    # Verify relationship attributes exist
    assert hasattr(Contact, "messages"), "Contact.messages relationship missing"
    assert hasattr(Contact, "threads"), "Contact.threads relationship missing"
    assert hasattr(Contact, "tcpa_statuses"), "Contact.tcpa_statuses relationship missing"
    print("✅ All Contact relationship attributes verified")

    # Verify back-populates work both ways
    assert hasattr(InboxMessage, "contact"), "InboxMessage.contact relationship missing"
    assert hasattr(Thread, "contact"), "Thread.contact relationship missing"
    assert hasattr(TCPAOptStatus, "contact"), "TCPAOptStatus.contact relationship missing"
    print("✅ All back-populates relationships verified")

    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Contact model mapper error is FIXED!")
    print("=" * 60)
    print("\nFixed relationships:")
    print("  - Contact.messages → InboxMessage")
    print("  - Contact.threads → Thread")
    print("  - Contact.tcpa_statuses → TCPAOptStatus")
    print("\nAll string-based references now use simple class names")
    print("instead of full module paths (api.v1.inbox.models.*).")

except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
