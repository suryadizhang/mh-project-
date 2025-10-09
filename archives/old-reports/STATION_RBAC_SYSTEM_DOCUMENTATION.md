# Station-Aware RBAC System Documentation

## Overview

This document describes the comprehensive Role-Based Access Control (RBAC) system with multi-tenant station scoping implemented for the MyHibachi platform. The system provides a unified permission source that both AI agents and APIs respect, enabling secure multi-tenant operations with proper data isolation.

## Architecture

### Core Components

1. **Station Models** (`apps/api/app/auth/station_models.py`)
   - `Station`: Main tenant entity representing business locations
   - `StationUser`: User-station assignments with roles and permissions
   - `StationAuditLog`: Comprehensive audit trail for all station operations
   - `StationAccessToken`: Station-scoped authentication tokens

2. **Station Authentication** (`apps/api/app/auth/station_auth.py`)
   - `StationAuthenticationService`: Enhanced authentication with station context
   - `StationContext`: Container for station-specific permission data
   - JWT tokens with embedded station context

3. **Station Middleware** (`apps/api/app/auth/station_middleware.py`)
   - `AuthenticatedUser`: Enhanced user object with station context
   - Permission decorators for FastAPI endpoints
   - Audit logging helpers

4. **Agent Gateway** (`apps/ai-api/app/services/agent_gateway.py`)
   - `StationAwareAgentGatewayService`: AI agents with station-scoped permissions
   - Station-aware tool and action filtering
   - Backward compatibility with existing `AgentGatewayService`

5. **Unified Chat API** (`apps/ai-api/app/routers/v1/unified_chat.py`)
   - Station context extraction from JWT tokens
   - Agent permission validation based on station roles
   - Station-scoped responses with audit metadata

## Database Schema

### New Tables

```sql
-- Station entity table
CREATE TABLE stations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    location VARCHAR(200),
    phone VARCHAR(20),
    email VARCHAR(100),
    manager_name VARCHAR(100),
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id)
);

-- User-station assignments with roles
CREATE TABLE station_users (
    id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES stations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    permissions TEXT[] DEFAULT '{}',
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(station_id, user_id)
);

-- Comprehensive audit logging
CREATE TABLE station_audit_logs (
    id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES stations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Station-scoped access tokens
CREATE TABLE station_access_tokens (
    id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES stations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    permissions TEXT[] DEFAULT '{}',
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

### Enhanced Existing Tables

```sql
-- Add station_id to existing tables for multi-tenant isolation
ALTER TABLE customers ADD COLUMN station_id INTEGER REFERENCES stations(id);
ALTER TABLE bookings ADD COLUMN station_id INTEGER REFERENCES stations(id);
ALTER TABLE message_threads ADD COLUMN station_id INTEGER REFERENCES stations(id);
```

### Row Level Security (RLS) Policies

```sql
-- Enable RLS on core tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_threads ENABLE ROW LEVEL SECURITY;

-- Create policies for station isolation
CREATE POLICY customers_station_isolation ON customers
    FOR ALL TO authenticated_users
    USING (station_id = current_setting('app.current_station_id')::INTEGER);

CREATE POLICY bookings_station_isolation ON bookings
    FOR ALL TO authenticated_users
    USING (station_id = current_setting('app.current_station_id')::INTEGER);
```

## Role Hierarchy

### 1. Super Admin
- **Scope**: Global across all stations
- **Permissions**: All operations (`*`)
- **Capabilities**:
  - Create, manage, and delete stations
  - Assign users to any station with any role
  - Access cross-station analytics and reporting
  - Override station-specific restrictions
  - Access all AI agents

### 2. Admin
- **Scope**: Single station (assigned)
- **Permissions**: 
  - `manage_users`, `manage_bookings`, `view_analytics`
  - `view_customers`, `manage_staff`, `view_reports`
- **Capabilities**:
  - Full management within assigned station
  - User and role management (except super admin)
  - Access to admin and analytics AI agents
  - Station configuration and settings

### 3. Station Admin
- **Scope**: Single station (assigned)
- **Permissions**:
  - `manage_bookings`, `view_customers`, `manage_staff`
  - `view_analytics`, `view_station_users`
- **Capabilities**:
  - Operational management within station
  - Staff scheduling and coordination
  - Access to staff and support AI agents
  - Limited user management

### 4. Customer Support
- **Scope**: Single station (assigned)
- **Permissions**:
  - `view_bookings`, `view_customers`, `create_bookings`
  - `update_bookings`, `view_basic_analytics`
- **Capabilities**:
  - Customer service operations
  - Booking management and support
  - Access to customer and support AI agents
  - Basic reporting

## Permission Matrix

| Permission | Super Admin | Admin | Station Admin | Customer Support |
|------------|-------------|-------|---------------|------------------|
| `manage_stations` | ✅ | ❌ | ❌ | ❌ |
| `manage_users` | ✅ | ✅ | ❌ | ❌ |
| `manage_bookings` | ✅ | ✅ | ✅ | ❌ |
| `view_customers` | ✅ | ✅ | ✅ | ✅ |
| `create_bookings` | ✅ | ✅ | ✅ | ✅ |
| `update_bookings` | ✅ | ✅ | ✅ | ✅ |
| `cancel_bookings` | ✅ | ✅ | ✅ | ❌ |
| `manage_staff` | ✅ | ✅ | ✅ | ❌ |
| `view_analytics` | ✅ | ✅ | ✅ | ❌ |
| `view_reports` | ✅ | ✅ | ❌ | ❌ |
| `view_audit_logs` | ✅ | ✅ | ❌ | ❌ |
| `manage_settings` | ✅ | ✅ | ❌ | ❌ |
| `export_data` | ✅ | ✅ | ❌ | ❌ |

## AI Agent Access Matrix

| Agent | Super Admin | Admin | Station Admin | Customer Support | Public |
|-------|-------------|-------|---------------|------------------|--------|
| `customer` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `support` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `staff` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `admin` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `analytics` | ✅ | ✅ | ❌ | ❌ | ❌ |

## API Endpoints

### Station Management

```http
GET    /api/admin/stations/                    # List stations
POST   /api/admin/stations/                    # Create station (super admin only)
GET    /api/admin/stations/{id}                # Get station details
PUT    /api/admin/stations/{id}                # Update station
DELETE /api/admin/stations/{id}                # Delete station (super admin only)
```

### User-Station Management

```http
GET    /api/admin/stations/{id}/users          # List station users
POST   /api/admin/stations/{id}/users          # Assign user to station
PUT    /api/admin/stations/{id}/users/{user_id} # Update user assignment
DELETE /api/admin/stations/{id}/users/{user_id} # Remove user from station
```

### Audit Logging

```http
GET    /api/admin/stations/{id}/audit          # Get station audit logs
GET    /api/admin/audit/cross-station          # Cross-station audit (super admin only)
```

### AI Chat API

```http
POST   /v1/chat                                # Unified chat with station context
POST   /v1/chat/stream                         # Streaming chat with station context
GET    /v1/agents                              # List available agents
GET    /v1/agents/{agent}                      # Get agent capabilities
GET    /v1/health                              # Health check with RBAC status
```

## Authentication Flow

### 1. Station-Aware Login

```http
POST /auth/station-login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password",
  "station_id": 1
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "station_context": {
    "station_id": 1,
    "station_name": "Main Location",
    "role": "admin",
    "permissions": ["manage_users", "view_analytics"],
    "is_super_admin": false
  }
}
```

### 2. JWT Token Structure

```json
{
  "user_id": 123,
  "email": "user@example.com",
  "station_context": {
    "station_id": 1,
    "station_name": "Main Location",
    "role": "admin",
    "permissions": ["manage_users", "view_analytics"],
    "is_super_admin": false
  },
  "exp": 1640995200,
  "iat": 1640991600
}
```

### 3. API Request with Station Context

```http
POST /v1/chat
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
X-Agent: staff
Content-Type: application/json

{
  "message": "Show me today's bookings",
  "context": {"department": "operations"}
}
```

## Implementation Examples

### 1. Permission Checking

```python
from app.auth.station_middleware import require_station_permission

@router.get("/bookings")
async def get_bookings(
    current_user: AuthenticatedUser = Depends(require_station_permission("view_bookings"))
):
    # User is guaranteed to have view_bookings permission
    # and current_user.station_id contains their station scope
    pass
```

### 2. Station-Scoped Queries

```python
from app.auth.station_middleware import get_current_station_user

@router.get("/customers")
async def get_customers(
    current_user: AuthenticatedUser = Depends(get_current_station_user),
    db: Session = Depends(get_db)
):
    # Automatically filter by station unless super admin
    query = db.query(Customer)
    
    if not current_user.is_super_admin:
        query = query.filter(Customer.station_id == current_user.station_id)
    
    return query.all()
```

### 3. AI Agent with Station Context

```python
from app.services.agent_gateway import StationAwareAgentGatewayService

gateway = StationAwareAgentGatewayService()

response = await gateway.process_request(
    agent="staff",
    message="Show me pending bookings",
    station_context=current_user.station_context
)
# Response will be filtered to only show bookings from user's station
```

### 4. Audit Logging

```python
from app.auth.station_middleware import log_station_activity

await log_station_activity(
    db=db,
    user_id=current_user.user_id,
    station_id=current_user.station_id,
    action="create_booking",
    resource_type="booking",
    resource_id=str(booking.id),
    details={"customer_id": booking.customer_id, "amount": booking.total}
)
```

## Security Features

### 1. Multi-Tenant Data Isolation

- **Row Level Security (RLS)** policies enforce data separation at database level
- **Application-level filtering** provides additional protection
- **Station ID validation** ensures users can only access their assigned station
- **Cross-station access prevention** blocks unauthorized data access

### 2. Permission Validation

- **Role-based permissions** with granular control
- **Permission inheritance** with role hierarchy
- **Dynamic permission checking** for all operations
- **Permission escalation prevention** blocks unauthorized privilege increases

### 3. Audit Trail

- **Comprehensive logging** of all sensitive operations
- **IP address and user agent tracking** for security analysis
- **Station-scoped audit logs** with appropriate access controls
- **Tamper-resistant logging** with immutable entries

### 4. Token Security

- **JWT with station context** embedded in secure tokens
- **Token expiration** with configurable timeouts
- **Token revocation** capability for security incidents
- **Station-scoped token validation** prevents cross-station token abuse

## Backward Compatibility

The system maintains full backward compatibility:

1. **Existing APIs** continue to work without station context
2. **Public access** defaults to customer agent with basic permissions
3. **Legacy authentication** still functions alongside station-aware auth
4. **Gradual migration** path for existing users and integrations

### Migration Strategy

1. **Phase 1**: Deploy RBAC system alongside existing auth
2. **Phase 2**: Create default station for existing data
3. **Phase 3**: Migrate existing users to station assignments
4. **Phase 4**: Enable station-scoped features progressively
5. **Phase 5**: Deprecate legacy auth methods (optional)

## Testing

### Integration Tests

Run the comprehensive integration test suite:

```bash
cd scripts
python test_station_rbac_integration.py --api-url http://localhost:8001 --ai-api-url http://localhost:8002
```

### Unit Tests

```bash
# Run station RBAC unit tests
pytest tests/test_station_rbac.py -v

# Run with coverage
pytest tests/test_station_rbac.py --cov=app.auth --cov-report=html
```

### Security Testing

1. **Permission escalation tests**: Verify users cannot gain unauthorized permissions
2. **Cross-station access tests**: Ensure data isolation between stations
3. **Token manipulation tests**: Validate JWT security and station context integrity
4. **SQL injection prevention**: Test RLS policies and parameterized queries

## Monitoring and Observability

### Key Metrics

1. **Authentication Events**
   - Station login attempts and success rates
   - Token creation and validation events
   - Permission denied incidents

2. **Permission Usage**
   - Permission check frequency by role
   - Agent access patterns by station
   - Cross-station access attempts (security events)

3. **Audit Activity**
   - Audit log volume by station
   - Critical action frequency
   - Security event correlation

### Alerts

1. **Security Alerts**
   - Multiple failed authentication attempts
   - Cross-station access violations
   - Permission escalation attempts
   - Unusual agent access patterns

2. **Operational Alerts**
   - High audit log volume
   - Token expiration rates
   - Station configuration changes

## Troubleshooting

### Common Issues

1. **"Access denied to this station"**
   - Check user's station assignment
   - Verify JWT token contains correct station context
   - Ensure user has active assignment

2. **"Agent access denied"**
   - Verify user's role allows requested agent
   - Check permission matrix for role-agent mapping
   - Ensure station context is properly set

3. **"No station context found"**
   - Verify JWT token includes station_context
   - Check Authorization header format
   - Ensure token is not expired

### Debug Steps

1. **Check user station assignments**:
   ```sql
   SELECT su.*, s.name as station_name 
   FROM station_users su 
   JOIN stations s ON su.station_id = s.id 
   WHERE su.user_id = ?;
   ```

2. **Verify token content**:
   ```python
   import jwt
   payload = jwt.decode(token, options={"verify_signature": False})
   print(payload.get("station_context"))
   ```

3. **Check audit logs**:
   ```sql
   SELECT * FROM station_audit_logs 
   WHERE user_id = ? AND action LIKE '%denied%' 
   ORDER BY timestamp DESC LIMIT 10;
   ```

## Future Enhancements

### Planned Features

1. **Dynamic Permissions**: Runtime permission modification without system restart
2. **Permission Templates**: Pre-defined permission sets for common roles
3. **Cross-Station Reporting**: Controlled cross-station data access for reporting
4. **API Rate Limiting**: Station-scoped rate limiting for fair resource usage
5. **Advanced Audit**: Real-time audit event streaming and alerting

### Scalability Considerations

1. **Horizontal Scaling**: Station-aware load balancing and data partitioning
2. **Caching**: Permission and station context caching for performance
3. **Database Optimization**: Indexing strategies for multi-tenant queries
4. **Microservices**: Split station management into dedicated service

---

This documentation provides a comprehensive overview of the station-aware RBAC system. For specific implementation details, refer to the source code and inline documentation in the respective modules.