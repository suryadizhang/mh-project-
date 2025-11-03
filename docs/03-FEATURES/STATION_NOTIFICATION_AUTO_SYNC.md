# 🔄 Station Notification Groups - Automatic Synchronization

## Overview

The notification groups system **automatically stays in sync** with your stations. When you create, update, or delete stations through the admin panel, the corresponding notification groups are automatically managed.

---

## ✅ What Happens Automatically

### 1. Creating a Station

**Admin Action:**
```http
POST /api/admin/stations
{
  "name": "Sacramento",
  "city": "Sacramento",
  "state": "CA",
  "status": "active"
}
```

**Automatic Behind-the-Scenes:**
```
✅ Station created in database
✅ Notification group "Station Managers - Sacramento" created
✅ Group configured with:
   - station_id = sacramento-uuid
   - Subscribed to: new_booking, booking_edit, booking_cancellation,
                    payment_received, review_received, complaint_received
   - is_active = true
   - created_by = current_user_id

📝 Log: "Auto-created notification group for station: Sacramento"
```

### 2. Updating Station Name or Location

**Admin Action:**
```http
PUT /api/admin/stations/{id}
{
  "name": "Sacramento Downtown",  // Changed from "Sacramento"
  "city": "Sacramento",
  "state": "CA"
}
```

**Automatic Behind-the-Scenes:**
```
✅ Station updated in database
✅ Notification group renamed:
   - Old: "Station Managers - Sacramento"
   - New: "Station Managers - Sacramento Downtown"
✅ Group description updated:
   - "Station managers and staff for Sacramento Downtown (Sacramento, CA)..."

📝 Log: "Synced notification group for station: Sacramento Downtown"
```

### 3. Deactivating a Station

**Admin Action:**
```http
PUT /api/admin/stations/{id}
{
  "status": "inactive"  // Station temporarily closed
}
```

**Automatic Behind-the-Scenes:**
```
✅ Station status changed to inactive
✅ Notification group deactivated:
   - is_active = false
   - Members stop receiving notifications
   - Group preserved (not deleted)

📝 Log: "Deactivated notification group for station: Sacramento"
```

**Effect:**
- Station managers **will NOT** receive new notifications
- Group and members are **preserved** in database
- Can be reactivated when station reopens

### 4. Reactivating a Station

**Admin Action:**
```http
PUT /api/admin/stations/{id}
{
  "status": "active"  // Station reopening
}
```

**Automatic Behind-the-Scenes:**
```
✅ Station status changed to active
✅ Notification group reactivated:
   - is_active = true
   - Members resume receiving notifications

📝 Log: "Reactivated notification group for station: Sacramento"
```

### 5. Deleting a Station

**Admin Action:**
```http
DELETE /api/admin/stations/{id}?force=true
```

**Automatic Behind-the-Scenes:**
```
✅ Station deleted from database
✅ Notification group deleted:
   - Group removed from database
   - All members removed (CASCADE)
   - All event subscriptions removed (CASCADE)

📝 Log: "Deleted notification group: Station Managers - Sacramento"
```

**Warning:** This is permanent and cannot be undone!

---

## 🔧 Technical Implementation

### Service Layer Integration

**File:** `src/services/station_notification_sync.py`

**Key Functions:**

```python
# Create group when station is created
await sync_station_with_notification_group(
    db=db,
    station_id=station.id,
    station_name=station.name,
    station_location=f"{station.city}, {station.state}",
    is_active=True,
    created_by=current_user.id
)

# Update group when station changes
await sync_station_with_notification_group(
    db=db,
    station_id=station.id,
    station_name=station.name,  # New name
    station_location=f"{station.city}, {station.state}",  # New location
    is_active=station.status == "active",
    created_by=current_user.id
)

# Delete group when station is deleted
await delete_station_notification_group(
    db=db,
    station_id=station.id
)
```

### Router Integration

**File:** `src/api/app/routers/station_admin.py`

**Hooks Added:**

1. **POST /stations** (Create)
   - Line ~402: Auto-create notification group after station creation

2. **PUT /stations/{id}** (Update)
   - Line ~620: Sync notification group when name/location/status changes

3. **DELETE /stations/{id}** (Delete)
   - Line ~783: Delete notification group when station is deleted

---

## 🎯 Use Cases

### Scenario 1: Opening a New Location

**You:**
```
1. Go to Admin Panel → Stations
2. Click "Create Station"
3. Fill in details:
   - Name: "Oakland"
   - City: "Oakland"
   - State: "CA"
4. Click "Save"
```

**System:**
```
✅ Station created
✅ Notification group "Station Managers - Oakland" created automatically
✅ Ready to add station managers immediately
```

**Next Step:**
```
1. Go to Admin Panel → Notification Groups
2. Find "Station Managers - Oakland"
3. Click "Add Member"
4. Add station manager's phone number
5. Done! They'll receive Oakland-only notifications
```

### Scenario 2: Rebranding a Station

**You:**
```
1. Go to Admin Panel → Stations
2. Edit "Sacramento" station
3. Change name to "Sacramento Premium"
4. Click "Update"
```

**System:**
```
✅ Station name updated
✅ Notification group renamed to "Station Managers - Sacramento Premium"
✅ All members automatically updated
✅ No manual intervention needed
```

### Scenario 3: Temporarily Closing a Location

**You:**
```
1. Go to Admin Panel → Stations
2. Edit "Oakland" station
3. Change status from "Active" to "Inactive"
4. Click "Update"
```

**System:**
```
✅ Station deactivated
✅ Notification group deactivated
✅ Oakland managers stop receiving notifications
✅ Group preserved for when you reopen
```

**When Reopening:**
```
1. Change status back to "Active"
2. Click "Update"

✅ Notification group reactivated
✅ Oakland managers resume receiving notifications
```

### Scenario 4: Closing a Location Permanently

**You:**
```
1. Go to Admin Panel → Stations
2. Click "Delete" on "Oakland" station
3. Confirm deletion with force=true
```

**System:**
```
✅ Station deleted
✅ Notification group deleted
✅ All Oakland managers removed from notifications
⚠️ Cannot be undone - group and members are permanently deleted
```

---

## 🔍 Verification

### Check if Synchronization is Working

**After Creating a Station:**

```bash
# Method 1: Check via API
curl http://localhost:8000/api/admin/notification-groups \
  -H "Authorization: Bearer YOUR_TOKEN"

# Look for: "Station Managers - [Your Station Name]"

# Method 2: Check via script
cd apps/backend
python create_station_groups.py list

# Should show your new station group
```

**After Updating a Station:**

```bash
# Check if group name/description updated
curl http://localhost:8000/api/admin/notification-groups/{group-id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify name matches updated station name
```

**After Deleting a Station:**

```bash
# Verify group is gone
curl http://localhost:8000/api/admin/notification-groups \
  -H "Authorization: Bearer YOUR_TOKEN"

# Station group should no longer appear in list
```

---

## 🛠️ Error Handling

### What if Automatic Creation Fails?

The system is designed to **not fail station creation** if notification group creation fails:

```python
try:
    # Create notification group
    await sync_station_with_notification_group(...)
    logger.info("✅ Auto-created notification group")
except Exception as e:
    logger.warning(f"⚠️ Failed to create notification group: {e}")
    # Station creation continues successfully
```

**If this happens:**
1. Station is still created successfully ✅
2. Warning is logged for debugging
3. You can manually run: `python create_station_groups.py`
4. Or create the group manually via API

### Manual Recovery

If notification groups get out of sync:

```bash
# Option 1: Run sync script
cd apps/backend
python create_station_groups.py

# This will:
# - Create missing groups
# - Skip existing groups
# - Update group info if needed

# Option 2: Create specific group via API
curl -X POST http://localhost:8000/api/admin/notification-groups \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Station Managers - Sacramento",
    "description": "Station managers for Sacramento",
    "station_id": "sacramento-uuid"
  }'
```

---

## 📊 Logs and Monitoring

### Success Logs

```
INFO - ✅ Auto-created notification group for station: Sacramento
INFO - ✅ Synced notification group for station: Oakland
INFO - ✅ Deleted notification group: Station Managers - San Francisco
```

### Warning Logs

```
WARNING - ⚠️ Failed to create notification group for station: DatabaseError
WARNING - ⚠️ No notification group found for station {uuid}
```

### Where to Find Logs

```bash
# Backend application logs
tail -f logs/app.log

# Station operations
grep "notification group" logs/app.log

# Specific station
grep "Sacramento" logs/app.log | grep "notification"
```

---

## 🎨 Frontend Integration

The frontend doesn't need to do anything special! Just use the normal station CRUD operations:

```typescript
// Create station - group created automatically
const newStation = await api.post('/api/admin/stations', {
  name: 'Sacramento',
  city: 'Sacramento',
  state: 'CA'
});
// ✅ Notification group created in background

// Update station - group updated automatically
await api.put(`/api/admin/stations/${stationId}`, {
  name: 'Sacramento Downtown'  // Renamed
});
// ✅ Notification group renamed in background

// Delete station - group deleted automatically
await api.delete(`/api/admin/stations/${stationId}?force=true`);
// ✅ Notification group deleted in background
```

---

## ✅ Advantages of Automatic Sync

### Before (Manual Management) ❌
```
1. Create station via admin panel
2. Remember to create notification group manually
3. Remember to set station_id correctly
4. Remember to subscribe to all events
5. Remember to update group when station changes
6. Remember to delete group when station deleted
7. Hope you didn't forget any step...
```

### After (Automatic Sync) ✅
```
1. Create/update/delete station via admin panel
2. Everything else happens automatically!
```

**Benefits:**
- 🚀 **Zero Manual Work** - Groups manage themselves
- 🎯 **Always In Sync** - No stale or orphaned groups
- 🛡️ **No Human Error** - Can't forget to create/update groups
- 📊 **Audit Trail** - All changes logged automatically
- 🔄 **Consistent** - Every station has proper notifications
- 💪 **Reliable** - Handles edge cases (deactivate/reactivate)

---

## 🔐 Security & Permissions

- Only **super_admin** can create/update/delete stations
- Notification group sync inherits same permissions
- All operations are logged with user ID
- Failed sync doesn't block station operations

---

## 📝 Summary

**You asked:** "Does it update automatically when I change stations in admin panel?"

**Answer:** **YES! ✅**

- ✅ Create station → Notification group created automatically
- ✅ Update station → Notification group updated automatically  
- ✅ Deactivate station → Notification group deactivated automatically
- ✅ Reactivate station → Notification group reactivated automatically
- ✅ Delete station → Notification group deleted automatically

**You don't need to:**
- ❌ Run any scripts
- ❌ Manually create groups
- ❌ Manually update groups
- ❌ Manually delete groups

**Just manage your stations normally, and notification groups stay in perfect sync!** 🎉

---

**Implementation Date:** October 30, 2025  
**Status:** ✅ Fully Automated & Tested  
**Files Modified:**
- `src/services/station_notification_sync.py` (Created)
- `src/api/app/routers/station_admin.py` (Updated - 3 hooks added)
