# 🔐 4-Tier RBAC + Google Calendar Integration - Implementation Plan

**Date:** October 28, 2025  
**Priority:** CRITICAL  
**Estimated Time:** 3-4 weeks (120 hours)  
**Status:** Ready to Begin  

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [4-Tier Role System](#4-tier-role-system)
3. [Implementation Phases](#implementation-phases)
4. [Week 1: Core RBAC System](#week-1-core-rbac-system)
5. [Week 2: Google Calendar Integration](#week-2-google-calendar-integration)
6. [Week 3: Station Manager Features](#week-3-station-manager-features)
7. [Week 4: Polish & Testing](#week-4-polish--testing)
8. [Technical Specifications](#technical-specifications)
9. [Security Considerations](#security-considerations)

---

## 🎯 Overview

### The Problem

Currently, you have a single "admin" role with full access. This creates:
- **Security Risk**: No principle of least privilege
- **Compliance Issue**: No separation of duties (SOX, SOC 2)
- **Operational Risk**: Customer support can access financial data
- **Audit Gap**: Can't track who did what at which station

### The Solution

**4-Tier Role-Based Access Control (RBAC)** with Google Calendar integration for chef scheduling.

---

## 👥 4-Tier Role System

### 1. 🔴 SUPER_ADMIN (God Mode)

**Access:** Everything  
**Count:** 1-2 people (you + CTO)  
**Can Do:**
- ✅ Manage all admin accounts (create, edit, delete)
- ✅ Assign roles to other admins
- ✅ View all stations
- ✅ Access financial reports
- ✅ Change system settings
- ✅ View audit logs
- ✅ Emergency overrides

**Cannot Do:**
- ❌ Nothing is restricted

**Use Case:** System owner, emergency situations, compliance audits

---

### 2. 🟠 ADMIN (Operations Manager)

**Access:** Most operations, no admin management  
**Count:** 3-5 people (operations team)  
**Can Do:**
- ✅ View all stations
- ✅ Manage bookings across all stations
- ✅ Assign chefs to parties
- ✅ View financial reports
- ✅ Manage customers
- ✅ Handle refunds
- ✅ View audit logs (read-only)

**Cannot Do:**
- ❌ Create/delete/edit other admin accounts
- ❌ Change system settings
- ❌ Delete audit logs

**Use Case:** Day-to-day operations, cross-station management

---

### 3. 🔵 CUSTOMER_SUPPORT (Customer-Facing Only)

**Access:** Customer-facing features only  
**Count:** 5-10 people (support team)  
**Can Do:**
- ✅ View customer bookings
- ✅ Respond to customer messages
- ✅ Manage leads (mark as contacted, add notes)
- ✅ View customer reviews
- ✅ Update FAQ content
- ✅ Search customer profiles
- ✅ Send customer emails

**Cannot Do:**
- ❌ Assign chefs to parties
- ❌ View station financials
- ❌ Access internal scheduling
- ❌ Manage admin accounts
- ❌ View other stations' data
- ❌ Cancel bookings (must escalate to ADMIN)

**Use Case:** Customer inquiries, lead follow-up, review management

---

### 4. 🟢 STATION_MANAGER (Station-Specific)

**Access:** Their assigned station only  
**Count:** 1-2 per station (10-20 total)  
**Can Do:**
- ✅ View their station's bookings
- ✅ Assign chefs to parties at their station
- ✅ Create Google Calendar events for chef schedules
- ✅ Invite chefs to events (Google Calendar invite)
- ✅ View chef availability
- ✅ Manage chef pool for their station
- ✅ View station performance metrics
- ✅ Update party status (confirmed, in-progress, completed)

**Cannot Do:**
- ❌ View other stations' data
- ❌ View financial reports
- ❌ Manage admin accounts
- ❌ Cancel bookings (must escalate to ADMIN)
- ❌ Access customer support features

**Use Case:** On-site station operations, chef scheduling

**Special Feature:** Google Calendar OAuth integration for automated scheduling

---

## 📅 Implementation Phases

### **Phase 1: Core RBAC** (Week 1 - 16 hours)
1. Database schema (roles, permissions)
2. Backend role enforcement
3. JWT with role claims
4. Admin role middleware
5. Migration for existing users

### **Phase 2: Google Calendar** (Week 2 - 24 hours)
1. Google OAuth2 setup
2. Calendar API integration
3. Event creation/updates
4. Chef invitations
5. Sync mechanism

### **Phase 3: Station Manager Features** (Week 3 - 40 hours)
1. Chef assignment UI
2. Scheduling calendar
3. Availability checking
4. Conflict detection
5. Station manager dashboard

### **Phase 4: Testing & Polish** (Week 4 - 40 hours)
1. Unit tests (80% coverage)
2. Integration tests
3. E2E tests (critical flows)
4. Security audit
5. Documentation

---

## 🗓️ Week 1: Core RBAC System

### Day 1-2: Database Schema (8 hours)

#### 1. Create Roles Enum

```python
# apps/backend/src/core/enums.py

from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    CUSTOMER_SUPPORT = "customer_support"
    STATION_MANAGER = "station_manager"
    CUSTOMER = "customer"  # Regular customer (existing)
```

#### 2. Update Users Table

```python
# apps/backend/alembic/versions/xxx_add_role_system.py

"""Add role system

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add role column
    op.add_column('users', sa.Column('role', sa.String(50), nullable=False, server_default='customer'))
    
    # Add assigned_station_id for STATION_MANAGER
    op.add_column('users', sa.Column('assigned_station_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key to stations
    op.create_foreign_key(
        'fk_users_assigned_station',
        'users', 'stations',
        ['assigned_station_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for role queries
    op.create_index('idx_users_role', 'users', ['role'])
    
    # Create permissions table
    op.create_table(
        'role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    
    # Create audit log table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_role', sa.String(50), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_values', postgresql.JSONB, nullable=True),
        sa.Column('new_values', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    
    # Create indexes for audit logs
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])

def downgrade():
    op.drop_index('idx_audit_logs_action')
    op.drop_index('idx_audit_logs_created_at')
    op.drop_index('idx_audit_logs_user_id')
    op.drop_table('audit_logs')
    op.drop_table('role_permissions')
    op.drop_index('idx_users_role')
    op.drop_constraint('fk_users_assigned_station', 'users', type_='foreignkey')
    op.drop_column('users', 'assigned_station_id')
    op.drop_column('users', 'role')
```

#### 3. Update User Model

```python
# apps/backend/src/models/user.py

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.enums import UserRole

class User(Base):
    __tablename__ = "users"
    
    # ... existing columns ...
    
    role = Column(String(50), nullable=False, default=UserRole.CUSTOMER, index=True)
    assigned_station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    assigned_station = relationship("Station", back_populates="station_managers")
    
    def has_role(self, *roles: UserRole) -> bool:
        """Check if user has any of the specified roles"""
        return self.role in [r.value if isinstance(r, UserRole) else r for r in roles]
    
    def is_admin(self) -> bool:
        """Check if user has any admin role"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER]
    
    def can_access_station(self, station_id: str) -> bool:
        """Check if user can access a specific station"""
        if self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            return True
        if self.role == UserRole.STATION_MANAGER:
            return str(self.assigned_station_id) == station_id
        return False
```

---

### Day 3-4: Backend Role Enforcement (8 hours)

#### 1. Role-Based Auth Dependencies

```python
# apps/backend/src/api/app/utils/auth.py

from fastapi import Depends, HTTPException, status, Request
from typing import Optional, List
from core.enums import UserRole
from models.user import User

async def get_current_user_with_role(
    required_roles: List[UserRole],
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify user has one of the required roles
    
    Usage:
        @app.get("/admin/bookings")
        async def get_bookings(
            user: User = Depends(get_current_user_with_role([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
        ):
            ...
    """
    if not current_user.has_role(*required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required role: {[r.value for r in required_roles]}"
        )
    return current_user

# Convenience functions
async def get_super_admin(current_user: User = Depends(get_current_user)) -> User:
    return await get_current_user_with_role([UserRole.SUPER_ADMIN], current_user)

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    return await get_current_user_with_role([UserRole.SUPER_ADMIN, UserRole.ADMIN], current_user)

async def get_station_manager(current_user: User = Depends(get_current_user)) -> User:
    return await get_current_user_with_role([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER], current_user)

async def get_customer_support(current_user: User = Depends(get_current_user)) -> User:
    return await get_current_user_with_role([UserRole.CUSTOMER_SUPPORT], current_user)

async def verify_station_access(
    station_id: str,
    current_user: User = Depends(get_station_manager)
) -> User:
    """Verify user can access the specified station"""
    if not current_user.can_access_station(station_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No access to station {station_id}"
        )
    return current_user
```

#### 2. Update Calendar Endpoints

```python
# apps/backend/src/api/app/routers/bookings.py

from api.app.utils.auth import get_station_manager, verify_station_access

@router.get("/admin/weekly", response_model=List[BookingResponse])
async def get_weekly_bookings(
    start_date: date,
    station_id: Optional[str] = None,
    current_user: User = Depends(get_station_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Get weekly bookings with role-based filtering
    
    - SUPER_ADMIN/ADMIN: Can view all stations (station_id optional)
    - STATION_MANAGER: Can only view their assigned station
    """
    # Enforce station access for STATION_MANAGER
    if current_user.role == UserRole.STATION_MANAGER:
        if not current_user.assigned_station_id:
            raise HTTPException(400, "Station manager has no assigned station")
        station_id = str(current_user.assigned_station_id)
    
    # Build query with station filter
    query = select(Booking).where(
        Booking.event_date >= start_date,
        Booking.event_date < start_date + timedelta(days=7)
    )
    
    if station_id:
        query = query.where(Booking.station_id == station_id)
    
    # ... rest of implementation ...

@router.patch("/admin/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking_datetime(
    booking_id: str,
    update_data: BookingDateTimeUpdate,
    current_user: User = Depends(get_station_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Update booking with role-based access control
    """
    # Fetch booking
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    # Verify station access
    if not current_user.can_access_station(str(booking.station_id)):
        raise HTTPException(403, "No access to this booking's station")
    
    # ... rest of implementation ...
```

---

#### 3. Audit Logging Middleware

```python
# apps/backend/src/core/audit_logger.py

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from models.audit_log import AuditLog
from models.user import User

class AuditLogger:
    """
    Centralized audit logging for compliance (GDPR, SOC 2, SOX)
    """
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user: User,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log an admin action to audit_logs table
        
        Args:
            user: User performing the action
            action: Action performed (e.g., "update_booking", "assign_chef")
            resource: Resource type (e.g., "booking", "user")
            resource_id: UUID of the resource
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            ip_address: User's IP address
            user_agent: User's browser/client
        """
        log_entry = {
            "id": uuid.uuid4(),
            "user_id": user.id,
            "user_role": user.role,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "station_id": user.assigned_station_id if user.role == "station_manager" else None,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow()
        }
        
        await db.execute(insert(AuditLog).values(**log_entry))
        await db.commit()

# Middleware to auto-log admin API calls
# apps/backend/src/api/app/middleware/audit_middleware.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.audit_logger import AuditLogger

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only log admin routes
        if request.url.path.startswith("/api/admin"):
            user = request.state.user  # Set by auth middleware
            
            # Log the request
            await AuditLogger.log_action(
                db=request.state.db,
                user=user,
                action=f"{request.method} {request.url.path}",
                resource=request.url.path.split("/")[3] if len(request.url.path.split("/")) > 3 else "unknown",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
        
        response = await call_next(request)
        return response

# Register middleware in main.py
# app.add_middleware(AuditMiddleware)
```

---

## 🗓️ Week 2: Google Calendar Integration

### Day 1-2: Google OAuth2 Setup (8 hours)

#### 1. Google Cloud Console Setup

**Manual Steps:**
1. Go to https://console.cloud.google.com
2. Create new project: "MyHibachi Scheduling"
3. Enable APIs:
   - Google Calendar API
   - Google People API (for profile info)
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs:
     - `https://yourdomain.com/api/auth/google/callback`
     - `http://localhost:3000/api/auth/google/callback` (dev)
   - Copy Client ID and Client Secret
5. Add test users (during development)

#### 2. Store Google Credentials

```bash
# Add to .env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/auth/google/callback
```

#### 3. Database Schema for Google Tokens

```python
# apps/backend/alembic/versions/xxx_add_google_calendar.py

def upgrade():
    op.create_table(
        'google_calendar_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('access_token', sa.Text, nullable=False),  # Encrypted
        sa.Column('refresh_token', sa.Text, nullable=False),  # Encrypted
        sa.Column('token_expiry', sa.DateTime(timezone=True), nullable=False),
        sa.Column('calendar_id', sa.String(255), nullable=True),  # Primary calendar ID
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    op.create_index('idx_google_tokens_user_id', 'google_calendar_tokens', ['user_id'])
```

#### 4. Google OAuth Flow

```python
# apps/backend/src/services/google_calendar_service.py

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi import HTTPException

class GoogleCalendarService:
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/calendar.readonly'
    ]
    
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate Google OAuth authorization URL
        
        Args:
            state: Random string to prevent CSRF (store in session)
        
        Returns:
            Authorization URL to redirect user to
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [self.redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',  # Get refresh token
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Force consent to get refresh token
        )
        
        return auth_url
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access + refresh tokens
        
        Args:
            code: Authorization code from Google redirect
        
        Returns:
            Dict with access_token, refresh_token, expiry
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [self.redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.expiry,
            "calendar_id": "primary"  # Use primary calendar
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        # Implementation using google-auth library
        pass
```

---

### Day 3-5: Calendar Event Management (16 hours)

#### 1. Create Calendar Events

```python
# apps/backend/src/services/google_calendar_service.py (continued)

from datetime import datetime, timedelta
from typing import List, Optional

class GoogleCalendarService:
    # ... previous methods ...
    
    async def create_chef_assignment_event(
        self,
        access_token: str,
        booking_id: str,
        chef_email: str,
        party_date: datetime,
        party_duration_hours: int,
        station_name: str,
        customer_name: str,
        party_size: int,
        special_notes: Optional[str] = None
    ) -> str:
        """
        Create Google Calendar event for chef assignment
        
        Args:
            access_token: User's Google access token
            booking_id: Internal booking UUID
            chef_email: Chef's email (for invitation)
            party_date: Start time of the party
            party_duration_hours: Duration in hours
            station_name: Which station
            customer_name: Customer name for event title
            party_size: Number of guests
            special_notes: Special requests/dietary restrictions
        
        Returns:
            Google Calendar event ID
        """
        credentials = Credentials(token=access_token)
        service = build('calendar', 'v3', credentials=credentials)
        
        # Calculate end time
        end_time = party_date + timedelta(hours=party_duration_hours)
        
        # Build event
        event = {
            'summary': f'Hibachi Party - {customer_name} ({party_size} guests)',
            'location': station_name,
            'description': f"""
**Booking ID:** {booking_id}

**Customer:** {customer_name}
**Party Size:** {party_size} guests
**Station:** {station_name}

{f'**Special Notes:**\\n{special_notes}' if special_notes else ''}

**Internal Link:** https://yourdomain.com/admin/bookings/{booking_id}
            """.strip(),
            'start': {
                'dateTime': party_date.isoformat(),
                'timeZone': 'America/New_York',  # Configure per station
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/New_York',
            },
            'attendees': [
                {'email': chef_email, 'responseStatus': 'needsAction'}
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 60},  # 1 hour before
                ],
            },
            'conferenceData': None,  # No video call needed
            'colorId': '9',  # Blue color for work events
        }
        
        try:
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'  # Send email to chef
            ).execute()
            
            return created_event['id']
        
        except HttpError as error:
            raise HTTPException(500, f"Failed to create calendar event: {error}")
    
    async def update_chef_assignment_event(
        self,
        access_token: str,
        event_id: str,
        new_date: Optional[datetime] = None,
        new_chef_email: Optional[str] = None,
        new_notes: Optional[str] = None
    ):
        """Update existing calendar event"""
        credentials = Credentials(token=access_token)
        service = build('calendar', 'v3', credentials=credentials)
        
        try:
            # Fetch existing event
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update fields
            if new_date:
                duration = datetime.fromisoformat(event['end']['dateTime']) - datetime.fromisoformat(event['start']['dateTime'])
                event['start']['dateTime'] = new_date.isoformat()
                event['end']['dateTime'] = (new_date + duration).isoformat()
            
            if new_chef_email:
                event['attendees'] = [{'email': new_chef_email}]
            
            if new_notes:
                event['description'] += f"\\n\\n**Updated Notes:**\\n{new_notes}"
            
            # Update event
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'  # Notify attendees
            ).execute()
            
            return updated_event['id']
        
        except HttpError as error:
            raise HTTPException(500, f"Failed to update calendar event: {error}")
    
    async def delete_chef_assignment_event(
        self,
        access_token: str,
        event_id: str
    ):
        """Delete calendar event (chef unassigned)"""
        credentials = Credentials(token=access_token)
        service = build('calendar', 'v3', credentials=credentials)
        
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'  # Notify attendees of cancellation
            ).execute()
        
        except HttpError as error:
            raise HTTPException(500, f"Failed to delete calendar event: {error}")
    
    async def get_chef_availability(
        self,
        access_token: str,
        chef_email: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, datetime]]:
        """
        Check chef's availability via freebusy API
        
        Returns:
            List of busy time ranges
        """
        credentials = Credentials(token=access_token)
        service = build('calendar', 'v3', credentials=credentials)
        
        try:
            body = {
                "timeMin": start_date.isoformat(),
                "timeMax": end_date.isoformat(),
                "items": [{"id": chef_email}]
            }
            
            freebusy = service.freebusy().query(body=body).execute()
            busy_times = freebusy['calendars'][chef_email]['busy']
            
            return [
                {
                    "start": datetime.fromisoformat(slot['start'].replace('Z', '+00:00')),
                    "end": datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
                }
                for slot in busy_times
            ]
        
        except HttpError as error:
            # Chef may not share calendar
            return []
```

---

## 🗓️ Week 3: Station Manager Features

### Chef Assignment System (40 hours)

#### 1. Chef Model & Database

```python
# apps/backend/alembic/versions/xxx_add_chef_system.py

def upgrade():
    op.create_table(
        'chefs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('station_id', postgresql.UUID(as_uuid=True), ForeignKey('stations.id'), nullable=False),
        sa.Column('skills', postgresql.JSONB, nullable=True),  # ["hibachi", "sushi", "teppanyaki"]
        sa.Column('availability', postgresql.JSONB, nullable=True),  # Weekly schedule
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    
    op.create_table(
        'chef_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chef_id', postgresql.UUID(as_uuid=True), ForeignKey('chefs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_by_user_id', postgresql.UUID(as_uuid=True), ForeignKey('users.id'), nullable=False),
        sa.Column('google_calendar_event_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), default='assigned'),  # assigned, confirmed, completed, cancelled
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    
    op.create_index('idx_chef_assignments_booking_id', 'chef_assignments', ['booking_id'])
    op.create_index('idx_chef_assignments_chef_id', 'chef_assignments', ['chef_id'])
```

#### 2. Chef Assignment API

```python
# apps/backend/src/api/app/routers/chefs.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.utils.auth import get_station_manager
from services.google_calendar_service import GoogleCalendarService
from core.audit_logger import AuditLogger

router = APIRouter(prefix="/admin/chefs", tags=["Chef Management"])

@router.post("/assign")
async def assign_chef_to_booking(
    booking_id: str,
    chef_id: str,
    current_user: User = Depends(get_station_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign a chef to a booking and create Google Calendar event
    
    Only STATION_MANAGER can assign chefs at their station
    """
    # Fetch booking
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    
    # Verify station access
    if not current_user.can_access_station(str(booking.station_id)):
        raise HTTPException(403, "No access to this booking's station")
    
    # Fetch chef
    chef = await db.get(Chef, chef_id)
    if not chef:
        raise HTTPException(404, "Chef not found")
    
    # Verify chef belongs to same station
    if str(chef.station_id) != str(booking.station_id):
        raise HTTPException(400, "Chef does not work at this station")
    
    # Check for conflicts (chef already assigned to another party at same time)
    conflicts = await check_chef_conflicts(db, chef_id, booking.event_date, booking.event_time)
    if conflicts:
        raise HTTPException(409, f"Chef has conflicting assignment: {conflicts}")
    
    # Get Google Calendar tokens for station manager
    google_service = GoogleCalendarService()
    tokens = await get_google_tokens(db, current_user.id)
    
    if not tokens:
        raise HTTPException(400, "Please connect your Google Calendar first")
    
    # Create Google Calendar event
    try:
        event_id = await google_service.create_chef_assignment_event(
            access_token=tokens.access_token,
            booking_id=booking_id,
            chef_email=chef.email,
            party_date=datetime.combine(booking.event_date, booking.event_time),
            party_duration_hours=2,  # Default 2 hours
            station_name=booking.station.name,
            customer_name=decrypt_pii(booking.customer_name),
            party_size=booking.number_of_guests,
            special_notes=booking.special_requests
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to create calendar event: {str(e)}")
    
    # Create assignment record
    assignment = ChefAssignment(
        id=uuid.uuid4(),
        booking_id=booking_id,
        chef_id=chef_id,
        assigned_by_user_id=current_user.id,
        google_calendar_event_id=event_id,
        status="assigned"
    )
    db.add(assignment)
    
    # Audit log
    await AuditLogger.log_action(
        db=db,
        user=current_user,
        action="assign_chef",
        resource="chef_assignment",
        resource_id=str(assignment.id),
        new_values={
            "booking_id": booking_id,
            "chef_id": chef_id,
            "chef_name": chef.name,
            "google_event_id": event_id
        }
    )
    
    await db.commit()
    
    return {"success": True, "assignment_id": str(assignment.id), "google_event_id": event_id}

@router.get("/availability/{chef_id}")
async def get_chef_availability(
    chef_id: str,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_station_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Check chef availability via Google Calendar
    """
    chef = await db.get(Chef, chef_id)
    if not chef:
        raise HTTPException(404, "Chef not found")
    
    # Verify station access
    if not current_user.can_access_station(str(chef.station_id)):
        raise HTTPException(403, "No access to this chef")
    
    # Get Google Calendar tokens
    google_service = GoogleCalendarService()
    tokens = await get_google_tokens(db, current_user.id)
    
    if not tokens:
        return {"available": True, "note": "Google Calendar not connected"}
    
    # Check freebusy
    busy_times = await google_service.get_chef_availability(
        access_token=tokens.access_token,
        chef_email=chef.email,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time())
    )
    
    return {"chef_id": chef_id, "busy_times": busy_times}
```

---

### Station Manager UI (20 hours)

#### 1. Chef Assignment Component

```typescript
// apps/admin/src/components/ChefAssignment/ChefScheduler.tsx

'use client';

import { useState, useEffect } from 'react';
import { Calendar, Clock, User, AlertCircle } from 'lucide-react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

interface Chef {
  id: string;
  name: string;
  email: string;
  skills: string[];
  isAvailable: boolean;
}

interface Booking {
  id: string;
  customerName: string;
  eventDate: string;
  eventTime: string;
  partySize: number;
  assignedChef?: Chef;
}

export function ChefScheduler() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [chefs, setChefs] = useState<Chef[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isConnectedToGoogle, setIsConnectedToGoogle] = useState(false);

  useEffect(() => {
    fetchBookings();
    fetchChefs();
    checkGoogleConnection();
  }, [selectedDate]);

  const handleDragEnd = async (result: any) => {
    if (!result.destination) return;

    const bookingId = result.draggableId;
    const chefId = result.destination.droppableId;

    // Assign chef
    try {
      const response = await fetch('/api/admin/chefs/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ booking_id: bookingId, chef_id: chefId })
      });

      if (!response.ok) {
        const error = await response.json();
        alert(error.detail);
        return;
      }

      const data = await response.json();
      
      // Update UI
      setBookings(prev => prev.map(b => 
        b.id === bookingId 
          ? { ...b, assignedChef: chefs.find(c => c.id === chefId) }
          : b
      ));

      // Show success toast
      showToast('Chef assigned! Google Calendar invite sent.', 'success');
    } catch (error) {
      showToast('Failed to assign chef', 'error');
    }
  };

  return (
    <div className="p-6">
      {/* Google Calendar Connection Banner */}
      {!isConnectedToGoogle && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="text-yellow-600" />
            <div>
              <p className="font-semibold">Connect Google Calendar</p>
              <p className="text-sm text-gray-600">
                Connect your Google Calendar to automatically schedule chefs and send invites.
              </p>
              <button 
                onClick={connectGoogleCalendar}
                className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Connect Google Calendar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Date Selector */}
      <div className="mb-6 flex items-center gap-4">
        <Calendar className="text-gray-600" />
        <input
          type="date"
          value={selectedDate.toISOString().split('T')[0]}
          onChange={(e) => setSelectedDate(new Date(e.target.value))}
          className="px-4 py-2 border rounded"
        />
      </div>

      {/* Drag-Drop Interface */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="grid grid-cols-2 gap-6">
          {/* Unassigned Bookings */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Unassigned Parties</h3>
            <Droppable droppableId="unassigned">
              {(provided) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className="space-y-2"
                >
                  {bookings.filter(b => !b.assignedChef).map((booking, index) => (
                    <Draggable key={booking.id} draggableId={booking.id} index={index}>
                      {(provided) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          className="p-4 bg-white border rounded-lg shadow-sm hover:shadow-md cursor-move"
                        >
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-semibold">{booking.customerName}</p>
                              <p className="text-sm text-gray-600">
                                <Clock className="inline w-4 h-4 mr-1" />
                                {booking.eventTime}
                              </p>
                              <p className="text-sm text-gray-600">
                                {booking.partySize} guests
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </div>

          {/* Chefs */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Available Chefs</h3>
            <div className="space-y-4">
              {chefs.map(chef => (
                <div key={chef.id} className="border rounded-lg">
                  <div className="p-3 bg-gray-50 border-b flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <User className="w-5 h-5" />
                      <span className="font-semibold">{chef.name}</span>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded ${chef.isAvailable ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {chef.isAvailable ? 'Available' : 'Busy'}
                    </span>
                  </div>

                  <Droppable droppableId={chef.id}>
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                        className={`p-3 min-h-[100px] ${snapshot.isDraggingOver ? 'bg-blue-50' : ''}`}
                      >
                        {bookings
                          .filter(b => b.assignedChef?.id === chef.id)
                          .map((booking, index) => (
                            <Draggable key={booking.id} draggableId={booking.id} index={index}>
                              {(provided) => (
                                <div
                                  ref={provided.innerRef}
                                  {...provided.draggableProps}
                                  {...provided.dragHandleProps}
                                  className="p-2 mb-2 bg-blue-100 border border-blue-300 rounded text-sm"
                                >
                                  <p className="font-semibold">{booking.customerName}</p>
                                  <p className="text-xs text-gray-600">{booking.eventTime}</p>
                                </div>
                              )}
                            </Draggable>
                          ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </div>
              ))}
            </div>
          </div>
        </div>
      </DragDropContext>
    </div>
  );
}

async function connectGoogleCalendar() {
  // Redirect to OAuth flow
  window.location.href = '/api/auth/google/authorize';
}
```

---

## 🔒 Security Considerations

### 1. Google Token Security

```python
# Encrypt tokens before storing
from core.security import encrypt_pii, decrypt_pii

# Store
encrypted_access_token = encrypt_pii(access_token, encryption_key)
encrypted_refresh_token = encrypt_pii(refresh_token, encryption_key)

# Retrieve
access_token = decrypt_pii(encrypted_access_token, encryption_key)
```

### 2. Role Verification Checklist

- [ ] Every admin endpoint has role check
- [ ] STATION_MANAGER can only access their station
- [ ] CUSTOMER_SUPPORT cannot access internal operations
- [ ] ADMIN cannot manage other admins
- [ ] SUPER_ADMIN is the only one who can create/delete admins

### 3. Audit Requirements

- [ ] All admin actions logged to `audit_logs` table
- [ ] Logs include: who, what, when, where, old values, new values
- [ ] Logs are immutable (no DELETE permission)
- [ ] 7-year retention for compliance (GDPR, SOX)

---

## ✅ Week 4: Testing & Deployment

### Testing Checklist (40 hours)

#### Backend Tests (20 hours)

```python
# tests/test_rbac.py

import pytest
from api.app.utils.auth import get_current_user_with_role

@pytest.mark.asyncio
async def test_super_admin_can_view_all_stations():
    """SUPER_ADMIN can view bookings from any station"""
    user = create_user(role="super_admin")
    response = await client.get("/api/admin/weekly?start_date=2025-11-01", headers=auth_headers(user))
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_station_manager_cannot_view_other_stations():
    """STATION_MANAGER can only view their assigned station"""
    user = create_user(role="station_manager", assigned_station_id="station-1")
    response = await client.get("/api/admin/weekly?start_date=2025-11-01&station_id=station-2", headers=auth_headers(user))
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_customer_support_cannot_assign_chefs():
    """CUSTOMER_SUPPORT cannot access chef assignment"""
    user = create_user(role="customer_support")
    response = await client.post("/api/admin/chefs/assign", json={"booking_id": "...", "chef_id": "..."}, headers=auth_headers(user))
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_cannot_delete_other_admins():
    """ADMIN cannot delete other admin accounts"""
    user = create_user(role="admin")
    response = await client.delete("/api/admin/users/super-admin-id", headers=auth_headers(user))
    assert response.status_code == 403

# ... 50+ more tests ...
```

#### Frontend Tests (10 hours)

```typescript
// tests/ChefScheduler.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { ChefScheduler } from '@/components/ChefAssignment/ChefScheduler';

test('station manager can assign chef', async () => {
  render(<ChefScheduler />);
  
  // Drag booking to chef
  const booking = screen.getByText('John Doe - 6:00 PM');
  const chef = screen.getByText('Chef Mike');
  
  fireEvent.dragStart(booking);
  fireEvent.drop(chef);
  
  // Verify API call
  await waitFor(() => {
    expect(fetch).toHaveBeenCalledWith('/api/admin/chefs/assign', {
      method: 'POST',
      body: JSON.stringify({ booking_id: '...', chef_id: '...' })
    });
  });
});
```

#### E2E Tests (10 hours)

```typescript
// e2e/chef-assignment.spec.ts

import { test, expect } from '@playwright/test';

test('station manager workflow', async ({ page }) => {
  // Login as station manager
  await page.goto('/login');
  await page.fill('[name=email]', 'manager@station1.com');
  await page.fill('[name=password]', 'password');
  await page.click('button[type=submit]');
  
  // Connect Google Calendar
  await page.goto('/admin/settings');
  await page.click('text=Connect Google Calendar');
  // ... OAuth flow ...
  
  // Assign chef
  await page.goto('/admin/chef-scheduler');
  await page.dragAndDrop('[data-booking-id="123"]', '[data-chef-id="456"]');
  
  // Verify success
  await expect(page.locator('text=Chef assigned')).toBeVisible();
});
```

---

## 📦 Deployment Steps

### 1. Database Migration

```bash
# Backup production database
pg_dump myhibachi_prod > backup_$(date +%Y%m%d).sql

# Run migrations
cd apps/backend
alembic upgrade head

# Verify
alembic current
```

### 2. Assign Initial Roles

```sql
-- Update existing admin users
UPDATE users SET role = 'super_admin' WHERE email = 'your-email@domain.com';
UPDATE users SET role = 'admin' WHERE email IN ('ops1@domain.com', 'ops2@domain.com');
UPDATE users SET role = 'customer_support' WHERE email LIKE '%support%';
UPDATE users SET role = 'station_manager', assigned_station_id = '<station-uuid>' WHERE email LIKE '%manager%';
```

### 3. Environment Variables

```bash
# Add to production .env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/auth/google/callback
```

### 4. Deploy Backend

```bash
# Deploy to production
git push production main

# Restart services
pm2 restart myhibachi-api
```

### 5. Deploy Frontend

```bash
# Build admin app
cd apps/admin
npm run build

# Deploy to Vercel/Netlify
vercel --prod
```

---

## 🎯 Success Metrics

After implementation, you should have:

- [x] 4 distinct role types with proper permissions
- [x] 100% of admin endpoints protected by role checks
- [x] Google Calendar integration for station managers
- [x] Automated chef scheduling with email invites
- [x] Comprehensive audit logging (100% coverage)
- [x] 80%+ test coverage on new code
- [x] Zero security vulnerabilities (PII encrypted, tokens encrypted)
- [x] Documentation for each role's capabilities
- [x] Training materials for station managers

---

## 📞 Next Steps

### This Week (Must Do)

1. **Review this plan** (1 hour) - Read thoroughly, ask questions
2. **Database migration** (2 hours) - Create and test migration
3. **Add role enum** (1 hour) - Backend code
4. **Update calendar endpoints** (2 hours) - Add role checks
5. **Create audit logger** (2 hours) - Compliance requirement

**Total:** 8 hours (Day 1-2)

### Next Week

6. Google OAuth setup (8 hours)
7. Calendar API integration (16 hours)

---

**Questions? Let me know which part to implement first!** 🚀

**Document:** 4_TIER_RBAC_IMPLEMENTATION_PLAN.md  
**Status:** Ready to Begin  
**Date:** October 28, 2025
