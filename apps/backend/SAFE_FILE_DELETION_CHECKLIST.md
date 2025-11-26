# Safe File Deletion Checklist

**Purpose**: Identify legacy/duplicate models safe for deletion
**Approach**: Conservative - only delete files with clear duplicates
or deprecation warnings

---

## ✅ SAFE TO DELETE (Confirmed Duplicates)

### 1. `models/customer.py` ✅ DELETE

**Reason**:

- Has `⚠️ DEPRECATED` warning in docstring
- Maps to `public.customers` (table doesn't exist)
- Duplicate of `db/models/core.py::Customer`
- Wrong schema (no schema = public, should be core)
- Wrong field names (email vs email_encrypted)

**Before deletion**: Run this check

```bash
grep -r "from models.customer import" src/ --exclude-dir=models
# If any results: Update those imports first
```

---

### 2. `models/events.py` ⚠️ CHECK FIRST, THEN DELETE

**Reason**:

- Duplicate exists: `db/models/events.py`
- Need to verify both have same content

**Before deletion**: Compare files

```bash
# Check if files are identical or if models/ has unique business logic
diff src/models/events.py src/db/models/events.py
```

**If different**: Merge unique logic into `db/models/events.py` before
deleting

---

### 3. `models/lead.py` ⚠️ CHECK FIRST, THEN DELETE

**Reason**:

- Duplicate exists: `db/models/lead.py`

**Before deletion**: Compare files

```bash
diff src/models/lead.py src/db/models/lead.py
```

---

### 4. `models/newsletter.py` ⚠️ CHECK FIRST, THEN DELETE

**Reason**:

- Duplicate exists: `db/models/newsletter.py`

**Before deletion**: Compare files

```bash
diff src/models/newsletter.py src/db/models/newsletter.py
```

---

## ⏸️ MAYBE DELETE (Need Verification)

### 5. `models/booking.py` ⚠️ VERIFY FIRST

**Reason**:

- Partial duplicate of `db/models/core.py::Booking`
- May have business logic (validation methods, properties)
- Recently fixed BookingStatus enum in `db/models/core.py`

**Before deletion**: Check for business logic

```bash
# Look for methods beyond __init__
grep -A 5 "def " src/models/booking.py | grep -v "__init__"
```

**If has unique methods**:

- Copy methods to `db/models/core.py::Booking`
- Add tests for those methods
- Then delete

**If no unique methods**:

- ✅ Safe to delete

---

## 🔒 KEEP (No Duplicates or Shared Code)

### Files to KEEP in `models/`:

1. **`models/base.py`** ✅ KEEP
   - Base model class
   - May be used by other legacy models
   - Delete only after all legacy models deleted

2. **`models/mixins.py`** ✅ KEEP
   - Shared mixins (TimestampMixin, etc.)
   - May be used across multiple models
   - Can be merged into `db/models/` later if needed

3. **`models/email.py`** ✅ KEEP
   - No duplicate in `db/models/`
   - Likely still in use

4. **`models/email_label.py`** ✅ KEEP
   - No duplicate in `db/models/`

5. **`models/escalation.py`** ✅ KEEP
   - No duplicate in `db/models/`

6. **`models/knowledge_base.py`** ✅ KEEP
   - No duplicate in `db/models/`

7. **`models/notification.py`** ✅ KEEP
   - No duplicate in `db/models/`

8. **`models/payment_notification.py`** ✅ KEEP
   - No duplicate in `db/models/`

9. **`models/review.py`** ✅ KEEP
   - No duplicate in `db/models/`

10. **`models/role.py`** ✅ KEEP
    - No duplicate in `db/models/` (identity.py has User roles, but
      this may be different)

11. **`models/social.py`** ✅ KEEP
    - No duplicate in `db/models/`

12. **`models/system_event.py`** ✅ KEEP
    - No duplicate in `db/models/`

13. **`models/terms_acknowledgment.py`** ✅ KEEP
    - No duplicate in `db/models/`

14. **`models/booking_reminder.py`** ✅ KEEP
    - No duplicate in `db/models/`
    - Maps to `public.booking_reminders` table (exists)

15. **`models/business.py`** ✅ KEEP
    - No duplicate in `db/models/`

16. **`models/call_recording.py`** ✅ KEEP
    - No duplicate in `db/models/`

17. **`models/contact.py`** ✅ KEEP
    - No duplicate in `db/models/`

---

## Deletion Procedure

### Step 1: Backup Everything

```bash
cd "c:\Users\surya\projects\MH webapps\apps\backend"

# Create timestamped backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item -Path "src\models" -Destination "src\models_BACKUP_$timestamp" -Recurse

Write-Host "✅ Backup created: src\models_BACKUP_$timestamp"
```

### Step 2: Verify No Active Imports

```bash
# For each file to delete, check for active imports
$filesToCheck = @(
    "models/customer.py",
    "models/events.py",
    "models/lead.py",
    "models/newsletter.py"
)

foreach ($file in $filesToCheck) {
    $modulePath = $file -replace '\.py$', '' -replace '/', '.'
    Write-Host "`n Checking imports for $modulePath..."

    # Search all Python files except the model file itself
    Get-ChildItem -Path "src" -Recurse -Filter "*.py" | Where-Object {
        $_.FullName -notlike "*\models\*"
    } | Select-String -Pattern "from $modulePath import" -CaseSensitive
}
```

### Step 3: Update Imports (if needed)

```bash
# If imports found, create migration script
# Example: Replace customer imports
(Get-ChildItem -Path "src" -Recurse -Filter "*.py") | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $content = $content -replace 'from models\.customer import Customer', 'from db.models.core import Customer'
    Set-Content -Path $_.FullName -Value $content
}
```

### Step 4: Delete Files (One at a Time)

```bash
# Delete customer.py (confirmed safe)
Remove-Item "src\models\customer.py" -Force
Write-Host "✅ Deleted models/customer.py"

# Run tests to verify nothing broke
pytest tests/ -x  # -x stops on first failure

# If tests pass, continue with next file
# If tests fail, restore from backup and investigate
```

### Step 5: Validate After Each Deletion

```bash
# After deleting each file:
# 1. Run backend startup test
cd "src"
python -c "from main import app; print('✅ Backend imports successfully')"

# 2. Run specific tests related to deleted model
pytest tests/test_<related_tests>.py -v

# 3. If all pass, commit the deletion
git add .
git commit -m "chore: Delete legacy models/<filename> (duplicate of db/models/...)"

# 4. If anything fails, restore from backup
```

---

## Import Migration Map

After deletion, update all imports:

```python
# OLD → NEW
"from models.customer import Customer"          → "from db.models.core import Customer"
"from models.booking import Booking"            → "from db.models.core import Booking"
"from models.events import Event"               → "from db.models.events import Event"
"from models.lead import Lead"                  → "from db.models.lead import Lead"
"from models.newsletter import NewsletterSubscriber" → "from db.models.newsletter import NewsletterSubscriber"
```

---

## Rollback Plan

If anything breaks:

```bash
# Restore entire models/ directory
Remove-Item "src\models" -Recurse -Force
Copy-Item -Path "src\models_BACKUP_$timestamp" -Destination "src\models" -Recurse

Write-Host "✅ Rolled back to backup"
```

---

## Final Cleanup (After All Deletions)

Once all legacy models deleted and imports updated:

```bash
# If models/ directory only has __init__.py and base.py left
# Consider moving base.py and mixins.py to db/models/
mv src/models/base.py src/db/models/base.py
mv src/models/mixins.py src/db/models/mixins.py

# Update imports
# ... (similar to above)

# Delete empty models/ directory
Remove-Item "src\models" -Recurse -Force

Write-Host "✅ Legacy models/ directory removed"
```

---

## Summary

**Immediate Deletions** (after verification):

1. ✅ `models/customer.py` - Deprecated, wrong schema
2. ⚠️ `models/events.py` - Check diff first
3. ⚠️ `models/lead.py` - Check diff first
4. ⚠️ `models/newsletter.py` - Check diff first
5. ⚠️ `models/booking.py` - Check for business logic first

**Keep for Now**:

- All other files in `models/` (no duplicates)
- `models/base.py` and `models/mixins.py` (shared code)

**Total Files to Delete**: 4-5 files (out of 23)

**Estimated Time**: 1-2 hours (including verification and testing)
