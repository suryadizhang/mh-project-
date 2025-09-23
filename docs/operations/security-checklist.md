# My Hibachi Security Checklist

## Server Security

### SSH Configuration
- [ ] SSH key-based authentication enabled
- [ ] Password authentication disabled
- [ ] Root login disabled
- [ ] SSH port changed from default (optional)
- [ ] SSH banner configured
- [ ] Failed login monitoring enabled

**Verification Commands:**
```bash
# Check SSH configuration
sudo sshd -T | grep -E "(passwordauthentication|permitrootlogin|pubkeyauthentication)"

# Review SSH logs
sudo journalctl -u ssh | tail -20
```

### Firewall Configuration
- [ ] UFW enabled and configured
- [ ] Only necessary ports open
- [ ] Default deny incoming rule
- [ ] Logging enabled

**Verification Commands:**
```bash
# Check firewall status
sudo ufw status verbose

# Review firewall logs
sudo tail -f /var/log/ufw.log
```

### System Security
- [ ] Automatic security updates enabled
- [ ] Fail2ban configured and running
- [ ] System packages up to date
- [ ] Unnecessary services disabled
- [ ] File permissions properly set

**Verification Commands:**
```bash
# Check system updates
sudo apt list --upgradable

# Check fail2ban status
sudo fail2ban-client status

# Check running services
sudo systemctl list-units --type=service --state=running
```

## Application Security

### Environment Variables
- [ ] All secrets stored in environment files
- [ ] Environment files have restricted permissions (600)
- [ ] No hardcoded secrets in code
- [ ] Regular secret rotation schedule

**Verification Commands:**
```bash
# Check environment file permissions
ls -la /opt/myhibachi/config/.env

# Verify no secrets in git history
git log --all --grep="password\|secret\|key" --oneline
```

### Database Security
- [ ] Database credentials are strong
- [ ] Database access restricted to application only
- [ ] Regular credential rotation
- [ ] Database encryption at rest (if supported)
- [ ] Connection encryption (SSL/TLS)

**Verification Commands:**
```bash
# Check database connections
docker compose exec postgres psql -U myhibachi -c "\conninfo"

# Verify database access restrictions
docker compose exec postgres psql -U myhibachi -c "SELECT * FROM pg_hba_file_rules;"
```

### API Security
- [ ] JWT secrets are strong (>32 characters)
- [ ] JWT tokens have appropriate expiration
- [ ] Rate limiting enabled and configured
- [ ] CORS properly configured
- [ ] Input validation implemented
- [ ] SQL injection protection verified

**Verification Commands:**
```bash
# Test rate limiting
curl -I http://localhost:8000/health
for i in {1..100}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health; done

# Check CORS configuration
curl -H "Origin: https://malicious-site.com" -H "Access-Control-Request-Method: POST" -X OPTIONS http://localhost:8000/api/bookings
```

### Authentication & Authorization
- [ ] Admin endpoints properly protected
- [ ] Role-based access control implemented
- [ ] Password policies enforced
- [ ] Account lockout mechanisms
- [ ] Session management secure

**Verification Commands:**
```bash
# Test admin endpoint protection
curl -X GET http://localhost:8000/admin/analytics

# Test authentication requirements
curl -X POST http://localhost:8000/api/bookings -d '{"test":"data"}'
```

## Infrastructure Security

### Docker Security
- [ ] Containers run as non-root users
- [ ] Resource limits configured
- [ ] Security profiles applied
- [ ] Regular image updates
- [ ] No privileged containers

**Verification Commands:**
```bash
# Check container users
docker compose exec fastapi-backend whoami

# Check container resource limits
docker stats --no-stream

# Check for privileged containers
docker inspect $(docker ps -q) | grep -i privileged
```

### Network Security
- [ ] SSL/TLS certificates valid and auto-renewing
- [ ] Strong cipher suites configured
- [ ] HSTS headers enabled
- [ ] Internal network isolation
- [ ] No unnecessary network exposure

**Verification Commands:**
```bash
# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com < /dev/null

# Test SSL configuration
curl -I https://yourdomain.com

# Check for SSL vulnerabilities
nmap --script ssl-enum-ciphers -p 443 yourdomain.com
```

### File System Security
- [ ] Proper file permissions set
- [ ] No world-writable files
- [ ] Log files protected
- [ ] Backup files secured
- [ ] Temporary files cleaned up

**Verification Commands:**
```bash
# Find world-writable files
find /opt/myhibachi -type f -perm -002 2>/dev/null

# Check log file permissions
ls -la /var/log/myhibachi/

# Check backup file permissions
ls -la /var/backups/myhibachi/
```

## Monitoring & Incident Response

### Logging & Monitoring
- [ ] Comprehensive logging enabled
- [ ] Log aggregation configured
- [ ] Security event monitoring
- [ ] Alerting system functional
- [ ] Log retention policy implemented

**Verification Commands:**
```bash
# Check log files
sudo journalctl -u myhibachi-health-monitor --since "1 hour ago"

# Verify monitoring is working
python3 ops/system_health_monitor.py --once

# Check log rotation
sudo logrotate -d /etc/logrotate.d/myhibachi
```

### Backup Security
- [ ] Backups encrypted
- [ ] Backup verification automated
- [ ] Offsite backup storage
- [ ] Backup access controls
- [ ] Recovery procedures tested

**Verification Commands:**
```bash
# Test backup creation
python3 ops/backup_db.py

# Verify backup integrity
python3 ops/backup_db.py --verify-only /var/backups/myhibachi/latest_backup.sql.gz

# Check backup permissions
ls -la /var/backups/myhibachi/
```

### Incident Response
- [ ] Incident response plan documented
- [ ] Emergency contacts list maintained
- [ ] Escalation procedures defined
- [ ] Communication plan established
- [ ] Post-incident review process

## Compliance & Auditing

### Data Protection
- [ ] Data encryption at rest
- [ ] Data encryption in transit
- [ ] Personal data handling compliance
- [ ] Data retention policies
- [ ] Data access logging

### Security Auditing
- [ ] Regular security assessments
- [ ] Vulnerability scanning
- [ ] Penetration testing
- [ ] Code security reviews
- [ ] Dependency vulnerability checks

**Verification Commands:**
```bash
# Check for vulnerable dependencies
docker compose exec fastapi-backend pip-audit

# Scan for common vulnerabilities
docker run --rm -v /opt/myhibachi/app:/code clair-scanner:latest /code
```

## Monthly Security Review Checklist

### Review Actions
- [ ] Review and rotate secrets
- [ ] Update system packages
- [ ] Review user access and permissions
- [ ] Analyze security logs
- [ ] Test backup and recovery procedures
- [ ] Review firewall rules
- [ ] Update security documentation

### Metrics to Review
- [ ] Failed login attempts
- [ ] Rate limiting triggers
- [ ] SSL certificate expiration dates
- [ ] System resource usage patterns
- [ ] Error rates and types
- [ ] Response time trends

### Security Tests
- [ ] Attempt unauthorized API access
- [ ] Test rate limiting effectiveness
- [ ] Verify CORS configuration
- [ ] Test SSL/TLS configuration
- [ ] Simulate security incidents

## Security Incident Response

### Immediate Response (0-1 hour)
1. **Isolate affected systems**
   ```bash
   # Block suspicious IPs
   sudo ufw deny from <suspicious-ip>
   
   # Stop affected services if necessary
   docker compose stop <affected-service>
   ```

2. **Assess impact**
   ```bash
   # Check system health
   python3 ops/system_health_monitor.py --once
   
   # Review recent logs
   sudo journalctl --since "1 hour ago" | grep -i "error\|fail\|attack"
   ```

3. **Document incident**
   - Time of detection
   - Affected systems
   - Initial assessment
   - Actions taken

### Short-term Response (1-24 hours)
1. **Detailed investigation**
2. **Implement containment measures**
3. **Notify stakeholders**
4. **Begin recovery procedures**

### Long-term Response (1-7 days)
1. **Root cause analysis**
2. **Implement fixes**
3. **Update security measures**
4. **Post-incident review**
5. **Update documentation**

## Emergency Contacts

### Internal Team
- **System Administrator**: [contact info]
- **Development Team Lead**: [contact info]
- **Security Officer**: [contact info]

### External Services
- **Hosting Provider**: [contact info]
- **SSL Certificate Provider**: [contact info]
- **Domain Registrar**: [contact info]
- **Security Consultant**: [contact info]

## Security Tools and Resources

### Recommended Tools
- **Vulnerability Scanning**: OpenVAS, Nessus
- **Log Analysis**: ELK Stack, Splunk
- **Network Monitoring**: Wireshark, ntopng
- **Security Testing**: OWASP ZAP, Burp Suite

### Security References
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CIS Controls**: https://www.cisecurity.org/controls/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **Ubuntu Security**: https://ubuntu.com/security

---

**Last Updated**: [Date]
**Review Schedule**: Monthly
**Next Review**: [Date]