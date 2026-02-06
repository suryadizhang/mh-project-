# Database Setup Guide - Local Development

**Purpose:** Set up a local PostgreSQL database with realistic test
data for development and testing.

**Date:** October 20, 2025  
**Status:** Ready to Execute

---

## 📋 Table of Contents

1. [Install PostgreSQL](#install-postgresql)
2. [Create Database](#create-database)
3. [Configure Environment](#configure-environment)
4. [Run Migrations](#run-migrations)
5. [Seed Test Data](#seed-test-data)
6. [Verify Setup](#verify-setup)
7. [Troubleshooting](#troubleshooting)

---

## 🐘 Install PostgreSQL

### **Windows (Recommended: PostgreSQL 14+)**

**Option 1: Official Installer (Recommended)**

```powershell
# Download installer from:
# https://www.postgresql.org/download/windows/

# Or use Chocolatey:
choco install postgresql14 -y

# Or use winget:
winget install PostgreSQL.PostgreSQL.14
```

**After Installation:**

1. Default port: `5432`
2. Default user: `postgres`
3. You'll be prompted to set a password during installation (remember
   this!)
4. pgAdmin 4 is included for GUI management

**Option 2: Docker (Alternative)**

```powershell
# Pull PostgreSQL image
docker pull postgres:14

# Run container
docker run --name myhibachi-postgres `
  -e POSTGRES_PASSWORD=yourpassword `
  -e POSTGRES_DB=myhibachi `
  -p 5432:5432 `
  -d postgres:14

# Verify it's running
docker ps
```

---

## 🗄️ Create Database

### **Method 1: Using psql (Command Line)**

```powershell
# Connect to PostgreSQL as postgres user
# Enter password when prompted
psql -U postgres -h localhost

# In psql shell:
CREATE DATABASE myhibachi;
CREATE USER myhibachi_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE myhibachi TO myhibachi_user;
ALTER DATABASE myhibachi OWNER TO myhibachi_user;

# Connect to new database
\c myhibachi

# Grant schema privileges
GRANT ALL ON SCHEMA public TO myhibachi_user;

# Exit
\q
```

### **Method 2: Using pgAdmin 4 (GUI)**

1. Open pgAdmin 4
2. Right-click **Databases** → **Create** → **Database**
3. Name: `myhibachi`
4. Owner: Create new user `myhibachi_user` or use existing
5. Save

---

## ⚙️ Configure Environment

### **Create/Update `.env` File**

```powershell
# Navigate to backend directory
cd "c:\Users\surya\projects\MH webapps\apps\backend"

# Create .env file (or update existing)
@"
# Database Configuration
DATABASE_URL=postgresql://myhibachi_user:your_secure_password_here@localhost:5432/myhibachi

# Redis Configuration (optional for now)
REDIS_URL=redis://localhost:6379/0

# Application Settings
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# CORS Settings
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO

# Stripe (test keys for development)
STRIPE_SECRET_KEY=sk_test_your_test_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Email (optional for testing)
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your_mailtrap_user
SMTP_PASSWORD=your_mailtrap_password
"@ | Out-File -FilePath .env -Encoding utf8
```

**Important:** Replace `your_secure_password_here` with the actual
password you set for `myhibachi_user`.

---

## 🔄 Run Migrations

### **Install Alembic (if not already installed)**

```powershell
# Activate virtual environment
cd "c:\Users\surya\projects\MH webapps"
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r apps\backend\requirements.txt
```

### **Run Migrations**

```powershell
# Navigate to backend directory
cd apps\backend

# Check Alembic status
alembic current

# Run all migrations
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade -> xxxxx, create initial tables
# INFO  [alembic.runtime.migration] Running upgrade xxxxx -> yyyyy, add new columns
# ... (multiple migration steps)
```

### **Verify Tables Created**

```powershell
# Connect to database
psql -U myhibachi_user -d myhibachi -h localhost

# List all tables
\dt

# Expected tables:
# - alembic_version
# - users
# - customers
# - stations
# - bookings
# - payments
# - stripe_customers
# - stripe_payment_intents
# - (other tables based on your schema)

# Exit
\q
```

---

## 🌱 Seed Test Data

I've created a comprehensive data seeding script. Let's create it:

### **Create Data Seeding Script**

See `apps/backend/scripts/seed_test_data.py` (created below)

### **Run Seeding Script**

```powershell
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd apps\backend

# Run seeding script
python scripts\seed_test_data.py

# Expected output:
# 🌱 Starting database seeding...
# ✅ Created 10 stations
# ✅ Created 1000 customers
# ✅ Created 5000 bookings
# ✅ Created 3000 payments
# 🎉 Seeding complete!
```

### **What Data Gets Seeded?**

| Entity                     | Count | Details                                   |
| -------------------------- | ----- | ----------------------------------------- |
| **Stations**               | 10    | Different locations with addresses        |
| **Customers**              | 1,000 | Realistic names, emails, phones           |
| **Bookings**               | 5,000 | Mix of statuses, dates (last 2 years)     |
| **Payments**               | 3,000 | Associated with bookings, various amounts |
| **Stripe Customers**       | 1,000 | One per customer                          |
| **Stripe Payment Intents** | 3,000 | One per payment                           |

---

## ✅ Verify Setup

### **1. Check Database Connection**

```powershell
# Test connection from Python
python -c "from sqlalchemy import create_engine; from dotenv import load_dotenv; import os; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); print('✅ Database connection successful!' if engine.connect() else '❌ Connection failed')"
```

### **2. Check Row Counts**

```sql
-- Connect to database
psql -U myhibachi_user -d myhibachi -h localhost

-- Count rows in each table
SELECT 'stations' AS table_name, COUNT(*) AS row_count FROM stations
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'bookings', COUNT(*) FROM bookings
UNION ALL
SELECT 'payments', COUNT(*) FROM payments;

-- Expected output:
--  table_name | row_count
-- ------------+-----------
--  stations   |        10
--  customers  |      1000
--  bookings   |      5000
--  payments   |      3000
```

### **3. Test API Endpoints**

```powershell
# Start backend server
cd apps\backend
uvicorn api.app.main:app --reload --port 8000

# In another terminal, test endpoints:

# Health check
curl http://localhost:8000/health

# Get bookings (should return data with cursor pagination)
curl http://localhost:8000/api/bookings?limit=10

# Payment analytics (optimized CTE query)
curl http://localhost:8000/api/payments/analytics

# Booking KPIs (optimized CTE query)
curl http://localhost:8000/api/admin/kpis

# Customer analytics (optimized CTE query)
curl "http://localhost:8000/api/admin/customer-analytics?customer_id=1"
```

---

## 🔧 Troubleshooting

### **Issue: `psql: FATAL: password authentication failed`**

**Solution:**

1. Reset password:
   ```sql
   ALTER USER myhibachi_user WITH PASSWORD 'new_password';
   ```
2. Update `.env` with new password
3. Verify `pg_hba.conf` allows password authentication

### **Issue: `psql: could not connect to server: Connection refused`**

**Solution:**

1. Check if PostgreSQL is running:

   ```powershell
   # Check service status
   Get-Service postgresql*

   # Start service if stopped
   Start-Service postgresql-x64-14
   ```

2. Verify port 5432 is not blocked by firewall

### **Issue: Alembic migration fails**

**Solution:**

1. Check database connection in `.env`
2. Verify database exists:
   ```sql
   \l  -- List all databases
   ```
3. Check Alembic configuration:
   ```powershell
   cat alembic.ini | Select-String "sqlalchemy.url"
   ```

### **Issue: Seeding script fails with foreign key errors**

**Solution:**

1. Drop all tables and re-run migrations:

   ```sql
   -- Connect to database
   \c myhibachi

   -- Drop all tables (DESTRUCTIVE!)
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   GRANT ALL ON SCHEMA public TO myhibachi_user;
   ```

2. Re-run migrations:

   ```powershell
   alembic upgrade head
   ```

3. Re-run seeding script

### **Issue: Import errors in seeding script**

**Solution:**

```powershell
# Ensure all dependencies are installed
pip install faker python-dotenv sqlalchemy asyncpg psycopg2-binary

# If using asyncio, install:
pip install asyncio
```

---

## 📊 Next Steps After Setup

1. **Test Optimized Endpoints** (MEDIUM #34):
   - Run queries and measure response times
   - Verify cursor pagination works bidirectionally
   - Test CTE queries return correct data

2. **Analyze Query Performance** (MEDIUM #35):
   - Enable PostgreSQL slow query log
   - Identify queries > 50ms
   - Use `EXPLAIN ANALYZE` to find bottlenecks

3. **Add Database Indexes** (MEDIUM #35):
   - Create indexes for frequently queried columns
   - Add composite indexes for multi-column filters
   - Measure performance improvements

4. **Load Testing**:
   - Use Apache Bench to test under load
   - Verify 15-25x performance improvements hold
   - Test with 100+ concurrent users

---

## 🎯 Quick Command Reference

```powershell
# Start PostgreSQL service
Start-Service postgresql-x64-14

# Stop PostgreSQL service
Stop-Service postgresql-x64-14

# Connect to database
psql -U myhibachi_user -d myhibachi -h localhost

# Run migrations
cd apps\backend; alembic upgrade head

# Seed data
cd apps\backend; python scripts\seed_test_data.py

# Start backend server
cd apps\backend; uvicorn api.app.main:app --reload --port 8000

# View logs
Get-Content -Path "C:\Program Files\PostgreSQL\14\data\log\postgresql-*.log" -Tail 50
```

---

## 📚 Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/14/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Faker Documentation](https://faker.readthedocs.io/)

---

_Last Updated: October 20, 2025_
