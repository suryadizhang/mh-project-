# 🍱 My Hibachi - Stripe Integration Backend (FastAPI)

Production-ready Stripe integration for My Hibachi catering services
with comprehensive payment processing, customer management, and
analytics.

## 🚀 Features

- **Complete Stripe Integration**: Checkout, Payment Intents, Customer
  Portal, Webhooks
- **Payment Flows**: Deposits, balance collection, add-ons, full
  purchases
- **Customer Management**: Automatic Stripe customer creation,
  analytics tracking
- **Invoice & Quote System**: Hosted invoices, quote generation and
  acceptance
- **Refund & Dispute Handling**: Admin refund processing, dispute
  tracking
- **Analytics Dashboard**: Payment analytics, customer insights,
  revenue tracking
- **Tax Integration**: Automatic tax calculation (configurable)
- **Comprehensive Logging**: Webhook audit trail, payment tracking

## 🏗️ Architecture

- **FastAPI**: Modern Python web framework with automatic OpenAPI docs
- **PostgreSQL**: Primary database with async support
- **SQLAlchemy**: ORM with async support and Alembic migrations
- **Stripe Python SDK**: Official Stripe integration
- **Pydantic**: Data validation and serialization
- **JWT Authentication**: Secure API access (integrates with existing
  auth)

## 📋 Requirements

- Python 3.11+
- PostgreSQL 12+
- Stripe Account (test/live)
- Redis (optional, for caching)

## 🔧 Environment Setup

### 1. Clone and Setup

```bash
cd myhibachi-backend-fastapi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required Configuration:**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/myhibachi_db
DATABASE_URL_SYNC=postgresql://<username>:<password>@localhost:5432/myhibachi_db

# Stripe (Get from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_your_test_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_publishable_key_here

# Security
SECRET_KEY=your-super-secret-jwt-key-here-change-in-production
```

### 3. Database Setup

```bash
# Create database
createdb myhibachi_db

# Run migrations
alembic upgrade head

# Setup Stripe products (development only)
python -c "
from utils.stripe_setup import setup_stripe_products
import asyncio
asyncio.run(setup_stripe_products())
"
```

### 4. Start Development Server

```bash
uvicorn src.main:app --reload --port 8000
```

API Documentation: http://localhost:8000/docs

## 🧪 Testing Setup

### Stripe CLI Setup

1. **Install Stripe CLI**: https://stripe.com/docs/stripe-cli
2. **Login**: `stripe login`
3. **Forward webhooks**:
   ```bash
   stripe listen --forward-to localhost:8000/api/stripe/webhook
   ```
   Copy the webhook secret to your `.env` file.

### Test Cards

- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **3D Secure**: 4000 0027 6000 3184
- **Insufficient Funds**: 4000 0000 0000 9995

## 📊 Database Schema

### Core Tables

- **customers**: User-Stripe customer mapping with analytics
- **payments**: All payment records (Stripe, Zelle, Venmo)
- **invoices**: Balance collection and hosted invoices
- **products/prices**: Stripe product/price mirrors
- **webhook_events**: Webhook audit trail
- **refunds**: Refund tracking
- **disputes**: Dispute management

### Key Relationships

```mermaid
graph TD
    A[customers] --> B[payments]
    A --> C[invoices]
    B --> D[refunds]
    B --> E[disputes]
    F[products] --> G[prices]
    H[webhook_events] --> I[Event Processing]
```

## 🔗 API Endpoints

### Stripe Integration

- `POST /api/stripe/create-checkout-session` - Create Checkout session
- `POST /api/stripe/create-payment-intent` - Create Payment Intent
- `POST /api/stripe/portal-link` - Customer portal access
- `POST /api/stripe/webhook` - Webhook handler
- `POST /api/stripe/refund` - Process refunds (admin)
- `GET /api/stripe/payments` - List payments
- `GET /api/stripe/invoices` - List invoices
- `GET /api/stripe/analytics/payments` - Payment analytics (admin)

### Authentication

- `GET /api/auth/me` - Current user info
- `POST /api/auth/login` - Login (placeholder)
- `POST /api/auth/logout` - Logout (placeholder)

### Bookings

- `GET /api/bookings` - List bookings
- `GET /api/bookings/{id}` - Get booking details
- `POST /api/bookings` - Create booking
- `PUT /api/bookings/{id}` - Update booking

## 🎯 Payment Flows

### 1. Booking Deposit Flow

```python
# Frontend calls
checkout_session = await client.post("/api/stripe/create-checkout-session", {
    "booking_id": "booking-123",
    "line_items": [
        {"name": "Booking Deposit", "amount": 10000, "quantity": 1}  # $100
    ],
    "mode": "payment"
})

# Redirect to checkout_session.url
# On success, webhook processes payment
```

### 2. Payment Element Flow

```python
# Create payment intent
intent = await client.post("/api/stripe/create-payment-intent", {
    "booking_id": "booking-123",
    "amount": 10000,  # $100 in cents
    "payment_type": "deposit"
})

# Use intent.client_secret with Stripe Elements
# Confirm payment on frontend
```

### 3. Balance Collection

```python
# Create invoice for remaining balance
invoice = stripe.Invoice.create(
    customer=customer_id,
    collection_method="send_invoice",
    days_until_due=7
)

# Invoice payment triggers webhook
```

## 🔧 Webhook Events Handled

- **checkout.session.completed** - Checkout payment success
- **payment_intent.succeeded** - Payment success
- **payment_intent.payment_failed** - Payment failure
- **payment_intent.canceled** - Payment cancellation
- **invoice.payment_succeeded** - Invoice payment
- **invoice.payment_failed** - Invoice payment failure
- **customer.created** - Customer creation
- **charge.dispute.created** - Dispute creation
- **customer.subscription.\*** - Subscription events (future)

## 🏃‍♂️ Smoke Test Plan

### Prerequisites

```bash
# 1. Start servers
uvicorn src.main:app --reload --port 8000
cd ../myhibachi-frontend && npm run dev

# 2. Start webhook forwarding
stripe listen --forward-to localhost:8000/api/stripe/webhook
```

### Test Scenario

1. **Create Test Booking**

   ```bash
   curl -X POST http://localhost:8000/api/bookings \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer dev-token" \
     -d '{
       "date": "2024-12-25",
       "time": "18:00",
       "guests": 8,
       "menu": "adult",
       "location": "123 Main St, San Jose, CA"
     }'
   ```

2. **Start Checkout Session**

   ```bash
   curl -X POST http://localhost:8000/api/stripe/create-checkout-session \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer dev-token" \
     -d '{
       "booking_id": "booking-123",
       "line_items": [
         {"name": "Booking Deposit", "amount": 10000, "quantity": 1}
       ]
     }'
   ```

3. **Complete Payment**
   - Visit checkout URL
   - Use card: 4242 4242 4242 4242
   - Complete payment

4. **Verify Webhook Processing**

   ```bash
   # Check webhook events
   curl http://localhost:8000/api/stripe/payments?booking_id=booking-123 \
     -H "Authorization: Bearer dev-token"
   ```

5. **Admin Panel Verification**

   ```bash
   # View payment in admin
   curl http://localhost:8000/api/stripe/analytics/payments \
     -H "Authorization: Bearer admin-token"
   ```

6. **Test Refund**

   ```bash
   curl -X POST http://localhost:8000/api/stripe/refund \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer admin-token" \
     -d '{
       "payment_id": "payment-123",
       "amount": 50.00,
       "reason": "customer_request"
     }'
   ```

7. **Verify Refund Webhook**
   - Check that refund webhook updates payment status
   - Verify refund record creation

## 🛠️ Development Tools

### CLI Commands

```bash
# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1

# Setup Stripe products
python -c "from utils.stripe_setup import setup_stripe_products; import asyncio; asyncio.run(setup_stripe_products())"

# Create test data
python -c "from utils.stripe_setup import create_test_data; print(create_test_data())"

# Code formatting
black src/
flake8 src/

# Type checking
mypy src/
```

### Testing

```bash
# Run tests
pytest

# Test with coverage
pytest --cov=app tests/

# Test specific webhook events
stripe trigger payment_intent.succeeded
stripe trigger customer.created
```

## 🚨 Common Issues & Solutions

### 1. Webhook Signature Verification Failed

```bash
# Check webhook secret matches
echo $STRIPE_WEBHOOK_SECRET

# Verify webhook endpoint URL
stripe listen --print-secret
```

### 2. Database Connection Issues

```bash
# Check database is running
pg_isready -h localhost -p 5432

# Verify connection string
psql $DATABASE_URL_SYNC
```

### 3. Stripe API Key Issues

```bash
# Test API key
stripe customers list --api-key $STRIPE_SECRET_KEY
```

## 🔒 Security Best Practices

1. **Environment Variables**: Never commit secrets to git
2. **Webhook Verification**: Always verify webhook signatures
3. **Idempotency**: Use idempotency keys for critical operations
4. **Input Validation**: Validate all user inputs with Pydantic
5. **Rate Limiting**: Implement rate limiting for public endpoints
6. **HTTPS Only**: Use HTTPS in production
7. **Admin Routes**: Protect admin routes with proper authentication

## 🚀 Production Deployment

### Environment Checklist

- [ ] Update all environment variables for production
- [ ] Set `ENVIRONMENT=production`
- [ ] Use live Stripe keys
- [ ] Configure production database
- [ ] Set up proper webhook endpoint
- [ ] Enable automatic tax if required
- [ ] Configure email service
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up SSL certificates

### Go-Live Checklist

- [ ] Test all payment flows in production
- [ ] Verify webhook delivery
- [ ] Test refund process
- [ ] Check admin panel access
- [ ] Verify customer portal
- [ ] Test dispute handling
- [ ] Monitor error rates
- [ ] Set up alerts

## 📞 Support

For issues and questions:

- Check API documentation at `/docs`
- Review webhook events in Stripe Dashboard
- Check application logs
- Verify environment configuration

## 📈 Monitoring & Analytics

The system provides comprehensive analytics:

- Payment success/failure rates
- Customer lifetime value
- Payment method preferences
- Revenue trends
- Dispute rates
- Refund patterns

Access analytics via `/api/stripe/analytics/payments` (admin only).
