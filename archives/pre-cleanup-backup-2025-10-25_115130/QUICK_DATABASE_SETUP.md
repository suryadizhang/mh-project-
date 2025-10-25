# Quick Start: Database Setup & Testing

**Goal:** Set up a local PostgreSQL database with test data so you can test and optimize your application.

**Time Required:** ~30 minutes

---

## 🚀 Quick Setup Steps

### **Step 1: Install PostgreSQL (5 minutes)**

```powershell
# Using Chocolatey (recommended)
choco install postgresql14 -y

# OR using winget
winget install PostgreSQL.PostgreSQL.14

# OR download installer from:
# https://www.postgresql.org/download/windows/
```

**During installation:**
- Port: `5432` (default)
- Password: Choose a secure password (remember this!)
- Locale: Default

---

### **Step 2: Create Database (2 minutes)**

```powershell
# Connect to PostgreSQL
psql -U postgres -h localhost

# In psql, run:
```

```sql
CREATE DATABASE myhibachi;
CREATE USER myhibachi_user WITH PASSWORD 'MySecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE myhibachi TO myhibachi_user;
ALTER DATABASE myhibachi OWNER TO myhibachi_user;
\c myhibachi
GRANT ALL ON SCHEMA public TO myhibachi_user;
\q
```

---

### **Step 3: Configure Environment (1 minute)**

```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"

# Create/edit .env file
notepad .env
```

**Add this to `.env`:**

```env
DATABASE_URL=postgresql://myhibachi_user:MySecurePassword123!@localhost:5432/myhibachi
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
```

---

### **Step 4: Run Migrations (2 minutes)**

```powershell
# Activate virtual environment
cd "c:\Users\surya\projects\MH webapps"
.\.venv\Scripts\Activate.ps1

# Navigate to backend
cd apps\backend

# Run migrations
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade -> xxxxx, create initial tables
```

---

### **Step 5: Install Dependencies for Seeding (1 minute)**

```powershell
# Install Faker for generating test data
pip install faker asyncpg

# Verify installation
python -c "import faker; print('✅ Faker installed')"
```

---

### **Step 6: Seed Test Data (5-10 minutes)**

```powershell
# Run seeding script
cd apps\backend
python scripts\seed_test_data.py
```

**Expected output:**
```
🌱 MyHibachi Test Data Seeding
⚠️  WARNING: This will add test data to your database.
🏢 Creating 10 stations...
✅ Created 10 stations
👥 Creating 1000 customers...
   Progress: 100/1000 customers created...
   ...
✅ Created 1000 customers
📅 Creating 5000 bookings...
   ...
✅ Created 5000 bookings
💳 Creating 3000 payments...
   ...
✅ Created 3000 payments
🎉 SEEDING COMPLETE!
```

---

### **Step 7: Verify Setup (2 minutes)**

```powershell
# Check row counts
psql -U myhibachi_user -d myhibachi -h localhost
```

```sql
SELECT 'stations' AS table, COUNT(*) FROM stations
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'bookings', COUNT(*) FROM bookings
UNION ALL SELECT 'payments', COUNT(*) FROM payments;
```

**Expected output:**
```
  table     | count
------------+-------
 stations   |    10
 customers  |  1000
 bookings   |  5000
 payments   |  3000
```

```sql
\q
```

---

### **Step 8: Start Backend Server (1 minute)**

```powershell
cd apps\backend
uvicorn api.app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

### **Step 9: Test API Endpoints (2 minutes)**

**In a new terminal:**

```powershell
# Test health check
curl http://localhost:8000/health

# Test bookings (cursor pagination)
curl "http://localhost:8000/api/bookings?limit=10" | jq

# Test payment analytics (CTE query)
curl "http://localhost:8000/api/payments/analytics?days=30" | jq

# Test booking KPIs (CTE query)
curl "http://localhost:8000/api/admin/kpis?days=30" | jq

# Test customer analytics
curl "http://localhost:8000/api/admin/customer-analytics?customer_id=1" | jq
```

**If you don't have `jq`, install it:**
```powershell
choco install jq
```

**Or just view raw JSON:**
```powershell
curl "http://localhost:8000/api/bookings?limit=10"
```

---

## ✅ Verification Checklist

- ✅ PostgreSQL service running
- ✅ Database `myhibachi` created
- ✅ User `myhibachi_user` has access
- ✅ All tables created (check with `\dt` in psql)
- ✅ Test data seeded (1000 customers, 5000 bookings, 3000 payments)
- ✅ Backend server starts without errors
- ✅ API endpoints return data

---

## 🧪 Now You Can Test & Optimize!

### **Test Cursor Pagination (MEDIUM #34 Phase 2)**

```powershell
# Get first page
curl "http://localhost:8000/api/bookings?limit=50"

# Get next page (use cursor from response)
curl "http://localhost:8000/api/bookings?cursor=CURSOR_VALUE&limit=50"

# Get previous page
curl "http://localhost:8000/api/bookings?cursor=CURSOR_VALUE&direction=prev&limit=50"
```

### **Test CTE Queries (MEDIUM #34 Phase 3)**

```powershell
# Payment analytics (should be ~10-15ms)
Measure-Command { curl "http://localhost:8000/api/payments/analytics?days=90" }

# Booking KPIs (should be ~12-17ms)
Measure-Command { curl "http://localhost:8000/api/admin/kpis?days=30" }

# Customer analytics (should be ~15-20ms)
Measure-Command { curl "http://localhost:8000/api/admin/customer-analytics?customer_id=1" }
```

### **Analyze Slow Queries (MEDIUM #35)**

**Enable query logging:**

```powershell
# Find postgresql.conf
psql -U postgres -c "SHOW config_file;"

# Edit it (example path)
notepad "C:\Program Files\PostgreSQL\14\data\postgresql.conf"
```

**Add these lines:**
```ini
log_min_duration_statement = 50  # Log queries > 50ms
log_statement = 'all'
```

**Restart PostgreSQL:**
```powershell
Restart-Service postgresql-x64-14
```

**View logs:**
```powershell
Get-Content "C:\Program Files\PostgreSQL\14\data\log\postgresql-*.log" -Tail 50
```

### **Add Indexes (MEDIUM #35)**

```powershell
# Create migration
alembic revision -m "add_performance_indexes"

# Edit migration file (see MEDIUM_35_DATABASE_INDEXES.md for full index list)

# Run migration
alembic upgrade head

# Verify indexes created
psql -U myhibachi_user -d myhibachi -h localhost -c "\di"
```

### **Benchmark Performance**

```powershell
# Load test with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/bookings?limit=50

# Expected with indexes:
# Requests per second: 200-500
# Time per request: 20-50ms (mean)
```

---

## 🔧 Troubleshooting

### **psql: command not found**

Add PostgreSQL to PATH:
```powershell
$env:Path += ";C:\Program Files\PostgreSQL\14\bin"
```

### **Connection refused**

Check if PostgreSQL is running:
```powershell
Get-Service postgresql*
Start-Service postgresql-x64-14
```

### **Password authentication failed**

Reset password:
```sql
-- As postgres user:
ALTER USER myhibachi_user WITH PASSWORD 'NewPassword123!';
```

Update `.env` with new password.

### **Alembic migration fails**

Check database connection:
```powershell
python -c "from sqlalchemy import create_engine; from dotenv import load_dotenv; import os; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); print('✅ Connected' if engine.connect() else '❌ Failed')"
```

### **Seeding script fails**

Ensure dependencies installed:
```powershell
pip install faker asyncpg sqlalchemy python-dotenv
```

Drop and recreate database:
```sql
DROP DATABASE myhibachi;
CREATE DATABASE myhibachi OWNER myhibachi_user;
```

Re-run migrations and seeding.

---

## 📚 Next Steps

1. **Manual Testing:** Test all optimized endpoints with real data
2. **Performance Analysis:** Enable query logging, identify slow queries
3. **Add Indexes:** Create indexes for frequently queried columns
4. **Load Testing:** Use Apache Bench to test under load
5. **Deploy to Plesk:** Follow `MEDIUM_31_QUICK_DEPLOYMENT_GUIDE.md`

---

## 📖 Related Documentation

- **Full Setup Guide:** `DATABASE_SETUP_GUIDE.md`
- **Index Strategy:** `MEDIUM_35_DATABASE_INDEXES.md`
- **Load Balancer:** `MEDIUM_31_QUICK_DEPLOYMENT_GUIDE.md`
- **Query Optimizations:** `MEDIUM_34_PHASE_3_QUERY_HINTS_COMPLETE.md`

---

**🎉 You're ready to test and optimize!**

*Total setup time: ~30 minutes*
