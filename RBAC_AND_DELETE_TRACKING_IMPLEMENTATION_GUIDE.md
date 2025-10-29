# 🔐 RBAC & Delete Tracking Implementation Guide

**Date:** October 28, 2025  
**Status:** Implementation Ready  
**Estimated Time:** Week 1-2 (60 hours total)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [4-Tier Role System](#4-tier-role-system)
3. [Delete Tracking System](#delete-tracking-system)
4. [Customer Support Permissions](#customer-support-permissions)
5. [Audit Logging](#audit-logging)
6. [Implementation Steps](#implementation-steps)
7. [Database Schema](#database-schema)
8. [Code Examples](#code-examples)
9. [Testing Strategy](#testing-strategy)

---

## 🎯 Overview

### Requirements

✅ **4-Tier Admin Roles:**
- SUPER_ADMIN - Full system access
- ADMIN - Most operations, cannot manage admin accounts
- CUSTOMER_SUPPORT - Customer-facing operations + booking management
- STATION_MANAGER - Station-specific operations

✅ **Enhanced Customer Support:**
- View/Add/Edit/DELETE bookings
- Manage customer leads and reviews
- NO access to internal operations (chef assignment, financials)

✅ **Universal Delete Tracking:**
- ALL delete actions require mandatory reason (min 10 chars)
- Warning modal with two-step confirmation
- Applies to ALL admin roles (including SUPER_ADMIN)
- Auto-logged to audit trail

✅ **Comprehensive Audit Logging:**
- Log ALL admin actions (VIEW/CREATE/UPDATE/DELETE)
- Store: who, what, when, where, why, old/new values
- Filterable log viewer with export

---

## 🔐 4-Tier Role System

### Role Hierarchy

```
SUPER_ADMIN (Level 4) - God Mode
    ↓
ADMIN (Level 3) - Almost God Mode
    ↓
CUSTOMER_SUPPORT (Level 2) - Customer-Facing
    ↓
STATION_MANAGER (Level 1) - Station-Specific
```

### Detailed Permissions Matrix

| Permission | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
|------------|-------------|-------|------------------|-----------------|
| **Bookings** |
| View All Bookings | ✅ | ✅ | ✅ | ❌ (station only) |
| Add Booking | ✅ | ✅ | ✅ | ❌ |
| Edit Booking | ✅ | ✅ | ✅ | ❌ |
| Delete Booking (with reason) | ✅ | ✅ | ✅ | ❌ |
| Reschedule Booking | ✅ | ✅ | ✅ | ❌ |
| **Customers** |
| View Customers | ✅ | ✅ | ✅ | ❌ |
| Add Customer | ✅ | ✅ | ✅ | ❌ |
| Edit Customer | ✅ | ✅ | ✅ | ❌ |
| Delete Customer (with reason) | ✅ | ✅ | ✅ | ❌ |
| **Leads** |
| View Leads | ✅ | ✅ | ✅ | ❌ |
| Qualify Leads | ✅ | ✅ | ✅ | ❌ |
| Delete Leads (with reason) | ✅ | ✅ | ✅ | ❌ |
| **Reviews** |
| View Reviews | ✅ | ✅ | ✅ | ❌ |
| Moderate Reviews | ✅ | ✅ | ✅ | ❌ |
| Delete Reviews (with reason) | ✅ | ✅ | ✅ | ❌ |
| **Chef Management** |
| View Chefs (All) | ✅ | ✅ | ❌ | ❌ (station only) |
| Assign Chef to Party | ✅ | ✅ | ❌ | ✅ (station only) |
| Manage Chef Schedule | ✅ | ✅ | ❌ | ✅ (station only) |
| **Station Management** |
| View All Stations | ✅ | ✅ | ❌ | ❌ (own only) |
| Edit Station Settings | ✅ | ✅ | ❌ | ✅ (own only) |
| Delete Station (with reason) | ✅ | ❌ | ❌ | ❌ |
| **Admin Management** |
| View All Admins | ✅ | ❌ | ❌ | ❌ |
| Create Admin | ✅ | ❌ | ❌ | ❌ |
| Edit Admin | ✅ | ❌ | ❌ | ❌ |
| Delete Admin (with reason) | ✅ | ❌ | ❌ | ❌ |
| Assign Roles | ✅ | ❌ | ❌ | ❌ |
| **Financial** |
| View Financial Reports | ✅ | ✅ | ❌ | ❌ |
| Process Refunds | ✅ | ✅ | ❌ | ❌ |
| **Audit Logs** |
| View All Logs | ✅ | ✅ | ❌ | ❌ (station only) |
| Export Logs | ✅ | ✅ | ❌ | ❌ |
| **System** |
| View Analytics | ✅ | ✅ | ❌ | ✅ (station only) |
| Manage Settings | ✅ | ✅ | ❌ | ❌ |

---

## 🗑️ Delete Tracking System

### Requirements

1. **Mandatory Delete Reason** - ALL delete actions require reason (min 10 chars, max 500 chars)
2. **Warning Modal** - Two-step confirmation before delete
3. **Audit Logging** - Auto-log to audit_logs table
4. **Soft Delete** - Option to restore within 30 days
5. **Applies to ALL Roles** - Even SUPER_ADMIN must provide reason

### Delete Modal Flow

```
User clicks "Delete" button
    ↓
Show DeleteConfirmationModal
    ↓
User sees resource details + warning
    ↓
User types delete reason (min 10 chars)
    ↓
Character counter shows (10/500)
    ↓
User checks "I understand" checkbox
    ↓
"Confirm Delete" button becomes enabled
    ↓
User clicks "Confirm Delete"
    ↓
Loading state (button disabled, spinner)
    ↓
API call: DELETE /api/{resource}/{id} with { reason }
    ↓
Backend logs to audit_logs table
    ↓
Backend performs soft delete (or hard delete)
    ↓
Success: Show toast "Booking deleted successfully"
    ↓
Refresh data, close modal
```

### Resources Requiring Delete Reason

- ✅ Bookings
- ✅ Customers
- ✅ Leads
- ✅ Reviews
- ✅ Chefs
- ✅ Stations
- ✅ Admin Accounts
- ✅ FAQs
- ✅ Blog Posts

---

## 👥 Customer Support Enhanced Permissions

### What Customer Support CAN Do

**Booking Management:**
- ✅ View all bookings (all stations)
- ✅ Add booking on behalf of customer
- ✅ Edit booking details (date, time, package, add-ons, special requests)
- ✅ Delete booking (with mandatory reason)
- ✅ Reschedule booking
- ✅ Cancel booking (with reason)
- ✅ Upgrade/downgrade package
- ✅ Add notes to booking

**Customer Management:**
- ✅ View customer profiles
- ✅ Edit customer information
- ✅ View customer booking history
- ✅ Add internal notes
- ✅ Delete customer (with reason)

**Lead Management:**
- ✅ View leads
- ✅ Qualify/disqualify leads
- ✅ Assign leads to sales team
- ✅ Add notes to leads
- ✅ Delete leads (with reason)

**Review Management:**
- ✅ View reviews
- ✅ Moderate reviews (approve/reject)
- ✅ Reply to reviews
- ✅ Delete reviews (with reason)

**FAQ Management:**
- ✅ Add FAQ
- ✅ Edit FAQ
- ✅ Delete FAQ (with reason)

**Communication:**
- ✅ Send email to customer
- ✅ View message history
- ✅ Add internal notes

### What Customer Support CANNOT Do

**Internal Operations:**
- ❌ Assign chef to party
- ❌ Manage chef schedules
- ❌ View chef availability
- ❌ Access Google Calendar integration

**Station Management:**
- ❌ Edit station settings
- ❌ View station financials
- ❌ Manage station staff

**Financial:**
- ❌ Process refunds (without approval)
- ❌ View financial reports
- ❌ Edit pricing

**Admin Management:**
- ❌ Create/edit/delete admin accounts
- ❌ Change user roles
- ❌ View admin activity logs (except own)

**System:**
- ❌ Access system settings
- ❌ Manage integrations
- ❌ Export database

---

## 📝 Comprehensive Audit Logging

### What Gets Logged

**ALL Admin Actions:**
- ✅ VIEW - Important resource views (customer PII, financials)
- ✅ CREATE - New bookings, customers, leads, reviews, admins
- ✅ UPDATE - Any edits to existing resources
- ✅ DELETE - All deletions (with reason)

### Audit Log Schema

```typescript
interface AuditLog {
  id: string;                    // UUID
  timestamp: Date;               // When action occurred
  
  // Who
  user_id: string;               // User who performed action
  user_role: 'SUPER_ADMIN' | 'ADMIN' | 'CUSTOMER_SUPPORT' | 'STATION_MANAGER';
  user_name: string;             // Display name
  user_email: string;            // Email for contact
  
  // What
  action: 'VIEW' | 'CREATE' | 'UPDATE' | 'DELETE';
  resource_type: string;         // 'booking', 'customer', 'lead', etc.
  resource_id: string;           // ID of affected resource
  resource_name?: string;        // Friendly name (for UI)
  
  // Where
  ip_address: string;            // Request IP
  user_agent: string;            // Browser/device info
  station_id?: string;           // Station context (if applicable)
  
  // Why (for deletes)
  delete_reason?: string;        // Mandatory for DELETE actions
  
  // Details
  old_values?: Record<string, any>;  // Before state (JSON)
  new_values?: Record<string, any>;  // After state (JSON)
  metadata?: Record<string, any>;    // Additional context
}
```

### Example Audit Logs

**Example 1: Customer Support Deletes Booking**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-28T14:30:00Z",
  "user_id": "user_123",
  "user_role": "CUSTOMER_SUPPORT",
  "user_name": "Sarah Johnson",
  "user_email": "sarah@myhibachi.com",
  "action": "DELETE",
  "resource_type": "booking",
  "resource_id": "booking_456",
  "resource_name": "John Doe - Oct 30, 2025",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "station_id": "station_789",
  "delete_reason": "Customer called to cancel due to family emergency. Already processed refund via Stripe.",
  "old_values": {
    "customer_name": "John Doe",
    "booking_date": "2025-10-30",
    "booking_time": "18:00",
    "package": "Premium Hibachi Experience",
    "status": "confirmed",
    "total_amount": 450.00
  },
  "metadata": {
    "refund_id": "re_1234567890",
    "customer_notified": true
  }
}
```

**Example 2: Admin Edits Customer Info**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2025-10-28T15:45:00Z",
  "user_id": "admin_456",
  "user_role": "ADMIN",
  "user_name": "Mike Chen",
  "user_email": "mike@myhibachi.com",
  "action": "UPDATE",
  "resource_type": "customer",
  "resource_id": "customer_789",
  "resource_name": "Jane Smith",
  "ip_address": "192.168.1.101",
  "user_agent": "Mozilla/5.0...",
  "old_values": {
    "phone": "555-0100",
    "email": "jane.old@example.com"
  },
  "new_values": {
    "phone": "555-0199",
    "email": "jane.new@example.com"
  },
  "metadata": {
    "reason": "Customer requested email update"
  }
}
```

**Example 3: Super Admin Deletes Admin Account**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2025-10-28T16:00:00Z",
  "user_id": "superadmin_001",
  "user_role": "SUPER_ADMIN",
  "user_name": "Alex Rodriguez",
  "user_email": "alex@myhibachi.com",
  "action": "DELETE",
  "resource_type": "admin",
  "resource_id": "admin_999",
  "resource_name": "Tom Wilson (ADMIN)",
  "ip_address": "192.168.1.102",
  "user_agent": "Mozilla/5.0...",
  "delete_reason": "Employee termination - last day 10/27/2025. All access revoked per HR policy. Admin account no longer needed.",
  "old_values": {
    "name": "Tom Wilson",
    "email": "tom@myhibachi.com",
    "role": "ADMIN",
    "stations": ["station_1", "station_2"],
    "active": true
  },
  "metadata": {
    "hr_ticket": "HR-2025-1234",
    "notified_admins": ["superadmin_001", "superadmin_002"]
  }
}
```

---

## 🛠️ Implementation Steps

### Phase 1: Database Schema (Day 1 - 4 hours)

**Step 1: Create Audit Logs Table**

```sql
-- Migration: 001_create_audit_logs_table.sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Who
    user_id UUID NOT NULL REFERENCES users(id),
    user_role VARCHAR(50) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    
    -- What
    action VARCHAR(10) NOT NULL CHECK (action IN ('VIEW', 'CREATE', 'UPDATE', 'DELETE')),
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    resource_name VARCHAR(255),
    
    -- Where
    ip_address INET,
    user_agent TEXT,
    station_id UUID REFERENCES stations(id),
    
    -- Why (for deletes)
    delete_reason TEXT,
    
    -- Details
    old_values JSONB,
    new_values JSONB,
    metadata JSONB,
    
    -- Indexes
    CONSTRAINT delete_must_have_reason CHECK (
        action != 'DELETE' OR (delete_reason IS NOT NULL AND length(delete_reason) >= 10)
    )
);

-- Indexes for fast queries
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_station_id ON audit_logs(station_id);
CREATE INDEX idx_audit_logs_user_role ON audit_logs(user_role);
```

**Step 2: Add Soft Delete Columns**

```sql
-- Migration: 002_add_soft_delete_columns.sql
ALTER TABLE bookings ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE bookings ADD COLUMN deleted_by UUID REFERENCES users(id);
ALTER TABLE bookings ADD COLUMN delete_reason TEXT;

ALTER TABLE customers ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE customers ADD COLUMN deleted_by UUID REFERENCES users(id);
ALTER TABLE customers ADD COLUMN delete_reason TEXT;

ALTER TABLE leads ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE leads ADD COLUMN deleted_by UUID REFERENCES users(id);
ALTER TABLE leads ADD COLUMN delete_reason TEXT;

ALTER TABLE reviews ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE reviews ADD COLUMN deleted_by UUID REFERENCES users(id);
ALTER TABLE reviews ADD COLUMN delete_reason TEXT;

-- Indexes for soft delete queries
CREATE INDEX idx_bookings_deleted_at ON bookings(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_customers_deleted_at ON customers(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_leads_deleted_at ON leads(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_reviews_deleted_at ON reviews(deleted_at) WHERE deleted_at IS NULL;
```

**Step 3: Update Users Table with Roles**

```sql
-- Migration: 003_add_user_roles.sql
CREATE TYPE user_role AS ENUM ('SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT', 'STATION_MANAGER');

ALTER TABLE users ADD COLUMN role user_role DEFAULT 'CUSTOMER_SUPPORT';
ALTER TABLE users ADD COLUMN assigned_station_id UUID REFERENCES stations(id);

-- Migrate existing users (update manually based on your needs)
UPDATE users SET role = 'SUPER_ADMIN' WHERE email IN ('alex@myhibachi.com', 'owner@myhibachi.com');
UPDATE users SET role = 'ADMIN' WHERE is_admin = true AND role IS NULL;

-- Create index
CREATE INDEX idx_users_role ON users(role);
```

### Phase 2: Backend Implementation (Day 2-3 - 12 hours)

**Step 1: Create Audit Logger Service**

```python
# apps/backend/src/core/audit_logger.py

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from .database import audit_logs_table

class AuditLogger:
    """
    Comprehensive audit logging service for all admin actions.
    
    Usage:
        await audit_logger.log(
            session=db,
            user=current_user,
            action="DELETE",
            resource_type="booking",
            resource_id=booking_id,
            resource_name=f"{booking.customer_name} - {booking.date}",
            delete_reason=request.delete_reason,
            old_values=booking.to_dict(),
            ip_address=request.client.host,
            station_id=booking.station_id
        )
    """
    
    @staticmethod
    async def log(
        session: AsyncSession,
        user: Dict[str, Any],
        action: str,  # 'VIEW', 'CREATE', 'UPDATE', 'DELETE'
        resource_type: str,
        resource_id: str,
        resource_name: Optional[str] = None,
        delete_reason: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        station_id: Optional[UUID] = None,
    ):
        """Log an admin action to audit_logs table."""
        
        # Validate delete actions have reason
        if action == "DELETE":
            if not delete_reason or len(delete_reason) < 10:
                raise ValueError("Delete actions require a reason (min 10 characters)")
        
        # Insert audit log
        stmt = insert(audit_logs_table).values(
            user_id=user["id"],
            user_role=user["role"],
            user_name=user.get("name", user.get("email")),
            user_email=user["email"],
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            resource_name=resource_name,
            ip_address=ip_address,
            user_agent=user_agent,
            station_id=station_id,
            delete_reason=delete_reason,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata or {},
        )
        
        await session.execute(stmt)
        await session.commit()
    
    @staticmethod
    async def log_view(session: AsyncSession, user: Dict, resource_type: str, resource_id: str, **kwargs):
        """Log a VIEW action."""
        await AuditLogger.log(session, user, "VIEW", resource_type, resource_id, **kwargs)
    
    @staticmethod
    async def log_create(session: AsyncSession, user: Dict, resource_type: str, resource_id: str, new_values: Dict, **kwargs):
        """Log a CREATE action."""
        await AuditLogger.log(session, user, "CREATE", resource_type, resource_id, new_values=new_values, **kwargs)
    
    @staticmethod
    async def log_update(session: AsyncSession, user: Dict, resource_type: str, resource_id: str, old_values: Dict, new_values: Dict, **kwargs):
        """Log an UPDATE action."""
        await AuditLogger.log(session, user, "UPDATE", resource_type, resource_id, old_values=old_values, new_values=new_values, **kwargs)
    
    @staticmethod
    async def log_delete(session: AsyncSession, user: Dict, resource_type: str, resource_id: str, delete_reason: str, old_values: Dict, **kwargs):
        """Log a DELETE action."""
        await AuditLogger.log(session, user, "DELETE", resource_type, resource_id, delete_reason=delete_reason, old_values=old_values, **kwargs)


# Convenience instance
audit_logger = AuditLogger()
```

**Step 2: Create Role-Based Auth Dependencies**

```python
# apps/backend/src/api/app/utils/auth.py

from fastapi import Depends, HTTPException, Request
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    STATION_MANAGER = "STATION_MANAGER"


class Permission:
    """Permission checks for role-based access control."""
    
    # Booking permissions
    BOOKING_VIEW_ALL = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    BOOKING_CREATE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    BOOKING_UPDATE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    BOOKING_DELETE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    
    # Customer permissions
    CUSTOMER_VIEW = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    CUSTOMER_MANAGE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    CUSTOMER_DELETE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    
    # Chef permissions
    CHEF_VIEW_ALL = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    CHEF_ASSIGN = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER]
    
    # Admin permissions
    ADMIN_MANAGE = [UserRole.SUPER_ADMIN]
    
    # Financial permissions
    FINANCIAL_VIEW = [UserRole.SUPER_ADMIN, UserRole.ADMIN]


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency to require specific roles.
    
    Usage:
        @router.get("/admin/bookings")
        async def get_bookings(
            current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]))
        ):
            ...
    """
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = UserRole(current_user.get("role"))
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {', '.join([r.value for r in allowed_roles])}"
            )
        
        return current_user
    
    return role_checker


# Convenience dependencies
require_super_admin = require_role([UserRole.SUPER_ADMIN])
require_admin = require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])
require_customer_support = require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT])
require_station_manager = require_role([UserRole.STATION_MANAGER])
```

**Step 3: Update Booking DELETE Endpoint**

```python
# apps/backend/src/api/app/routers/bookings.py

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from core.audit_logger import audit_logger
from api.app.utils.auth import require_customer_support, UserRole

router = APIRouter()


class DeleteBookingRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for deletion (required)")


@router.delete("/bookings/{booking_id}", status_code=200)
async def delete_booking(
    booking_id: str,
    request: Request,
    delete_request: DeleteBookingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_customer_support),  # SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT
):
    """
    Delete a booking (soft delete with audit trail).
    
    **Required:** Delete reason (min 10 characters)
    **Permissions:** SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT
    **Audit:** Logged to audit_logs table
    """
    
    # Fetch booking
    booking = await booking_service.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Multi-tenant check
    if current_user["role"] == UserRole.STATION_MANAGER:
        if booking.station_id != current_user.get("assigned_station_id"):
            raise HTTPException(status_code=403, detail="Can only delete bookings from your assigned station")
    
    # Store old values for audit
    old_values = {
        "customer_name": booking.customer_name,
        "booking_date": str(booking.booking_date),
        "booking_time": booking.booking_time,
        "package": booking.package,
        "status": booking.status,
        "total_amount": float(booking.total_amount),
    }
    
    # Perform soft delete
    booking.deleted_at = datetime.utcnow()
    booking.deleted_by = current_user["id"]
    booking.delete_reason = delete_request.reason
    
    await db.commit()
    
    # Log to audit trail
    await audit_logger.log_delete(
        session=db,
        user=current_user,
        resource_type="booking",
        resource_id=booking_id,
        resource_name=f"{booking.customer_name} - {booking.booking_date}",
        delete_reason=delete_request.reason,
        old_values=old_values,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        station_id=booking.station_id,
        metadata={
            "customer_id": booking.customer_id,
            "total_amount": float(booking.total_amount),
        }
    )
    
    # TODO: Send notification to customer
    # await email_service.send_booking_cancelled(booking, delete_request.reason)
    
    return {
        "success": True,
        "message": "Booking deleted successfully",
        "deleted_at": booking.deleted_at,
        "deleted_by": current_user["name"],
        "reason": delete_request.reason,
    }
```

### Phase 3: Frontend Components (Day 4-5 - 16 hours)

**Step 1: DeleteConfirmationModal Component**

```typescript
// apps/admin/src/components/DeleteConfirmationModal.tsx

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { AlertTriangle, Loader2 } from 'lucide-react';

interface DeleteConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason: string) => Promise<void>;
  resourceType: string;
  resourceName: string;
  warningMessage?: string;
}

export function DeleteConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  resourceType,
  resourceName,
  warningMessage = 'This action cannot be undone.',
}: DeleteConfirmationModalProps) {
  const [reason, setReason] = useState('');
  const [understood, setUnderstood] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    // Validation
    if (reason.length < 10) {
      setError('Reason must be at least 10 characters');
      return;
    }

    if (!understood) {
      setError('You must confirm that you understand');
      return;
    }

    setIsDeleting(true);
    setError('');

    try {
      await onConfirm(reason);
      handleClose();
    } catch (err: any) {
      setError(err.message || 'Failed to delete');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClose = () => {
    setReason('');
    setUnderstood(false);
    setError('');
    onClose();
  };

  const isReasonValid = reason.length >= 10 && reason.length <= 500;
  const canConfirm = isReasonValid && understood && !isDeleting;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-red-100 p-2">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <DialogTitle className="text-xl">Delete {resourceType}?</DialogTitle>
              <DialogDescription className="text-sm text-gray-500 mt-1">
                {resourceName}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Warning Message */}
          <div className="rounded-md bg-red-50 border border-red-200 p-3">
            <p className="text-sm text-red-800">{warningMessage}</p>
          </div>

          {/* Reason Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Reason for deletion <span className="text-red-500">*</span>
            </label>
            <Textarea
              placeholder="Please provide a detailed reason for deleting this record..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className={`min-h-[100px] ${
                reason.length > 0 && !isReasonValid ? 'border-red-500' : ''
              }`}
              disabled={isDeleting}
              maxLength={500}
            />
            <div className="flex justify-between text-xs">
              <span className={reason.length < 10 ? 'text-red-500' : 'text-gray-500'}>
                Minimum 10 characters required
              </span>
              <span className={reason.length > 500 ? 'text-red-500' : 'text-gray-500'}>
                {reason.length}/500
              </span>
            </div>
          </div>

          {/* Confirmation Checkbox */}
          <div className="flex items-start space-x-2">
            <Checkbox
              id="understand"
              checked={understood}
              onCheckedChange={(checked) => setUnderstood(checked as boolean)}
              disabled={isDeleting}
            />
            <label
              htmlFor="understand"
              className="text-sm text-gray-700 cursor-pointer select-none"
            >
              I understand that this action will be permanently logged and may be irreversible
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-md bg-red-50 border border-red-200 p-2">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirm}
              disabled={!canConfirm}
              className="min-w-[120px]"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Confirm Delete'
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

**Step 2: Usage Example in Booking Management**

```typescript
// apps/admin/src/components/BookingActions.tsx

import { useState } from 'react';
import { DeleteConfirmationModal } from './DeleteConfirmationModal';
import { useToast } from '@/components/ui/use-toast';
import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface BookingActionsProps {
  booking: {
    id: string;
    customer_name: string;
    booking_date: string;
    booking_time: string;
  };
  onDeleted: () => void;
}

export function BookingActions({ booking, onDeleted }: BookingActionsProps) {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const { toast } = useToast();

  const handleDelete = async (reason: string) => {
    const response = await fetch(`/api/bookings/${booking.id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete booking');
    }

    toast({
      title: 'Booking Deleted',
      description: `${booking.customer_name}'s booking has been deleted successfully.`,
      variant: 'default',
    });

    onDeleted();
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowDeleteModal(true)}
        className="text-red-600 hover:text-red-700 hover:bg-red-50"
      >
        <Trash2 className="h-4 w-4 mr-1" />
        Delete
      </Button>

      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
        resourceType="Booking"
        resourceName={`${booking.customer_name} - ${booking.booking_date} ${booking.booking_time}`}
        warningMessage="This booking will be deleted. The customer will be notified via email."
      />
    </>
  );
}
```

**Step 3: Role-Based UI Hook**

```typescript
// apps/admin/src/hooks/usePermissions.ts

import { useAuth } from '@/contexts/AuthContext';

export enum UserRole {
  SUPER_ADMIN = 'SUPER_ADMIN',
  ADMIN = 'ADMIN',
  CUSTOMER_SUPPORT = 'CUSTOMER_SUPPORT',
  STATION_MANAGER = 'STATION_MANAGER',
}

export function usePermissions() {
  const { user } = useAuth();
  const userRole = user?.role as UserRole;

  return {
    // Booking permissions
    canViewAllBookings: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT].includes(userRole),
    canAddBooking: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT].includes(userRole),
    canEditBooking: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT].includes(userRole),
    canDeleteBooking: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT].includes(userRole),
    
    // Customer permissions
    canManageCustomers: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT].includes(userRole),
    
    // Chef permissions
    canAssignChef: [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER].includes(userRole),
    
    // Admin permissions
    canManageAdmins: userRole === UserRole.SUPER_ADMIN,
    
    // Financial permissions
    canViewFinancials: [UserRole.SUPER_ADMIN, UserRole.ADMIN].includes(userRole),
    
    // Audit permissions
    canViewAllAuditLogs: [UserRole.SUPER_ADMIN, UserRole.ADMIN].includes(userRole),
    
    // Helper
    isSuperAdmin: userRole === UserRole.SUPER_ADMIN,
    isAdmin: userRole === UserRole.ADMIN,
    isCustomerSupport: userRole === UserRole.CUSTOMER_SUPPORT,
    isStationManager: userRole === UserRole.STATION_MANAGER,
  };
}
```

**Step 4: Role-Based Component Wrapper**

```typescript
// apps/admin/src/components/RequireRole.tsx

import { ReactNode } from 'react';
import { usePermissions, UserRole } from '@/hooks/usePermissions';
import { useAuth } from '@/contexts/AuthContext';

interface RequireRoleProps {
  role: UserRole | UserRole[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function RequireRole({ role, children, fallback = null }: RequireRoleProps) {
  const { user } = useAuth();
  const userRole = user?.role as UserRole;

  const allowedRoles = Array.isArray(role) ? role : [role];
  const hasPermission = allowedRoles.includes(userRole);

  if (!hasPermission) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

// Usage example:
// <RequireRole role={UserRole.SUPER_ADMIN}>
//   <DeleteAdminButton />
// </RequireRole>
```

### Phase 4: Testing (Day 6-7 - 16 hours)

**Backend Tests:**

```python
# apps/backend/tests/test_booking_delete.py

import pytest
from fastapi.testclient import TestClient

def test_delete_booking_without_reason_fails(client: TestClient, customer_support_token: str):
    """Test that deleting without reason returns 422."""
    response = client.delete(
        "/api/bookings/test_booking_id",
        headers={"Authorization": f"Bearer {customer_support_token}"},
        json={}  # Missing reason
    )
    assert response.status_code == 422

def test_delete_booking_with_short_reason_fails(client: TestClient, customer_support_token: str):
    """Test that reason must be at least 10 characters."""
    response = client.delete(
        "/api/bookings/test_booking_id",
        headers={"Authorization": f"Bearer {customer_support_token}"},
        json={"reason": "Short"}  # Only 5 chars
    )
    assert response.status_code == 422

def test_delete_booking_success(client: TestClient, customer_support_token: str, db: AsyncSession):
    """Test successful booking deletion with audit logging."""
    response = client.delete(
        "/api/bookings/test_booking_id",
        headers={"Authorization": f"Bearer {customer_support_token}"},
        json={"reason": "Customer requested cancellation due to weather concerns"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify audit log created
    audit_log = await db.execute(
        "SELECT * FROM audit_logs WHERE resource_id = 'test_booking_id' AND action = 'DELETE'"
    )
    assert audit_log is not None
    assert audit_log["delete_reason"] == "Customer requested cancellation due to weather concerns"

def test_customer_support_can_delete_booking(client: TestClient, customer_support_token: str):
    """Test that CUSTOMER_SUPPORT role can delete bookings."""
    response = client.delete(
        "/api/bookings/test_booking_id",
        headers={"Authorization": f"Bearer {customer_support_token}"},
        json={"reason": "This is a valid reason for deletion"}
    )
    assert response.status_code == 200

def test_station_manager_cannot_delete_other_station_booking(client: TestClient, station_manager_token: str):
    """Test that STATION_MANAGER cannot delete bookings from other stations."""
    response = client.delete(
        "/api/bookings/other_station_booking_id",
        headers={"Authorization": f"Bearer {station_manager_token}"},
        json={"reason": "This is a valid reason for deletion"}
    )
    assert response.status_code == 403
```

**Frontend Tests:**

```typescript
// apps/admin/src/components/__tests__/DeleteConfirmationModal.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DeleteConfirmationModal } from '../DeleteConfirmationModal';

describe('DeleteConfirmationModal', () => {
  const mockOnConfirm = jest.fn().mockResolvedValue(undefined);
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly when open', () => {
    render(
      <DeleteConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        resourceType="Booking"
        resourceName="John Doe - Oct 28, 2025"
      />
    );

    expect(screen.getByText('Delete Booking?')).toBeInTheDocument();
    expect(screen.getByText('John Doe - Oct 28, 2025')).toBeInTheDocument();
  });

  it('disables confirm button when reason is too short', () => {
    render(
      <DeleteConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        resourceType="Booking"
        resourceName="John Doe - Oct 28, 2025"
      />
    );

    const textarea = screen.getByPlaceholderText(/provide a detailed reason/i);
    fireEvent.change(textarea, { target: { value: 'Short' } });

    const confirmButton = screen.getByRole('button', { name: /confirm delete/i });
    expect(confirmButton).toBeDisabled();
  });

  it('enables confirm button when reason is valid and checkbox is checked', () => {
    render(
      <DeleteConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        resourceType="Booking"
        resourceName="John Doe - Oct 28, 2025"
      />
    );

    const textarea = screen.getByPlaceholderText(/provide a detailed reason/i);
    fireEvent.change(textarea, { target: { value: 'This is a valid reason for deletion' } });

    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    const confirmButton = screen.getByRole('button', { name: /confirm delete/i });
    expect(confirmButton).not.toBeDisabled();
  });

  it('calls onConfirm with reason when confirmed', async () => {
    render(
      <DeleteConfirmationModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        resourceType="Booking"
        resourceName="John Doe - Oct 28, 2025"
      />
    );

    const reason = 'This is a valid reason for deletion';
    const textarea = screen.getByPlaceholderText(/provide a detailed reason/i);
    fireEvent.change(textarea, { target: { value: reason } });

    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    const confirmButton = screen.getByRole('button', { name: /confirm delete/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledWith(reason);
    });
  });
});
```

---

## 📊 Expected Timeline

### Week 1: Foundation (40 hours)

| Day | Task | Hours | Status |
|-----|------|-------|--------|
| Mon | Database schema (audit_logs, soft delete) | 4h | 🔴 |
| Mon | User roles migration | 2h | 🔴 |
| Tue | AuditLogger service | 4h | 🔴 |
| Tue | Role-based auth dependencies | 4h | 🔴 |
| Wed | Update booking DELETE endpoint | 3h | 🔴 |
| Wed | Update customer DELETE endpoint | 3h | 🔴 |
| Thu | DeleteConfirmationModal component | 6h | 🔴 |
| Thu | RequireRole component + hook | 2h | 🔴 |
| Fri | Backend tests (delete + auth) | 6h | 🔴 |
| Fri | Frontend tests (modal + permissions) | 6h | 🔴 |

**Total Week 1: 40 hours**

### Week 2: Advanced Features (20 hours)

| Day | Task | Hours | Status |
|-----|------|-------|--------|
| Mon | Customer Support dashboard | 8h | 🔴 |
| Tue | Audit log viewer UI | 6h | 🔴 |
| Wed | Soft delete restore functionality | 4h | 🔴 |
| Thu | Email notifications for deletions | 2h | 🔴 |

**Total Week 2: 20 hours**

---

## ✅ Success Criteria

- [ ] **Database:** audit_logs table created with proper indexes
- [ ] **Database:** Soft delete columns added to all resources
- [ ] **Database:** User roles enum and migration completed
- [ ] **Backend:** AuditLogger service implemented and tested
- [ ] **Backend:** Role-based auth dependencies working
- [ ] **Backend:** All DELETE endpoints require reason (validated)
- [ ] **Backend:** All DELETE actions logged to audit_logs
- [ ] **Frontend:** DeleteConfirmationModal component complete
- [ ] **Frontend:** Role-based UI components (RequireRole, usePermissions)
- [ ] **Frontend:** Customer Support can delete bookings
- [ ] **Frontend:** Audit log viewer functional
- [ ] **Tests:** 80%+ backend test coverage
- [ ] **Tests:** 80%+ frontend test coverage
- [ ] **Documentation:** API docs updated with new endpoints
- [ ] **Documentation:** User guide for delete workflow

---

## 🚀 Ready to Start?

**Next Steps:**

1. Review this guide
2. Start with Phase 1 (Database Schema) - Day 1
3. Follow implementation steps sequentially
4. Test each component before moving to next phase
5. Update TODO list as you complete each task

**Questions? Issues?** Refer back to this guide or ask for clarification!

---

**Document:** RBAC_AND_DELETE_TRACKING_IMPLEMENTATION_GUIDE.md  
**Status:** Ready for Implementation  
**Date:** October 28, 2025  
**Estimated Completion:** Week 2 (60 hours total)
