# 🍱 My Hibachi - Booking System Backend Structure

## 📡 API Endpoints

### 1. Get Fully Booked Dates

```
GET /api/v1/bookings/booked-dates
```

**Purpose**: Returns dates that are completely unavailable (all time slots booked)

**Response Example**:

```json
{
  "success": true,
  "bookedDates": ["2025-08-10", "2025-08-15"],
  "message": "Found 2 fully booked date(s)"
}
```

### 2. Get Availability for Specific Date

```
GET /api/v1/bookings/availability?date=YYYY-MM-DD
```

**Purpose**: Returns time slot availability for a specific date

**Response Example**:

```json
{
  "success": true,
  "date": "2025-08-08",
  "timeSlots": [
    {
      "time": "12PM",
      "available": 0,
      "maxCapacity": 2,
      "booked": 2,
      "isAvailable": false
    },
    {
      "time": "3PM",
      "available": 1,
      "maxCapacity": 2,
      "booked": 1,
      "isAvailable": true
    }
  ]
}
```

### 3. Create Booking (Ready for Implementation)

```
POST /api/v1/bookings/availability
```

**Purpose**: Reserve a time slot for a customer

**Request Body**:

```json
{
  "date": "2025-08-09",
  "time": "3PM",
  "customerInfo": {
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "(555) 123-4567",
    "guestCount": 8
  }
}
```

## 🗂️ Database Schema Recommendations

### Bookings Table

```sql
CREATE TABLE bookings (
    id UUID PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    event_date DATE NOT NULL,
    event_time VARCHAR(10) NOT NULL, -- '12PM', '3PM', '6PM', '9PM'
    guest_count INTEGER NOT NULL,
    venue_address JSONB NOT NULL,
    billing_address JSONB,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'confirmed', 'cancelled'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Time Slots Configuration Table

```sql
CREATE TABLE time_slot_config (
    id SERIAL PRIMARY KEY,
    time_slot VARCHAR(10) NOT NULL, -- '12PM', '3PM', '6PM', '9PM'
    max_capacity INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT true
);
```

## 🔧 Current Mock Data Structure

The system currently uses mock data to demonstrate functionality:

```typescript
// Mock availability data
const MOCK_AVAILABILITY = {
  '2025-08-08': {
    '12PM': { booked: 2, maxCapacity: 2 }, // Fully booked
    '3PM': { booked: 1, maxCapacity: 2 }, // 1 slot available
    '6PM': { booked: 0, maxCapacity: 2 }, // 2 slots available
    '9PM': { booked: 2, maxCapacity: 2 } // Fully booked
  }
  // ... more dates
}
```

## ✨ Frontend Features

### Date Selection

- ✅ **React DatePicker**: Professional date selection with custom styling
- ✅ **48-Hour Rule**: Enforces minimum advance booking requirement
- ✅ **Blocked Dates**: Automatically excludes fully booked dates
- ✅ **No Previous Years**: Prevents navigation to past years

### Time Slot Selection

- ✅ **Dynamic Loading**: Fetches availability when date is selected
- ✅ **Visual Indicators**: Shows available slots vs "Fully Booked"
- ✅ **Real-time Updates**: Updates based on actual bookings
- ✅ **Smart Messaging**: User-friendly availability feedback

### User Experience

- ✅ **Loading States**: Shows progress during API calls
- ✅ **Error Handling**: Graceful fallbacks if APIs fail
- ✅ **Validation**: Comprehensive form validation with helpful messages
- ✅ **Responsive Design**: Works on all device sizes

## 🚀 Next Implementation Steps

1. **Database Integration**:
   - Replace mock data with real database queries
   - Implement booking creation and updates
   - Add booking status management

2. **Payment Processing**:
   - Integrate payment gateway (Stripe, Square, etc.)
   - Handle deposits and final payments
   - Send confirmation emails

3. **Admin Panel**:
   - View and manage bookings
   - Adjust time slot capacity
   - Handle cancellations and rescheduling

4. **Notifications**:
   - Email confirmations to customers
   - SMS reminders before events
   - Admin notifications for new bookings

## 📱 API Testing

You can test the APIs using curl:

```bash
# Get fully booked dates
curl http://localhost:3001/api/v1/bookings/booked-dates

# Get availability for a specific date
curl "http://localhost:3001/api/v1/bookings/availability?date=2025-08-08"
```

The system is now ready for production database integration! 🎉
