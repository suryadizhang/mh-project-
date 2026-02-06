# 🎯 Calendar Views - Quick Start Guide

## Access the Calendar

1. **Navigate to Bookings Page**

   ```
   http://localhost:3000/booking
   ```

2. **Click "Calendar View" Button**
   - Located in top-right header
   - Next to "New Booking" button

3. **Direct Access**
   ```
   http://localhost:3000/booking/calendar
   ```

---

## 📅 Weekly View

### What You'll See

- **7 columns**: Sunday through Saturday
- **13 rows**: Time slots from 10 AM to 10 PM
- **Booking cards**: Color-coded by status
- **Today highlight**: Blue background for current day

### How to Use

1. **Drag bookings** between time slots to reschedule
2. **Click bookings** to view details (TODO: modal)
3. **Navigate**: Previous/Next week buttons
4. **Jump to today**: Click "Today" button

### Visual Layout

```
┌─────┬───────┬───────┬───────┬───────┬───────┬───────┬───────┐
│Time │  Sun  │  Mon  │  Tue  │  Wed  │  Thu  │  Fri  │  Sat  │
├─────┼───────┼───────┼───────┼───────┼───────┼───────┼───────┤
│10 AM│ ✅ 2  │       │ ⏳ 1  │       │       │       │       │
│     │ [Book]│       │ [Book]│       │       │       │       │
├─────┼───────┼───────┼───────┼───────┼───────┼───────┼───────┤
│11 AM│       │ ✅ 1  │       │ ✅ 2  │       │       │       │
│     │       │ [Book]│       │ [Book]│       │       │       │
├─────┼───────┼───────┼───────┼───────┼───────┼───────┼───────┤
│12 PM│       │       │ ✅ 3  │       │ ⏳ 1  │       │       │
└─────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┘
```

---

## 📆 Monthly View

### What You'll See

- **7 columns**: Days of the week
- **4-6 rows**: Full calendar month
- **Day cells**: Up to 3 bookings visible
- **Stats**: Confirmed/pending counts + revenue per day

### How to Use

1. **Drag bookings** between days (keeps same time slot)
2. **Click day** to see all bookings (TODO: modal)
3. **Click booking** to view details
4. **Navigate**: Previous/Next month buttons
5. **View stats**: Revenue and counts per day

### Visual Layout

```
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│   Sun    │   Mon    │   Tue    │   Wed    │   Thu    │   Fri    │   Sat    │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│    1     │    2     │    3     │    4     │    5     │    6     │    7     │
│  2 📅    │  1 📅    │          │  3 📅    │  1 📅    │  2 📅    │          │
│ [Smith]  │ [Jones]  │          │ [Davis]  │ [Wilson] │ [Brown]  │          │
│ [Taylor] │          │          │ [Miller] │          │ [Garcia] │          │
│          │          │          │ [+1 more]│          │          │          │
│ ───────  │ ───────  │          │ ───────  │ ───────  │ ───────  │          │
│ ✅ 2     │ ⏳ 1     │          │ ✅ 2     │ ✅ 1     │ ✅ 2     │          │
│ $1,200   │  $600    │          │ $1,800   │  $450    │ $1,050   │          │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## 🎨 Status Colors

| Status           | Color  | Draggable |
| ---------------- | ------ | --------- |
| ✅ **Confirmed** | Green  | Yes       |
| ⏳ **Pending**   | Yellow | Yes       |
| ❌ **Cancelled** | Red    | No        |
| ✔️ **Completed** | Blue   | No        |

---

## 🖱️ Drag & Drop Guide

### Weekly View - Change Time

1. **Hover** over a booking card
2. **Click and hold** to start dragging
3. **Drag** to target time slot
4. **Release** to drop and update

### Monthly View - Change Day

1. **Hover** over a booking card
2. **Click and hold** to start dragging
3. **Drag** to target day
4. **Release** to drop (keeps same time)

### Rules

- ❌ Can't drag to past dates
- ❌ Can't drag cancelled bookings
- ❌ Can't drag completed bookings
- ✅ Confirmed and pending only

---

## 🔧 Navigation Controls

### Header Buttons

- **[<]** Previous week/month
- **[Today]** Jump to current date
- **[>]** Next week/month
- **[🔄]** Refresh data

### View Switcher

- **Week** - 7-day time grid
- **Month** - Full calendar month

---

## 📊 Quick Stats (Top Right)

- **Total Bookings** - All bookings in current view
- **Confirmed** - Green count
- **Pending** - Yellow count

---

## ⚡ Keyboard Shortcuts (TODO)

Future enhancements:

- `←` Previous week/month
- `→` Next week/month
- `T` Today
- `W` Week view
- `M` Month view
- `ESC` Close modal

---

## 🐛 Troubleshooting

### Bookings not showing?

- Check date range (current week/month only)
- Click refresh button
- Check browser console for errors

### Drag not working?

- Only confirmed/pending bookings can be dragged
- Can't drag to past dates
- Check if booking is cancelled/completed

### API errors?

- Ensure backend is running
- Check `/api/bookings/admin/weekly` endpoint
- Check `/api/bookings/admin/monthly` endpoint
- Check `/api/bookings/admin/:id` PATCH endpoint

### TypeScript errors?

- Run `npm run typecheck`
- All calendar files should have 0 errors
- Check imports and type definitions

---

## 📱 Mobile Support

**Current Status:** Desktop-optimized  
**TODO:** Mobile touch support

For now, use desktop/tablet for best experience:

- Desktop: Full drag-drop support
- Tablet: Works with mouse/trackpad
- Mobile: View-only (no drag-drop yet)

---

## 🚀 Quick Test Checklist

### Before Demo/Production

- [ ] Navigate to calendar page
- [ ] Switch between week and month views
- [ ] Click Previous/Next buttons
- [ ] Click Today button
- [ ] Drag a confirmed booking to new slot
- [ ] Verify booking updates in API
- [ ] Check color coding is correct
- [ ] Verify stats display correctly
- [ ] Test with multiple bookings in one slot
- [ ] Test with empty days/slots
- [ ] Test error handling (disconnect API)

---

## 📞 Support

**Issues?** Check:

1. `CALENDAR_VIEWS_COMPLETE.md` - Full documentation
2. Console logs - Developer tools
3. Network tab - API calls
4. Backend logs - Server errors

**Questions?** Review:

- Component files - Inline comments
- Type definitions - `calendar.types.ts`
- Hook files - `useCalendarData.ts`, `useDragDrop.ts`

---

**Ready to use! 🎉**

Navigate to: `http://localhost:3000/booking/calendar`
