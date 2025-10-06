# SSL Configuration Template for Production Deployment

## Plesk VPS SSL Configuration

### 1. Automatic SSL (Let's Encrypt)
- Enable in Plesk panel: Websites & Domains → SSL/TLS Certificates
- Select "Let's Encrypt" option
- Domains: api.yourdomain.com, ai-api.yourdomain.com

### 2. Custom SSL Certificate
- Upload certificate files in Plesk panel
- Configure automatic renewal

### 3. SSL Redirect Configuration
```nginx
# Force HTTPS redirect (automatically configured in Plesk)
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Vercel SSL Configuration

### Automatic SSL
- Vercel automatically provides SSL certificates
- Enable in project settings → Domains
- Configure custom domains with automatic SSL

### Environment Variables for SSL
```env
# Production environment variables
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_AI_API_URL=https://ai-api.yourdomain.com
NEXT_PUBLIC_APP_URL=https://yourdomain.com
```

## Security Headers Configuration

Already configured in Next.js applications:
- Strict-Transport-Security
- X-Frame-Options
- X-Content-Type-Options
- Content-Security-Policy

## SSL Verification Commands

```bash
# Test SSL configuration
curl -I https://api.yourdomain.com/health
curl -I https://ai-api.yourdomain.com/health
curl -I https://yourdomain.com

# Check SSL certificate
openssl s_client -connect api.yourdomain.com:443 -servername api.yourdomain.com
```