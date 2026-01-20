# 🔒 Cloudflare WAF Setup Guide

**MyHibachi Platform Security**

**Date:** November 14, 2025  
**Status:** Phase 1 - Week 1 - Day 1-2  
**Cost:** $0/month (Cloudflare Free Tier)

---

## 🎯 Objectives

1. Protect admin panel from unauthorized access and attacks
2. Protect customer site from DDoS, bots, and scraping
3. Ensure dynamic content (pricing, menu) flows through unaffected
4. Rate limit API endpoints to prevent abuse

---

## 📋 Prerequisites

- [ ] Domain DNS access (myhibachichef.com)
- [ ] Cloudflare account (free tier)
- [ ] Admin access to hosting provider
- [ ] Backup of current DNS settings

---

## 🚀 Step 1: Cloudflare Account Setup (30 minutes)

### 1.1 Create Cloudflare Account

```bash
# Go to: https://dash.cloudflare.com/sign-up
# Use business email: admin@myhibachichef.com
```

### 1.2 Add Site to Cloudflare

1. Click "Add a Site"
2. Enter: `myhibachichef.com`
3. Select: **Free Plan** ($0/month)
4. Click "Continue"

### 1.3 DNS Records Import

Cloudflare will scan your existing DNS records. Verify:

```yaml
Expected DNS Records:
  - myhibachichef.com → A record → Your server IP
  - www.myhibachichef.com → CNAME → myhibachichef.com
  - admin.mysticdatanode.net → A record → Your server IP
  - mhapi.mysticdatanode.net → A record → Your server IP (if separate)
```

**⚠️ IMPORTANT:**

- Orange cloud icon = Proxied through Cloudflare (WAF protection) ✅
- Grey cloud icon = DNS only (no protection) ❌

**Set to Proxied (Orange Cloud):**

- ✅ `myhibachichef.com`
- ✅ `www.myhibachichef.com`
- ✅ `admin.mysticdatanode.net`
- ✅ `mhapi.mysticdatanode.net`

### 1.4 Update Nameservers

Cloudflare will provide 2 nameservers:

```
ns1.cloudflare.com
ns2.cloudflare.com
```

**Update at your domain registrar** (e.g., GoDaddy, Namecheap):

1. Log into domain registrar
2. Find "Nameservers" or "DNS Management"
3. Replace existing nameservers with Cloudflare's
4. Save changes

**⏱️ Propagation Time:** 2-24 hours (usually ~2 hours)

### 1.5 Verify DNS Propagation

```bash
# Check nameservers (Windows PowerShell)
nslookup -type=NS myhibachichef.com

# Expected output:
# nameserver = ns1.cloudflare.com
# nameserver = ns2.cloudflare.com
```

---

## 🛡️ Step 2: SSL/TLS Configuration (15 minutes)

### 2.1 Enable Full (Strict) SSL

**Path:** SSL/TLS → Overview

**Select:** Full (strict)

- ✅ Encrypts traffic between users and Cloudflare
- ✅ Encrypts traffic between Cloudflare and your server
- ✅ Validates SSL certificate on your server

**⚠️ Requires:** Valid SSL certificate on your origin server

### 2.2 Always Use HTTPS

**Path:** SSL/TLS → Edge Certificates

**Enable:**

- ✅ Always Use HTTPS (redirect HTTP → HTTPS)
- ✅ Automatic HTTPS Rewrites
- ✅ Minimum TLS Version: TLS 1.2

### 2.3 HSTS (HTTP Strict Transport Security)

**Path:** SSL/TLS → Edge Certificates

**Enable HSTS:**

```yaml
Max Age: 12 months
Include Subdomains: Yes
Preload: Yes (after testing)
```

**⚠️ WARNING:** Start with 1 week for testing, then increase to 12
months

---

## 🔥 Step 3: WAF Rules for Admin Panel (2 hours)

### 3.1 Admin IP Whitelist Challenge

**Path:** Security → WAF → Custom Rules

**Rule 1: Challenge Unknown Admin IPs**

```yaml
Rule Name: Admin IP Challenge
If:
  - Hostname equals "admin.mysticdatanode.net"
  - IP Address is not in [YOUR_OFFICE_IPS]

Then:
  - Action: Managed Challenge (CAPTCHA)
```

**Add Your Office/Home IPs:**

```javascript
// Example IPs (replace with your actual IPs)
ip.src in {
  192.168.1.100  // Your office
  203.0.113.45   // Your home
  198.51.100.78  // Team member 1
}
```

**How to find your IP:**

```bash
# Visit: https://whatismyipaddress.com/
# Or PowerShell:
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

---

### 3.2 Admin Rate Limiting

**Path:** Security → WAF → Rate Limiting Rules

**Rule 2: Admin Login Rate Limit**

```yaml
Rule Name: Admin Login Protection
If:
  - Hostname equals "admin.mysticdatanode.net"
  - URI Path contains "/api/auth/login"

Then:
  - Requests: 5 per minute per IP
  - Action: Block for 10 minutes
  - Response: 429 Too Many Requests
```

**Rule 3: Admin API Rate Limit**

```yaml
Rule Name: Admin API General Rate Limit
If:
  - Hostname equals "admin.mysticdatanode.net"
  - URI Path starts with "/api/"

Then:
  - Requests: 100 per minute per IP
  - Action: Block for 5 minutes
```

---

### 3.3 Admin SQL Injection Protection

**Path:** Security → WAF → Managed Rules

**Enable:**

- ✅ Cloudflare Managed Ruleset
- ✅ Cloudflare OWASP Core Ruleset

**Custom Rule 4: SQL Injection Block**

```yaml
Rule Name: Admin SQL Injection Block
If:
  - Hostname equals "admin.mysticdatanode.net"
  - URI Query String contains "' OR '1'='1"
  - OR URI Query String contains "UNION SELECT"
  - OR URI Query String contains "DROP TABLE"
  - OR URI Query String contains "<script"

Then:
  - Action: Block
  - Log: Yes
```

---

### 3.4 Admin XSS Protection

**Rule 5: XSS Attack Block**

```yaml
Rule Name: Admin XSS Protection
If:
  - Hostname equals "admin.mysticdatanode.net"
  - URI contains "<script"
  - OR URI contains "javascript:"
  - OR URI contains "onerror="
  - OR URI contains "onload="

Then:
  - Action: Block
  - Log: Yes
```

---

## 🌐 Step 4: WAF Rules for Customer Site (2 hours)

### 4.1 DDoS Protection

**Path:** Security → DDoS

**Enable:**

- ✅ HTTP DDoS Attack Protection (Auto)
- ✅ Network-layer DDoS Attack Protection (Auto)

**Custom Rule 6: Customer API Rate Limit**

```yaml
Rule Name: Customer API Balanced Rate Limit
If:
  - Hostname equals "myhibachichef.com"
  - URI Path starts with "/api/"

Then:
  - Requests: 300 per minute per IP
  - Action: Challenge (not block)
  - Burst allowance: 50 requests
```

---

### 4.2 Bot Protection (Allow Good Bots)

**Path:** Security → Bots

**Settings:**

```yaml
Bot Fight Mode: Off (use custom rules instead)

Custom Rule 7: Bot Management
If:
  - Hostname equals "myhibachichef.com"
  - Bot Score less than 30 (likely bot)
  - AND NOT Bot Management (Verified Bot)
  - AND NOT User Agent contains "Googlebot"
  - AND NOT User Agent contains "Bingbot"
  - AND NOT User Agent contains "facebookexternalhit"

Then:
  - Action: Managed Challenge
```

**✅ Allowed Bots:**

- Googlebot (SEO)
- Bingbot (SEO)
- Facebook crawler (social sharing)
- Twitter crawler (social sharing)

---

### 4.3 Booking Form Protection

**Rule 8: Booking Submission Rate Limit**

```yaml
Rule Name: Booking Form Protection
If:
  - Hostname equals "myhibachichef.com"
  - URI Path equals "/api/bookings"
  - Method equals "POST"

Then:
  - Requests: 5 per hour per IP
  - Action: Challenge
  - Response: 'Please wait before submitting another booking'
```

---

### 4.4 Quote API Protection

**Rule 9: Quote Calculator Rate Limit**

```yaml
Rule Name: Quote API Protection
If:
  - Hostname equals "myhibachichef.com"
  - URI Path equals "/api/quote"
  - Method equals "POST"

Then:
  - Requests: 30 per minute per IP
  - Action: Challenge after limit
```

---

### 4.5 Contact Form Protection

**Rule 10: Contact Form Rate Limit**

```yaml
Rule Name: Contact Form Protection
If:
  - Hostname equals "myhibachichef.com"
  - URI Path equals "/api/contact"
  - Method equals "POST"

Then:
  - Requests: 3 submissions, then require CAPTCHA
  - Period: 1 hour
  - Action: Managed Challenge
```

---

## 🌍 Step 5: Geographic Protection (30 minutes)

### 5.1 Allow Primary Markets

**Path:** Security → WAF → Custom Rules

**Rule 11: Geographic Access Control**

```yaml
Rule Name: Geographic Protection
If:
  - Country is not in {US, CA} # USA, Canada
  - URI Path starts with "/api/"

Then:
  - Action: Managed Challenge (verify they're human)
  - Log: Yes
```

**✅ Always Allow:**

- United States (primary market)
- Canada (secondary market)

**⚠️ Challenge (Not Block):**

- All other countries (legitimate international customers can prove
  they're human)

---

## 📊 Step 6: Caching Configuration (1 hour)

### 6.1 Static Asset Caching

**Path:** Caching → Configuration

**Browser Cache TTL:** 4 hours  
**Cloudflare Cache TTL:** Respect existing headers

**Cache Everything for Static Assets:**

```yaml
Rule Name: Static Asset Cache
If:
  - File Extension is in {jpg, jpeg, png, gif, ico, css, js, woff,
    woff2, ttf}

Then:
  - Cache Level: Standard
  - Edge Cache TTL: 1 month
  - Browser Cache TTL: 1 week
```

---

### 6.2 API Response Caching (Optional)

**⚠️ IMPORTANT:** Only cache safe, public API responses

**DO NOT CACHE:**

- ❌ `/api/auth/*` (authentication)
- ❌ `/api/bookings/*` (user-specific data)
- ❌ `/api/admin/*` (admin data)

**SAFE TO CACHE:**

- ✅ `/api/menu` (menu items - public)
- ✅ `/api/pricing` (pricing - public)
- ✅ `/api/faqs` (FAQs - public)

**Rule 12: Public API Cache**

```yaml
Rule Name: Cache Public APIs
If:
  - URI Path matches regex "^/api/(menu|pricing|faqs)$"

Then:
  - Cache Level: Standard
  - Edge Cache TTL: 5 minutes
  - Browser Cache TTL: 1 minute
```

**✅ This ensures:**

- Dynamic pricing updates every 5 minutes on Cloudflare edge
- Dynamic menu updates every 5 minutes
- No stale data for more than 5 minutes

---

## 🔍 Step 7: Monitoring & Alerts (30 minutes)

### 7.1 Enable Security Analytics

**Path:** Analytics → Security

**Monitor:**

- WAF events (blocks, challenges)
- Rate limiting hits
- Bot traffic patterns
- DDoS attacks mitigated

### 7.2 Set Up Email Alerts

**Path:** Notifications → Add

**Create Alerts:**

```yaml
Alert 1: High Attack Volume
Trigger: More than 100 requests blocked in 5 minutes
Email: admin@myhibachichef.com

Alert 2: Rate Limit Exceeded
Trigger: Any rate limit rule triggers
Email: admin@myhibachichef.com

Alert 3: DDoS Attack
Trigger: DDoS protection engaged
Email: admin@myhibachichef.com, team@myhibachichef.com
```

---

## ✅ Step 8: Testing & Verification (2 hours)

### 8.1 Test Admin Panel Protection

**Test 1: IP Challenge**

```bash
# Access admin panel from unknown IP (use VPN or mobile data)
# Expected: Cloudflare CAPTCHA challenge
curl https://admin.mysticdatanode.net/
```

**Test 2: Rate Limiting**

```bash
# Attempt 10 login requests in 1 minute
for ($i=0; $i -lt 10; $i++) {
  curl -X POST https://admin.mysticdatanode.net/api/auth/login -d '{"email":"test@test.com","password":"test"}'
}

# Expected: First 5 succeed, next 5 blocked (429 Too Many Requests)
```

**Test 3: SQL Injection Block**

```bash
# Attempt SQL injection
curl "https://admin.mysticdatanode.net/api/users?id=1' OR '1'='1"

# Expected: 403 Forbidden (blocked by WAF)
```

---

### 8.2 Test Customer Site Protection

**Test 1: Quote API Rate Limit**

```bash
# Make 35 quote requests in 1 minute
for ($i=0; $i -lt 35; $i++) {
  curl -X POST https://myhibachichef.com/api/quote -d '{"adults":10,"children":2}'
}

# Expected: First 30 succeed, next 5 challenged
```

**Test 2: Bot Detection**

```bash
# Access with bot user agent
curl -A "BadBot/1.0" https://myhibachichef.com/

# Expected: Cloudflare challenge
```

**Test 3: Good Bot Allowed**

```bash
# Access with Googlebot user agent
curl -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" https://myhibachichef.com/

# Expected: 200 OK (no challenge)
```

---

### 8.3 Test Dynamic Content (CRITICAL)

**Test 1: Pricing API Flows Through**

```bash
# Get pricing
curl https://myhibachichef.com/api/pricing

# Expected: Current prices returned (not cached indefinitely)
```

**Test 2: Menu API Flows Through**

```bash
# Get menu
curl https://myhibachichef.com/api/menu

# Expected: Current menu returned
```

**Test 3: Admin Updates Reflected**

```bash
# 1. Admin updates price in dashboard
# 2. Wait 5 minutes (cache TTL)
# 3. Check customer site

# Expected: New prices visible after 5 minutes
```

**✅ Verification:** WAF inspects **requests** (blocks attacks), not
**responses** (API data flows through)

---

## 📋 Step 9: Documentation (30 minutes)

### 9.1 Record Configuration

**Create:** `CLOUDFLARE_CONFIG_BACKUP.txt`

```yaml
# Cloudflare Configuration Backup
# Date: November 14, 2025

DNS Records:
- myhibachichef.com → A → YOUR_SERVER_IP (Proxied)
- admin.mysticdatanode.net → A → YOUR_SERVER_IP (Proxied)
- www.myhibachichef.com → CNAME → myhibachichef.com (Proxied)

Nameservers:
- ns1.cloudflare.com
- ns2.cloudflare.com

SSL/TLS: Full (strict)
HSTS: Enabled (12 months)

WAF Rules: 12 total
- 5 Admin protection rules
- 5 Customer site rules
- 1 Geographic rule
- 1 Cache rule

Rate Limits:
- Admin login: 5/minute per IP
- Admin API: 100/minute per IP
- Customer API: 300/minute per IP
- Booking: 5/hour per IP
- Quote: 30/minute per IP
- Contact: 3 then CAPTCHA

Allowed IPs (Admin):
- 192.168.1.100 (Office)
- 203.0.113.45 (Home)
```

### 9.2 Create Runbook

**Create:** `CLOUDFLARE_RUNBOOK.md`

```markdown
# Cloudflare WAF Runbook

## Emergency: Site Down

1. Check Cloudflare status: https://www.cloudflarestatus.com/
2. Check DNS propagation: nslookup myhibachichef.com
3. Verify origin server responding: curl -H "Host: myhibachichef.com"
   http://YOUR_SERVER_IP
4. Disable Cloudflare proxy (grey cloud) if emergency

## Add New Admin IP

1. Go to: Security → WAF → Custom Rules
2. Edit: "Admin IP Challenge"
3. Add IP to allowlist
4. Save and deploy

## Adjust Rate Limits

1. Go to: Security → WAF → Rate Limiting Rules
2. Edit rule
3. Adjust "Requests per period"
4. Save and deploy

## View Attack Logs

1. Go to: Analytics → Security
2. Filter by: Blocked, Challenged
3. Export if needed

## Whitelist Legitimate User

1. Go to: Security → WAF → Tools
2. Enter IP or User Agent
3. Add to allowlist
4. Set expiration
```

---

## 🎉 Completion Checklist

### Phase 1 Deliverables:

- [ ] Cloudflare account configured (free tier)
- [ ] DNS pointed to Cloudflare (propagated)
- [ ] 12 WAF rules deployed (5 admin, 5 customer, 1 geo, 1 cache)
- [ ] Rate limiting configured (6 rules)
- [ ] SSL/TLS enabled (full strict mode)
- [ ] HSTS enabled (12 months)
- [ ] Email alerts configured (3 alerts)
- [ ] Testing completed (all 8 tests passing)
- [ ] Documentation created (config backup + runbook)
- [ ] This guide: `CLOUDFLARE_WAF_SETUP.md`

### Success Criteria:

- ✅ Admin panel protected with IP challenge
- ✅ Customer site protected from DDoS/bots
- ✅ Dynamic content flows through (no interference)
- ✅ Rate limits preventing abuse
- ✅ SSL/TLS with HSTS enabled
- ✅ Monitoring and alerts active
- ✅ $0/month cost maintained

---

## 🆘 Troubleshooting

### Issue: Site Not Loading After DNS Change

**Solution:**

1. DNS propagation takes 2-24 hours
2. Clear browser cache (Ctrl+Shift+Delete)
3. Flush DNS: `ipconfig /flushdns`
4. Check: https://dnschecker.org/

### Issue: Admin Can't Access Panel (Blocked)

**Solution:**

1. Add admin IP to whitelist (see Runbook)
2. Temporarily disable "Admin IP Challenge" rule
3. Use "Bypass" option in Cloudflare dashboard

### Issue: Customer API Returning Stale Data

**Solution:**

1. Purge cache: Caching → Configuration → Purge Everything
2. Reduce cache TTL to 1 minute for testing
3. Verify API response headers: `Cache-Control: no-cache`

### Issue: Too Many False Positives (Legitimate Users Blocked)

**Solution:**

1. Review: Analytics → Security → Firewall Events
2. Identify pattern (IP range, user agent, country)
3. Add exception rule above blocking rule
4. Monitor for 24 hours

### Issue: Rate Limit Too Strict

**Solution:**

1. Adjust "Requests per period" (increase)
2. Change action from "Block" to "Challenge"
3. Monitor legitimate user impact

---

## 📞 Support

**Cloudflare Free Tier Support:**

- Community Forum: https://community.cloudflare.com/
- Documentation: https://developers.cloudflare.com/
- Status Page: https://www.cloudflarestatus.com/

**MyHibachi Technical Support:**

- Email: tech@myhibachichef.com
- Emergency: +1 (916) 740-8768

---

**Next Phase:** Database Audit Logging (Week 1, Day 3-4)

**Estimated Time:** 6-8 hours total **Status:** ✅ Ready for Execution
