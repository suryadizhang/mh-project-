# 🏢 Enterprise Multi-Contact Management System

**Date**: November 21, 2025  
**Status**: 🔍 Research & Design Phase  
**Problem**: How to handle customers with multiple phone numbers, multiple emails, and unified communications?

---

## 🎯 The Problem

**Current Limitation**:
```sql
customers:
  id: UUID
  email: VARCHAR (UNIQUE)  ← Only ONE email allowed
  phone: VARCHAR           ← Only ONE phone allowed
```

**Real-World Scenarios**:

### Scenario 1: Business Owner
```text
John Doe (Restaurant Owner) contacts you via:
- Personal phone: (916) 555-1234
- Business phone: (916) 555-9999
- Personal email: john.doe@gmail.com
- Business email: john@johnsrestaurant.com
- Instagram DM: @johndoe_personal
- Facebook: John's Restaurant (business page)

Question: How do we know these are ALL the same person? 🤔
```

### Scenario 2: Family Bookings
```text
Sarah Johnson books for family events:
- Her phone: (916) 555-5678
- Husband's phone: (916) 555-5679
- Home phone: (916) 555-5680
- Her email: sarah@example.com
- Shared email: thejohnsons@example.com

Question: Link to ONE customer or separate? 🤔
```

### Scenario 3: Assistant Booking
```text
CEO's assistant books corporate events:
- CEO's phone: (916) 555-8888
- Assistant's phone: (916) 555-8889
- CEO's email: ceo@company.com
- Assistant's email: assistant@company.com

Question: Who is the "customer"? 🤔
```

---

## 🏆 Enterprise Best Practices (How Big Companies Handle This)

### ✅ Solution 1: **Contact Methods Table** (Salesforce, HubSpot, Zendesk)

**Architecture**:
```
Customer (Master Record)
    ↓ has many
ContactMethods (Phone/Email/Social)
    ↓ has many
Conversations (Threads)
```

**Database Design**:
```sql
-- Master customer record
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    preferred_contact_method_id UUID,  -- FK to contact_methods
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Contact methods (phones, emails, social handles)
CREATE TABLE contact_methods (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    
    -- Contact info
    type VARCHAR(50) NOT NULL,  -- 'phone', 'email', 'social_handle'
    value VARCHAR(255) NOT NULL,  -- '+19165551234', 'john@email.com', '@johndoe'
    platform VARCHAR(50),  -- 'instagram', 'facebook', 'sms', etc.
    
    -- Metadata
    label VARCHAR(50),  -- 'personal', 'business', 'home', 'assistant'
    is_primary BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    
    -- Communication preferences
    opt_in_sms BOOLEAN DEFAULT false,
    opt_in_email BOOLEAN DEFAULT false,
    opt_in_marketing BOOLEAN DEFAULT false,
    
    -- Tracking
    first_used_at TIMESTAMP,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    UNIQUE(type, value, platform)  -- Prevent duplicates
);

-- Index for fast lookup
CREATE INDEX idx_contact_methods_value ON contact_methods(value);
CREATE INDEX idx_contact_methods_customer_type ON contact_methods(customer_id, type);
CREATE INDEX idx_contact_methods_primary ON contact_methods(is_primary) WHERE is_primary = true;
```

**Example Data**:
```sql
-- Customer: John Doe
customers:
id: 550e8400-...
name: John Doe
preferred_contact_method_id: aaa-111-... (points to personal phone)

contact_methods:
id: aaa-111-... | customer_id: 550e8400-... | type: phone  | value: +19165551234 | label: personal  | is_primary: true  | is_verified: true
id: bbb-222-... | customer_id: 550e8400-... | type: phone  | value: +19165559999 | label: business  | is_primary: false | is_verified: true
id: ccc-333-... | customer_id: 550e8400-... | type: email  | value: john@gmail.com | label: personal | is_primary: true  | is_verified: true
id: ddd-444-... | customer_id: 550e8400-... | type: email  | value: john@work.com  | label: business | is_primary: false | is_verified: false
id: eee-555-... | customer_id: 550e8400-... | type: social | value: johndoe | platform: instagram | label: personal | is_primary: false
```

**Benefits**:
- ✅ **Unlimited contacts** per customer
- ✅ **Primary contact** clearly marked
- ✅ **Labels** (personal/business/home/assistant)
- ✅ **Verification status** tracked
- ✅ **TCPA compliance** (opt-in per method)
- ✅ **Usage tracking** (which contact used most)

---

### ✅ Solution 2: **Identity Resolution Engine** (Segment, mParticle, Twilio)

**Architecture**:
```
Multiple Identifiers → Identity Graph → Single Customer Profile
```

**How It Works**:

```python
# Customer first contacts via Instagram
Message: "Book for 6 people. Call me at (916) 555-1234"

System creates:
1. Customer record (ID: 550e8400-...)
2. Contact method: phone +19165551234 (primary)
3. Contact method: social @johndoe (instagram)
4. Identity link: instagram:@johndoe → customer 550e8400

# Same customer books online with different phone
Booking form:
  Phone: (916) 555-9999  (business number)
  Email: john@work.com

System logic:
1. Check: Does phone +19165559999 exist? NO
2. Check: Does email john@work.com exist? NO
3. ASK USER: "We found similar customer. Is this you?"
   - Name: John Doe
   - Instagram: @johndoe
   - Phone: (916) 555-1234
4. User confirms: YES
5. System adds:
   - Contact method: phone +19165559999 (label: business)
   - Contact method: email john@work.com (label: business)
   - Links to SAME customer (550e8400)

Result: ONE customer with MULTIPLE contact methods! ✅
```

**Identity Matching Algorithm**:
```python
async def find_customer_by_any_contact(
    phone: Optional[str] = None,
    email: Optional[str] = None,
    social_handle: Optional[str] = None,
    social_platform: Optional[str] = None
) -> Optional[Customer]:
    """
    Find customer by ANY contact method.
    
    Returns:
    - Exact match: Customer found
    - Multiple matches: Return all (let user choose)
    - No match: None
    """
    
    # Build query for ANY matching contact method
    stmt = select(Customer).join(ContactMethod).where(
        or_(
            and_(ContactMethod.type == 'phone', ContactMethod.value == phone),
            and_(ContactMethod.type == 'email', ContactMethod.value == email),
            and_(
                ContactMethod.type == 'social',
                ContactMethod.value == social_handle,
                ContactMethod.platform == social_platform
            )
        )
    )
    
    result = await db.execute(stmt)
    customers = result.scalars().all()
    
    if len(customers) == 1:
        return customers[0]  # Exact match
    elif len(customers) > 1:
        return customers  # Multiple matches - need user to choose
    else:
        return None  # No match
```

**Benefits**:
- ✅ **Fuzzy matching** (find similar customers)
- ✅ **Merge capability** (combine duplicate profiles)
- ✅ **Confidence scoring** (how sure we are)
- ✅ **User confirmation** (let user decide)

---

### ✅ Solution 3: **Hierarchical Contacts** (Microsoft Dynamics, Oracle CRM)

**Use Case**: Corporate bookings with assistants

**Architecture**:
```
Account (Company)
    ↓ has many
Contacts (People)
    ↓ has many
ContactMethods (Phones/Emails)
```

**Example**:
```sql
-- Account (Company)
accounts:
id: abc-123-...
name: "Tech Corp Inc."
type: corporate

-- Contacts (People at company)
contacts:
id: contact-1 | account_id: abc-123 | name: John Smith (CEO)     | role: decision_maker
id: contact-2 | account_id: abc-123 | name: Jane Doe (Assistant) | role: booking_contact

-- Contact Methods
contact_methods:
-- CEO
id: cm-1 | contact_id: contact-1 | type: phone | value: +19165558888 | label: direct
id: cm-2 | contact_id: contact-1 | type: email | value: ceo@techcorp.com

-- Assistant
id: cm-3 | contact_id: contact-2 | type: phone | value: +19165558889 | label: office
id: cm-4 | contact_id: contact-2 | type: email | value: assistant@techcorp.com
```

**Benefits**:
- ✅ **Company relationships** tracked
- ✅ **Multiple decision makers** handled
- ✅ **Roles defined** (who books, who approves, who pays)

---

## 📧 Email Integration Status

### Current State:

**What We Have**:
```python
# models/customer.py
class Customer(BaseModel):
    email = Column(String, nullable=False, unique=True, index=True)
    # ❌ Only ONE email allowed
    # ❌ No verification status
    # ❌ No email preferences (opt-in/opt-out)
```

**What's Missing**:
- ❌ **Multiple emails** (personal + business)
- ❌ **Email verification** (confirmed vs unconfirmed)
- ❌ **Email preferences** (marketing opt-in/out)
- ❌ **Email validation** (same as phone E.164 standard)
- ❌ **Bounce tracking** (which emails are dead)
- ❌ **Email conversations** (support tickets, replies)

### Email Integration We Need:

```python
# Email features to add:
1. Email normalization (lowercase, trim spaces)
2. Email verification (send verification link)
3. Email preferences (marketing, transactional, booking updates)
4. Email bounce tracking (hard bounce = invalid, soft bounce = temporary)
5. Email conversation threading (ticket system)
6. Email templates (booking confirmation, reminders, etc.)
```

---

## 🎯 Recommended Solution for My Hibachi

### **Option A: Enterprise-Grade (Recommended)** ⭐

**Implement Contact Methods Table**

**Why?**
- ✅ Handles ALL scenarios (personal + business phone/email)
- ✅ Industry standard (Salesforce, HubSpot use this)
- ✅ TCPA compliant (opt-in per contact method)
- ✅ Scalable (add WhatsApp, Telegram later)
- ✅ Clean separation (customer vs. contact info)

**Implementation Plan**:

```sql
-- New table (Migration 012)
CREATE TABLE public.contact_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES public.customers(id) ON DELETE CASCADE,
    
    -- Contact info
    type VARCHAR(50) NOT NULL,  -- 'phone', 'email', 'social_handle'
    value VARCHAR(255) NOT NULL,
    platform VARCHAR(50),  -- For social: 'instagram', 'facebook', etc.
    
    -- Metadata
    label VARCHAR(50),  -- 'personal', 'business', 'home', 'mobile', 'office'
    is_primary BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    
    -- Communication preferences (TCPA compliance)
    can_sms BOOLEAN DEFAULT false,
    can_call BOOLEAN DEFAULT false,
    can_email BOOLEAN DEFAULT false,
    can_marketing BOOLEAN DEFAULT false,
    opt_in_date TIMESTAMP,
    opt_out_date TIMESTAMP,
    
    -- Tracking
    first_used_at TIMESTAMP DEFAULT now(),
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    -- Validation
    validation_errors JSONB,  -- Store bounce info, validation failures
    is_valid BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    
    UNIQUE(type, value, platform)
);

CREATE INDEX idx_contact_methods_customer ON contact_methods(customer_id);
CREATE INDEX idx_contact_methods_value ON contact_methods(value);
CREATE INDEX idx_contact_methods_type_value ON contact_methods(type, value);
CREATE INDEX idx_contact_methods_primary ON contact_methods(is_primary) WHERE is_primary = true;
```

**Migration Strategy**:
```python
# Migration 012: Migrate existing data
def upgrade():
    # 1. Create contact_methods table
    op.create_table(...)
    
    # 2. Migrate existing phone numbers
    op.execute("""
        INSERT INTO contact_methods (customer_id, type, value, label, is_primary, is_verified)
        SELECT 
            id as customer_id,
            'phone' as type,
            phone as value,
            'primary' as label,
            true as is_primary,
            true as is_verified
        FROM customers
        WHERE phone IS NOT NULL
    """)
    
    # 3. Migrate existing emails
    op.execute("""
        INSERT INTO contact_methods (customer_id, type, value, label, is_primary, is_verified)
        SELECT 
            id as customer_id,
            'email' as type,
            email as value,
            'primary' as label,
            true as is_primary,
            true as is_verified
        FROM customers
        WHERE email IS NOT NULL
    """)
    
    # 4. Keep customers.phone and customers.email for backward compatibility
    # (will be deprecated later)
```

**Updated Conversation Unification**:
```python
class ConversationUnificationService:
    
    async def find_customer_by_any_contact(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        social_handle: Optional[str] = None,
        platform: Optional[str] = None
    ) -> tuple[Optional[Customer], Optional[ContactMethod]]:
        """
        Find customer by ANY contact method.
        
        Returns: (customer, contact_method_used)
        """
        
        # Search contact_methods table
        stmt = select(ContactMethod, Customer).join(Customer).where(
            or_(
                and_(ContactMethod.type == 'phone', ContactMethod.value == phone),
                and_(ContactMethod.type == 'email', ContactMethod.value == email),
                and_(
                    ContactMethod.type == 'social_handle',
                    ContactMethod.value == social_handle,
                    ContactMethod.platform == platform
                )
            )
        )
        
        result = await self.db.execute(stmt)
        row = result.first()
        
        if row:
            contact_method, customer = row
            # Update usage tracking
            contact_method.last_used_at = datetime.utcnow()
            contact_method.usage_count += 1
            await self.db.commit()
            
            return (customer, contact_method)
        
        return (None, None)
    
    async def add_contact_method(
        self,
        customer_id: UUID,
        contact_type: str,
        value: str,
        label: str = 'primary',
        is_primary: bool = False,
        platform: Optional[str] = None
    ) -> ContactMethod:
        """
        Add new contact method to customer.
        
        Handles:
        - Phone normalization (E.164)
        - Email normalization (lowercase)
        - Duplicate detection
        - Primary contact switching
        """
        
        # Normalize value
        if contact_type == 'phone':
            value = validate_phone(value)  # → +19165551234
        elif contact_type == 'email':
            value = value.lower().strip()
        
        # Check if exists
        existing = await self.db.execute(
            select(ContactMethod).where(
                and_(
                    ContactMethod.type == contact_type,
                    ContactMethod.value == value,
                    ContactMethod.platform == platform
                )
            )
        )
        
        if existing.scalar_one_or_none():
            raise ValueError(f"Contact method {value} already exists")
        
        # If marking as primary, unmark others
        if is_primary:
            await self.db.execute(
                update(ContactMethod)
                .where(
                    and_(
                        ContactMethod.customer_id == customer_id,
                        ContactMethod.type == contact_type
                    )
                )
                .values(is_primary=False)
            )
        
        # Create new contact method
        contact_method = ContactMethod(
            customer_id=customer_id,
            type=contact_type,
            value=value,
            label=label,
            platform=platform,
            is_primary=is_primary,
            first_used_at=datetime.utcnow()
        )
        
        self.db.add(contact_method)
        await self.db.commit()
        
        return contact_method
```

**API Examples**:

```python
# Get customer's all contact methods
GET /api/v1/customers/{customer_id}/contacts

Response:
{
    "customer_id": "550e8400-...",
    "name": "John Doe",
    "contacts": {
        "phones": [
            {
                "id": "aaa-111-...",
                "value": "+19165551234",
                "label": "personal",
                "is_primary": true,
                "is_verified": true,
                "can_sms": true,
                "last_used": "2025-11-21T10:30:00Z"
            },
            {
                "id": "bbb-222-...",
                "value": "+19165559999",
                "label": "business",
                "is_primary": false,
                "is_verified": true,
                "can_sms": false,
                "last_used": "2025-11-20T14:00:00Z"
            }
        ],
        "emails": [
            {
                "id": "ccc-333-...",
                "value": "john@gmail.com",
                "label": "personal",
                "is_primary": true,
                "is_verified": true,
                "can_marketing": true
            },
            {
                "id": "ddd-444-...",
                "value": "john@work.com",
                "label": "business",
                "is_primary": false,
                "is_verified": false,
                "can_marketing": false
            }
        ],
        "social": [
            {
                "id": "eee-555-...",
                "platform": "instagram",
                "value": "johndoe",
                "label": "personal",
                "is_verified": true
            }
        ]
    }
}

# Add new contact method
POST /api/v1/customers/{customer_id}/contacts

Request:
{
    "type": "phone",
    "value": "(916) 555-9999",
    "label": "business",
    "is_primary": false
}

Response:
{
    "id": "fff-666-...",
    "type": "phone",
    "value": "+19165559999",  # Auto-normalized
    "label": "business",
    "is_primary": false,
    "is_verified": false,  # Needs verification
    "created_at": "2025-11-21T15:00:00Z"
}

# Set primary contact
PATCH /api/v1/customers/{customer_id}/contacts/{contact_id}/set-primary

Response:
{
    "message": "Contact method set as primary",
    "old_primary": "aaa-111-...",
    "new_primary": "fff-666-..."
}
```

---

### **Option B: Hybrid Approach** (Simpler)

**Keep current single phone/email + Add contact_methods for extras**

```python
customers:
  phone: VARCHAR  # Primary phone (backward compatible)
  email: VARCHAR  # Primary email (backward compatible)

contact_methods:  # Additional contacts only
  customer_id: UUID
  type: VARCHAR
  value: VARCHAR
  label: VARCHAR (e.g., 'secondary', 'business', 'assistant')
```

**Benefits**:
- ✅ Less migration work
- ✅ Backward compatible
- ✅ Handles "one customer, multiple contacts" case

**Drawbacks**:
- ⚠️ Still limited (one "primary" in customers table)
- ⚠️ Two places to check (customers.phone + contact_methods)

---

## 📊 Comparison Table

| Feature | Current (Single) | Option A (Enterprise) | Option B (Hybrid) |
|---------|-----------------|---------------------|------------------|
| Multiple phones | ❌ No | ✅ Unlimited | ✅ Unlimited |
| Multiple emails | ❌ No | ✅ Unlimited | ✅ Unlimited |
| Primary contact | ❌ Implicit | ✅ Explicit flag | ⚠️ In customers table |
| Verification status | ❌ No | ✅ Per contact | ⚠️ Only for extras |
| TCPA compliance | ⚠️ Basic | ✅ Per contact opt-in | ⚠️ Mixed |
| Usage tracking | ❌ No | ✅ Last used, count | ❌ No |
| Labels (personal/business) | ❌ No | ✅ Yes | ✅ Yes |
| Migration complexity | N/A | 🟡 Medium | 🟢 Low |
| Industry standard | ❌ No | ✅ Yes (Salesforce) | ⚠️ Partial |

---

## 🚀 Recommendation

### **Go with Option A: Enterprise Contact Methods** ⭐

**Why?**
1. **Scalable**: Handles ALL future scenarios
2. **TCPA Compliant**: Per-contact opt-in tracking
3. **Industry Standard**: Proven by Salesforce, HubSpot, Zendesk
4. **Future-Proof**: Easy to add WhatsApp, Telegram, etc.
5. **Better UX**: Customer can choose which contact to use

**Implementation Timeline**:

```
Phase 1 (Now): Migration 011 (Social Models) ← You are here
Phase 2 (Next): Migration 012 (Contact Methods) ← Add this
Phase 3 (Then): Update APIs to use contact_methods
Phase 4 (Finally): Deprecate customers.phone/email (keep for backward compat)
```

---

## 🎯 Next Steps

### Before Proceeding to Feature Activation:

**Decision Point**:
1. ✅ **Run Migration 011** (Social Models) - SAFE, already reviewed
2. ⏸️ **Design Migration 012** (Contact Methods) - NEW, needs your approval
3. 🚀 **Continue with features** - Can proceed, contact_methods is optional enhancement

**My Recommendation**:
```
Option 1: Run Migration 011 NOW → Activate features → Add contact_methods later ✅
Option 2: Design contact_methods first → Run both migrations → Activate features
```

**Which do you prefer?**
- **A**: Run 011 now, add contact_methods later (faster, iterative)
- **B**: Design contact_methods now, run both migrations together (comprehensive)

---

**Questions for you**:
1. Do you want multiple phones/emails per customer? (I recommend YES)
2. Do you handle corporate bookings? (Assistant books for CEO)
3. Should we track which contact method customer prefers?
4. Do you need email verification (confirm email address)?
5. Do you send marketing emails? (Need opt-in tracking)

Let me know your preference and I'll create the complete migration! 🚀
