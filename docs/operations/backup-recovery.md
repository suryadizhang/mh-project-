# My Hibachi Backup and Recovery Procedures

## Overview

This document outlines comprehensive backup and recovery procedures for the My Hibachi application stack, including databases, application files, configurations, and system state.

## Backup Strategy

### Backup Types

1. **Database Backups** (Critical)
   - PostgreSQL dumps with compression
   - Daily automated backups
   - Point-in-time recovery capability
   - Retention: 30 days local, 90 days cloud

2. **Application Backups** (Important)
   - Source code and configurations
   - User-uploaded files
   - SSL certificates
   - Weekly automated backups

3. **System Backups** (Important)
   - System configurations
   - Docker volumes
   - Log files
   - Monthly automated backups

4. **Configuration Backups** (Critical)
   - Environment variables
   - Docker compose files
   - Nginx configurations
   - Daily automated backups

### Backup Locations

1. **Local Storage**: `/var/backups/myhibachi/`
2. **Cloud Storage**: AWS S3 bucket (encrypted)
3. **Offsite Storage**: Secondary cloud provider (optional)

## Database Backup Procedures

### Automated Daily Backups

The system automatically creates database backups using the `backup_db.py` script via systemd timer.

**Backup Process:**
```bash
# Manual backup execution
cd /opt/myhibachi/app
python3 ops/backup_db.py

# Check backup status
sudo systemctl status myhibachi-backup.timer
sudo journalctl -u myhibachi-backup.service -f
```

**Backup Files Location:**
```
/var/backups/myhibachi/
├── myhibachi_backup_20240115_030000.sql.gz
├── myhibachi_backup_20240114_030000.sql.gz
└── ...
```

### Manual Database Backup

```bash
# Switch to myhibachi user
sudo su - myhibachi

# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/var/backups/myhibachi/myhibachi_manual_${TIMESTAMP}.sql"

# Create backup using pg_dump
docker compose exec postgres pg_dump \
    -h localhost \
    -U myhibachi \
    -d myhibachi \
    --format=custom \
    --verbose \
    --file=/backups/$(basename $BACKUP_FILE)

# Compress backup
gzip $BACKUP_FILE

# Verify backup
python3 ops/backup_db.py --verify-only ${BACKUP_FILE}.gz
```

### Point-in-Time Recovery Setup

```bash
# Enable WAL archiving in PostgreSQL
docker compose exec postgres psql -U myhibachi -d myhibachi -c "
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'cp %p /backups/wal/%f';
"

# Restart PostgreSQL
docker compose restart postgres

# Create WAL archive directory
mkdir -p /var/backups/myhibachi/wal
chmod 750 /var/backups/myhibachi/wal
```

## Database Recovery Procedures

### Full Database Restore

1. **Stop Application Services**
   ```bash
   # Stop application containers
   docker compose stop fastapi-backend myhibachi-frontend myhibachi-ai-backend
   ```

2. **Backup Current Database** (if possible)
   ```bash
   # Create backup of current state before restore
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   docker compose exec postgres pg_dump \
       -U myhibachi \
       -d myhibachi \
       --format=custom \
       --file=/backups/pre_restore_backup_${TIMESTAMP}.sql
   ```

3. **Drop and Recreate Database**
   ```bash
   # Connect to PostgreSQL
   docker compose exec postgres psql -U postgres

   # Drop and recreate database
   DROP DATABASE IF EXISTS myhibachi;
   CREATE DATABASE myhibachi OWNER myhibachi;
   \q
   ```

4. **Restore from Backup**
   ```bash
   # Decompress backup if needed
   gunzip /var/backups/myhibachi/myhibachi_backup_YYYYMMDD_HHMMSS.sql.gz

   # Restore database
   docker compose exec postgres pg_restore \
       -U myhibachi \
       -d myhibachi \
       --verbose \
       --clean \
       --if-exists \
       /backups/myhibachi_backup_YYYYMMDD_HHMMSS.sql
   ```

5. **Verify Restore**
   ```bash
   # Check database connectivity
   docker compose exec postgres psql -U myhibachi -d myhibachi -c "\dt"

   # Verify data integrity
   docker compose exec postgres psql -U myhibachi -d myhibachi -c "
   SELECT COUNT(*) FROM bookings;
   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM waitlist;
   "
   ```

6. **Start Application Services**
   ```bash
   # Start application
   docker compose start fastapi-backend myhibachi-frontend myhibachi-ai-backend

   # Verify application health
   python3 ops/system_health_monitor.py --once
   ```

### Point-in-Time Recovery

```bash
# Stop PostgreSQL
docker compose stop postgres

# Restore base backup
docker compose exec postgres pg_restore \
    -U postgres \
    --clean \
    --if-exists \
    /backups/base_backup_YYYYMMDD.sql

# Apply WAL files up to specific time
docker compose exec postgres pg_ctl start -D /var/lib/postgresql/data

# Connect and set recovery target
docker compose exec postgres psql -U postgres -c "
SELECT pg_create_restore_point('before_recovery');
"

# Note: Full PITR setup requires more complex configuration
# Consider PostgreSQL streaming replication for production
```

## Application File Backups

### Configuration Files Backup

```bash
# Create configuration backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/myhibachi/config_${TIMESTAMP}"

mkdir -p $BACKUP_DIR

# Backup environment files
cp /opt/myhibachi/config/.env $BACKUP_DIR/
cp /opt/myhibachi/app/docker-compose.prod.yml $BACKUP_DIR/

# Backup Nginx configuration
sudo cp -r /etc/nginx/sites-available $BACKUP_DIR/nginx/
sudo cp -r /etc/ssl/certs $BACKUP_DIR/ssl/

# Backup systemd service files
cp /etc/systemd/system/myhibachi-*.service $BACKUP_DIR/systemd/
cp /etc/systemd/system/myhibachi-*.timer $BACKUP_DIR/systemd/

# Create archive
tar -czf "${BACKUP_DIR}.tar.gz" -C /var/backups/myhibachi config_${TIMESTAMP}/
rm -rf $BACKUP_DIR
```

### Application Code Backup

```bash
# Backup application code (if not using git)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar -czf "/var/backups/myhibachi/app_code_${TIMESTAMP}.tar.gz" \
    -C /opt/myhibachi \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git' \
    app/
```

### Docker Volumes Backup

```bash
# Backup named volumes
docker run --rm \
    -v myhibachi_postgres_data:/source \
    -v /var/backups/myhibachi:/backup \
    alpine \
    tar -czf /backup/postgres_volume_$(date +%Y%m%d_%H%M%S).tar.gz -C /source .

docker run --rm \
    -v myhibachi_redis_data:/source \
    -v /var/backups/myhibachi:/backup \
    alpine \
    tar -czf /backup/redis_volume_$(date +%Y%m%d_%H%M%S).tar.gz -C /source .
```

## Recovery Testing

### Monthly Recovery Test

```bash
#!/bin/bash
# Monthly recovery test script

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_DIR="/tmp/recovery_test_${TIMESTAMP}"
LOG_FILE="/var/log/myhibachi/recovery_test_${TIMESTAMP}.log"

mkdir -p $TEST_DIR
exec > >(tee -a $LOG_FILE)
exec 2>&1

echo "Starting recovery test at $(date)"

# 1. Create test backup
echo "Creating test backup..."
python3 ops/backup_db.py --no-s3

# 2. Find latest backup
LATEST_BACKUP=$(ls -t /var/backups/myhibachi/myhibachi_backup_*.sql.gz | head -1)
echo "Using backup: $LATEST_BACKUP"

# 3. Create test environment
echo "Setting up test environment..."
cd $TEST_DIR
cp /opt/myhibachi/app/docker-compose.prod.yml docker-compose.test.yml

# Modify for test (different ports, database name)
sed -i 's/5432:5432/5433:5432/' docker-compose.test.yml
sed -i 's/myhibachi/myhibachi_test/g' docker-compose.test.yml

# 4. Start test database
echo "Starting test database..."
docker compose -f docker-compose.test.yml up -d postgres

# Wait for database to be ready
sleep 30

# 5. Restore backup to test database
echo "Restoring backup..."
gunzip -c $LATEST_BACKUP > test_backup.sql
docker compose -f docker-compose.test.yml exec postgres createdb -U postgres myhibachi_test
docker compose -f docker-compose.test.yml exec postgres pg_restore \
    -U postgres \
    -d myhibachi_test \
    test_backup.sql

# 6. Verify restore
echo "Verifying restore..."
RECORD_COUNT=$(docker compose -f docker-compose.test.yml exec postgres psql \
    -U postgres \
    -d myhibachi_test \
    -t -c "SELECT COUNT(*) FROM bookings;")

echo "Records in test database: $RECORD_COUNT"

# 7. Cleanup
echo "Cleaning up test environment..."
docker compose -f docker-compose.test.yml down -v
rm -rf $TEST_DIR

echo "Recovery test completed at $(date)"
echo "Test result: $([ $RECORD_COUNT -gt 0 ] && echo 'PASSED' || echo 'FAILED')"
```

## Disaster Recovery Scenarios

### Scenario 1: Database Corruption

**Symptoms:**
- Database connection errors
- Data inconsistency
- Application crashes

**Recovery Steps:**
1. Stop application immediately
2. Assess corruption extent
3. Restore from latest backup
4. Verify data integrity
5. Restart application
6. Monitor for issues

**Recovery Time**: 15-30 minutes
**Data Loss**: Up to 24 hours (since last backup)

### Scenario 2: Complete Server Failure

**Symptoms:**
- Server unresponsive
- Hardware failure
- OS corruption

**Recovery Steps:**
1. Provision new server
2. Install required software
3. Restore configurations from backup
4. Restore database from cloud backup
5. Deploy application
6. Update DNS if needed

**Recovery Time**: 2-4 hours
**Data Loss**: Up to 24 hours

### Scenario 3: Security Breach

**Symptoms:**
- Unauthorized access detected
- Data modification
- Suspicious activities

**Recovery Steps:**
1. Isolate affected systems
2. Assess damage extent
3. Restore from clean backup (before breach)
4. Apply security patches
5. Change all credentials
6. Implement additional security measures

**Recovery Time**: 4-8 hours
**Data Loss**: Variable (depends on breach timeline)

## Backup Monitoring and Alerting

### Backup Health Checks

```bash
# Add to system_health_monitor.py
def check_backup_health():
    """Check backup system health"""
    alerts = []
    
    # Check recent backups
    backup_dir = Path("/var/backups/myhibachi")
    recent_backups = list(backup_dir.glob("myhibachi_backup_*.sql.gz"))
    recent_backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not recent_backups:
        alerts.append("No database backups found")
    else:
        latest_backup = recent_backups[0]
        backup_age = time.time() - latest_backup.stat().st_mtime
        
        if backup_age > 86400 * 2:  # 2 days
            alerts.append(f"Latest backup is {backup_age/86400:.1f} days old")
            
        # Check backup size
        if latest_backup.stat().st_size < 1024:  # 1KB minimum
            alerts.append("Latest backup file is suspiciously small")
    
    return alerts
```

### Backup Verification Alerts

```bash
# Create backup verification cron job
sudo crontab -e

# Add line for daily backup verification
0 4 * * * /opt/myhibachi/venv/bin/python3 /opt/myhibachi/ops/backup_db.py --verify-only $(ls -t /var/backups/myhibachi/myhibachi_backup_*.sql.gz | head -1) || echo "Backup verification failed" | mail -s "Backup Alert" admin@yourdomain.com
```

## Cloud Backup Configuration

### AWS S3 Backup Setup

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Test S3 upload
aws s3 cp /var/backups/myhibachi/test_file.txt s3://your-backup-bucket/test/

# Configure backup script for S3
export AWS_S3_BUCKET=your-backup-bucket
export AWS_REGION=us-east-1
```

### Backup Encryption

```bash
# Encrypt backup before upload
gpg --symmetric --cipher-algo AES256 backup_file.sql.gz

# Upload encrypted backup
aws s3 cp backup_file.sql.gz.gpg s3://your-backup-bucket/encrypted/

# Decrypt for restore
gpg --decrypt backup_file.sql.gz.gpg > backup_file.sql.gz
```

## Maintenance and Best Practices

### Regular Maintenance Tasks

1. **Weekly**
   - Verify backup completion
   - Check backup file sizes
   - Test random backup restore
   - Clean up old local backups

2. **Monthly**
   - Full recovery test
   - Update backup procedures
   - Review retention policies
   - Test cloud backup access

3. **Quarterly**
   - Disaster recovery drill
   - Update recovery documentation
   - Review and test all scenarios
   - Update contact information

### Best Practices

1. **3-2-1 Backup Rule**
   - 3 copies of important data
   - 2 different storage types
   - 1 offsite backup

2. **Test Regularly**
   - Automate backup verification
   - Perform regular restore tests
   - Document all procedures
   - Train team members

3. **Monitor and Alert**
   - Set up backup monitoring
   - Configure failure alerts
   - Track backup metrics
   - Regular health checks

4. **Security**
   - Encrypt backups
   - Secure backup storage
   - Limit access permissions
   - Regular credential rotation

---

**Document Owner**: System Administrator
**Last Updated**: [Date]
**Review Schedule**: Quarterly
**Next Review**: [Date]