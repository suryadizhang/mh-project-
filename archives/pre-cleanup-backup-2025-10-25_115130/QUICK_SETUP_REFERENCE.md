# 🔑 Quick Environment Variables Reference

## **REQUIRED API KEYS FOR LOCAL TESTING**

### 🟡 **CRITICAL - Payment Testing (Stripe)**
```bash
# Get from: https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE  
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE
```

### 🟡 **CRITICAL - AI Features (OpenAI)**
```bash
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-YOUR_OPENAI_KEY_HERE
```

### 🟠 **IMPORTANT - Email Notifications (Gmail)**
```bash
# Use Gmail App Password (not regular password)
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

### 🔵 **OPTIONAL - SMS Features (RingCentral)**
```bash
# Get from: https://developers.ringcentral.com/
RINGCENTRAL_CLIENT_ID=your_client_id
RINGCENTRAL_CLIENT_SECRET=your_client_secret
RINGCENTRAL_JWT_TOKEN=your_jwt_token
```

---

## **QUICK SETUP COMMANDS**

```bash
# 1. Start Database Services
docker-compose up -d postgres redis

# 2. Install Dependencies  
npm install && pip install -r requirements.txt

# 3. Setup Frontend Dependencies
cd apps/customer && npm install && cd ../..
cd apps/admin && npm install && cd ../..

# 4. Run Database Migrations
cd apps/api && alembic upgrade head && cd ../..

# 5. Start All Services
./scripts/start-local.sh
```

---

## **TEST URLs**

- **Customer App**: http://localhost:3000
- **Admin Dashboard**: http://localhost:3001  
- **API Backend**: http://localhost:8000
- **AI API**: http://localhost:8002
- **API Docs**: http://localhost:8000/docs

---

## **TEST PAYMENT CARD**

- **Card Number**: 4242 4242 4242 4242
- **Expiry**: Any future date
- **CVC**: Any 3 digits

---

## **MINIMAL .env FILES NEEDED**

1. `apps/customer/.env.local` - Frontend config + public Stripe key
2. `apps/admin/.env.local` - Admin frontend config  
3. `apps/api/.env` - Backend API + secret Stripe key + email config
4. `apps/ai-api/.env` - OpenAI key for AI features

See `LOCAL_DEVELOPMENT_SETUP.md` for complete templates.