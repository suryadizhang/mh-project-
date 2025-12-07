# My Hibachi RBAC Permission Matrix

> **Last Updated:** November 30, 2025 **Status:** Production Ready
> (CORRECTED)

## Role Hierarchy

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ SUPER_ADMIN (Platform Owner)                                                  │
│ • Full system access across ALL stations                                      │
│ • Manage all admin accounts and their station assignments                     │
│ • Create/delete stations and system settings                                  │
│ • Can create: ALL account types (ADMIN, CUSTOMER_SUPPORT, etc.)              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────────┐
│ ADMIN (Station Admin - Multi-Station via Assignment)                          │
│ • Access ASSIGNED stations (can be multiple or ALL, assigned by SUPER_ADMIN)  │
│ • Full CRUD for bookings, customers, chefs in assigned stations              │
│ • Can create/delete: STATION_MANAGER and CHEF accounts for assigned stations │
│ • CANNOT manage other ADMIN or SUPER_ADMIN accounts                          │
│ • CANNOT create/delete stations (only SUPER_ADMIN)                           │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────────┐
│ CUSTOMER_SUPPORT                                                              │
│ • ALL customer-related operations (bookings, reviews, complaints, inquiries)  │
│ • Can VIEW and EDIT bookings directly (no approval needed for edits)         │
│ • DELETE bookings requires approval from ADMIN or SUPER_ADMIN                │
│ • Full access to customer, lead, review, complaint features                  │
│ • No access to financial, system settings, or user account management        │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────────┐
│ STATION_MANAGER                                                               │
│ • View-only access to their assigned station                                 │
│ • Schedule internal chefs for their station                                  │
│ • Can create/delete: CHEF accounts for their station ONLY                    │
│ • NO booking adjustments (handled by customer support + admin)               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────────────┐
│ CHEF (Future - Backend ready, UI pending)                                     │
│ • View their own schedule                                                     │
│ • Update their availability                                                   │
│ • Dedicated chef portal page (future admin panel improvement)                │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Permission Matrix

### Legend

- ✅ = Full access (direct, no approval needed)
- 🔐 = Requires approval from ADMIN or SUPER_ADMIN
- 📍 = Station-scoped (only assigned station(s))
- ❌ = No access

---

### Booking Permissions

| Permission            | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| --------------------- | :---------: | :---: | :--------------: | :-------------: |
| View All Bookings     |     ✅      |  ❌   |        ✅        |       ❌        |
| View Station Bookings |     ✅      |  📍   |        ✅        |       📍        |
| Create Booking        |     ✅      |  ✅   |        ✅        |       ❌        |
| Update/Edit Booking   |     ✅      |  📍   |        ✅        |       ❌        |
| Delete/Cancel Booking |     ✅      |  📍   |        🔐        |       ❌        |

**Note:** CUSTOMER_SUPPORT can VIEW and EDIT bookings directly. Only
DELETE/CANCEL requires approval from ADMIN or SUPER_ADMIN.

---

### Customer Permissions

| Permission      | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| --------------- | :---------: | :---: | :--------------: | :-------------: |
| View Customers  |     ✅      |  ✅   |        ✅        |       ❌        |
| Create Customer |     ✅      |  ✅   |        ✅        |       ❌        |
| Update Customer |     ✅      |  ✅   |        ✅        |       ❌        |
| Delete Customer |     ✅      |  ✅   |        ❌        |       ❌        |

---

### Lead Permissions

| Permission   | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| ------------ | :---------: | :---: | :--------------: | :-------------: |
| View Leads   |     ✅      |  ✅   |        ✅        |       ❌        |
| Manage Leads |     ✅      |  ✅   |        ✅        |       ❌        |
| Delete Lead  |     ✅      |  ✅   |        ❌        |       ❌        |

---

### Review Permissions

| Permission       | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| ---------------- | :---------: | :---: | :--------------: | :-------------: |
| View Reviews     |     ✅      |  ✅   |        ✅        |       ❌        |
| Moderate Reviews |     ✅      |  ✅   |        ❌        |       ❌        |
| Delete Review    |     ✅      |  ✅   |        ❌        |       ❌        |

---

### Chef Permissions

| Permission             | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| ---------------------- | :---------: | :---: | :--------------: | :-------------: |
| View All Chefs         |     ✅      |  ❌   |        ❌        |       ❌        |
| View Station Chefs     |     ✅      |  📍   |        ❌        |       📍        |
| Create Chef Account    |     ✅      |  📍   |        ❌        |       📍        |
| Delete Chef Account    |     ✅      |  📍   |        ❌        |       📍        |
| Assign Chef to Booking |     ✅      |  📍   |        ❌        |       ❌        |
| Schedule Chefs         |     ✅      |  📍   |        ❌        |       📍        |

**Note:** Both ADMIN and STATION_MANAGER can create/delete CHEF
accounts for their assigned stations. STATION_MANAGER can only manage
chefs for their specific station.

---

### Staff Permissions

| Permission          | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| ------------------- | :---------: | :---: | :--------------: | :-------------: |
| View All Staff      |     ✅      |  ❌   |        ❌        |       ❌        |
| View Station Staff  |     ✅      |  📍   |        ❌        |       ❌        |
| Manage Staff (CRUD) |     ✅      |  📍   |        ❌        |       ❌        |

---

### Station Permissions

| Permission         | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| ------------------ | :---------: | :---: | :--------------: | :-------------: |
| View All Stations  |     ✅      |  ❌   |        ❌        |       ❌        |
| View Own Station   |     ✅      |  📍   |        ❌        |       📍        |
| Create Station     |     ✅      |  ❌   |        ❌        |       ❌        |
| Manage Own Station |     ✅      |  📍   |        ❌        |       ❌        |
| Delete Station     |     ✅      |  ❌   |        ❌        |       ❌        |

---

### Admin User Permissions

| Permission              | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| ----------------------- | :---------: | :---: | :--------------: | :-------------: |
| View All Admins         |     ✅      |  ❌   |        ❌        |       ❌        |
| Create ADMIN Account    |     ✅      |  ❌   |        ❌        |       ❌        |
| Create CUSTOMER_SUPPORT |     ✅      |  ❌   |        ❌        |       ❌        |
| Create STATION_MANAGER  |     ✅      |  📍   |        ❌        |       ❌        |
| Delete STATION_MANAGER  |     ✅      |  📍   |        ❌        |       ❌        |
| Assign Roles            |     ✅      |  ❌   |        ❌        |       ❌        |

**Note:** ADMIN can create/delete STATION_MANAGER accounts only for
their assigned stations. Only SUPER_ADMIN can create ADMIN or
CUSTOMER_SUPPORT accounts.

---

### Financial Permissions

| Permission              | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| ----------------------- | :---------: | :---: | :--------------: | :-------------: |
| View All Financials     |     ✅      |  ❌   |        ❌        |       ❌        |
| View Station Financials |     ✅      |  📍   |        ❌        |       ❌        |
| Process Refund          |     ✅      |  📍   |        ❌        |       ❌        |
| Financial Reports       |     ✅      |  📍   |        ❌        |       ❌        |

---

### Audit & System Permissions

| Permission              | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| ----------------------- | :---------: | :---: | :--------------: | :-------------: |
| View All Audit Logs     |     ✅      |  ❌   |        ❌        |       ❌        |
| View Station Audit Logs |     ✅      |  📍   |        ❌        |       ❌        |
| View Own Audit Logs     |     ✅      |  ✅   |        ✅        |       ✅        |
| Export Audit Logs       |     ✅      |  📍   |        ❌        |       ❌        |
| System Settings         |     ✅      |  ❌   |        ❌        |       ❌        |
| All Analytics           |     ✅      |  ❌   |        ❌        |       ❌        |
| Station Analytics       |     ✅      |  📍   |        ❌        |       📍        |

---

### Approval Workflow Permissions

| Permission       | SUPER_ADMIN | ADMIN | CUSTOMER_SUPPORT | STATION_MANAGER |
| ---------------- | :---------: | :---: | :--------------: | :-------------: |
| Grant Approval   |     ✅      |  📍   |        ❌        |       ❌        |
| Request Approval |     ❌      |  ❌   |        ✅        |       ❌        |

---

## Approval Workflow for Customer Support

CUSTOMER_SUPPORT has **DIRECT access** to edit bookings. Only
**DELETE/CANCEL** requires approval.

### When Approval is Required:

| Action                    | Direct Access | Requires Approval |
| ------------------------- | :-----------: | :---------------: |
| View Bookings             |      ✅       |         -         |
| Edit/Update Booking       |      ✅       |         -         |
| Create Booking            |      ✅       |         -         |
| **Delete/Cancel Booking** |       -       |        🔐         |

### Approval Flow for Delete/Cancel:

1. **CS initiates delete/cancel** → System marks action as "pending
   approval"
2. **Approval request sent** to ADMIN (for that station) or
   SUPER_ADMIN
3. **ADMIN/SUPER_ADMIN reviews** → Approve with passcode or reject
4. **If approved** → Booking deleted/cancelled with audit log
5. **If rejected** → CS notified, booking unchanged

### Passcode Flow (Alternative)

- ADMIN/SUPER_ADMIN provides one-time passcode to CS
- CS enters passcode to authorize the delete
- Passcode expires after single use or 15 minutes

---

## Roles NOT in Active Use (Admin Panel)

| Role  | Status      | Notes                                                                           |
| ----- | ----------- | ------------------------------------------------------------------------------- |
| STAFF | ❌ Not Used | Deprecated - use CUSTOMER_SUPPORT or STATION_MANAGER                            |
| CHEF  | 🔮 Future   | Backend ready. Will have dedicated page for: view schedule, update availability |

**Note:** CHEF role exists in the system. ADMIN and STATION_MANAGER
can create chef accounts. The CHEF-facing UI (for chefs to view their
schedule and update availability) is planned for future development.

---

## Implementation Files

| Component            | File Location                                                  |
| -------------------- | -------------------------------------------------------------- |
| Backend Roles        | `apps/backend/src/core/config.py` (UserRole enum)              |
| Backend Permissions  | `apps/backend/src/utils/auth.py` (Permission class)            |
| Frontend Permissions | `apps/admin/src/hooks/usePermissions.ts`                       |
| Database Roles       | `apps/backend/src/db/models/identity/roles.py` (RoleType enum) |

---

## Quick Code Reference

### Backend - Check Permission

```python
from utils.auth import Permission, has_permission, can_access_station, can_modify_booking

# Check if user can delete booking
if has_permission(current_user, Permission.BOOKING_DELETE):
    # Direct delete allowed
    pass

# Check station access (supports multi-station ADMIN)
if can_access_station(current_user, station_id):
    # User can access this station
    pass

# Check if user needs approval for booking deletion
can_modify, needs_approval = can_modify_booking(current_user)
if needs_approval:
    # CUSTOMER_SUPPORT deleting - trigger approval workflow
    pass
else:
    # ADMIN/SUPER_ADMIN - direct delete
    pass

# Check account creation permissions
if has_permission(current_user, Permission.ACCOUNT_CREATE_STATION_MANAGER):
    # ADMIN creating STATION_MANAGER for their assigned station
    pass

if has_permission(current_user, Permission.ACCOUNT_CREATE_CHEF):
    # ADMIN or STATION_MANAGER creating CHEF account
    pass
```

### Frontend - Check Permission

```tsx
import { usePermissions } from '@/hooks/usePermissions';

function BookingActions() {
  const {
    canUpdateBooking, // Direct edit access
    canDeleteBooking, // Direct delete (ADMIN, SUPER_ADMIN)
    needsApprovalForBookingDelete, // CS needs approval for delete only
    canCreateChefAccount, // ADMIN and STATION_MANAGER
    canCreateStationManagerAccount, // ADMIN only
    isAssignmentScoped, // ADMIN/SM limited to assigned stations
  } = usePermissions();

  const handleDelete = () => {
    if (canDeleteBooking) {
      // Direct delete allowed
    } else if (needsApprovalForBookingDelete) {
      // Show approval request modal (CS deleting)
    }
  };

  return (
    <>
      <Button onClick={handleEdit} disabled={!canUpdateBooking}>
        Edit Booking
      </Button>
      <Button
        onClick={handleDelete}
        disabled={!canDeleteBooking && !needsApprovalForBookingDelete}
        variant="destructive"
      >
        Delete Booking
      </Button>
    </>
  );
}
```
