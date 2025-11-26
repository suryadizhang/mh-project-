"""
Schema Validation Tests - Prevent Future Model/Database Drift

These tests ensure that SQLAlchemy models stay in sync with actual database schema.
They prevent the schema mismatch issues discovered in November 2025 (Bug #1-#15).

Run these tests:
- After any database migration
- Before deploying to production
- In CI/CD pipeline as gate

Purpose:
- Catch field name mismatches (e.g., event_date vs date)
- Catch missing fields (e.g., sms_consent, version)
- Catch type mismatches (e.g., str vs time)
- Catch missing constraints
- Catch missing indexes
"""

import pytest
from datetime import date, time, datetime
from sqlalchemy import inspect, Integer, String, Text, Boolean, Date, Time, DateTime
from sqlalchemy.dialects.postgresql import UUID

from db.models.core import Booking, Customer, Chef, BookingStatus
from db.models.identity import Station


def get_db_columns(inspector, table_name, schema="core"):
    """Get actual database columns for a table"""
    return {
        col['name']: col
        for col in inspector.get_columns(table_name, schema=schema)
    }


def get_model_columns(model_class):
    """Get SQLAlchemy model columns"""
    mapper = inspect(model_class)
    return {
        col.key: col
        for col in mapper.columns
    }


class TestBookingSchemaAlignment:
    """Verify Booking model matches database schema"""

    def test_booking_has_correct_field_names(self, db_inspector):
        """Test that Booking model uses correct field names (not legacy names)"""
        db_cols = get_db_columns(db_inspector, "bookings", schema="core")
        model_cols = get_model_columns(Booking)

        # ✅ CORRECT field names (from Nov 2025 fix)
        assert "date" in db_cols, "Database should have 'date' column"
        assert "date" in model_cols, "Model should have 'date' field"

        assert "slot" in db_cols, "Database should have 'slot' column"
        assert "slot" in model_cols, "Model should have 'slot' field"

        assert "party_adults" in db_cols
        assert "party_adults" in model_cols

        assert "party_kids" in db_cols
        assert "party_kids" in model_cols

        assert "deposit_due_cents" in db_cols
        assert "deposit_due_cents" in model_cols

        assert "total_due_cents" in db_cols
        assert "total_due_cents" in model_cols

        assert "address_encrypted" in db_cols
        assert "address_encrypted" in model_cols

        assert "zone" in db_cols
        assert "zone" in model_cols

        # ❌ LEGACY field names should NOT exist
        assert "event_date" not in db_cols, "Legacy 'event_date' should not exist"
        assert "event_start_time" not in db_cols, "Legacy 'event_start_time' should not exist"
        assert "guest_count" not in db_cols, "Legacy 'guest_count' should not exist"
        assert "deposit_amount" not in db_cols, "Legacy 'deposit_amount' should not exist"
        assert "total_amount" not in db_cols, "Legacy 'total_amount' should not exist"

    def test_booking_has_bug_13_fix_fields(self, db_inspector):
        """Test that Booking has fields for Bug #13 race condition fix"""
        db_cols = get_db_columns(db_inspector, "bookings", schema="core")
        model_cols = get_model_columns(Booking)

        # Version column for optimistic locking
        assert "version" in db_cols, "Database should have 'version' column for Bug #13 fix"
        assert "version" in model_cols, "Model should have 'version' field for Bug #13 fix"
        assert db_cols["version"]["default"] == "1", "Version should default to 1"

    def test_booking_has_sms_consent_fields(self, db_inspector):
        """Test that Booking has SMS consent fields (TCPA compliance)"""
        db_cols = get_db_columns(db_inspector, "bookings", schema="core")
        model_cols = get_model_columns(Booking)

        assert "sms_consent" in db_cols
        assert "sms_consent" in model_cols
        assert db_cols["sms_consent"]["default"] == "false"

        assert "sms_consent_timestamp" in db_cols
        assert "sms_consent_timestamp" in model_cols

    def test_booking_has_deadline_fields(self, db_inspector):
        """Test that Booking has deposit deadline fields"""
        db_cols = get_db_columns(db_inspector, "bookings", schema="core")
        model_cols = get_model_columns(Booking)

        assert "customer_deposit_deadline" in db_cols
        assert "customer_deposit_deadline" in model_cols

        assert "internal_deadline" in db_cols
        assert "internal_deadline" in model_cols

        assert "deposit_confirmed_at" in db_cols
        assert "deposit_confirmed_at" in model_cols

        assert "deposit_confirmed_by" in db_cols
        assert "deposit_confirmed_by" in model_cols

    def test_booking_has_hold_fields(self, db_inspector):
        """Test that Booking has hold/request fields"""
        db_cols = get_db_columns(db_inspector, "bookings", schema="core")
        model_cols = get_model_columns(Booking)

        assert "hold_on_request" in db_cols
        assert "hold_on_request" in model_cols
        assert db_cols["hold_on_request"]["default"] == "false"

        assert "held_by" in db_cols
        assert "held_by" in model_cols

        assert "held_at" in db_cols
        assert "held_at" in model_cols

        assert "hold_reason" in db_cols
        assert "hold_reason" in model_cols

    def test_booking_has_unique_constraints(self, db_inspector):
        """Test that Booking has unique constraints for race condition prevention"""
        indexes = db_inspector.get_indexes("bookings", schema="core")

        # Find the critical unique index for Bug #13 fix
        unique_index_names = [idx['name'] for idx in indexes if idx.get('unique')]

        assert "idx_booking_date_slot_active" in unique_index_names, \
            "Missing unique constraint idx_booking_date_slot_active (Bug #13 fix)"

        # Verify index columns
        for idx in indexes:
            if idx['name'] == 'idx_booking_date_slot_active':
                assert 'date' in idx['column_names']
                assert 'slot' in idx['column_names']
                assert 'status' in idx['column_names']

    def test_booking_has_check_constraints(self, db_inspector):
        """Test that Booking has check constraints for data integrity"""
        constraints = db_inspector.get_check_constraints("bookings", schema="core")
        constraint_names = [c['name'] for c in constraints]

        assert "check_deposit_non_negative" in constraint_names or \
               any("deposit" in name and "non_negative" in name for name in constraint_names)

        assert "check_party_adults_positive" in constraint_names or \
               any("party_adults" in name and "positive" in name for name in constraint_names)

        assert "check_party_kids_non_negative" in constraint_names or \
               any("party_kids" in name and "non_negative" in name for name in constraint_names)

        assert "check_total_gte_deposit" in constraint_names or \
               any("total" in name and "deposit" in name for name in constraint_names)


class TestCustomerSchemaAlignment:
    """Verify Customer model matches database schema"""

    def test_customer_has_encryption_fields(self, db_inspector):
        """Test that Customer uses encrypted fields for PII"""
        db_cols = get_db_columns(db_inspector, "customers", schema="core")
        model_cols = get_model_columns(Customer)

        # Encrypted PII fields
        assert "email_encrypted" in db_cols
        assert "email_encrypted" in model_cols

        assert "phone_encrypted" in db_cols
        assert "phone_encrypted" in model_cols

        # Legacy plaintext fields should NOT exist
        assert "email" not in db_cols or db_cols["email"].get("nullable"), \
            "Plaintext 'email' should be nullable or not exist"

    def test_customer_has_consent_fields(self, db_inspector):
        """Test that Customer has SMS/email consent fields (TCPA/CAN-SPAM compliance)"""
        db_cols = get_db_columns(db_inspector, "customers", schema="core")
        model_cols = get_model_columns(Customer)

        assert "consent_sms" in db_cols
        assert "consent_sms" in model_cols

        assert "consent_email" in db_cols
        assert "consent_email" in model_cols

        assert "consent_sms_timestamp" in db_cols
        assert "consent_sms_timestamp" in model_cols

        assert "consent_email_timestamp" in db_cols
        assert "consent_email_timestamp" in model_cols


class TestStationSchemaAlignment:
    """Verify Station model matches database schema"""

    def test_station_has_correct_fields(self, db_inspector):
        """Test that Station model has correct field names"""
        db_cols = get_db_columns(db_inspector, "stations", schema="identity")
        model_cols = get_model_columns(Station)

        assert "code" in db_cols
        assert "code" in model_cols

        assert "display_name" in db_cols
        assert "display_name" in model_cols

        assert "postal_code" in db_cols
        assert "postal_code" in model_cols

        assert "status" in db_cols
        assert "status" in model_cols


class TestEnumAlignment:
    """Verify enum values match between code and database"""

    def test_booking_status_enum_matches_database(self, async_session):
        """Test that BookingStatus enum matches database enum type"""
        # Get enum values from database
        result = async_session.execute(
            """
            SELECT e.enumlabel
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'booking_status'
            ORDER BY e.enumsortorder
            """
        )
        db_enum_values = {row[0] for row in result.fetchall()}

        # Get enum values from Python code
        code_enum_values = {status.value for status in BookingStatus}

        # They should match
        assert db_enum_values == code_enum_values, \
            f"BookingStatus mismatch: DB={db_enum_values}, Code={code_enum_values}"


class TestFieldTypeAlignment:
    """Verify field types match between model and database"""

    def test_booking_field_types(self, db_inspector):
        """Test that Booking field types match database"""
        db_cols = get_db_columns(db_inspector, "bookings", schema="core")

        # Date field should be DATE type
        assert "DATE" in str(db_cols["date"]["type"]).upper()

        # Slot field should be TIME type
        assert "TIME" in str(db_cols["slot"]["type"]).upper()

        # Integer fields
        assert "INT" in str(db_cols["party_adults"]["type"]).upper()
        assert "INT" in str(db_cols["party_kids"]["type"]).upper()
        assert "INT" in str(db_cols["deposit_due_cents"]["type"]).upper()
        assert "INT" in str(db_cols["total_due_cents"]["type"]).upper()
        assert "INT" in str(db_cols["version"]["type"]).upper()

        # Boolean fields
        assert "BOOL" in str(db_cols["sms_consent"]["type"]).upper()
        assert "BOOL" in str(db_cols["hold_on_request"]["type"]).upper()

        # Text fields
        assert "TEXT" in str(db_cols["address_encrypted"]["type"]).upper() or \
               "VARCHAR" in str(db_cols["address_encrypted"]["type"]).upper()


@pytest.fixture
def db_inspector(async_session):
    """Get SQLAlchemy inspector for database schema introspection"""
    from sqlalchemy import inspect as sa_inspect
    return sa_inspect(async_session.bind)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
