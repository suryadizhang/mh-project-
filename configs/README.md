# MyHibachi Nginx Load Balancer Configuration Files

This directory contains all configuration files needed to deploy the
Nginx load balancer on your Plesk VPS.

## 📁 Directory Structure

```
configs/
├── nginx/
│   ├── myhibachi-upstream.conf       # Upstream backend pool configuration
│   └── vhost_nginx.conf              # Virtual host configuration
├── systemd/
│   └── myhibachi-backend@.service    # Systemd service template
├── scripts/
│   ├── deploy_myhibachi.sh           # Zero-downtime deployment script
│   └── check_myhibachi_health.sh     # Health monitoring script
└── README.md                         # This file
```

## 🚀 Deployment Instructions

### **1. Copy Nginx Configuration Files**

```bash
# Copy upstream configuration
sudo cp configs/nginx/myhibachi-upstream.conf /etc/nginx/conf.d/

# Copy vhost configuration
sudo cp configs/nginx/vhost_nginx.conf /var/www/vhosts/myhibachi.com/conf/

# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

### **2. Install Systemd Service**

```bash
# Copy service template
sudo cp configs/systemd/myhibachi-backend@.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable myhibachi-backend@1.service
sudo systemctl enable myhibachi-backend@2.service
sudo systemctl enable myhibachi-backend@3.service

# Start services
sudo systemctl start myhibachi-backend@1.service
sudo systemctl start myhibachi-backend@2.service
sudo systemctl start myhibachi-backend@3.service

# Check status
sudo systemctl status myhibachi-backend@*.service
```

### **3. Install Deployment Script**

```bash
# Copy deployment script
sudo cp configs/scripts/deploy_myhibachi.sh /usr/local/bin/

# Make executable
sudo chmod +x /usr/local/bin/deploy_myhibachi.sh

# Test deployment
sudo /usr/local/bin/deploy_myhibachi.sh
```

### **4. Install Health Check Script**

```bash
# Copy health check script
sudo cp configs/scripts/check_myhibachi_health.sh /usr/local/bin/

# Make executable
sudo chmod +x /usr/local/bin/check_myhibachi_health.sh

# Edit email address in script
sudo nano /usr/local/bin/check_myhibachi_health.sh
# Change: ALERT_EMAIL="ops@myhibachi.com" to your email

# Test health check manually
sudo /usr/local/bin/check_myhibachi_health.sh

# Check log output
tail /var/log/myhibachi-health-check.log

# Add to crontab (run every 5 minutes)
sudo crontab -e
# Add line:
# */5 * * * * /usr/local/bin/check_myhibachi_health.sh
```

## ✅ Verification Checklist

After deployment, verify everything is working:

### **1. Check Backend Instances**

```bash
# All should return HTTP 200
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8003/health
```

### **2. Check Nginx Load Balancer**

```bash
# Should return HTTP 200
curl https://myhibachichef.com/health

# Check which backend served request
curl -I https://myhibachichef.com/health | grep X-Backend-Server

# Make 30 requests and verify distribution
for i in {1..30}; do
  curl -s -I https://myhibachichef.com/health | grep X-Backend-Server
done | sort | uniq -c
```

### **3. Check SSL Certificate**

```bash
# Should show Let's Encrypt certificate
curl -vI https://myhibachichef.com 2>&1 | grep -A 10 "SSL certificate"

# Or use online tool:
# https://www.ssllabs.com/ssltest/analyze.html?d=myhibachichef.com
```

### **4. Check Systemd Services**

```bash
# All should show "active (running)"
systemctl status myhibachi-backend@1.service
systemctl status myhibachi-backend@2.service
systemctl status myhibachi-backend@3.service
```

### **5. Check Logs**

```bash
# Nginx access logs
tail -f /var/www/vhosts/myhibachi.com/logs/access_ssl_log

# Nginx error logs
tail -f /var/www/vhosts/myhibachi.com/logs/error_log

# Backend application logs (systemd journal)
journalctl -u myhibachi-backend@1.service -f
journalctl -u myhibachi-backend@2.service -f
journalctl -u myhibachi-backend@3.service -f

# Health check logs
tail -f /var/log/myhibachi-health-check.log
```

## 🔧 Customization

### **Adjusting Backend Pool**

Edit `configs/nginx/myhibachi-upstream.conf`:

```nginx
# Add more instances:
server 127.0.0.1:8004 max_fails=2 fail_timeout=30s weight=1 backup;

# Change load balancing algorithm:
ip_hash;  # Sticky sessions based on client IP

# Adjust health check parameters:
max_fails=3;  # Mark unhealthy after 3 failures
fail_timeout=60s;  # Keep marked unhealthy for 60 seconds
```

### **Adjusting Resource Limits**

Edit `configs/systemd/myhibachi-backend@.service`:

```ini
# Increase memory limit
MemoryLimit=2G

# Increase CPU quota
CPUQuota=100%  # 100% of 1 core = full core

# Increase workers per instance
Environment="WORKERS=4"
```

### **Adjusting Health Check Frequency**

Edit crontab:

```bash
# Check every minute (instead of 5 minutes)
* * * * * /usr/local/bin/check_myhibachi_health.sh

# Check every 10 minutes
*/10 * * * * /usr/local/bin/check_myhibachi_health.sh
```

## 🐛 Troubleshooting

### **Backend Not Starting**

```bash
# Check service status
systemctl status myhibachi-backend@1.service

# View full logs
journalctl -u myhibachi-backend@1.service -n 100 --no-pager

# Check if port is in use
lsof -i :8001

# Check Python virtual environment
ls -la /var/www/vhosts/myhibachi.com/backend/.venv/bin/uvicorn
```

### **Nginx Configuration Error**

```bash
# Test configuration
nginx -t

# View detailed error
nginx -T 2>&1 | less

# Check syntax of specific file
nginx -t -c /etc/nginx/conf.d/myhibachi-upstream.conf
```

### **Load Balancer Not Distributing**

```bash
# Check upstream status (if nginx_upstream_check_module available)
curl http://localhost/nginx_status

# Check Nginx error log
tail -100 /var/www/vhosts/myhibachi.com/logs/error_log

# Verify upstream configuration loaded
nginx -T | grep -A 20 "upstream myhibachi_backend"
```

### **Health Checks Failing**

```bash
# Test health endpoint directly
curl -v http://127.0.0.1:8001/health

# Check database connectivity
sudo -u postgres psql -c "SELECT 1;"

# Check Redis connectivity
redis-cli ping

# Check disk space
df -h

# Check memory
free -h
```

## 📊 Performance Tuning

### **Nginx Worker Processes**

Edit `/etc/nginx/nginx.conf`:

```nginx
# Set to number of CPU cores
worker_processes auto;

# Increase worker connections
events {
    worker_connections 4096;
    use epoll;  # Linux-optimized event model
}
```

### **Backend Instance Tuning**

For higher throughput, adjust workers and resource limits:

```ini
# In myhibachi-backend@.service
Environment="WORKERS=4"  # More workers per instance
MemoryLimit=2G  # More memory
CPUQuota=100%  # Full CPU core
```

## 📚 Additional Resources

- [MEDIUM_31_LOAD_BALANCER_COMPLETE.md](../MEDIUM_31_LOAD_BALANCER_COMPLETE.md) -
  Full implementation guide
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Plesk Documentation](https://docs.plesk.com/)

## 🆘 Support

If you encounter issues:

1. Check logs first (Nginx, systemd journal, health check log)
2. Verify all configuration files are in correct locations
3. Test each component individually (backend → Nginx → SSL)
4. Review `MEDIUM_31_LOAD_BALANCER_COMPLETE.md` for detailed
   troubleshooting

---

_Last Updated: January 15, 2025_
