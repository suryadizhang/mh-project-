# GSM + Enhanced Variables System Test Plan

## 🧪 **Current Status Test**

You're now ready to test the hybrid system! Here's what we've
implemented:

### **✅ What's Ready:**

1. **GSM Client Library** (`libs/gsm-client/`) - Enterprise secret
   management
2. **Backend Integration** (`apps/backend/src/config/gsm-config.ts`) -
   Config loader with fallbacks
3. **Enhanced Super Admin UI**
   (`apps/admin/src/app/superadmin/variables/`) - Variable management
   interface
4. **GitHub Actions Workflow**
   (`.github/workflows/sync-gsm-to-vercel.yml`) - Automated
   deployments
5. **Secret Rotation Scripts** (`scripts/rotate-secret.sh`) -
   Production-ready rotation tools
6. **Variables API**
   (`apps/backend/src/api/superadmin/variables.py`) - RESTful variable
   management

### **🎯 What You Need To Do Next:**

## **Phase 1: Quick Test (5 minutes)**

### **Test 1: Performance Monitoring System**

Your current file shows excellent performance testing infrastructure.
Let's verify it works with GSM:

```bash
# Run your existing performance tests
cd apps/backend/tests
python test_performance_comprehensive.py -v -m performance

# This will test:
# ✅ API response times < 500ms
# ✅ Database queries < 100ms
# ✅ Concurrent request handling (50+ requests)
# ✅ Voice AI latency < 2s
# ✅ Memory usage under load
```

### **Test 2: Service Connectivity**

```bash
# Test your existing services
cd tests/production
python quick_service_test.py

# Should show:
# ✅ Main API (localhost:8003) - ONLINE
# ✅ AI API (localhost:8002) - ONLINE
# ✅ Admin Panel (localhost:3001) - ONLINE
# ✅ Customer App (localhost:3000) - ONLINE
```

### **Test 3: Variables UI (without GSM)**

```bash
# Start your admin panel
cd apps/admin
npm run dev

# Visit: http://localhost:3001/superadmin/variables
# Should show: Variable management interface with sample data
```

## **Phase 2: GSM Integration (15 minutes)**

### **Step 1: Create Secrets in Google Cloud Console**

In the Secret Manager page you have open, create these secrets:

```
Secret Name: prod-global-CONFIG_VERSION
Secret Value: 1

Secret Name: prod-global-STRIPE_SECRET_KEY
Secret Value: [your-stripe-secret-key]

Secret Name: prod-backend-api-JWT_SECRET
Secret Value: [generate-random-string]

Secret Name: prod-frontend-web-NEXT_PUBLIC_API_URL
Secret Value: http://localhost:8003
```

### **Step 2: Test GSM Access**

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"

# Test access (if you have gcloud installed)
chmod +x scripts/test-gsm-access.sh
./scripts/test-gsm-access.sh

# Should show:
# ✅ Authentication OK
# ✅ Project: your-project-id
# ✅ Testing prod-global-CONFIG_VERSION... OK
```

## **Phase 3: Full Integration (30 minutes)**

### **Step 1: Backend GSM Integration**

The backend will automatically try to load from GSM and fallback to
environment variables:

```bash
# Start backend with GSM integration
cd apps/backend/src
python main.py

# Check logs for:
# "🔑 Loading configuration from Google Secret Manager..."
# "✅ GSM configuration loaded (version: 1)"
# OR
# "📁 Using environment variable configuration (GSM unavailable)"
```

### **Step 2: Frontend Integration**

The GitHub Actions workflow will sync secrets to Vercel automatically
when you push:

```bash
# Make a test change to trigger deployment
echo "# GSM Test" >> apps/customer/README.md
git add apps/customer/README.md
git commit -m "test: trigger GSM sync workflow"
git push

# Check GitHub Actions for:
# ✅ Sync Customer Frontend - Success
# ✅ Fetch secrets from GSM - Success
# ✅ Update Vercel Environment Variables - Success
```

### **Step 3: Variable Management Integration**

```bash
# Test the Variables API
curl http://localhost:8003/api/superadmin/variables/

# Should return:
# [{"key":"BASE_PRICE_PER_PERSON","value":75,"type":"number",...}]

# Test bulk update
curl -X POST http://localhost:8003/api/superadmin/variables/bulk-update \
  -H "Content-Type: application/json" \
  -d '{"variables":[{"key":"BASE_PRICE_PER_PERSON","value":80}]}'
```

## **🔧 Troubleshooting**

### **If GSM Access Fails:**

```bash
# Check authentication
gcloud auth list

# Check project
gcloud config get-value project

# Check Secret Manager API is enabled
gcloud services list --enabled | grep secretmanager
```

### **If Backend Integration Fails:**

```bash
# Check environment variables
echo $GOOGLE_APPLICATION_CREDENTIALS
echo $GCP_PROJECT_ID

# Check service account file exists
ls -la path/to/service-account-key.json
```

### **If GitHub Actions Fails:**

1. Check GitHub Secrets are set correctly
2. Verify Vercel tokens are valid
3. Check repository permissions

## **🎯 Success Criteria**

### **✅ Immediate Success (No GSM required):**

- Performance tests pass
- Service connectivity works
- Variables UI loads with sample data
- Existing functionality unchanged

### **✅ GSM Integration Success:**

- Secrets accessible from Google Cloud Console
- Backend loads config from GSM + fallback
- Variables UI can sync to/from GSM
- GitHub Actions deploys with GSM secrets

### **✅ Full Hybrid Success:**

- Edit variables in Super Admin UI
- Changes sync to both local files AND GSM
- Config version increments automatically
- All services reload with new values
- Zero downtime secret updates

## **📊 What You'll Get**

### **Before (Current):**

- ❌ Manual environment variable management
- ❌ Secrets scattered across platforms
- ❌ No centralized variable management
- ❌ Manual rotation requires multiple steps

### **After (Hybrid System):**

- ✅ **One interface** to manage all 127+ variables
- ✅ **Enterprise secret management** with Google Secret Manager
- ✅ **Automatic synchronization** across all services
- ✅ **Zero-downtime updates** with config versioning
- ✅ **Production-ready rotation** with safety checks
- ✅ **Fallback to environment variables** for reliability

## **🚀 Ready to Test?**

Start with **Phase 1** (no GSM required) to verify your existing
system works perfectly with the enhanced variable management.

Then move to **Phase 2** when you're ready to add the enterprise GSM
layer.

The beauty is: **your existing system keeps working exactly as
before**, and you gain enterprise capabilities on top!

**Which phase would you like to test first?**
