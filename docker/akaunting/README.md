# Akaunting Integration for MyHibachi

## Overview

This directory contains the configuration and scripts for deploying
Akaunting as the accounting system for MyHibachi.

## Directory Structure

```
docker/akaunting/
├── docker-compose.yml       # Main Docker Compose configuration
├── .env.example            # Environment template
├── cloudflared-config.yml  # Updated tunnel config (reference)
├── install.sh              # VPS installation script
└── README.md               # This file
```

## Quick Start

### 1. VPS Upgrade (if not done)

Upgrade IONOS VPS from M to L (8GB RAM):

- Login: https://my.ionos.com/
- Server & Cloud → VPS → Upgrade → VPS Linux L

### 2. Copy Files to VPS

```powershell
# From your local machine
scp -r docker/akaunting/* root@108.175.12.154:/opt/akaunting/
```

### 3. Run Installation

```bash
ssh root@108.175.12.154
cd /opt/akaunting
chmod +x install.sh
./install.sh
```

### 4. Complete Setup Wizard

1. Open https://accounting.mysticdatanode.net
2. Follow the wizard
3. Create admin account
4. Create companies for each station

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       VPS                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Akaunting Stack (Port 9000)                      │  │
│  │  ├── akaunting-app      (Web UI + API)            │  │
│  │  ├── akaunting-redis    (Cache/Session)           │  │
│  │  ├── akaunting-scheduler (Cron jobs)              │  │
│  │  └── akaunting-queue    (Background jobs)         │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                               │
│  ┌───────────────────────┴───────────────────────────┐  │
│  │  PostgreSQL (localhost:5432)                       │  │
│  │  ├── myhibachi_production                         │  │
│  │  ├── myhibachi_staging                            │  │
│  │  └── akaunting                                    │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                               │
│  ┌───────────────────────┴───────────────────────────┐  │
│  │  FastAPI (Port 8000)                              │  │
│  │  └── services/accounting/                         │  │
│  │      ├── akaunting_client.py                      │  │
│  │      ├── invoice_sync_service.py                  │  │
│  │      ├── payment_sync_service.py                  │  │
│  │      ├── vendor_sync_service.py                   │  │
│  │      └── chef_payroll_service.py                  │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                               │
│  ┌───────────────────────┴───────────────────────────┐  │
│  │  Cloudflare Tunnel                                │  │
│  │  ├── mhapi.mysticdatanode.net → :8000             │  │
│  │  ├── accounting.mysticdatanode.net → :9000        │  │
│  │  └── ssh.mhapi.mysticdatanode.net → :22           │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Companies Setup

Create one company per station:

| Station Code   | Company Name        | Tax Rate   |
| -------------- | ------------------- | ---------- |
| AUS            | My Hibachi Austin   | 8.25% (TX) |
| DFW            | My Hibachi Dallas   | 8.25% (TX) |
| HOU            | My Hibachi Houston  | 8.25% (TX) |
| CA-FREMONT-001 | My Hibachi Bay Area | 9.25% (CA) |

## API Integration

### Get API Token

1. Login to Akaunting as admin
2. Settings → API
3. Create Personal Access Token
4. Copy token and save to Google Secret Manager:
   ```bash
   gcloud secrets create AKAUNTING_API_TOKEN --data-file=-
   ```

### FastAPI Configuration

Add to `apps/backend/src/core/config.py`:

```python
class Settings(BaseSettings):
    # Akaunting
    AKAUNTING_URL: str = "http://localhost:9000"
    AKAUNTING_API_TOKEN: str = ""
```

### Usage Example

```python
from services.accounting import AkauntingClient, InvoiceSyncService

# Create invoice for booking
async with InvoiceSyncService(db) as service:
    invoice = await service.create_invoice_for_booking(
        booking_id=booking.id,
        auto_send=True,
    )
```

## Database Schema

The integration uses the `accounting` schema in PostgreSQL:

- `accounting.company_mappings` - Station → Company
- `accounting.customer_mappings` - Customer → Contact
- `accounting.chef_vendor_mappings` - Chef → Vendor
- `accounting.invoice_mappings` - Booking → Invoice
- `accounting.payment_mappings` - Payment → Transaction
- `accounting.chef_payment_mappings` - Chef payroll tracking
- `accounting.sync_history` - Audit log

Run migration:

```bash
psql -U myhibachi_user -d myhibachi_production \
  -f database/migrations/BATCH_7A_ACCOUNTING_SCHEMA.sql
```

## Maintenance

### View Logs

```bash
docker-compose -f /opt/akaunting/docker-compose.yml logs -f
```

### Restart

```bash
docker-compose -f /opt/akaunting/docker-compose.yml restart
```

### Backup

```bash
# Database
pg_dump -U akaunting_user akaunting > /opt/akaunting/backups/akaunting_$(date +%Y%m%d).sql

# Files (uploads, logos)
tar -czf /opt/akaunting/backups/akaunting_files_$(date +%Y%m%d).tar.gz \
  /var/lib/docker/volumes/akaunting_akaunting_data \
  /var/lib/docker/volumes/akaunting_akaunting_uploads
```

### Update

```bash
cd /opt/akaunting
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### Container not starting

```bash
docker-compose logs akaunting
# Check for database connection errors
```

### Can't access via browser

```bash
# Check tunnel status
cloudflared tunnel list

# Check if route is configured
cat /etc/cloudflared/config.yml | grep accounting

# Restart tunnel
systemctl restart cloudflared
```

### Database connection issues

```bash
# Test connection from host
psql -U akaunting_user -d akaunting -c "SELECT 1;"

# Check pg_hba.conf allows Docker connections
```

## Security Notes

- Akaunting is behind Cloudflare (DDoS protection, WAF)
- Consider adding Cloudflare Access for admin protection
- Database password stored in .env (not in repo)
- API token in Google Secret Manager
