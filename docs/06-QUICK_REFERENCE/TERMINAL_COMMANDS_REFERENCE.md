# Terminal Commands Reference

## Currently Running Services

### Terminal 1: Backend API (Port 8000)

```powershell
Set-Location "C:\Users\surya\projects\MH webapps\apps\backend"
& "C:\Users\surya\projects\MH webapps\.venv\Scripts\Activate.ps1"
$env:PYTHONPATH="src"
uvicorn api.app.main:app --reload --port 8000 --host 0.0.0.0
```

**Terminal ID**: bf2c1b44-2b1f-4483-8543-47ddbd8aa4c8  
**Status**: ✅ Running  
**URL**: http://localhost:8000

### Terminal 2: Customer Frontend (Port 3000)

```powershell
Set-Location "C:\Users\surya\projects\MH webapps\apps\customer"
npm run dev
```

**Terminal ID**: 13e5dfc0-9012-4e5e-9419-ab1ae216582c  
**Status**: ✅ Running  
**URL**: http://localhost:3000

### Terminal 3: Admin Frontend (Port 3001)

```powershell
Set-Location "C:\Users\surya\projects\MH webapps\apps\admin"
npm run dev
```

**Terminal ID**: 5326cd9b-c864-4a9a-91fb-7961f8e5ee56  
**Status**: ✅ Running  
**URL**: http://localhost:3001

---

## How to Stop Services

Press `CTRL+C` in each terminal window to stop the respective service.

---

## How to Restart Services

If any service crashes or you need to restart:

1. Press `CTRL+C` to stop the service
2. Press `↑` (up arrow) to recall the last command
3. Press `Enter` to restart

---

## Database Commands

### Connect to PostgreSQL:

```powershell
psql -U myhibachi_user -d myhibachi_platform
```

### Check migrations:

```powershell
Set-Location "C:\Users\surya\projects\MH webapps\apps\backend"
& "C:\Users\surya\projects\MH webapps\.venv\Scripts\Activate.ps1"
alembic current
alembic history
```

### Run migrations:

```powershell
alembic upgrade head
```

---

## Useful Database Queries

### Check review system:

```sql
SELECT * FROM feedback.customer_reviews ORDER BY created_at DESC LIMIT 10;
SELECT * FROM feedback.discount_coupons ORDER BY created_at DESC LIMIT 10;
SELECT * FROM feedback.review_escalations ORDER BY created_at DESC LIMIT 10;
```

### Check QR tracking:

```sql
SELECT * FROM marketing.qr_codes;
SELECT * FROM marketing.qr_scans ORDER BY scanned_at DESC LIMIT 10;
```

### Check QR scan analytics:

```sql
SELECT
    qc.code,
    qc.type,
    qc.campaign_name,
    COUNT(qs.id) as total_scans,
    COUNT(DISTINCT qs.ip_address) as unique_scans,
    SUM(CASE WHEN qs.converted_to_booking THEN 1 ELSE 0 END) as conversions
FROM marketing.qr_codes qc
LEFT JOIN marketing.qr_scans qs ON qc.id = qs.qr_code_id
GROUP BY qc.id, qc.code, qc.type, qc.campaign_name
ORDER BY total_scans DESC;
```

---

## Clear Python Cache (if needed)

If you encounter import errors after code changes:

```powershell
Set-Location "C:\Users\surya\projects\MH webapps\apps\backend"
Remove-Item -Recurse -Force src\__pycache__, src\api\__pycache__, src\api\app\__pycache__, src\api\app\models\__pycache__, src\api\app\services\__pycache__, src\api\app\routers\__pycache__ -ErrorAction SilentlyContinue
Write-Host "Python cache cleared"
```

Then restart the backend server.

---

## Test API with curl

### Health check:

```powershell
curl http://localhost:8000/api/health
```

### Track QR scan:

```powershell
curl -X POST http://localhost:8000/api/qr/scan/BC001 -H "Content-Type: application/json" -d '{}'
```

### List QR codes:

```powershell
curl http://localhost:8000/api/qr/
```

---

## Browser Testing URLs

| Test               | URL                                  |
| ------------------ | ------------------------------------ |
| Customer Homepage  | http://localhost:3000                |
| Admin Dashboard    | http://localhost:3001                |
| API Documentation  | http://localhost:8000/docs           |
| API Health Check   | http://localhost:8000/api/health     |
| Review Page (test) | http://localhost:3000/review/test-id |
| QR Redirect Test   | http://localhost:3000/contact.html   |
| Contact Page       | http://localhost:3000/contact        |

---

## Development Tips

1. **Hot Reload**: All three services support hot reload - just save
   your files
2. **Logs**: Watch the terminal output for errors and API calls
3. **Database Changes**: After migration changes, restart backend
   server
4. **Frontend Changes**: Next.js will auto-reload in browser
5. **API Testing**: Use http://localhost:8000/docs for interactive
   testing

---

**All services are running in separate terminals as requested!** ✅
