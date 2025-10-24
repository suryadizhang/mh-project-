# Timezone & Daylight Saving Time (DST) Guide

## ✅ How DST is Automatically Handled

Your timezone utilities already handle DST automatically! Here's how:

### **1. zoneinfo Module (Python 3.9+)**
```python
from zoneinfo import ZoneInfo

# This automatically handles DST transitions
tz = ZoneInfo("America/New_York")
current_time = datetime.now(tz)
```

**Benefits**:
- Uses IANA timezone database (tzdata)
- Automatically applies DST rules for each timezone
- Handles historical DST changes
- Updates when DST rules change

### **2. How It Works**

#### Standard Time (Winter)
```python
from datetime import datetime
from zoneinfo import ZoneInfo

# January 15, 2025 (Standard Time)
tz = ZoneInfo("America/New_York")
winter_time = datetime(2025, 1, 15, 14, 0, tzinfo=tz)
print(winter_time)  # 2025-01-15 14:00:00 EST
print(winter_time.tzname())  # "EST" (Eastern Standard Time)
print(winter_time.utcoffset())  # -5:00:00 (UTC-5)
```

#### Daylight Saving Time (Summer)
```python
# July 15, 2025 (Daylight Saving Time)
summer_time = datetime(2025, 7, 15, 14, 0, tzinfo=tz)
print(summer_time)  # 2025-07-15 14:00:00 EDT
print(summer_time.tzname())  # "EDT" (Eastern Daylight Time)
print(summer_time.utcoffset())  # -4:00:00 (UTC-4)
```

**Notice**: Same code, but automatically uses EDT in summer!

### **3. DST Transition Example**

```python
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

tz = ZoneInfo("America/New_York")

# March 9, 2025 - Day before DST starts
before_dst = datetime(2025, 3, 9, 14, 0, tzinfo=tz)
print(f"{before_dst} | {before_dst.tzname()}")  # EST

# March 10, 2025 - Day after DST starts (clocks spring forward)
after_dst = datetime(2025, 3, 10, 14, 0, tzinfo=tz)
print(f"{after_dst} | {after_dst.tzname()}")  # EDT

# Automatically adds 1 hour!
```

## 🎯 Best Practices for Your Application

### **1. Store Everything in UTC**
```python
from api.app.utils.timezone_utils import utc_now

# For database timestamps
created_at = utc_now()  # Always UTC
```

### **2. Convert to Local for Display**
```python
from api.app.utils.timezone_utils import to_station_timezone, format_for_display

# Get booking from database (stored in UTC)
booking_time_utc = booking.created_at  # UTC timestamp

# Convert to station's local time for display
station_tz = "America/Chicago"
local_time = to_station_timezone(booking_time_utc, station_tz)

# Format for user
display_string = format_for_display(booking_time_utc, station_tz)
# "Oct 23, 2025 2:30 PM CDT" (automatically shows CDT in summer)
```

### **3. Handle Station-Specific Times**
```python
from api.app.utils.timezone_utils import now_in_timezone

# Get current time in station's timezone
station_tz = station.timezone  # "America/Los_Angeles"
current_local_time = now_in_timezone(station_tz)

# This automatically uses PST in winter, PDT in summer
```

## 📊 Common US Timezones & DST Rules

| Timezone | Standard | DST | UTC Offset (Standard) | UTC Offset (DST) |
|----------|----------|-----|----------------------|------------------|
| America/New_York | EST | EDT | UTC-5 | UTC-4 |
| America/Chicago | CST | CDT | UTC-6 | UTC-5 |
| America/Denver | MST | MDT | UTC-7 | UTC-6 |
| America/Los_Angeles | PST | PDT | UTC-8 | UTC-7 |
| America/Anchorage | AKST | AKDT | UTC-9 | UTC-8 |
| Pacific/Honolulu | HST | - | UTC-10 | No DST |

**Note**: Hawaii (HST) does NOT observe daylight saving time!

## 🔧 How to Test DST Transitions

```python
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from api.app.utils.timezone_utils import to_station_timezone, utc_now

def test_dst_transition():
    """Test that DST transitions are handled correctly."""
    tz = ZoneInfo("America/New_York")
    
    # Create UTC time
    utc_time = datetime(2025, 3, 10, 12, 0, tzinfo=ZoneInfo("UTC"))
    
    # Convert to Eastern time (during DST)
    eastern_time = to_station_timezone(utc_time, "America/New_York")
    
    # Should be EDT (UTC-4) not EST (UTC-5)
    assert eastern_time.tzname() == "EDT"
    assert eastern_time.hour == 8  # 12:00 UTC - 4 hours = 8:00 AM EDT
    
def test_winter_time():
    """Test standard time (winter)."""
    utc_time = datetime(2025, 1, 15, 12, 0, tzinfo=ZoneInfo("UTC"))
    eastern_time = to_station_timezone(utc_time, "America/New_York")
    
    # Should be EST (UTC-5)
    assert eastern_time.tzname() == "EST"
    assert eastern_time.hour == 7  # 12:00 UTC - 5 hours = 7:00 AM EST
```

## ⚠️ Common Pitfalls to Avoid

### **DON'T: Use naive datetimes**
```python
# ❌ BAD - No timezone info, ambiguous
now = datetime.now()  # Is this UTC? Local? Unknown!
```

### **DO: Always use timezone-aware datetimes**
```python
# ✅ GOOD - Clear timezone
from api.app.utils.timezone_utils import utc_now, now_in_timezone

utc_time = utc_now()  # Clear: This is UTC
local_time = now_in_timezone("America/Chicago")  # Clear: This is Chicago time
```

### **DON'T: Use utcnow() (deprecated)**
```python
# ❌ BAD - Deprecated in Python 3.12+
now = datetime.utcnow()  # Returns naive datetime
```

### **DO: Use timezone.utc**
```python
# ✅ GOOD - Returns timezone-aware datetime
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

## 🚀 Real-World Usage Examples

### Example 1: Booking Creation
```python
from api.app.utils.timezone_utils import utc_now, to_station_timezone

# User books for "7:00 PM" in their local timezone
booking_time_local = datetime(2025, 10, 25, 19, 0, tzinfo=ZoneInfo(station.timezone))

# Store in database as UTC
booking.scheduled_time = to_utc(booking_time_local)
booking.created_at = utc_now()

# When displaying to user, convert back
display_time = to_station_timezone(booking.scheduled_time, station.timezone)
```

### Example 2: Analytics Date Ranges
```python
from api.app.utils.timezone_utils import get_date_range_for_station

# Get last 30 days in station's timezone
# Automatically handles DST - if DST changed during this period, it's handled!
start_utc, end_utc = get_date_range_for_station(
    days=30,
    station_timezone="America/Los_Angeles"
)

# Query database with UTC times
results = await db.execute(
    select(Payment)
    .where(Payment.created_at >= start_utc)
    .where(Payment.created_at <= end_utc)
)
```

### Example 3: Multi-Timezone Display
```python
from api.app.utils.timezone_utils import format_for_display

# Same UTC timestamp shown in different timezones
utc_time = utc_now()

east_coast = format_for_display(utc_time, "America/New_York")
# "Oct 23, 2025 3:30 PM EDT"

west_coast = format_for_display(utc_time, "America/Los_Angeles")
# "Oct 23, 2025 12:30 PM PDT"

chicago = format_for_display(utc_time, "America/Chicago")
# "Oct 23, 2025 2:30 PM CDT"
```

## 📅 DST Transition Dates (US)

### 2025
- **Spring Forward**: March 9, 2025 at 2:00 AM → 3:00 AM
- **Fall Back**: November 2, 2025 at 2:00 AM → 1:00 AM

### 2026
- **Spring Forward**: March 8, 2026 at 2:00 AM → 3:00 AM
- **Fall Back**: November 1, 2026 at 2:00 AM → 1:00 AM

**Your code handles these automatically!** No manual updates needed.

## ✅ Verification Checklist

- [x] Using `zoneinfo.ZoneInfo` for timezone objects
- [x] Storing all database timestamps in UTC
- [x] Converting to local timezone for display only
- [x] Using timezone-aware datetime objects
- [x] Avoiding deprecated `datetime.utcnow()`
- [x] Testing DST transitions
- [x] Handling stations in different timezones

## 🎉 Summary

**Your timezone utilities already handle DST automatically!**

The `zoneinfo` module:
1. ✅ Automatically applies DST rules for each timezone
2. ✅ Handles transitions between standard and daylight time
3. ✅ Updates when government changes DST rules
4. ✅ Works for all IANA timezones worldwide
5. ✅ No manual intervention needed

**Just use the utility functions and DST is handled transparently!**
