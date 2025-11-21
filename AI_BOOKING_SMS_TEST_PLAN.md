# AI Booking Assistant - SMS Testing Plan

## ✅ Implementation Status

### Completed

- ✅ AI Booking Assistant Service (`ai_booking_assistant_service.py` -
  600 lines)
- ✅ SMS Webhook Integration (`sms_terms_webhook.py`)
- ✅ Customer Repository Integration
- ✅ All syntax errors fixed
- ✅ Import errors resolved

### Code Quality

- ✅ No compilation errors
- ✅ All imports resolve correctly
- ✅ Error handling implemented
- ✅ Logging throughout
- ✅ Clean architecture (services → repositories → models)

---

## 🧪 Testing Scenarios

### Scenario 1: Basic Inquiry (Happy Path)

**Objective**: Test AI intent classification and information
extraction

**Test Steps**:

1. Send SMS to `+19167408768`: "How much for 20 people?"

**Expected AI Response**:

```
Our packages start at $45/person for Standard, $55 for Premium, and $65 for Deluxe.

For 20 guests, that would be:
- Standard: $900
- Premium: $1,100
- Deluxe: $1,300

Would you like to book a Hibachi experience?
```

**Validation**:

- ✅ AI classifies intent as `INQUIRY`
- ✅ AI extracts `guest_count: 20`
- ✅ Response includes pricing for 3 packages
- ✅ Response is conversational and helpful

---

### Scenario 2: Complete Booking Flow (End-to-End)

**Objective**: Test full booking creation from SMS conversation

**Test Steps**:

1. **Initial Inquiry**
   - Send: "I want to book hibachi for December 20th"
   - Expected: AI confirms date, asks for time and guest count

2. **Provide Details**
   - Send: "6pm for 15 people at 123 Main St, Sacramento"
   - Expected: AI confirms all details, asks for confirmation

3. **Confirmation**
   - Send: "Yes, book it"
   - Expected: AI sends terms & conditions SMS

4. **Terms Acceptance**
   - Send: "AGREE"
   - Expected: Booking created, confirmation sent

**Validation**:

- ✅ All booking stages progress correctly
- ✅ Information extraction accurate
- ✅ Terms SMS sent with unique tracking ID
- ✅ Booking created in database
- ✅ Customer receives confirmation

---

### Scenario 3: Incomplete Information Handling

**Objective**: Test AI's ability to prompt for missing information

**Test Steps**:

1. Send: "Book hibachi"
2. Expected: AI asks for date
3. Send: "December 20th"
4. Expected: AI asks for time
5. Send: "6pm"
6. Expected: AI asks for guest count and address

**Validation**:

- ✅ AI identifies missing fields
- ✅ AI prompts naturally for each missing field
- ✅ AI remembers previous responses in conversation
- ✅ Stage progresses: INITIAL → COLLECTING_INFO

---

### Scenario 4: Human Escalation

**Objective**: Test escalation to staff for complex requests

**Test Steps**:

1. Send: "Can you do a dinner for 50 people with custom menu?"
2. Expected: AI recognizes complexity, escalates to staff
3. Expected: Staff notification sent
4. Expected: Customer informed that staff will follow up

**Validation**:

- ✅ AI detects need for human intervention
- ✅ `requires_human` flag set to true
- ✅ Staff notification sent
- ✅ Customer receives polite escalation message

---

### Scenario 5: Error Handling

**Objective**: Test graceful degradation when errors occur

**Test Steps**:

1. Send: "Book for 99999 people" (unrealistic)
2. Expected: AI handles gracefully, may escalate

**Test Case 2 - OpenAI API Failure**:

- Simulate API timeout
- Expected: Fallback response sent
- Expected: Error logged for monitoring

**Validation**:

- ✅ No crashes or unhandled exceptions
- ✅ Customer always receives a response
- ✅ Errors logged with full context
- ✅ Fallback messages are professional

---

## 🔍 Manual Testing Checklist

### Pre-Test Setup

- [ ] Backend server running (`docker-compose up -d`)
- [ ] Database migrations applied (014 & 015)
- [ ] OpenAI API key configured in `.env`
- [ ] RingCentral webhook registered
- [ ] Phone available for SMS testing

### During Testing - Monitor:

#### 1. **Backend Logs**

```powershell
# Terminal 1: Watch backend logs
docker-compose logs -f backend | Select-String -Pattern "🤖|AI|booking|ERROR"
```

**Look for**:

- `🤖 AI processing booking message from +1...`
- `✅ AI intent: INQUIRY/BOOKING/...`
- `📊 Extracted booking info: {...}`
- `✅ AI created booking #...`
- `📱 Terms SMS sent to +1...`
- ❌ Any ERROR messages

#### 2. **Database State**

```powershell
# Terminal 2: Check database
docker exec -it mh_webapps_postgres psql -U postgres -d mh_webapp_dev

# Check customers created
SELECT id, first_name, last_name, phone FROM public.customers WHERE phone LIKE '%your_test_phone%';

# Check bookings created
SELECT id, customer_id, event_date, guest_count, status FROM public.bookings ORDER BY created_at DESC LIMIT 5;

# Check terms acknowledgments
SELECT id, customer_id, booking_id, acknowledged, acknowledged_at FROM public.terms_acknowledgments ORDER BY created_at DESC LIMIT 5;
```

#### 3. **RingCentral SMS Logs**

- Check RingCentral dashboard for webhook hits
- Verify SMS responses are sent back to customer
- Check for any webhook failures or 500 errors

---

## 📊 Success Metrics

### Functional Metrics

- **Intent Classification Accuracy**: ≥ 90%
  - Correctly identifies INQUIRY, BOOKING, MODIFICATION, etc.
- **Information Extraction Accuracy**: ≥ 85%
  - Correctly extracts date, time, guest count, address
- **Response Time**: ≤ 3 seconds
  - Time from SMS received to response sent
- **Booking Completion Rate**: ≥ 70%
  - Percentage of conversations that result in bookings

### Technical Metrics

- **Error Rate**: ≤ 5%
  - Unhandled exceptions or crashes
- **Escalation Rate**: 10-20%
  - Appropriate escalation to humans
- **Terms Acknowledgment Rate**: ≥ 95%
  - Customers who complete terms acceptance

---

## 🐛 Troubleshooting Guide

### Issue: No Response from AI

**Possible Causes**:

1. OpenAI API key missing or invalid
2. Import error in AI service
3. Webhook not routing to AI handler

**Debug Steps**:

```powershell
# Check environment variables
docker exec mh_webapps_backend env | Select-String -Pattern "OPENAI"

# Check if AI service is imported
docker exec mh_webapps_backend python -c "from services.ai_booking_assistant_service import AIBookingAssistant; print('✅ Import successful')"

# Check webhook logs
docker-compose logs backend | Select-String -Pattern "sms_terms_webhook"
```

---

### Issue: Customer Not Created

**Possible Causes**:

1. Phone number format issue
2. Database connection error
3. CustomerRepository error

**Debug Steps**:

```sql
-- Check if customer exists
SELECT * FROM public.customers WHERE phone = '+1YOURNUMBER';

-- Check recent customer creations
SELECT * FROM public.customers ORDER BY created_at DESC LIMIT 10;
```

---

### Issue: Terms Not Sent

**Possible Causes**:

1. UnifiedNotificationService error
2. RingCentral API credentials invalid
3. Terms acknowledgment service error

**Debug Steps**:

```powershell
# Check notification service logs
docker-compose logs backend | Select-String -Pattern "UnifiedNotificationService|send_sms"

# Check RingCentral credentials
docker exec mh_webapps_backend env | Select-String -Pattern "RINGCENTRAL"
```

---

### Issue: Booking Not Created

**Possible Causes**:

1. Missing required booking fields
2. BookingService error
3. Database constraint violation

**Debug Steps**:

```sql
-- Check booking service logs
-- Look for: "Creating booking with data: {...}"

-- Check for failed bookings
SELECT * FROM public.bookings WHERE status = 'failed' OR status IS NULL ORDER BY created_at DESC;

-- Check database constraints
SELECT constraint_name, constraint_type FROM information_schema.table_constraints WHERE table_name = 'bookings';
```

---

## 🚀 Next Steps After Testing

### If All Tests Pass ✅

1. **Add Conversation Persistence** (1 hour)
   - Create `conversation_threads` table
   - Store multi-message conversations
   - Load conversation history in AI service

2. **Integrate Phone AI** (2 hours)
   - Modify `voice_ai_service.py`
   - Add call to `process_phone_booking_transcript()`
   - Test phone booking flow

3. **Integrate Web Chat** (1 hour)
   - Create chat API endpoint
   - Add call to `process_web_chat_message()`
   - Test chat widget integration

4. **Setup Monitoring** (2 hours)
   - Implement metrics dashboard
   - Add alerts for errors
   - Track booking success rate

5. **Staff Training** (1 hour)
   - Train on escalation handling
   - Provide AI capabilities overview
   - Practice scenarios

### If Tests Fail ❌

**Priority 1: Fix Blocking Issues**

- Any unhandled exceptions
- OpenAI API connectivity
- Database connection errors

**Priority 2: Fix Core Functionality**

- Intent classification accuracy
- Information extraction bugs
- Booking creation failures

**Priority 3: Improve User Experience**

- Response clarity
- Conversational flow
- Error messages

---

## 📝 Test Results Template

```markdown
## Test Execution Results

**Date**: [DATE] **Tester**: [NAME] **Environment**: Development

### Scenario 1: Basic Inquiry

- Status: ✅ PASS / ❌ FAIL
- Notes: [Any observations]

### Scenario 2: Complete Booking Flow

- Status: ✅ PASS / ❌ FAIL
- Booking ID: [ID]
- Terms Ack ID: [ID]
- Notes: [Any observations]

### Scenario 3: Incomplete Information

- Status: ✅ PASS / ❌ FAIL
- Notes: [Any observations]

### Scenario 4: Human Escalation

- Status: ✅ PASS / ❌ FAIL
- Notes: [Any observations]

### Scenario 5: Error Handling

- Status: ✅ PASS / ❌ FAIL
- Notes: [Any observations]

### Overall Assessment

- **Functional**: ✅ Ready / 🟡 Needs Work / ❌ Not Ready
- **Technical**: ✅ Stable / 🟡 Minor Issues / ❌ Major Issues
- **Recommendation**: [PROCEED / FIX ISSUES / REDESIGN]

### Issues Found

1. [Issue description]
   - Severity: High / Medium / Low
   - Steps to reproduce: [Steps]
   - Expected: [Expected behavior]
   - Actual: [Actual behavior]
```

---

## 🎯 Definition of Done

AI Booking SMS is **PRODUCTION READY** when:

- ✅ All 5 test scenarios pass
- ✅ No unhandled exceptions in 50 test messages
- ✅ Intent classification accuracy ≥ 90%
- ✅ Information extraction accuracy ≥ 85%
- ✅ Response time ≤ 3 seconds average
- ✅ Booking creation succeeds in happy path
- ✅ Terms SMS sent and tracked correctly
- ✅ Human escalation works appropriately
- ✅ Error logging captures all issues
- ✅ Staff trained and confident
- ✅ Monitoring dashboard operational

---

**READY TO TEST!** 🚀

Start with Scenario 1 (Basic Inquiry) to verify core AI functionality.
