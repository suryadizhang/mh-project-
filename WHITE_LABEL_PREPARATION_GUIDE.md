# 🏷️ White-Label Preparation Guide

**Prepare My Hibachi Chef for Future White-Labeling**

**Date:** November 4, 2025  
**Goal:** Abstract brand-specific code NOW so white-labeling later is
just config changes (not weeks of refactoring)

---

## 🎯 Strategy: "Code Once, Brand Many Times"

### Current State

```
My Hibachi Chef (hardcoded everywhere)
↓
Your catering business only
```

### After White-Label Prep

```
Brand-Agnostic Core System (configurable)
↓
My Hibachi Chef (config: brand_id=1)
↓
Future: Boston BBQ (config: brand_id=2), NYC Catering (brand_id=3), etc.
```

### Time Investment

- **Now:** 4-6 hours of abstraction work
- **Later (if you wait):** 2-3 weeks of refactoring
- **When white-labeling:** Just config changes (30 minutes per new
  brand)

---

## 📋 Step-by-Step Implementation

### Step 1: Create Multi-Tenant Database Schema (1 hour)

#### Add `businesses` table

```sql
-- apps/backend/migrations/versions/add_businesses_table.py

"""Add businesses table for white-label support

Revision ID: add_businesses_001
Revises: previous_migration
Create Date: 2025-11-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # Create businesses table
    op.create_table(
        'businesses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),  # "My Hibachi Chef"
        sa.Column('slug', sa.String(100), unique=True, nullable=False),  # "my-hibachi-chef"
        sa.Column('domain', sa.String(255), unique=True, nullable=True),  # "myhibachichef.com"

        # Branding
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(7), default='#FF6B6B'),  # Hex color
        sa.Column('secondary_color', sa.String(7), default='#4ECDC4'),

        # Contact info
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('address', sa.Text, nullable=True),

        # Business settings
        sa.Column('timezone', sa.String(50), default='America/Los_Angeles'),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('settings', JSONB, default={}),  # Flexible settings storage

        # Subscription (for white-label pricing)
        sa.Column('subscription_tier', sa.String(50), default='self_hosted'),  # 'self_hosted', 'basic', 'pro', 'enterprise'
        sa.Column('subscription_status', sa.String(20), default='active'),
        sa.Column('monthly_fee', sa.Numeric(10, 2), default=0.00),

        # Metadata
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Add business_id to existing tables
    tables_to_update = [
        'users',
        'bookings',
        'leads',
        'conversations',
        'menu_items',
        'reviews',
        'newsletter_subscribers',
        'ai_interactions',
    ]

    for table in tables_to_update:
        op.add_column(
            table,
            sa.Column('business_id', UUID(as_uuid=True), nullable=True)
        )
        op.create_foreign_key(
            f'fk_{table}_business',
            table, 'businesses',
            ['business_id'], ['id'],
            ondelete='CASCADE'
        )
        op.create_index(f'idx_{table}_business_id', table, ['business_id'])

    # Insert My Hibachi Chef as first business
    op.execute("""
        INSERT INTO businesses (name, slug, domain, phone, email, subscription_tier)
        VALUES (
            'My Hibachi Chef',
            'my-hibachi-chef',
            'myhibachichef.com',
            '(916) 740-8768',
            'contact@myhibachichef.com',
            'self_hosted'
        )
    """)

    # Update existing records to link to My Hibachi Chef
    op.execute("""
        UPDATE users SET business_id = (SELECT id FROM businesses WHERE slug = 'my-hibachi-chef');
        UPDATE bookings SET business_id = (SELECT id FROM businesses WHERE slug = 'my-hibachi-chef');
        UPDATE leads SET business_id = (SELECT id FROM businesses WHERE slug = 'my-hibachi-chef');
        -- ... repeat for all tables
    """)

    # Make business_id NOT NULL after backfill
    for table in tables_to_update:
        op.alter_column(table, 'business_id', nullable=False)

def downgrade():
    # Remove foreign keys and columns
    tables = ['users', 'bookings', 'leads', 'conversations', 'menu_items', 'reviews', 'newsletter_subscribers', 'ai_interactions']
    for table in tables:
        op.drop_constraint(f'fk_{table}_business', table)
        op.drop_column(table, 'business_id')

    op.drop_table('businesses')
```

---

### Step 2: Create Business Model (15 minutes)

```python
# apps/backend/src/models/business.py

from sqlalchemy import Column, String, Boolean, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..core.database import Base

class Business(Base):
    """
    Multi-tenant business entity for white-labeling.

    Each business represents a separate catering company using the platform.
    Currently only "My Hibachi Chef", but supports future white-label customers.
    """
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    domain = Column(String(255), unique=True, nullable=True)

    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#FF6B6B")
    secondary_color = Column(String(7), default="#4ECDC4")

    # Contact
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)

    # Settings
    timezone = Column(String(50), default="America/Los_Angeles")
    currency = Column(String(3), default="USD")
    settings = Column(JSONB, default={})

    # Subscription (for white-label pricing)
    subscription_tier = Column(String(50), default="self_hosted")
    subscription_status = Column(String(20), default="active")
    monthly_fee = Column(Numeric(10, 2), default=0.00)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="business")
    bookings = relationship("Booking", back_populates="business")
    leads = relationship("Lead", back_populates="business")

    def __repr__(self):
        return f"<Business {self.name}>"

    def get_setting(self, key: str, default=None):
        """Get a business-specific setting"""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value):
        """Set a business-specific setting"""
        if self.settings is None:
            self.settings = {}
        self.settings[key] = value
```

---

### Step 3: Add Business Context Middleware (30 minutes)

```python
# apps/backend/src/core/business_context.py

"""
Business Context Management

Automatically detects which business is being accessed based on:
1. Domain (myhibachichef.com vs bostonbbq.com)
2. Subdomain (mybusiness.platform.com)
3. API key header (X-Business-ID)
4. JWT token claim (business_id)
"""

from contextvars import ContextVar
from typing import Optional
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Context variable to store current business
_current_business: ContextVar[Optional[dict]] = ContextVar("current_business", default=None)

def get_current_business() -> Optional[dict]:
    """Get the current business from context"""
    return _current_business.get()

def set_current_business(business: dict):
    """Set the current business in context"""
    _current_business.set(business)

async def business_context_middleware(request: Request, call_next):
    """
    Middleware to detect and set business context for each request.

    Detection order:
    1. X-Business-ID header (for API clients)
    2. Domain/subdomain (for web requests)
    3. JWT token business_id claim
    4. Default to "My Hibachi Chef" (business_id=1)
    """

    from sqlalchemy import select
    from .database import async_session_maker
    from ..models.business import Business

    business = None

    # Method 1: Check X-Business-ID header
    business_id = request.headers.get("X-Business-ID")

    if business_id:
        async with async_session_maker() as db:
            result = await db.execute(
                select(Business).where(Business.id == business_id)
            )
            business = result.scalar_one_or_none()

    # Method 2: Check domain
    if not business:
        host = request.headers.get("host", "").split(":")[0]

        async with async_session_maker() as db:
            result = await db.execute(
                select(Business).where(Business.domain == host)
            )
            business = result.scalar_one_or_none()

    # Method 3: Check JWT token (extract business_id from token)
    if not business:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from .security import decode_token
                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                business_id = payload.get("business_id")

                if business_id:
                    async with async_session_maker() as db:
                        result = await db.execute(
                            select(Business).where(Business.id == business_id)
                        )
                        business = result.scalar_one_or_none()
            except Exception as e:
                logger.warning(f"Failed to extract business from JWT: {e}")

    # Method 4: Default to My Hibachi Chef
    if not business:
        async with async_session_maker() as db:
            result = await db.execute(
                select(Business).where(Business.slug == "my-hibachi-chef")
            )
            business = result.scalar_one_or_none()

    # Set business context
    if business:
        set_current_business({
            "id": str(business.id),
            "name": business.name,
            "slug": business.slug,
            "settings": business.settings,
        })
        logger.debug(f"Business context set: {business.name}")
    else:
        logger.error("No business found - this should not happen")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Business context not available"
        )

    # Process request
    response = await call_next(request)

    # Clear context
    set_current_business(None)

    return response
```

**Register middleware:**

```python
# apps/backend/src/main.py (add after imports)

from core.business_context import business_context_middleware

# Add middleware (BEFORE rate limiting)
app.middleware("http")(business_context_middleware)
```

---

### Step 4: Create Business Config Service (20 minutes)

```python
# apps/backend/src/services/business_config.py

"""
Business Configuration Service

Provides business-specific settings, branding, and content.
"""

from typing import Dict, Any, Optional
from ..core.business_context import get_current_business
import logging

logger = logging.getLogger(__name__)

class BusinessConfig:
    """Business-specific configuration"""

    @staticmethod
    def get_brand_name() -> str:
        """Get business brand name"""
        business = get_current_business()
        return business["name"] if business else "My Hibachi Chef"

    @staticmethod
    def get_contact_phone() -> str:
        """Get business phone number"""
        business = get_current_business()
        if business:
            settings = business.get("settings", {})
            return settings.get("phone", "(916) 740-8768")
        return "(916) 740-8768"

    @staticmethod
    def get_contact_email() -> str:
        """Get business contact email"""
        business = get_current_business()
        if business:
            settings = business.get("settings", {})
            return settings.get("email", "contact@myhibachichef.com")
        return "contact@myhibachichef.com"

    @staticmethod
    def get_ai_system_prompt() -> str:
        """Get business-specific AI system prompt"""
        brand_name = BusinessConfig.get_brand_name()
        phone = BusinessConfig.get_contact_phone()

        # Base prompt with brand placeholders
        return f"""You are an AI assistant for {brand_name}, a premier hibachi catering service.

**YOUR ROLE**:
- Help customers get accurate quotes for hibachi parties
- Answer questions about our services, pricing, and availability
- Be professional and helpful in your communication style

**PRICING & SERVICES**:
- Base Pricing: $55/adult (13+), $30/child (6-12), FREE under 5
- Party Minimum: $550 total
- Each guest gets 2 FREE proteins (Chicken, NY Strip Steak, Shrimp, Tofu, Vegetables)
- Premium Upgrades: Filet Mignon/Salmon/Scallops (+$5 each), Lobster Tail (+$15 each)
- 3rd Protein Rule: +$10 per extra protein beyond 2 per guest

**IMPORTANT TOOLS**:
You have access to tools for EXACT calculations. ALWAYS use tools for pricing - NEVER estimate or guess.

**RESPONSE GUIDELINES**:
1. Use tools for any pricing question
2. Break down costs clearly
3. Include contact info for booking: {phone}
4. Be transparent about what's included vs. upgrades

Generate accurate, helpful responses that make customers excited to book!"""

    @staticmethod
    def get_email_signature() -> str:
        """Get business email signature"""
        brand_name = BusinessConfig.get_brand_name()
        phone = BusinessConfig.get_contact_phone()
        email = BusinessConfig.get_contact_email()

        return f"""
Best regards,
{brand_name} Team

📞 {phone}
✉️ {email}
"""

    @staticmethod
    def get_setting(key: str, default: Any = None) -> Any:
        """Get a custom business setting"""
        business = get_current_business()
        if business:
            settings = business.get("settings", {})
            return settings.get(key, default)
        return default

# Singleton instance
_config = BusinessConfig()

def get_business_config() -> BusinessConfig:
    """Get business config instance"""
    return _config
```

---

### Step 5: Update AI Orchestrator to Use Business Config (15 minutes)

```python
# apps/backend/src/api/ai/orchestrator/ai_orchestrator.py

# Add import at top
from ...services.business_config import get_business_config

class AIOrchestrator:
    def _build_system_prompt(self, channel: str) -> str:
        """Build system prompt with business-specific branding"""

        # Get business config
        config = get_business_config()

        # Use business-specific prompt
        return config.get_ai_system_prompt()
```

---

### Step 6: Update Email Templates (20 minutes)

```python
# apps/backend/src/services/email_templates.py

from .business_config import get_business_config

class EmailTemplates:
    """Business-branded email templates"""

    @staticmethod
    def booking_confirmation(booking_data: dict) -> str:
        """Booking confirmation email"""
        config = get_business_config()
        brand_name = config.get_brand_name()
        signature = config.get_email_signature()

        return f"""
<h2>Booking Confirmed! 🎉</h2>

<p>Thank you for choosing {brand_name}!</p>

<p><strong>Booking Details:</strong></p>
<ul>
    <li>Date: {booking_data['event_date']}</li>
    <li>Guests: {booking_data['guest_count']}</li>
    <li>Location: {booking_data['address']}</li>
</ul>

{signature}
"""

    @staticmethod
    def quote_email(quote_data: dict) -> str:
        """Quote email"""
        config = get_business_config()
        brand_name = config.get_brand_name()

        return f"""
<h2>Your {brand_name} Quote</h2>

<p>Thank you for your interest! Here's your custom quote:</p>

<table>
    <tr><td>Base Price:</td><td>${quote_data['base_price']}</td></tr>
    <tr><td>Proteins:</td><td>${quote_data['protein_cost']}</td></tr>
    <tr><td>Travel:</td><td>${quote_data['travel_fee']}</td></tr>
    <tr><td><strong>Total:</strong></td><td><strong>${quote_data['total']}</strong></td></tr>
</table>

<p>Ready to book? Reply to this email or call us!</p>

{config.get_email_signature()}
"""
```

---

### Step 7: Environment Variables Setup (10 minutes)

```bash
# apps/backend/.env (add these)

# Business Configuration
DEFAULT_BUSINESS_SLUG=my-hibachi-chef
MULTI_TENANT_MODE=false  # Set to true when white-labeling

# My Hibachi Chef Branding (for backward compatibility)
BRAND_NAME=My Hibachi Chef
BRAND_PHONE=(916) 740-8768
BRAND_EMAIL=contact@myhibachichef.com
```

---

### Step 8: Create Business Admin Endpoints (30 minutes)

```python
# apps/backend/src/api/v1/endpoints/businesses.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ....core.database import get_db
from ....core.security import require_super_admin
from ....models.business import Business
from pydantic import BaseModel

router = APIRouter(prefix="/businesses", tags=["Businesses"])

class BusinessCreate(BaseModel):
    name: str
    slug: str
    domain: str | None = None
    phone: str | None = None
    email: str | None = None
    primary_color: str = "#FF6B6B"
    secondary_color: str = "#4ECDC4"

class BusinessResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain: str | None
    phone: str | None
    email: str | None
    is_active: bool
    subscription_tier: str

@router.get("/", response_model=List[BusinessResponse])
async def list_businesses(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """List all businesses (for white-label admin)"""
    result = await db.execute(select(Business))
    businesses = result.scalars().all()
    return businesses

@router.post("/", response_model=BusinessResponse)
async def create_business(
    business_data: BusinessCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Create a new business (for white-labeling)"""

    # Check if slug exists
    existing = await db.execute(
        select(Business).where(Business.slug == business_data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Business slug already exists")

    # Create business
    business = Business(**business_data.dict())
    db.add(business)
    await db.commit()
    await db.refresh(business)

    return business
```

---

### Step 9: Frontend Configuration (20 minutes)

```typescript
// apps/frontend/src/config/business.ts

/**
 * Business configuration for white-labeling support
 */

export interface BusinessConfig {
  name: string;
  logo: string;
  primaryColor: string;
  secondaryColor: string;
  phone: string;
  email: string;
}

// Fetch from backend or use defaults
let cachedConfig: BusinessConfig | null = null;

export async function getBusinessConfig(): Promise<BusinessConfig> {
  if (cachedConfig) {
    return cachedConfig;
  }

  try {
    // Fetch from backend API
    const response = await fetch('/api/config/business');
    const data = await response.json();

    cachedConfig = {
      name: data.name || 'My Hibachi Chef',
      logo: data.logo_url || '/logo.png',
      primaryColor: data.primary_color || '#FF6B6B',
      secondaryColor: data.secondary_color || '#4ECDC4',
      phone: data.phone || '(916) 740-8768',
      email: data.email || 'contact@myhibachichef.com',
    };
  } catch (error) {
    // Fallback to My Hibachi Chef defaults
    cachedConfig = {
      name: 'My Hibachi Chef',
      logo: '/logo.png',
      primaryColor: '#FF6B6B',
      secondaryColor: '#4ECDC4',
      phone: '(916) 740-8768',
      email: 'contact@myhibachichef.com',
    };
  }

  return cachedConfig;
}

// Usage in components
export function useBusinessConfig() {
  const [config, setConfig] = React.useState<BusinessConfig | null>(
    null
  );

  React.useEffect(() => {
    getBusinessConfig().then(setConfig);
  }, []);

  return config;
}
```

**Update components to use config:**

```tsx
// apps/frontend/src/components/Header.tsx

import { useBusinessConfig } from '@/config/business';

export function Header() {
  const config = useBusinessConfig();

  if (!config) return <div>Loading...</div>;

  return (
    <header>
      <img src={config.logo} alt={config.name} />
      <h1>{config.name}</h1>
      <a href={`tel:${config.phone}`}>{config.phone}</a>
    </header>
  );
}
```

---

## 🎯 Benefits of This Approach

### Now (Using as My Hibachi Chef)

✅ Clean, maintainable code  
✅ All brand info in one place (easy to update)  
✅ Database-driven configuration  
✅ No extra complexity for users

### Later (When White-Labeling)

✅ Add new business = 30 minutes (not 3 weeks)  
✅ Each business isolated in database  
✅ Automatic domain-based routing  
✅ No code changes needed per business

---

## 📊 White-Label Pricing Model (Future)

When you're ready to sell to other caterers:

```
Tier 1 - Starter: $500/month
- Up to 100 conversations/month
- Basic AI features
- Email support

Tier 2 - Professional: $1,500/month
- Unlimited conversations
- Advanced AI (sentiment, lead scoring)
- Phone support
- Custom branding

Tier 3 - Enterprise: $3,000+/month
- Everything in Pro
- Dedicated infrastructure
- Custom integrations
- White-glove onboarding
```

**Example Revenue:**

- 10 businesses × $1,500/month = $15,000/month
- 50 businesses × $1,500/month = $75,000/month

---

## ✅ Implementation Checklist

- [ ] Run database migration (add businesses table)
- [ ] Create Business model
- [ ] Add business context middleware
- [ ] Create business config service
- [ ] Update AI orchestrator to use config
- [ ] Update email templates
- [ ] Add environment variables
- [ ] Create business admin endpoints
- [ ] Update frontend components
- [ ] Test with My Hibachi Chef (should work exactly the same)
- [ ] Document for future white-label customers

**Total Time:** 4-6 hours  
**Future Benefit:** Saves 2-3 weeks when white-labeling

---

## 🚀 Next Steps

1. **Implement white-label structure** (this week, 4-6 hours)
2. **Continue using as My Hibachi Chef** (no change in functionality)
3. **When ready to white-label:** Just add new business via admin
   panel
4. **First white-label customer:** Onboard in 30 minutes, not 3 weeks

This gives you **optionality without complexity** - best of both
worlds! 🎯
