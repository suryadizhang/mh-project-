# 🧪 AI SMS Booking Assistant - Testing Guide

## ✅ Prerequisites Verified

### Configuration Status

- ✅ **Pricing**: $55 adult, $30 child, $550 minimum - CORRECT
- ✅ **Menu Items**: All proteins, upgrades, add-ons - ACCURATE
- ✅ **Business Policies**: Deposit, travel, cancellation - COMPLETE
- ✅ **Brand Voice**: Warm, friendly, professional - DEFINED
- ✅ **No Syntax Errors**: All code validated
- ✅ **Imports Resolved**: All dependencies correct

**Verification Run**: ✅ PASSED (except Unicode emoji in output -
non-critical)

---

## 🚀 Step-by-Step Testing Process

### Step 1: Start Docker Desktop (5 minutes)

**Action**: Launch Docker Desktop application

**Windows**:

1. Press `Windows` key
2. Type "Docker Desktop"
3. Click to launch
4. Wait for "Docker Desktop is running" in system tray

**Verify**:

```powershell
docker --version
# Should show: Docker version 20.x.x or higher
```

---

### Step 2: Start Backend Services (2 minutes)

```powershell
# Navigate to project
cd "C:\Users\surya\projects\MH webapps"

# Start all services (development profile)
docker-compose --profile development up -d

# Check status
docker-compose --profile development ps
```

**Expected Output**:

```
NAME                    STATUS              PORTS
myhibachi-backend       Up 30 seconds      0.0.0.0:8000->8000/tcp
myhibachi-postgres      Up 30 seconds      0.0.0.0:5432->5432/tcp
myhibachi-redis         Up 30 seconds      0.0.0.0:6379->6379/tcp
```

---

### Step 3: Verify Backend Health (1 minute)

```powershell
# Check backend logs
docker-compose --profile development logs unified-backend --tail=50

# Look for:
# ✅ "Application startup complete"
# ✅ "Uvicorn running on http://0.0.0.0:8000"
# ❌ No ERROR messages
```

**Test Health Endpoint**:

```powershell
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

---

### Step 4: Verify Environment Variables (2 minutes)

```powershell
# Check OpenAI API key
docker exec myhibachi-backend env | Select-String "OPENAI_API_KEY"
# Should show: OPENAI_API_KEY=sk-...

# Check RingCentral credentials
docker exec myhibachi-backend env | Select-String "RINGCENTRAL"
# Should show:
# RINGCENTRAL_CLIENT_ID=...
# RINGCENTRAL_CLIENT_SECRET=...
# RINGCENTRAL_JWT_TOKEN=...
# RINGCENTRAL_PHONE_NUMBER=+19167408768
```

**If Missing**:

1. Check `.env` file in project root
2. Restart containers:
   `docker-compose --profile development down; docker-compose --profile development up -d`

---

### Step 5: Test AI Configuration Import (1 minute)

```powershell
# Test if AI config loads correctly
docker exec myhibachi-backend python -c "from config.ai_booking_config import PRICING; print(f'Adult: \${PRICING[\"adult_base\"]}, Child: \${PRICING[\"child_base\"]}')"

# Expected output:
# Adult: $55, Child: $30
```

**If Error**: Check that `config/ai_booking_config.py` exists in
backend container

---

## 📱 SMS Testing Scenarios

### Test 1: Simple Pricing Inquiry (5 minutes)

**Objective**: Verify AI quotes correct pricing with warm tone

**Action**: From your phone, send SMS to `+19167408768`:

```
How much for 20 people?
```

**Monitor Backend**:

```powershell
# In separate terminal
docker-compose --profile development logs -f unified-backend | Select-String "AI|booking"
```

**Expected AI Response**:

```
Great question! For 20 guests, here's the breakdown:

**Standard Package:**
- Adults (13+): $55 per person
- If all adults: $1,100 total
- Includes 2 proteins per guest, fried rice, veggies, salad, sauces, and sake!

**Party Minimum:** $550 (you're well above that! ✓)

Would you like to book? I can help you choose your proteins and pick your perfect date! 🎉
```

**Verify**:

- ✅ Quotes $55/person (NOT $45 or other wrong price)
- ✅ Calculates $1,100 for 20 people correctly
- ✅ Uses warm, friendly tone with emoji
- ✅ Mentions party minimum
- ✅ Asks engaging follow-up question

**If Wrong Price Quoted**:

1. Check logs for errors
2. Verify AI config imported:
   `docker exec myhibachi-backend python -c "from config.ai_booking_config import PRICING; print(PRICING)"`
3. Restart backend:
   `docker-compose --profile development restart unified-backend`

---

### Test 2: Complete Booking Flow (10 minutes)

**Objective**: Test end-to-end booking with AI

**Step 1 - Initial Request**:

```
I want to book hibachi for December 20th
```

**Expected Response**:

```
Awesome! Let's get you booked for December 20th! 🎉

I just need a couple more details:
📍 What's the address in Sacramento?
👥 How many guests are you expecting?

Once I have that, I'll send you our Terms & Conditions to review, then we'll secure your date with a $100 deposit (fully refundable if you need to cancel 7+ days before).

Can't wait to make your event amazing! ✨
```

**Step 2 - Provide Details**:

```
6pm for 15 people at 123 Main St, Sacramento
```

**Expected Response**:

```
Perfect! Here's what I have:

📅 Date: December 20, 2025
🕐 Time: 6:00 PM
👥 Guests: 15 people
📍 Location: 123 Main St, Sacramento

💰 Estimated Total: $825 (15 × $55/person)

Is this correct? Reply YES to proceed! ✅
```

**Step 3 - Confirmation**:

```
YES
```

**Expected Response**:

```
Awesome! I'm sending you our Terms & Conditions right now. 📋

Please review and reply AGREE to complete your booking.

Once you agree, your deposit secures your date and we're all set! 🎉
```

**Step 4 - Terms Acceptance**:

```
AGREE
```

**Expected Response**:

```
🎉 BOOKING CONFIRMED! 🎉

Your hibachi experience is all set for December 20, 2025 at 6:00 PM!

**What's Next:**
✅ Deposit paid: $100
✅ Final balance due on event date
📧 Confirmation email sent
📅 We'll send a reminder closer to your event

**Questions?** Text us anytime at (916) 740-8768

We can't wait to make your event amazing! 🔥✨
```

**Verify Database**:

```powershell
# Check booking created
docker exec -it myhibachi-postgres psql -U postgres -d myhibachi -c "SELECT id, customer_id, event_date, guest_count, status FROM public.bookings ORDER BY created_at DESC LIMIT 1;"

# Check terms acknowledgment
docker exec -it myhibachi-postgres psql -U postgres -d myhibachi -c "SELECT id, customer_id, booking_id, acknowledged FROM public.terms_acknowledgments ORDER BY created_at DESC LIMIT 1;"
```

---

### Test 3: Add-On Inquiry (3 minutes)

**Objective**: Verify AI uses "add-on" terminology (not "upsell")

**Action**:

```
What extras can I add?
```

**Expected Response**:

```
Great question! We have some delicious add-on options to enhance your experience:

**Premium Protein Upgrades:**
- Lobster Tail: +$15/person 🦞
- Salmon: +$5/person 🐟
- Scallops: +$5/person
- Filet Mignon: +$5/person

**Appetizers & Sides:**
- Gyoza (dumplings): +$10/person
- Edamame: +$5/person
- Yakisoba Noodles: +$5/person
- Extra Fried Rice: +$5/person

Want to add any of these? Or you can stick with the standard package - it's already amazing! 😊
```

**Verify**:

- ✅ Uses "add-on" terminology (NEVER "upsell")
- ✅ Correct prices for all items
- ✅ Natural, non-pushy tone
- ✅ Affirms standard package is great too

---

### Test 4: Policy Question (3 minutes)

**Objective**: Verify AI knows business policies

**Action**:

```
What's your cancellation policy?
```

**Expected Response**:

```
Here's how our cancellation policy works:

📅 **Cancel 7+ Days Before Event:**
- Full refund of your $100 deposit ✅
- No questions asked!

⏰ **Cancel Within 7 Days:**
- $100 deposit is non-refundable ❌
- We understand emergencies happen though!

🔄 **Reschedule Instead?**
- Free reschedule within 48 hours of booking
- Additional reschedules: $100 fee

Need to make changes? Text us at (916) 740-8768 anytime! 😊
```

**Verify**:

- ✅ Mentions 7-day refund policy
- ✅ Correct deposit amount ($100)
- ✅ Mentions reschedule option
- ✅ Empathetic tone

---

### Test 5: Complex Request (Escalation) (2 minutes)

**Objective**: Verify AI escalates when appropriate

**Action**:

```
Can you do a custom menu for 100 people with special dietary restrictions?
```

**Expected Response**:

```
I want to make sure you get the best help for your special event! Let me connect you with our team.

**They'll reach out within:**
- 📱 Text/Call: 15-30 minutes
- 📧 Email: 1-2 hours

**Or reach out directly:**
📞 Text: (916) 740-8768
📧 Email: info@myhhibachichef.com

They'll take great care of you and can customize everything for your 100-guest event! 💫
```

**Verify**:

- ✅ Recognizes complexity
- ✅ Escalates to human
- ✅ Provides contact info
- ✅ Sets expectations for response time
- ✅ Maintains warm, helpful tone

---

## 📊 Success Criteria

### For Each Test:

**Pricing Accuracy**:

- [ ] Always quotes $55/adult, $30/child
- [ ] Calculates totals correctly
- [ ] Mentions $550 minimum when relevant
- [ ] Correct upgrade/add-on prices

**Brand Voice**:

- [ ] Warm and friendly tone
- [ ] Professional language
- [ ] Uses 1-3 emojis appropriately
- [ ] Asks engaging questions
- [ ] Clear next steps

**Completeness**:

- [ ] Provides all necessary information
- [ ] Answers customer's question fully
- [ ] Includes relevant policies
- [ ] Offers to help further

**Technical**:

- [ ] Response time < 5 seconds
- [ ] No errors in logs
- [ ] Database records created (for bookings)
- [ ] Terms SMS sent (for bookings)

---

## 🐛 Troubleshooting

### Issue: No SMS Response

**Check**:

```powershell
# 1. Backend running?
docker-compose --profile development ps

# 2. RingCentral webhook registered?
# Check RingCentral dashboard: https://developers.ringcentral.com

# 3. Any errors?
docker-compose --profile development logs unified-backend --tail=100 | Select-String "ERROR"

# 4. SMS webhook responding?
docker-compose --profile development logs unified-backend | Select-String "sms_terms_webhook"
```

**Solution**:

- Restart backend:
  `docker-compose --profile development restart unified-backend`
- Check `.env` file for RINGCENTRAL credentials
- Verify webhook URL in RingCentral dashboard

---

### Issue: Wrong Pricing Quoted

**Check**:

```powershell
# Verify AI config
docker exec myhibachi-backend python -c "from config.ai_booking_config import PRICING; import json; print(json.dumps(PRICING, indent=2))"
```

**Solution**:

- If config looks wrong, check
  `apps/backend/src/config/ai_booking_config.py`
- Rebuild container:
  `docker-compose --profile development build unified-backend`
- Restart:
  `docker-compose --profile development up -d unified-backend`

---

### Issue: Generic/Bland Responses

**Check**:

```powershell
# Verify brand personality loaded
docker exec myhibachi-backend python -c "from config.ai_booking_config import BRAND_PERSONALITY; print(BRAND_PERSONALITY[:200])"
```

**Solution**:

- Check OpenAI API key:
  `docker exec myhibachi-backend env | Select-String "OPENAI"`
- Check AI model setting in response generation
- Review logs for OpenAI API errors

---

### Issue: Booking Not Created in Database

**Check**:

```powershell
# Check database connection
docker exec myhibachi-backend python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.getenv('DATABASE_URL_SYNC')); print('Connected' if engine else 'Failed')"

# Check recent bookings
docker exec -it myhibachi-postgres psql -U postgres -d myhibachi -c "SELECT COUNT(*) FROM public.bookings;"
```

**Solution**:

- Check database migrations run:
  `docker exec myhibachi-backend alembic current`
- Run migrations if needed:
  `docker exec myhibachi-backend alembic upgrade head`
- Check logs for database errors

---

## ✅ Testing Completion Checklist

Once all tests pass:

- [ ] Test 1: Pricing inquiry - AI quotes $55/person ✅
- [ ] Test 2: Complete booking flow - Booking created ✅
- [ ] Test 3: Add-on inquiry - Uses correct terminology ✅
- [ ] Test 4: Policy question - Accurate information ✅
- [ ] Test 5: Complex request - Proper escalation ✅
- [ ] All responses use warm, friendly tone ✅
- [ ] No pricing errors (always $55/$30) ✅
- [ ] Response time < 5 seconds ✅
- [ ] No backend errors in logs ✅
- [ ] Database records created correctly ✅

**When Complete**: Update todo to mark "Test SMS AI with real
scenarios" as ✅ DONE

---

## 📝 Test Results Template

```markdown
## SMS AI Test Results - [DATE]

### Environment

- Backend: ✅ Running
- Database: ✅ Connected
- OpenAI API: ✅ Working
- RingCentral: ✅ Configured

### Test 1: Pricing Inquiry

- Status: ✅ PASS / ❌ FAIL
- Correct Price: ✅ $55 / ❌ Wrong
- Warm Tone: ✅ Yes / ❌ No
- Notes: [Any observations]

### Test 2: Booking Flow

- Status: ✅ PASS / ❌ FAIL
- Booking Created: ✅ Yes / ❌ No
- Terms Sent: ✅ Yes / ❌ No
- Notes: [Booking ID, any issues]

### Test 3: Add-On Inquiry

- Status: ✅ PASS / ❌ FAIL
- Correct Terminology: ✅ "add-on" / ❌ "upsell"
- Accurate Prices: ✅ Yes / ❌ No
- Notes: [Any observations]

### Test 4: Policy Question

- Status: ✅ PASS / ❌ FAIL
- Accurate Info: ✅ Yes / ❌ No
- Notes: [Any observations]

### Test 5: Escalation

- Status: ✅ PASS / ❌ FAIL
- Proper Escalation: ✅ Yes / ❌ No
- Notes: [Any observations]

### Overall Assessment

- **Pricing Accuracy**: ✅ 100% / ❌ Issues Found
- **Brand Voice**: ✅ Excellent / 🟡 Good / ❌ Needs Work
- **Technical**: ✅ Stable / 🟡 Minor Issues / ❌ Major Issues
- **Recommendation**: ✅ PRODUCTION READY / 🟡 MINOR FIXES / ❌ MAJOR
  WORK NEEDED

### Issues Found

1. [Issue description]
   - Impact: High/Medium/Low
   - Fix: [What needs to be done]

### Next Steps

- [ ] [Action item 1]
- [ ] [Action item 2]
```

---

## 🚀 After Successful Testing

1. **Mark Test Complete**: ✅ "Test SMS AI with real scenarios"

2. **Move to Next Phase**: Conversation Persistence
   - Create `conversation_threads` table
   - Update AI service to store/load history
   - Enable multi-message conversations

3. **Monitor Production**: First few days
   - Watch for pricing errors
   - Track customer satisfaction
   - Collect feedback for improvements

4. **Iterate**: Based on real usage
   - Update FAQ responses
   - Refine brand voice
   - Add new scenarios

---

**Ready to Test!** 🎉

**First Action**: Launch Docker Desktop, then run
`docker-compose --profile development up -d`
