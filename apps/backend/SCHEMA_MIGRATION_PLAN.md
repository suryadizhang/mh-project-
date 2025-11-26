# Schema Migration Plan - Auto-Generated Models

**Generated**: November 26, 2025 **Tool**: sqlacodegen **Status**:
READY FOR REVIEW

---

## Executive Summary

Auto-generated models from actual PostgreSQL database reveal
**CRITICAL differences** between current Python models and database
schema.

**Key Findings**:

1. ✅ Generated models match database 100%
2. 🔴 Current models have wrong field names, types, and missing
   columns
3. 🔴 Security issue: Models expect plaintext, DB has encrypted fields
4. ✅ Relationships are correct in generated models

---

## Critical Schema Mismatches Found

### 1. Customer Model (core.customers)

**Generated Model** (CORRECT - matches database):

```python
class Customers(Base):
    __tablename__ = 'customers'
    __table_args__ = {'schema': 'core'}

    id: Mapped[uuid.UUID]
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email_encrypted: Mapped[str] = mapped_column(Text)  # ✅ ENCRYPTED
    phone_encrypted: Mapped[str] = mapped_column(Text)  # ✅ ENCRYPTED
    consent_sms: Mapped[bool]  # ✅ Correct field name
    consent_email: Mapped[bool]  # ✅ Correct field name
    consent_updated_at: Mapped[Optional[datetime]]  # ✅ NEW field
    timezone: Mapped[str] = mapped_column(String(50))  # ✅ NEW field
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(50)))  # ✅ NEW field
    notes: Mapped[Optional[str]] = mapped_column(Text)  # ✅ NEW field
    deleted_at: Mapped[Optional[datetime]]  # ✅ NEW field (soft delete)
    station_id: Mapped[uuid.UUID]  # ✅ NOT NULL (required)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

**Current Model** (WRONG - db/models/core.py):

```python
class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {"schema": "core"}

    id: Mapped[UUID]
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str]  # ❌ WRONG - should be email_encrypted
    phone: Mapped[str]  # ❌ WRONG - should be phone_encrypted
    marketing_consent: Mapped[bool]  # ❌ WRONG - should be consent_email, consent_sms
    station_id: Mapped[Optional[UUID]]  # ❌ WRONG - should be NOT NULL
    # ❌ MISSING: consent_updated_at, timezone, tags, notes, deleted_at
```

**Legacy Model** (WRONG - models/customer.py):

```python
class Customer(BaseModel):
    __tablename__ = "customers"
    # ❌ NO SCHEMA - maps to public.customers (doesn't exist!)

    email = Column(String(255))  # ❌ Old-style Column, wrong name
    phone = Column(String(20))  # ❌ Old-style Column, wrong name
    email_notifications = Column(Boolean)  # ❌ Wrong field name
    sms_notifications = Column(Boolean)  # ❌ Wrong field name
    # ❌ MISSING: Most fields
```

**Impact**: 🔴 CRITICAL - Cannot create/query customers, security risk
(plaintext vs encrypted)

---

### 2. Booking Model (core.bookings)

**Generated Model** (CORRECT):

```python
class Bookings(Base):
    __tablename__ = 'bookings'
    __table_args__ = (
        CheckConstraint('deposit_due_cents >= 0', name='check_deposit_non_negative'),
        CheckConstraint('party_adults > 0', name='check_party_adults_positive'),
        CheckConstraint('party_kids >= 0', name='check_party_kids_non_negative'),
        CheckConstraint('total_due_cents >= deposit_due_cents', name='check_total_gte_deposit'),
        ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='RESTRICT'),
        Index('idx_booking_date_slot_active', 'date', 'slot', unique=True, postgresql_where=text("status IN ('new', 'deposit_pending', 'confirmed')")),
        {'schema': 'core'}
    )

    status: Mapped[Enum] = mapped_column(Enum('new', 'deposit_pending', 'confirmed', 'completed', 'cancelled', 'no_show', name='booking_status'))
    sms_consent: Mapped[bool]  # ✅ New field for booking-level consent
    sms_consent_timestamp: Mapped[Optional[datetime]]  # ✅ New field
```

**Current Model** (PARTIALLY FIXED):

```python
class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint(...),  # ✅ Has unique constraint (recently fixed)
        {"schema": "core"}
    )

    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, name="booking_status", native_enum=True, values_callable=...)
    )  # ✅ FIXED in recent session
    # ❌ MISSING: sms_consent, sms_consent_timestamp
    # ❌ MISSING: Some check constraints
```

**Impact**: ⚠️ MEDIUM - Status enum fixed, but missing consent fields
and constraints

---

### 3. Station Model (identity.stations)

**Generated Model** (CORRECT):

```python
class Stations(Base):
    __tablename__ = 'stations'
    __table_args__ = (
        Index('ix_identity_stations_code', 'code', unique=True),
        Index('ix_identity_stations_email', 'email', unique=True),
        {'schema': 'identity'}
    )

    id: Mapped[uuid.UUID]
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(20))  # ✅ Has code field
    display_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    address_line1: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2))
    postal_code: Mapped[str] = mapped_column(String(10))  # ✅ postal_code, not zip_code!
    country: Mapped[str] = mapped_column(String(2))
    timezone: Mapped[str] = mapped_column(String(50))
    # ... and more fields
```

**Issue in Tests**: Test tried to use `zip_code` field which doesn't
exist → should be `postal_code`

**Impact**: ⚠️ MEDIUM - Test fixture broken, but model may exist (need
to check)

---

## Files Generated

1. **`db/models_generated/core_generated.py`** (418 lines)
   - Customers
   - Bookings
   - Chefs
   - MessageThreads
   - Messages
   - Reviews
   - SocialAccounts
   - SocialIdentities
   - SocialMessages
   - SocialThreads

2. **`db/models_generated/identity_generated.py`** (generated)
   - Stations
   - Users
   - Roles
   - Permissions
   - StationUsers
   - StationAccessTokens
   - StationAuditLogs
   - RolePermissions
   - UserRoles

---

## Migration Strategy

### Phase 1: Backup Everything (5 minutes)

```bash
# Backup current models
cp -r src/models src/models_BACKUP_$(date +%Y%m%d)
cp -r src/db/models src/db/models_BACKUP_$(date +%Y%m%d)

# Backup tests
cp -r tests tests_BACKUP_$(date +%Y%m%d)
```

### Phase 2: Update Core Models (2 hours)

**File: `db/models/core.py`**

Update Customer class:

```python
class Customer(Base):  # Rename from Customer to match generated (or keep Customer and update fields)
    __tablename__ = 'customers'
    __table_args__ = (
        ForeignKeyConstraint(['station_id'], ['identity.stations.id'], ondelete='RESTRICT'),
        Index('idx_customer_station_email', 'station_id', 'email_encrypted', unique=True),
        {'schema': 'core'}
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))

    # ✅ UPDATE: Use encrypted fields
    email_encrypted: Mapped[str] = mapped_column(Text)
    phone_encrypted: Mapped[str] = mapped_column(Text)

    # ✅ UPDATE: Use correct consent field names
    consent_sms: Mapped[bool] = mapped_column(Boolean)
    consent_email: Mapped[bool] = mapped_column(Boolean)
    consent_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ✅ ADD: Missing fields
    timezone: Mapped[str] = mapped_column(String(50))
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(50)))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ✅ FIX: station_id is NOT NULL
    station_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ✅ ADD: Helper methods for encryption/decryption
    @property
    def email(self) -> str:
        """Decrypt and return email"""
        from core.encryption import decrypt_field  # TODO: Implement encryption module
        return decrypt_field(self.email_encrypted)

    @email.setter
    def email(self, value: str):
        """Encrypt and store email"""
        from core.encryption import encrypt_field
        self.email_encrypted = encrypt_field(value)

    @property
    def phone(self) -> str:
        """Decrypt and return phone"""
        from core.encryption import decrypt_field
        return decrypt_field(self.phone_encrypted)

    @phone.setter
    def phone(self, value: str):
        """Encrypt and store phone"""
        from core.encryption import encrypt_field
        self.phone_encrypted = encrypt_field(value)

    # Relationships
    station: Mapped['Station'] = relationship('Station', back_populates='customers')
    bookings: Mapped[list['Booking']] = relationship('Booking', back_populates='customer')
    message_threads: Mapped[list['MessageThread']] = relationship('MessageThread', back_populates='customer')
```

Update Booking class:

```python
class Booking(Base):
    # ... existing fields ...

    # ✅ ADD: Missing consent fields
    sms_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    sms_consent_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ✅ ADD: Missing check constraints
    __table_args__ = (
        CheckConstraint('deposit_due_cents >= 0', name='check_deposit_non_negative'),
        CheckConstraint('party_adults > 0', name='check_party_adults_positive'),
        CheckConstraint('party_kids >= 0', name='check_party_kids_non_negative'),
        CheckConstraint('total_due_cents >= deposit_due_cents', name='check_total_gte_deposit'),
        # ... existing constraints ...
        {'schema': 'core'}
    )
```

### Phase 3: Delete Legacy Models (15 minutes)

**SAFE TO DELETE** (duplicates that map to wrong tables or wrong
schemas):

```bash
# DELETE these legacy models (after verifying no critical business logic)
rm src/models/customer.py  # ✅ Duplicate, maps to public.customers (doesn't exist)
rm src/models/booking.py   # ✅ Duplicate, check if has business logic first
# DO NOT delete models/ that don't have duplicates in db/models/
```

**Files to CHECK before deletion**:

- `models/customer.py` - Has deprecation warning, safe to delete
- `models/booking.py` - Check if has business logic (validation,
  methods)
- `models/events.py` - Duplicate exists in `db/models/events.py`
- `models/lead.py` - Duplicate exists in `db/models/lead.py`
- `models/newsletter.py` - Duplicate exists in
  `db/models/newsletter.py`

**Files to KEEP** (no duplicates):

- `models/base.py` - Base model class, might be used
- `models/mixins.py` - Shared mixins
- `models/email.py`, `models/social.py`, etc. - No duplicates in
  db/models/

### Phase 4: Update All Imports (1-2 hours)

Find and replace all imports:

```bash
# Find all files importing from legacy models
grep -r "from models.customer import" src/

# Replace with new imports
sed -i 's/from models\.customer import Customer/from db.models.core import Customer/g' **/*.py
sed -i 's/from models\.booking import Booking/from db.models.core import Booking/g' **/*.py
```

**OR use safer approach** (recommended):

```python
# Create migration script
# migration/update_imports.py
import os
import re

OLD_IMPORTS = {
    "from models.customer import Customer": "from db.models.core import Customer",
    "from models.booking import Booking": "from db.models.core import Booking",
    # ... add more ...
}

for root, dirs, files in os.walk("src"):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()

            for old, new in OLD_IMPORTS.items():
                content = content.replace(old, new)

            with open(filepath, 'w') as f:
                f.write(content)
```

### Phase 5: Update Tests (1 hour)

**Bug #13 test fixture** (test_race_condition_fix.py):

```python
@pytest.fixture
async def customer(self, db_session):
    """Create real customer in database"""
    from db.models.core import Customer
    from db.models.identity import Station

    # Create station first
    station = Station(
        id=uuid.uuid4(),
        name="Test Station",
        code="TEST001",
        display_name="Test Station",
        email="test@station.com",
        phone="+1234567890",
        address_line1="123 Test St",
        city="Test City",
        state="CA",
        postal_code="90001",  # ✅ Use postal_code, not zip_code!
        country="US",
        timezone="America/Los_Angeles"
    )
    db_session.add(station)
    await db_session.commit()

    # Create customer with correct fields
    customer = Customer(
        id=uuid.uuid4(),
        station_id=station.id,  # ✅ Required, not optional
        first_name="Test",
        last_name="Customer",
        email="test@example.com",  # ✅ Use @property setter (encrypts automatically)
        phone="+1234567890",  # ✅ Use @property setter
        consent_sms=True,  # ✅ Correct field name
        consent_email=True,  # ✅ Correct field name
        timezone="America/New_York"  # ✅ Required field
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)
    return customer
```

### Phase 6: Create Encryption Module (1 hour)

**New file: `core/encryption.py`**

```python
"""Field-level encryption for PII data"""
from cryptography.fernet import Fernet
from core.config import get_settings

settings = get_settings()

# TODO: Move encryption key to Google Secret Manager
ENCRYPTION_KEY = settings.FIELD_ENCRYPTION_KEY  # Must be in .env

def encrypt_field(value: str) -> str:
    """Encrypt a field value"""
    if not value:
        return value

    fernet = Fernet(ENCRYPTION_KEY)
    encrypted = fernet.encrypt(value.encode())
    return encrypted.decode()

def decrypt_field(encrypted_value: str) -> str:
    """Decrypt a field value"""
    if not encrypted_value:
        return encrypted_value

    fernet = Fernet(ENCRYPTION_KEY)
    decrypted = fernet.decrypt(encrypted_value.encode())
    return decrypted.decode()
```

**Update `.env`**:

```bash
# Add encryption key (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
FIELD_ENCRYPTION_KEY=<generated_key>
```

### Phase 7: Add Schema Validation Test (30 minutes)

**New file: `tests/test_schema_validation.py`**

```python
"""Validate SQLAlchemy models match database schema"""
import pytest
from sqlalchemy import create_engine, inspect
from core.config import get_settings
from db.models.core import Customer, Booking, Chef
from db.models.identity import Station, User

def test_customer_model_matches_database():
    """Ensure Customer model matches core.customers table"""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL_SYNC)
    inspector = inspect(engine)

    # Get database columns
    db_columns = {
        col['name']: str(col['type'])
        for col in inspector.get_columns('customers', schema='core')
    }

    # Get model columns
    model_columns = {
        col.name: str(col.type)
        for col in Customer.__table__.columns
    }

    # Compare
    assert set(db_columns.keys()) == set(model_columns.keys()), \
        f"Column mismatch: DB has {set(db_columns.keys())}, Model has {set(model_columns.keys())}"
```

---

## Risk Assessment

### HIGH RISK ✅ MITIGATED

- **Encryption breaking**: Use @property decorators for backward
  compatibility
- **Foreign key violations**: Update all fixtures to create
  dependencies first
- **Import errors**: Create comprehensive import mapping before
  changes

### MEDIUM RISK ⚠️ MONITOR

- **Endpoints using old field names**: Audit all endpoints before
  deployment
- **Existing data migration**: Database already has encrypted data,
  models just need to match

### LOW RISK ✅ SAFE

- **Model deletion**: Legacy models have deprecation warnings, safe to
  remove
- **Relationship breaks**: Generated models have correct relationships

---

## Testing Checklist

- [ ] All imports updated and working
- [ ] Bug #13 tests pass with new Customer model
- [ ] Encryption/decryption works correctly
- [ ] All endpoints still work (integration tests)
- [ ] Schema validation test passes
- [ ] No AttributeError on customer.email (uses @property)
- [ ] station_id is required (not optional)
- [ ] Alembic can generate empty migration (no schema drift)

---

## Rollback Plan

If issues found:

1. **Restore backup models**:

   ```bash
   rm -r src/models
   mv src/models_BACKUP_20251126 src/models
   rm -r src/db/models
   mv src/db/models_BACKUP_20251126 src/db/models
   ```

2. **Rollback imports**:

   ```bash
   git checkout -- src/  # If committed to git
   ```

3. **Restore tests**:
   ```bash
   mv tests_BACKUP_20251126 tests
   ```

---

## Timeline

| Phase     | Task                     | Time        | Risk   | Status   |
| --------- | ------------------------ | ----------- | ------ | -------- |
| 1         | Backup files             | 5 min       | Low    | ⏺️ Ready |
| 2         | Update Customer model    | 1 hr        | High   | ⏺️ Ready |
| 2         | Update Booking model     | 30 min      | Medium | ⏺️ Ready |
| 2         | Update other core models | 30 min      | Medium | ⏺️ Ready |
| 3         | Delete legacy models     | 15 min      | Low    | ⏺️ Ready |
| 4         | Update imports           | 1-2 hrs     | Medium | ⏺️ Ready |
| 5         | Update tests             | 1 hr        | Medium | ⏺️ Ready |
| 6         | Create encryption module | 1 hr        | High   | ⏺️ Ready |
| 7         | Add schema validation    | 30 min      | Low    | ⏺️ Ready |
| 8         | Run all tests            | 30 min      | -      | ⏺️ Ready |
| **TOTAL** |                          | **4-6 hrs** |        |          |

---

## Next Steps

**DECISION REQUIRED**: Proceed with migration?

1. ✅ **YES** → Start with Phase 1 (backup)
2. ❌ **NO** → Keep using raw SQL workarounds (not sustainable)
3. ⏸️ **WAIT** → Need more review/testing

**Recommendation**: **YES - Proceed**. Generated models are guaranteed
to match database, and migration is well-planned with backups and
rollback strategy.
