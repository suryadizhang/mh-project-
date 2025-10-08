# My Hibachi Chef CRM - Sensitive Data Policy

## 🚨 CRITICAL SECURITY GUIDELINES

This document outlines what data **MUST NEVER** be committed to version control and what is safe to include in public repositories.

## ❌ NEVER COMMIT THESE (SECURITY VIOLATIONS)

### 🔐 Business Sensitive Information
- **EIN (Employer Identification Number)**: `39-2675702` - NEVER show publicly
- **Full Business Address**: `47481 Towhee Street, Fremont, CA 94538` - NEVER show publicly
- **Personal Gmail addresses**: Use business email only

### 🔑 API Keys & Secrets
- OpenAI API keys (`sk-proj-*`, `sk-*`)
- RingCentral credentials (client ID, secret, JWT tokens)
- Stripe keys (live keys, webhook secrets)
- Database passwords and connection strings
- Encryption keys
- JWT secrets
- OAuth tokens
- Webhook secrets

### 💳 Payment Information
- Credit card numbers
- Bank account information
- Payment processor secrets
- Financial transaction data

### 📧 Personal Information (PII)
- Customer email addresses (except when encrypted)
- Phone numbers (except business phone)
- Personal addresses
- Social security numbers
- Driver's license numbers

## ✅ SAFE TO INCLUDE PUBLICLY

### 🏢 Business Information
- Business name: `my Hibachi LLC`
- Business email: `cs@myhibachichef.com`
- Business phone: `+19167408768`
- City/state: `Fremont, California`
- Service areas: `Sacramento, Bay Area, Central Valley`
- Business type: Private chef catering

### 🔧 Technical Configuration
- Server hostnames (without credentials)
- Port numbers (standard ports)
- Public API endpoints
- Database schema (without data)
- Environment variable names (without values)
- Rate limiting configurations

### 📋 Application Metadata
- Version numbers
- Feature descriptions
- Architecture diagrams
- Documentation
- Code structure

## 🛡️ SECURE STORAGE REQUIREMENTS

### Environment Variables
All secrets MUST be stored in environment variables:

```bash
# ❌ WRONG - Never in code
STRIPE_SECRET_KEY = "sk_live_abc123"

# ✅ CORRECT - Environment variable
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
```

### File Locations
- **Development secrets**: `config/environments/secrets/.secrets.local` (gitignored)
- **Production secrets**: Environment variables on server
- **Templates**: `config/environments/.env.*.template` (no actual values)

### Git Configuration
Ensure these patterns are in `.gitignore`:
```
.secrets
.secrets.*
*.pem
*.key
config/environments/secrets/
.env
.env.*
!.env.example
!.env.*.template
```

## 🔄 MIGRATION FROM EXISTING SECRETS

### Immediate Actions Required
1. **Remove `.secrets` from git tracking**:
   ```bash
   git rm --cached .secrets
   ```

2. **Move to secure location**:
   ```bash
   mv .secrets config/environments/secrets/.secrets.local
   ```

3. **Update code references**:
   ```python
   # Change from reading .secrets to environment variables
   from core.config import get_settings
   settings = get_settings()
   ```

## 📞 CONTACT INFORMATION POLICY

### Public Contact Information
Use ONLY business contact information in public-facing materials:

**✅ APPROVED PUBLIC CONTACT:**
- Email: `cs@myhibachichef.com`
- Phone: `(916) 740-8768`
- Address: `Fremont, California` (city/state only)
- Service Areas: `Sacramento, Bay Area, Central Valley`

**❌ NEVER SHOW PUBLICLY:**
- Personal Gmail addresses
- Full street address
- EIN number
- Personal phone numbers

## 🏥 COMPLIANCE REQUIREMENTS

### RingCentral SMS Compliance
- Must have privacy policy with SMS terms
- Must have terms of service with STOP/START instructions
- Must include consent checkboxes on all forms
- Must link to privacy/terms from all pages

### GDPR/CCPA Compliance
- Encrypt all PII in database
- Use envelope encryption for sensitive data
- Implement data retention policies
- Provide data deletion capabilities

## 🚨 INCIDENT RESPONSE

### If Secrets Are Accidentally Committed:

1. **Immediate Actions**:
   ```bash
   # Remove from current commit
   git rm --cached filename
   git commit --amend
   
   # Force push (if not shared yet)
   git push --force
   ```

2. **If Already Pushed**:
   ```bash
   # Use BFG Repo-Cleaner for git history
   java -jar bfg.jar --delete-files .secrets
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

3. **Rotate All Exposed Secrets**:
   - Generate new API keys
   - Update all affected services
   - Monitor for unauthorized usage

## 🔍 AUDIT CHECKLIST

Before each commit, verify:
- [ ] No API keys in code
- [ ] No database passwords
- [ ] No personal information
- [ ] No full business address
- [ ] No EIN number
- [ ] All secrets in environment variables
- [ ] Templates contain no actual values

## 📖 TRAINING REQUIREMENTS

All developers must:
1. Read this policy before first commit
2. Use environment variables for all secrets
3. Never commit actual credentials
4. Understand PII encryption requirements
5. Know incident response procedures

## 📝 POLICY UPDATES

This policy will be updated as security requirements evolve. All team members will be notified of changes.

**Last Updated**: 2025-10-08
**Version**: 1.0
**Owner**: Security Team