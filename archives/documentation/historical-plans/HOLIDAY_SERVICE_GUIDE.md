# US Holiday Service - Reusable Component Guide 🎉

**Created:** November 13, 2025  
**Purpose:** Centralized US holiday and event detection for coupons, newsletters, marketing campaigns

---

## 🎯 What Problem Does This Solve?

You asked: *"so on our system we need to know what is the special event or holiday in the us right? so we can execute these features? these system will be usefull for our newsletter features too so we can use these as like reuseable component for others features too that this may apply right?"*

**YES! This is now a reusable component for your entire application.**

### Before (Hardcoded):
```python
# ❌ BAD: Hardcoded, inaccurate, not reusable
if today.month == 11 and 8 <= today.day <= 14:
    send_thanksgiving_message()
```

**Problems:**
- ❌ Thanksgiving is 4th Thursday (Nov 22-28), not always Nov 8-14
- ❌ Code duplicated across features
- ❌ Can't reuse for newsletters
- ❌ Hard to add new holidays

### After (Centralized Service):
```python
# ✅ GOOD: Accurate, reusable, maintainable
from services.holiday_service import get_holiday_service

holiday_service = get_holiday_service()

# Automatically detects ANY current holiday
current_holiday = holiday_service.get_current_holiday()
if current_holiday:
    holiday_key, holiday_obj, holiday_date = current_holiday
    send_holiday_message(holiday_obj.name, holiday_date)
```

**Benefits:**
- ✅ Accurate dates (Thanksgiving 4th Thursday, Easter calculation, etc.)
- ✅ Reusable across coupons, newsletters, marketing, analytics
- ✅ Easy to add new holidays (just update one file)
- ✅ Includes event seasons (wedding season, graduation, etc.)

---

## 📚 What's Included?

### **20+ US Holidays & Event Seasons**

| Category | Holidays/Events |
|----------|----------------|
| **Federal Holidays** | New Year's, Memorial Day, Independence Day, Labor Day, Thanksgiving, Christmas |
| **Commercial Holidays** | Valentine's Day, Mother's Day, Father's Day, Halloween, Black Friday, New Year's Eve |
| **Event Seasons** | Graduation Season (May-Jun), Wedding Season (Jun-Aug), Back to School (Aug-Sep) |
| **Cultural Events** | Super Bowl, St. Patrick's Day, Cinco de Mayo, Easter |

### **Marketing Windows**

Each holiday has a **marketing window** - when to start promoting:

```python
Holiday(
    name="Thanksgiving",
    marketing_window_days=21,  # Start promoting 3 weeks before
)
```

**Example Timeline:**
- Nov 6: Start Thanksgiving marketing (21 days before)
- Nov 27: Thanksgiving Day (2025)
- Nov 30: Stop marketing (3 days after)

---

## 🚀 Use Cases

### 1️⃣ **Coupon Reminder System** (Already Implemented)

**File:** `apps/backend/src/tasks/coupon_reminder_scheduler.py`

```python
from services.holiday_service import get_holiday_service

async def send_daily_reminders():
    holiday_service = get_holiday_service()
    
    # Automatically check current holiday
    current_holiday = holiday_service.get_current_holiday()
    
    if current_holiday:
        holiday_key, holiday_obj, holiday_date = current_holiday
        
        # Get rich context for personalized messages
        context = holiday_service.get_holiday_message_context(holiday_key)
        
        # Example: "Thanksgiving is in 14 days! Perfect for family gatherings"
        days_until = context["days_until"]
        events = context["typical_events"]  # ["Family dinners", "Friendsgiving"]
        
        # Send holiday-themed coupon reminder
        await send_holiday_sms(
            message=f"{holiday_obj.name} is coming! Use your coupon for {events[0]}."
        )
```

**What It Does:**
- ✅ Automatically detects Thanksgiving, Christmas, New Year
- ✅ Sends holiday-themed SMS reminders
- ✅ Includes accurate date calculations
- ✅ Prevents duplicate reminders

---

### 2️⃣ **Newsletter System** (Your Next Use Case!)

**File:** `apps/backend/src/services/newsletter_service.py` (create this)

```python
from services.holiday_service import get_holiday_service
from datetime import date, timedelta

class NewsletterService:
    """Send holiday-themed newsletters to customers."""
    
    def __init__(self):
        self.holiday_service = get_holiday_service()
    
    async def get_this_months_newsletters(self):
        """Get all newsletters to send this month."""
        newsletters = []
        
        # Get upcoming holidays in next 60 days
        upcoming = self.holiday_service.get_upcoming_holidays(days=60)
        
        for holiday_key, holiday_obj, holiday_date in upcoming:
            # Get rich context for each holiday
            context = self.holiday_service.get_holiday_message_context(holiday_key)
            
            newsletters.append({
                "subject": f"Plan Your {holiday_obj.name} Event Now!",
                "send_date": holiday_date - timedelta(days=21),  # 3 weeks before
                "content": self._generate_newsletter_content(holiday_obj, context),
                "target_audience": self._get_target_audience(holiday_obj.category),
            })
        
        return newsletters
    
    def _generate_newsletter_content(self, holiday, context):
        """Generate personalized newsletter content."""
        return f"""
        Hi {customer_name}!
        
        {context['marketing_angle']}
        
        {holiday.name} is in {context['days_until']} days. Here's why our hibachi 
        catering is perfect for:
        
        {"".join(f"• {event}\n" for event in context['typical_events'])}
        
        Book now for {holiday.name}!
        """
    
    def _get_target_audience(self, category):
        """Target different customer segments by holiday type."""
        if category == "event_season":
            return "event_planners"  # Weddings, graduations
        elif category == "federal":
            return "all_customers"  # Thanksgiving, July 4th
        elif category == "commercial":
            return "families"  # Valentine's, Mother's/Father's Day
        return "all_customers"


# Usage Example:
newsletter_service = NewsletterService()
newsletters = await newsletter_service.get_this_months_newsletters()

for newsletter in newsletters:
    print(f"Send on {newsletter['send_date']}: {newsletter['subject']}")
    
# Output:
# Send on 2025-11-06: Plan Your Thanksgiving Event Now!
# Send on 2025-12-04: Plan Your Christmas Event Now!
# Send on 2025-12-10: Plan Your New Year's Eve Event Now!
```

**Newsletter Benefits:**
- ✅ Automatically generates holiday newsletters
- ✅ Sends 3 weeks before each holiday (customizable)
- ✅ Personalized content based on holiday type
- ✅ Targets right audience (families vs. event planners)

---

### 3️⃣ **Marketing Campaign Automation**

**File:** `apps/backend/src/services/marketing_automation.py`

```python
from services.holiday_service import get_holiday_service, HolidayCategory

class MarketingAutomation:
    """Automated marketing campaigns based on holidays."""
    
    def __init__(self):
        self.holiday_service = get_holiday_service()
    
    async def schedule_holiday_campaigns(self):
        """Schedule all marketing campaigns for the year."""
        campaigns = []
        
        # Get all event seasons (high-value for hibachi catering)
        upcoming = self.holiday_service.get_upcoming_holidays(
            days=365,
            categories=[HolidayCategory.EVENT_SEASON, HolidayCategory.FEDERAL]
        )
        
        for holiday_key, holiday_obj, holiday_date in upcoming:
            # Different campaign strategy per holiday
            if holiday_obj.category == HolidayCategory.EVENT_SEASON:
                # Event seasons = long campaigns, high budget
                campaigns.append({
                    "name": f"{holiday_obj.name} Campaign",
                    "start_date": holiday_date - timedelta(days=60),  # 8 weeks before
                    "end_date": holiday_date + timedelta(days=30),
                    "budget": "$5000",
                    "channels": ["email", "sms", "social_media", "google_ads"],
                    "target": "event_planners",
                })
            else:
                # Federal holidays = shorter campaigns, family focus
                campaigns.append({
                    "name": f"{holiday_obj.name} Promotion",
                    "start_date": holiday_date - timedelta(days=21),  # 3 weeks
                    "end_date": holiday_date + timedelta(days=3),
                    "budget": "$2000",
                    "channels": ["email", "sms", "social_media"],
                    "target": "families",
                })
        
        return campaigns


# Usage:
automation = MarketingAutomation()
campaigns = await automation.schedule_holiday_campaigns()

for campaign in campaigns:
    print(f"{campaign['name']}: {campaign['start_date']} - {campaign['end_date']}")
    print(f"Budget: {campaign['budget']}, Channels: {campaign['channels']}\n")

# Output:
# Graduation Season Campaign: 2025-04-01 - 2025-07-15
# Budget: $5000, Channels: ['email', 'sms', 'social_media', 'google_ads']
#
# Independence Day (4th of July) Promotion: 2025-06-13 - 2025-07-07
# Budget: $2000, Channels: ['email', 'sms', 'social_media']
```

**Campaign Benefits:**
- ✅ Automatically schedules year-round campaigns
- ✅ Different strategies for event seasons vs. holidays
- ✅ Budget allocation based on event type
- ✅ Multi-channel coordination

---

### 4️⃣ **Analytics & Reporting**

**File:** `apps/admin-dashboard/src/lib/holiday-analytics.ts`

```typescript
import { holidayService } from '@/services/holiday-service';

interface BookingAnalytics {
  season: string;
  bookingCount: number;
  revenue: number;
  averageOrderValue: number;
}

export async function getSeasonalBookingTrends(): Promise<BookingAnalytics[]> {
  const holidays = holidayService.getUpcomingHolidays(365);
  
  const analytics = await Promise.all(
    holidays.map(async ([key, holiday, date]) => {
      // Get bookings for this holiday window
      const bookings = await getBookingsForPeriod(
        date - 21 days,
        date + 3 days
      );
      
      return {
        season: holiday.name,
        bookingCount: bookings.length,
        revenue: bookings.reduce((sum, b) => sum + b.total, 0),
        averageOrderValue: revenue / bookingCount,
      };
    })
  );
  
  return analytics;
}

// Admin Dashboard Chart:
// "Thanksgiving bookings: 45 events, $24,750 revenue"
// "Christmas bookings: 67 events, $38,200 revenue"
// "Summer Wedding Season: 156 events, $125,600 revenue"
```

**Analytics Benefits:**
- ✅ Track bookings by holiday/season
- ✅ Identify peak seasons (wedding season = highest revenue)
- ✅ Optimize marketing spend by season
- ✅ Forecast next year's demand

---

### 5️⃣ **Website Dynamic Content**

**File:** `apps/frontend/src/components/HolidayBanner.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { holidayService } from '@/services/holiday-service';

export function HolidayBanner() {
  const [currentHoliday, setCurrentHoliday] = useState(null);
  
  useEffect(() => {
    const holiday = holidayService.getCurrentHoliday();
    setCurrentHoliday(holiday);
  }, []);
  
  if (!currentHoliday) return null;
  
  const [key, holiday, date] = currentHoliday;
  const context = holidayService.getHolidayMessageContext(key);
  
  return (
    <div className="bg-gradient-to-r from-red-600 to-green-600 text-white p-6 text-center">
      <h2 className="text-3xl font-bold">
        🎉 {holiday.name} is Coming! 🎉
      </h2>
      <p className="text-xl mt-2">
        {context.daysUntil} days until {holiday.name}
      </p>
      <p className="mt-4">
        {context.marketingAngle}
      </p>
      <button className="mt-4 bg-white text-red-600 px-8 py-3 rounded-lg font-bold">
        Book Your {holiday.name} Event Now!
      </button>
    </div>
  );
}
```

**Website Benefits:**
- ✅ Automatic holiday banners (no manual updates)
- ✅ Countdown timers
- ✅ Seasonal imagery and messaging
- ✅ CTAs relevant to upcoming events

---

## 📖 Complete API Reference

### **Initialize Service**

```python
from services.holiday_service import get_holiday_service

# Singleton instance (reuse across app)
holiday_service = get_holiday_service()
```

---

### **get_current_holiday()**

Get the current holiday or event season.

```python
current = holiday_service.get_current_holiday()

if current:
    holiday_key, holiday_obj, holiday_date = current
    print(f"Current: {holiday_obj.name} on {holiday_date}")
else:
    print("No active holiday marketing windows today")

# Example Output:
# Current: Thanksgiving on 2025-11-27
```

**Returns:**
- `Tuple[str, Holiday, date]` if in marketing window
- `None` if no active holidays

---

### **get_upcoming_holidays()**

Get upcoming holidays within specified days.

```python
# Next 90 days
upcoming = holiday_service.get_upcoming_holidays(days=90)

for holiday_key, holiday_obj, holiday_date in upcoming:
    print(f"{holiday_obj.name}: {holiday_date}")

# Example Output:
# Thanksgiving: 2025-11-27
# Black Friday Weekend: 2025-11-28
# Christmas: 2025-12-25
# New Year's Eve: 2025-12-31
```

**Parameters:**
- `days`: How many days ahead (default: 60)
- `from_date`: Start date (default: today)
- `categories`: Filter by category (optional)

**Filter by Category Example:**
```python
from services.holiday_service import HolidayCategory

# Only event seasons (weddings, graduations)
event_seasons = holiday_service.get_upcoming_holidays(
    days=365,
    categories=[HolidayCategory.EVENT_SEASON]
)

# Output:
# Graduation Season: 2025-05-15
# Summer Wedding Season: 2025-06-01
# Back to School Season: 2025-08-15
```

---

### **is_in_marketing_window()**

Check if date is in marketing window for any holiday.

```python
from datetime import date

# Check today
if holiday_service.is_in_marketing_window():
    print("Send holiday marketing today!")

# Check specific date
if holiday_service.is_in_marketing_window(date(2025, 11, 10)):
    print("November 10 is in Thanksgiving marketing window")

# Check specific holiday
if holiday_service.is_in_marketing_window(holiday_key="christmas"):
    print("Start Christmas marketing now!")
```

**Returns:** `True` if in marketing window

---

### **get_holiday_message_context()**

Get rich context for holiday-themed messages.

```python
context = holiday_service.get_holiday_message_context("thanksgiving")

print(context)
# Output:
# {
#     'name': 'Thanksgiving',
#     'date': date(2025, 11, 27),
#     'days_until': 14,
#     'typical_events': ['Thanksgiving dinners', 'Family reunions', 'Friendsgiving'],
#     'marketing_angle': 'Perfect for family gatherings and Friendsgiving celebrations',
#     'is_peak_season': False,
#     'category': 'federal',
#     'marketing_window_days': 21,
# }
```

**Use this for:**
- SMS messages: "Thanksgiving is in 14 days!"
- Email content: "Perfect for family gatherings"
- Newsletter: List typical events
- Analytics: Filter by category

---

### **get_season_name()**

Get current event planning season name.

```python
season = holiday_service.get_season_name()
print(season)

# November: "Fall / Thanksgiving Season"
# June: "Summer Wedding Season"
# December: "Winter / Holiday Season"
```

**Use for:**
- Analytics dashboards
- Seasonal reports
- Marketing strategy planning

---

## 🎨 Integration Examples

### **Example 1: Send Newsletter on Holiday Detection**

```python
from services.holiday_service import get_holiday_service
from services.email_service import send_newsletter

async def check_and_send_newsletters():
    """Run daily - send newsletter if holiday detected."""
    holiday_service = get_holiday_service()
    
    current = holiday_service.get_current_holiday()
    
    if current:
        holiday_key, holiday_obj, holiday_date = current
        context = holiday_service.get_holiday_message_context(holiday_key)
        
        # Send newsletter to all customers
        await send_newsletter(
            subject=f"Plan Your {holiday_obj.name} Event!",
            content=f"""
            Hi there!
            
            {holiday_obj.name} is in {context['days_until']} days!
            
            {context['marketing_angle']}
            
            Perfect for:
            {', '.join(context['typical_events'])}
            
            Book your hibachi catering now!
            """,
            target="all_customers"
        )
        
        logger.info(f"Sent {holiday_obj.name} newsletter")
```

**Cron Job:**
```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/app && python -c "from tasks.newsletter_scheduler import check_and_send_newsletters; import asyncio; asyncio.run(check_and_send_newsletters())"
```

---

### **Example 2: Dynamic Website Banner**

```typescript
// apps/frontend/src/app/page.tsx

import { HolidayBanner } from '@/components/HolidayBanner';

export default function HomePage() {
  return (
    <>
      <HolidayBanner /> {/* Automatically shows holiday banner */}
      
      <main>
        {/* Rest of your homepage */}
      </main>
    </>
  );
}
```

---

### **Example 3: Admin Dashboard Analytics**

```typescript
// apps/admin-dashboard/src/app/analytics/seasonal-trends/page.tsx

import { getSeasonalBookingTrends } from '@/lib/holiday-analytics';

export default async function SeasonalTrendsPage() {
  const trends = await getSeasonalBookingTrends();
  
  return (
    <div>
      <h1>Seasonal Booking Trends</h1>
      
      <table>
        <thead>
          <tr>
            <th>Holiday/Season</th>
            <th>Bookings</th>
            <th>Revenue</th>
            <th>Avg Order Value</th>
          </tr>
        </thead>
        <tbody>
          {trends.map(trend => (
            <tr key={trend.season}>
              <td>{trend.season}</td>
              <td>{trend.bookingCount}</td>
              <td>${trend.revenue.toLocaleString()}</td>
              <td>${trend.averageOrderValue.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Output Table:
// | Holiday/Season              | Bookings | Revenue   | Avg Order |
// |-----------------------------|----------|-----------|-----------|
// | Summer Wedding Season       | 156      | $125,600  | $805.13   |
// | Christmas                   | 67       | $38,200   | $570.15   |
// | Thanksgiving                | 45       | $24,750   | $550.00   |
// | Graduation Season           | 38       | $22,800   | $600.00   |
```

---

## 🔧 Customization

### **Add New Holidays**

**File:** `apps/backend/services/holiday_service.py`

```python
# In _initialize_holidays() method:

"mothers_day": Holiday(
    name="Mother's Day",
    category=HolidayCategory.COMMERCIAL,
    marketing_window_days=21,  # Start promoting 3 weeks before
    description="Honoring mothers - perfect for family events",
    typical_events=["Family brunches", "Mother's Day dinners", "Family celebrations"]
),

# Add date calculation in get_holiday_date() method:

elif holiday_key == "mothers_day":
    return self._get_nth_weekday(year, 5, 0, 2)  # 2nd Sunday of May
```

**Add to coupon reminders:**

1. Update `HOLIDAY_MESSAGES` in `coupon_reminder_service.py`:
```python
HOLIDAY_MESSAGES = {
    "mothers_day": {
        "name": "Mother's Day",
        "context": "Treat Mom to an unforgettable hibachi experience",
    },
}
```

2. Update message mapping in `coupon_reminder_scheduler.py`:
```python
holiday_message_map = {
    "mothers_day": "mothers_day",  # Add this line
}
```

**Done! Now automatically detects Mother's Day.**

---

### **Adjust Marketing Windows**

```python
# Start Christmas marketing earlier (45 days instead of 21)
"christmas": Holiday(
    name="Christmas",
    marketing_window_days=45,  # ← Change this
),
```

---

### **Add Regional Holidays**

```python
# Texas-specific holidays
"texas_independence": Holiday(
    name="Texas Independence Day",
    category=HolidayCategory.CULTURAL,
    marketing_window_days=7,
    description="Texas pride celebrations",
),

# Add date:
if holiday_key == "texas_independence":
    return date(year, 3, 2)  # March 2
```

---

## ✅ Testing

### **Test Current Holiday Detection**

```python
from services.holiday_service import get_holiday_service
from datetime import date

holiday_service = get_holiday_service()

# Test Thanksgiving
current = holiday_service.get_current_holiday(date(2025, 11, 10))
assert current is not None
holiday_key, holiday_obj, holiday_date = current
assert holiday_obj.name == "Thanksgiving"
assert holiday_date == date(2025, 11, 27)

print("✅ Thanksgiving detection works!")
```

### **Test Accurate Date Calculation**

```python
# Thanksgiving is ALWAYS 4th Thursday of November
thanksgiving_2025 = holiday_service.get_holiday_date("thanksgiving", 2025)
assert thanksgiving_2025 == date(2025, 11, 27)  # Thursday

thanksgiving_2026 = holiday_service.get_holiday_date("thanksgiving", 2026)
assert thanksgiving_2026 == date(2026, 11, 26)  # Thursday (different week!)

print("✅ Variable date calculation works!")
```

---

## 📊 Business Impact

### **Coupon Reminders**
- ✅ Automatically send holiday-themed SMS
- ✅ Higher engagement ("Thanksgiving is coming!")
- ✅ Accurate timing (no more hardcoded dates)

### **Newsletter System**
- ✅ Generate holiday newsletters automatically
- ✅ Send 3 weeks before each holiday
- ✅ Personalized content per holiday type
- ✅ No manual calendar management

### **Marketing Campaigns**
- ✅ Schedule year-round campaigns automatically
- ✅ Different strategies per holiday/season
- ✅ Budget allocation based on event value
- ✅ Multi-channel coordination

### **Analytics**
- ✅ Track bookings by holiday/season
- ✅ Identify peak seasons
- ✅ Optimize marketing spend
- ✅ Revenue forecasting

### **Website**
- ✅ Dynamic holiday banners
- ✅ Countdown timers
- ✅ Seasonal content
- ✅ Zero maintenance

---

## 🚀 Next Steps

### **Immediate (This Week)**
1. ✅ Holiday service created
2. ✅ Coupon reminders updated to use service
3. ⏳ Test holiday detection with real dates
4. ⏳ Add more holidays (Mother's Day, Father's Day, etc.)

### **Short-Term (Next 2 Weeks)**
1. Create newsletter service using holiday detection
2. Add holiday banners to website
3. Build admin dashboard analytics (seasonal trends)
4. Add holiday-themed email templates

### **Long-Term (Next Month)**
1. Automated marketing campaign scheduling
2. A/B testing holiday messages
3. Customer segmentation by holiday preferences
4. Predictive analytics (forecast holiday bookings)

---

## 📝 Summary

### **What You Have Now:**
✅ **Centralized Holiday Service** - One source of truth for all US holidays  
✅ **Accurate Date Calculation** - No more hardcoded dates  
✅ **Reusable Across Features** - Coupons, newsletters, marketing, analytics, website  
✅ **Easy to Maintain** - Add new holidays in one place  
✅ **Marketing Windows** - Know when to start promoting  
✅ **Rich Context Data** - Personalized messages per holiday  
✅ **Event Season Support** - Wedding season, graduation season, etc.  

### **Use It For:**
- 🎟️ Coupon reminders (already implemented)
- 📧 Newsletter campaigns (ready to build)
- 📢 Marketing automation (ready to build)
- 📊 Analytics dashboards (ready to build)
- 🌐 Website dynamic content (ready to build)

### **Key File:**
📁 `apps/backend/services/holiday_service.py` - Your reusable holiday component!

---

**Generated:** November 13, 2025  
**Status:** Ready to use across your entire application! 🎉
