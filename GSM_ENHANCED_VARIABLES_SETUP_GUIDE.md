# My Hibachi GSM + Enhanced Variables Setup Guide

## 🎯 Overview

You're getting **BOTH systems**:

1. **Google Secret Manager (GSM)** - Enterprise backend secret
   management
2. **Enhanced Super Admin Variables UI** - User-friendly frontend
   management
3. **Hybrid sync mechanisms** - Best of both worlds

## 📋 Your Action Checklist

### ✅ **Step 1: GCP Setup (5 minutes)**

1. **Go to Google Cloud Console**: https://console.cloud.google.com
2. **Create/Select Project**: `my-hibachi-prod`
3. **Enable Secret Manager API**:
   ```bash
   gcloud services enable secretmanager.googleapis.com
   ```
4. **Create Service Accounts**:

   **Backend Service Account**:

   ```bash
   gcloud iam service-accounts create gsm-backend-reader \
     --display-name="GSM Backend Reader" \
     --description="Service account for backend services to read secrets"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:gsm-backend-reader@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"

   gcloud iam service-accounts keys create gsm-backend-reader-key.json \
     --iam-account="gsm-backend-reader@YOUR_PROJECT_ID.iam.gserviceaccount.com"
   ```

   **CI/CD Service Account**:

   ```bash
   gcloud iam service-accounts create gsm-ci-sync \
     --display-name="GSM CI Sync" \
     --description="Service account for GitHub Actions to sync secrets"

   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:gsm-ci-sync@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"

   gcloud iam service-accounts keys create gsm-ci-sync-key.json \
     --iam-account="gsm-ci-sync@YOUR_PROJECT_ID.iam.gserviceaccount.com"
   ```

### ✅ **Step 2: GitHub Secrets Setup**

Add these to your GitHub repository → Settings → Secrets and variables
→ Actions:

```bash
# Base64 encode the CI service account key
base64 -w 0 gsm-ci-sync-key.json
```

**GitHub Secrets to Add**:

- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_SERVICE_ACCOUNT_KEY_B64`: Base64 encoded `gsm-ci-sync-key.json`
- `VERCEL_TOKEN`: Your Vercel API token
- `VERCEL_ORG_ID`: Your Vercel organization ID
- `VERCEL_PROJECT_ID_CUSTOMER`: Customer frontend project ID
- `VERCEL_PROJECT_ID_ADMIN`: Admin frontend project ID

### ✅ **Step 3: VPS/Plesk Backend Setup**

1. **Upload Service Account Key**:

   ```bash
   # Upload gsm-backend-reader-key.json to your VPS
   scp gsm-backend-reader-key.json user@your-vps:/opt/myhibachi/config/
   ```

2. **Set Environment Variable** (in your systemd service or Plesk
   config):

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/opt/myhibachi/config/gsm-backend-reader-key.json"
   export GCP_PROJECT_ID="your-project-id"
   ```

3. **Install Dependencies**:
   ```bash
   # In your backend directory
   npm install @google-cloud/secret-manager
   # OR for Python
   pip install google-cloud-secret-manager
   ```

### ✅ **Step 4: Initialize Secrets in GSM**

Use the rotation script I created:

```bash
# Make script executable
chmod +x scripts/rotate-secret.sh

# Set your project ID
export GCP_PROJECT_ID="your-project-id"

# Create initial secrets (you'll be prompted for values)
./scripts/rotate-secret.sh --interactive prod-global-STRIPE_SECRET_KEY
./scripts/rotate-secret.sh --interactive prod-global-OPENAI_API_KEY
./scripts/rotate-secret.sh --interactive prod-backend-api-DB_URL
./scripts/rotate-secret.sh --interactive prod-backend-api-JWT_SECRET

# Set initial config version
echo "1" | ./scripts/rotate-secret.sh --from-file /dev/stdin prod-global-CONFIG_VERSION
```

---

## 🚀 What I've Implemented For You

### **1. GSM Client Library** (`libs/gsm-client/`)

- **Enterprise-grade secret management**
- **Automatic fallback** to environment variables
- **Caching and performance optimization**
- **Config versioning** for automatic reloads
- **TypeScript with full type safety**

**Usage Example**:

```typescript
import { createBackendAPIClient } from '../libs/gsm-client/src/index';

// In your backend startup
const gsmClient = createBackendAPIClient('prod');
const secrets = await gsmClient.getAllServiceSecrets();

// Access secrets
const dbUrl = await gsmClient.getSecret('DB_URL');
const jwtSecret = await gsmClient.getSecret('JWT_SECRET');
```

### **2. Backend Config Loader** (`apps/backend/src/config/gsm-config.ts`)

- **Automatic environment detection**
- **Graceful fallback** to existing .env files
- **Background config monitoring** (checks for updates every 5
  minutes)
- **Feature flag management**

**Usage Example**:

```typescript
import {
  loadConfig,
  getConfig,
  startConfigMonitoring,
} from './config/gsm-config';

// At app startup
await loadConfig();
startConfigMonitoring(); // Background updates

// Use throughout your app
const config = getConfig();
console.log('DB URL:', config.DB_URL);
console.log('AI V3 Enabled:', config.FF_ENABLE_AI_BOOKING_V3);
```

### **3. GitHub Actions Workflow** (`.github/workflows/sync-gsm-to-vercel.yml`)

- **Automatic deployment** on main/dev branch pushes
- **Reads secrets from GSM** based on environment
- **Updates Vercel env vars** automatically
- **Deploys both customer and admin** frontends

**Triggers on**:

- Push to `main` → Production deployment with prod secrets
- Push to `dev` → Preview deployment with dev secrets
- Manual trigger via GitHub UI

### **4. Enhanced Super Admin Variables UI**

- **Real-time variable editing** with type safety
- **Category filtering** (Pricing, Business, Features, etc.)
- **Priority-based organization** (Critical, High, Medium, Low)
- **Pending changes tracking** with visual indicators
- **Security masking** for sensitive variables

**Access**: `https://your-admin-domain.com/superadmin/variables`

### **5. Variables Management API** (`apps/backend/src/api/superadmin/variables.py`)

- **RESTful API** for variable CRUD operations
- **Bulk update support** for efficiency
- **GSM sync endpoints** (to/from cloud)
- **Config version management** for triggered reloads
- **File-based fallback** for existing workflow

### **6. Secret Rotation Scripts** (`scripts/rotate-secret.sh`)

- **Production-ready rotation** with safety checks
- **Interactive mode** for secure value entry
- **Automatic config version** increment for critical secrets
- **Verification and backup** options
- **Detailed post-rotation instructions**

---

## 🔄 How The Hybrid System Works

### **Development Workflow**:

1. **Edit variables** in Super Admin UI
2. **Changes saved** to both local files AND GSM
3. **Config version incremented** automatically
4. **All services reload** with new values
5. **Zero downtime** secret updates

### **Production Workflow**:

1. **Secrets stored** in GSM as source of truth
2. **Backends read** from GSM with local fallback
3. **Frontends sync** via GitHub Actions → Vercel
4. **Rotation scripts** for secure updates
5. **Automatic monitoring** for config changes

### **Emergency Fallback**:

- If GSM is down, services use environment variables
- If sync fails, manual deployment still works
- If GitHub Actions fails, Vercel CLI can be used
- All critical values have local backups

---

## 🧪 Testing Your Setup

### **Test Backend GSM Integration**:

```bash
cd apps/backend
npm run dev

# Check logs for:
# "✅ Configuration loaded successfully"
# "📊 Config version: 1"
# "🚀 Feature flags: AI_V3=true, Travel_V2=false"
```

### **Test Secret Rotation**:

```bash
# Test increment config version
./scripts/rotate-secret.sh --interactive prod-global-CONFIG_VERSION

# Check backend logs for:
# "🔄 Config version changed, reloading..."
```

### **Test GitHub Actions**:

1. Make a change to `apps/customer/`
2. Commit and push to `dev` branch
3. Check Actions tab for successful workflow
4. Verify Vercel preview deployment

### **Test Super Admin UI**:

1. Go to `http://localhost:3001/superadmin/variables`
2. Edit a non-critical variable
3. Save changes
4. Verify backend logs show reload

---

## 🔒 Security Best Practices

### **Secret Rotation Schedule**:

- **Critical secrets** (Stripe, DB): Every 90 days
- **API keys** (OpenAI, Maps): Every 6 months
- **Internal secrets** (JWT): Every year
- **Emergency rotation**: Immediately if compromised

### **Access Control**:

- **GSM secrets**: Only service accounts can access
- **GitHub secrets**: Only admins can modify
- **Super Admin UI**: Role-based access control
- **Rotation scripts**: Require authentication

### **Monitoring**:

- **Secret access** logged in GCP
- **Config changes** logged in application
- **Failed secret loads** trigger alerts
- **Unusual access patterns** monitored

---

## 📊 Cost Estimate

**Google Secret Manager**:

- **Secret storage**: $0.06 per secret per month
- **Secret access**: $0.03 per 10,000 accesses
- **Your estimated cost**: ~$1-2/month for 30 secrets

**Total Additional Infrastructure**: ~$1-2/month

**Time Savings**: ~10 hours/month (no manual secret sync) **Risk
Reduction**: Massive (centralized, audited, encrypted)

---

## 🎯 Next Steps

1. **Complete your GCP setup** (Steps 1-3 above)
2. **Test the system** with non-critical secrets first
3. **Migrate critical secrets** (Stripe, DB, etc.) gradually
4. **Set up rotation schedule** for ongoing maintenance
5. **Train your team** on the new workflow

The system is designed to work alongside your existing setup, so you
can migrate gradually and always fall back to environment variables if
needed.

**Ready to proceed?** Let me know when you've completed the GCP setup
and I'll help you test the first secret migration!

---

## 📞 Support

If you run into any issues:

1. Check the **troubleshooting section** in each component's README
2. Review **application logs** for specific error messages
3. Verify **service account permissions** in GCP console
4. Test **basic gcloud commands** for connectivity

The system is built with extensive error handling and fallbacks to
ensure reliability even during the migration process.
