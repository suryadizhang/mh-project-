#!/bin/bash
# MyHibachi Health Check Monitoring Script
# Location: /usr/local/bin/check_myhibachi_health.sh
# 
# This script monitors all backend instances and sends email alerts
# if any instance is unhealthy. It also attempts automatic restarts.
# 
# Setup:
#   1. Copy to /usr/local/bin/check_myhibachi_health.sh
#   2. chmod +x /usr/local/bin/check_myhibachi_health.sh
#   3. Add to crontab: */5 * * * * /usr/local/bin/check_myhibachi_health.sh
# 
# Prerequisites:
#   - mailutils or sendmail installed for email alerts
#   - Systemd services running

set -u  # Exit on undefined variable

# Configuration
BACKENDS=(8001 8002 8003)
ALERT_EMAIL="ops@myhibachi.com"  # CHANGE THIS
LOG_FILE="/var/log/myhibachi-health-check.log"
HEALTH_TIMEOUT=5  # seconds
MAX_LOG_SIZE=10485760  # 10MB

# Ensure log file exists
touch "$LOG_FILE"

# Rotate log if too large
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE") -gt $MAX_LOG_SIZE ]; then
    mv "$LOG_FILE" "$LOG_FILE.old"
    touch "$LOG_FILE"
fi

# Check if email is configured
send_email() {
    local subject="$1"
    local body="$2"
    
    if command -v mail &> /dev/null; then
        echo "$body" | mail -s "$subject" "$ALERT_EMAIL"
    elif command -v sendmail &> /dev/null; then
        echo -e "Subject: $subject\n\n$body" | sendmail "$ALERT_EMAIL"
    else
        echo "[$(date)] WARNING: Cannot send email - mailutils/sendmail not installed" >> "$LOG_FILE"
    fi
}

# Check each backend instance
all_healthy=true

for port in "${BACKENDS[@]}"; do
    # Calculate instance number (1, 2, 3) from port (8001, 8002, 8003)
    instance_num="${port:3:1}"
    
    # Perform health check
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$HEALTH_TIMEOUT" "http://127.0.0.1:$port/health" 2>/dev/null || echo "000")
    
    if [ "$response" != "200" ]; then
        # Instance is unhealthy
        all_healthy=false
        
        echo "[$(date)] ALERT: Backend on port $port is DOWN (HTTP $response)" >> "$LOG_FILE"
        
        # Check if service is actually running
        service_status=$(systemctl is-active "myhibachi-backend@$instance_num.service")
        
        # Send email alert
        send_email "CRITICAL: MyHibachi Backend Down (Port $port)" \
"Backend instance on port $port is not responding.

Details:
- Port: $port
- Instance: myhibachi-backend@$instance_num.service
- HTTP Response: $response
- Service Status: $service_status
- Timestamp: $(date)

Action taken: Attempting automatic restart...

Please investigate if problem persists.
"
        
        # Attempt automatic restart
        echo "[$(date)] Attempting restart of myhibachi-backend@$instance_num.service" >> "$LOG_FILE"
        systemctl restart "myhibachi-backend@$instance_num.service"
        
        # Wait a bit for service to start
        sleep 5
        
        # Check if restart was successful
        restart_response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$HEALTH_TIMEOUT" "http://127.0.0.1:$port/health" 2>/dev/null || echo "000")
        
        if [ "$restart_response" == "200" ]; then
            echo "[$(date)] SUCCESS: Backend@$instance_num restarted successfully" >> "$LOG_FILE"
            send_email "RESOLVED: MyHibachi Backend Recovered (Port $port)" \
"Backend instance on port $port has been automatically restarted and is now healthy.

Details:
- Port: $port
- Instance: myhibachi-backend@$instance_num.service
- HTTP Response: $restart_response (healthy)
- Recovery Time: $(date)

No further action required.
"
        else
            echo "[$(date)] FAILED: Backend@$instance_num restart failed (HTTP $restart_response)" >> "$LOG_FILE"
            send_email "URGENT: MyHibachi Backend Restart Failed (Port $port)" \
"Automatic restart of backend instance on port $port FAILED.

Details:
- Port: $port
- Instance: myhibachi-backend@$instance_num.service
- HTTP Response after restart: $restart_response
- Timestamp: $(date)

MANUAL INTERVENTION REQUIRED!

Troubleshooting steps:
1. Check logs: journalctl -u myhibachi-backend@$instance_num.service -n 50
2. Check if port is in use: lsof -i :$port
3. Check database connectivity
4. Check disk space: df -h
5. Check memory: free -h

Service may be in failed state. Manual restart may be needed.
"
        fi
    else
        # Instance is healthy
        echo "[$(date)] Backend on port $port is healthy (HTTP $response)" >> "$LOG_FILE"
    fi
done

# Summary
if [ "$all_healthy" = true ]; then
    echo "[$(date)] All backend instances are healthy ✓" >> "$LOG_FILE"
else
    echo "[$(date)] One or more backend instances are unhealthy!" >> "$LOG_FILE"
fi

# Add separator for readability
echo "---" >> "$LOG_FILE"
