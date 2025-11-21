# Google Cloud CLI Setup Commands

# Run these commands after installing gcloud

# 1. Initialize gcloud and authenticate

gcloud init

# 2. Set your project

gcloud config set project my-hibachi-crm

# 3. Enable Secret Manager API

gcloud services enable secretmanager.googleapis.com

# 4. Test authentication

gcloud auth list

# 5. Test Secret Manager access

gcloud secrets list

# 6. Once setup is complete, run the secrets creation script

bash scripts/create-gsm-secrets.sh
